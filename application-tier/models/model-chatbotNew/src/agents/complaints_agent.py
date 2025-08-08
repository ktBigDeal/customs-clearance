"""
Complaints Agent Module

상담 사례 전문 에이전트 - 실무 민원상담 사례 검색 및 응답 생성 통합
"""

import logging
import openai
from typing import List, Dict, Any, Optional, Tuple
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ComplaintsMemory:
    """상담 사례 전용 대화 기록 관리 클래스"""
    
    def __init__(self, max_history: int = 12):
        """
        초기화
        
        Args:
            max_history (int): 최대 대화 기록 수 (상담사례는 맥락이 중요)
        """
        self.max_history = max_history
        self.messages = []
        self.case_context = []  # 참조된 상담 사례들
        self.search_history = []  # 상담 검색 기록
        self.user_patterns = {}  # 사용자 질문 패턴 분석
        
    def add_user_message(self, message: str, search_context: Optional[Dict] = None) -> None:
        """사용자 메시지 추가"""
        message_data = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if search_context:
            message_data["search_context"] = search_context
            self.search_history.append(search_context)
            
            # 사용자 패턴 분석
            self._analyze_user_patterns(message)
        
        self.messages.append(message_data)
        self._trim_history()
    
    def add_assistant_message(self, message: str, source_cases: List[Dict] = None) -> None:
        """어시스턴트 메시지 추가"""
        self.messages.append({
            "role": "assistant", 
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "source_cases": source_cases or []
        })
        
        # 참조된 상담 사례들을 컨텍스트에 추가
        if source_cases:
            for case in source_cases:
                if case not in self.case_context:
                    self.case_context.append(case)
        
        self._trim_history()
    
    def get_conversation_history(self, include_timestamps: bool = False) -> List[Dict]:
        """대화 기록 조회"""
        if include_timestamps:
            return self.messages.copy()
        else:
            return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def get_recent_context(self, num_turns: int = 3) -> List[Dict]:
        """최근 대화 컨텍스트 조회 (상담사례는 맥락이 중요)"""
        recent_messages = self.messages[-num_turns*2:] if self.messages else []
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    
    def get_user_patterns(self) -> Dict[str, Any]:
        """사용자 질문 패턴 분석 결과 반환"""
        return self.user_patterns.copy()
    
    def clear_history(self) -> None:
        """대화 기록 초기화"""
        self.messages.clear()
        self.case_context.clear()
        self.search_history.clear()
        self.user_patterns.clear()
    
    def _analyze_user_patterns(self, message: str) -> None:
        """사용자 질문 패턴 분석"""
        # 간단한 키워드 기반 패턴 분석
        keywords = {
            "통관": ["통관", "신고", "신고서", "세관"],
            "관세": ["관세", "세금", "면세", "감면"],
            "절차": ["절차", "방법", "어떻게", "해야"],
            "서류": ["서류", "문서", "증명서", "허가서"],
            "FTA": ["FTA", "원산지", "특혜관세"],
            "검역": ["검역", "검사", "승인"]
        }
        
        for category, words in keywords.items():
            for word in words:
                if word in message:
                    self.user_patterns[category] = self.user_patterns.get(category, 0) + 1
    
    def _trim_history(self) -> None:
        """대화 기록 크기 제한"""
        if len(self.messages) > self.max_history:
            # 시스템 메시지는 유지하고 오래된 대화만 제거
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            
            # 최근 대화만 유지
            trimmed_other = other_messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + trimmed_other


class ComplaintsRetriever:
    """상담 사례 검색 및 관련 데이터 추적 클래스 (통합)"""
    
    def __init__(self,
                 embedder=None,
                 vector_store=None,
                 query_normalizer=None,
                 collection_name: str = "consultation_collection"):
        """
        초기화 (LangChain 표준 사용)
        
        Args:
            embedder: LangChain 임베딩 생성기
            vector_store: LangChain 벡터 저장소
            query_normalizer: 쿼리 정규화기
            collection_name (str): 사용할 컬렉션 이름
        """
        from ..utils.embeddings import LangChainEmbedder
        from ..utils.db_connect import LangChainVectorStore
        from ..utils.query_normalizer import get_query_normalizer
        
        # 기본값 설정 (자동 초기화)
        if embedder is None:
            self.embedder = LangChainEmbedder()
        else:
            self.embedder = embedder
            
        if vector_store is None:
            self.vector_store = LangChainVectorStore(
                collection_name=collection_name,
                embedding_function=self.embedder.embeddings
            )
        else:
            self.vector_store = vector_store
            
        if query_normalizer is None:
            self.query_normalizer = get_query_normalizer("trade")
        else:
            self.query_normalizer = query_normalizer
            
        self.collection_name = collection_name
        
        # 내부 문서 캐시 (성능 최적화용)
        self._document_cache = {}
        
        logger.info(f"ComplaintsRetriever initialized with collection: {collection_name}")
    
    def search_consultation_cases(self, 
                                 raw_query: str, 
                                 top_k: int = 8,
                                 include_related: bool = True,
                                 expand_with_synonyms: bool = True,
                                 similarity_threshold: float = 0.0,
                                 filter_by: Optional[Dict[str, Any]] = None,
                                 search_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        상담 사례 검색
        
        Args:
            raw_query (str): 원본 사용자 질의
            top_k (int): 반환할 상위 결과 수
            include_related (bool): 관련 문서 포함 여부
            expand_with_synonyms (bool): 동의어 확장 사용 여부
            similarity_threshold (float): 유사도 임계값 (0.0-1.0)
            filter_by (Optional[Dict[str, Any]]): 필터링 조건
            search_context (Optional[Dict[str, Any]]): 에이전트별 검색 컨텍스트 힌트
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 리스트
        """
        try:
            from ..utils.query_normalizer import AdvancedQueryProcessor
            
            # 1. consultation_case 데이터만 검색하도록 필터 강제 설정
            if not filter_by:
                filter_by = {}
            filter_by["data_type"] = "consultation_case"
            
            # 2. LLM 기반 메타데이터 필터 생성
            llm_filters = self._generate_llm_metadata_filters(raw_query, search_context)
            
            # 3. 기존 필터와 LLM 필터 병합
            combined_filters = self._merge_filters(filter_by, llm_filters)
            
            if combined_filters:
                filter_by.update(combined_filters)
            
            # 4. 쿼리 정규화 및 확장
            normalized_query = self.query_normalizer.normalize(raw_query, search_context)
            if expand_with_synonyms:
                expanded_query = self.query_normalizer.expand_query_with_synonyms(normalized_query)
            else:
                expanded_query = normalized_query
            
            logger.info(f"🔍 Query: '{raw_query}' → '{expanded_query}'")
            logger.info(f"🏷️ LLM Filters: {llm_filters}")
            
            # 5. 검색 컨텍스트 기반 특별 처리
            query_processor = AdvancedQueryProcessor(self.query_normalizer)
            if search_context and search_context.get("domain_hints"):
                logger.info(f"🎯 검색 컨텍스트 적용: {search_context.get('domain_hints')}")
                context_keywords = search_context.get("boost_keywords", [])
                if context_keywords:
                    enhanced_query = f"{raw_query} {' '.join(context_keywords)}"
                    processed_query = query_processor.process_complex_query(enhanced_query)
                else:
                    processed_query = query_processor.process_complex_query(raw_query)
            else:
                processed_query = query_processor.process_complex_query(raw_query)
            
            # 6. 사용할 쿼리 결정
            if expand_with_synonyms:
                search_query = processed_query["expanded_query"]
            else:
                search_query = processed_query["normalized_query"]
            
            logger.info(f"🔍 검색 쿼리: {search_query}")
            
            # 7. 벡터 유사도 검색
            where_condition = self._build_where_condition(filter_by)
            
            primary_results = self.vector_store.search_similar(
                query_text=search_query,
                top_k=top_k,
                where=where_condition
            )
            logger.info(f"📊 벡터 검색 결과: {len(primary_results)}개")
            
            # 8. 관련 데이터 확장 검색
            if include_related:
                expanded_results = self._expand_with_related_cases(primary_results, top_k)
            else:
                expanded_results = primary_results
            
            # 9. 결과 후처리 및 정렬
            final_results = self._post_process_results(expanded_results, processed_query, search_context)
            
            # 10. 유사도 임계값 필터링
            if similarity_threshold > 0.0:
                filtered_results = [result for result in final_results 
                                  if result.get("similarity", 0) >= similarity_threshold]
                logger.info(f"🎯 유사도 임계값 {similarity_threshold}로 필터링: {len(final_results)} → {len(filtered_results)}개")
                final_results = filtered_results
            
            logger.info(f"✅ {len(final_results)}개 결과 반환 (요청된 top_k: {top_k})")
            return final_results
            
        except Exception as e:
            logger.error(f"상담 사례 검색 실패: {e}")
            return []
    
    def _expand_with_related_cases(self, results: List[Dict[str, Any]], max_total: int) -> List[Dict[str, Any]]:
        """관련 상담 사례로 검색 결과 확장"""
        expanded_results = results.copy()
        seen_ids = {result.get("id", "") for result in results}
        
        for result in results[:3]:
            metadata = result.get("metadata", {})
            
            # 카테고리 기반 확장
            category = metadata.get("category", "")
            if category:
                related_cases = self._search_related_by_category(category, 2)
                for related in related_cases:
                    if related.get("id", "") not in seen_ids:
                        related["reference_info"] = {"is_related": True, "related_to": result.get("id", "")}
                        expanded_results.append(related)
                        seen_ids.add(related.get("id", ""))
        
        return expanded_results[:max_total]
    
    def _search_related_by_category(self, category: str, top_k: int) -> List[Dict[str, Any]]:
        """카테고리 기반 관련 사례 검색"""
        try:
            query = f"{category} 상담 사례"
            where_condition = {"category": {"$eq": category}}
            
            results = self.vector_store.search_similar(
                query_text=query,
                top_k=top_k,
                where=where_condition
            )
            
            for result in results:
                result["match_type"] = "related_category"
                result["category_match"] = category
            
            return results
            
        except Exception as e:
            logger.error(f"카테고리별 관련 사례 검색 실패: {e}")
            return []
    
    def _build_where_condition(self, filter_by: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """필터링 조건 구성"""
        if not filter_by:
            return None
        
        supported_fields = [
            "category", "sub_category", "consultation_type", "case_number", "data_type",
            "data_source", "management_number", "keywords", "priority", "status"
        ]
        
        conditions = []
        for key, value in filter_by.items():
            if key in supported_fields:
                conditions.append({key: {"$eq": value}})
        
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}
    
    def _post_process_results(self, results: List[Dict[str, Any]], processed_query: Dict[str, Any], search_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """검색 결과 후처리"""
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        # 중요도 점수 계산 및 정렬
        for result in results:
            importance_score = self._calculate_importance_score(result, processed_query)
            result["importance_score"] = importance_score
            
            # search_context 기반 부스팅
            if search_context:
                context_boost = self._apply_search_context_boost(result, search_context)
                result["context_boost"] = context_boost
                result["importance_score"] += context_boost
        
        # 중요도와 유사도를 결합한 점수로 정렬
        results.sort(key=lambda x: (
            x.get("importance_score", 0) * thresholds["importance_weight"] + 
            x.get("similarity", 0) * thresholds["similarity_weight"]
        ), reverse=True)
        
        return results
    
    def _apply_search_context_boost(self, result: Dict[str, Any], search_context: Dict[str, Any]) -> float:
        """검색 컨텍스트 기반 부스팅 점수 계산"""
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        boost_score = 0.0
        metadata = result.get("metadata", {})
        content = result.get("content", "")
        
        # 우선순위 데이터 소스 부스팅
        priority_sources = search_context.get("priority_data_sources", [])
        data_source = metadata.get("data_source", "")
        if data_source in priority_sources:
            boost_score += 0.3
            result["boosted"] = True
            result["boost_reason"] = f"우선순위 데이터소스: {data_source}"
        
        # 도메인 힌트 키워드 매칭
        domain_hints = search_context.get("domain_hints", [])
        for hint in domain_hints:
            if hint in content.lower() or hint in str(metadata).lower():
                boost_score += 0.2
                result["boosted"] = True
                result["boost_reason"] = result.get("boost_reason", "") + f" 도메인매칭: {hint}"
        
        # 부스팅 키워드 매칭
        boost_keywords = search_context.get("boost_keywords", [])
        for keyword in boost_keywords:
            if keyword in content or keyword in str(metadata):
                boost_score += 0.1
        
        return min(boost_score, thresholds["boost_score_limit"])
    
    def _calculate_importance_score(self, result: Dict[str, Any], processed_query: Dict[str, Any]) -> float:
        """문서 중요도 점수 계산"""
        score = 0.0
        metadata = result.get("metadata", {})
        
        # 상담 사례 데이터 우선 처리
        data_source = metadata.get("data_source", "")
        if data_source == "상담사례DB":
            score += 0.5
            
            priority = metadata.get("priority", 0)
            case_type = metadata.get("consultation_type", "")
            
            try:
                priority_int = int(priority) if priority else 0
            except (ValueError, TypeError):
                priority_int = 0
            
            if priority_int >= 2:
                score += 0.2
            if case_type == "complex":
                score += 0.15
            if metadata.get("has_precedent", False):
                score += 0.1
                
        elif "민원" in data_source or "상담" in data_source:
            score += 0.3
        
        # 상담 유형별 가중치
        consultation_type = metadata.get("consultation_type", "")
        if consultation_type == "complex_case":
            score += 0.25
        elif "procedure" in consultation_type:
            score += 0.2
        elif "document" in consultation_type:
            score += 0.3
        
        # 카테고리 매칭 가중치
        if result.get("match_type") == "exact_category":
            score += 0.4
        elif result.get("match_type") == "related_category":
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_llm_metadata_filters(self, query: str, search_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """LLM을 사용해서 쿼리에 맞는 메타데이터 필터를 지능적으로 생성"""
        try:
            intent_info = self.query_normalizer.extract_intent(query)
            filters = {}
            
            # 데이터 타입 결정
            if intent_info.get("intent_type") == "절차안내":
                filters["data_type"] = "consultation_case"
                filters["consultation_type"] = "procedure"
            elif intent_info.get("trade_category") == "실무상담":
                filters["data_type"] = "consultation_case"
                filters["data_source"] = "상담사례DB"
            elif search_context and search_context.get("agent_type") == "consultation_agent":
                filters["data_type"] = "consultation_case"
            
            logger.debug(f"🤖 LLM 생성 필터: {filters}")
            return filters
            
        except Exception as e:
            logger.error(f"LLM 메타데이터 필터 생성 실패: {e}")
            return {}
    
    def _merge_filters(self, user_filters: Optional[Dict[str, Any]], llm_filters: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 제공 필터와 LLM 생성 필터를 지능적으로 병합"""
        if not user_filters:
            return llm_filters
        
        if not llm_filters:
            return user_filters or {}
        
        merged = llm_filters.copy()
        merged.update(user_filters)
        return merged
    
    def get_langchain_retriever(self, 
                               search_type: str = "similarity",
                               search_kwargs: Optional[Dict[str, Any]] = None):
        """LangChain 표준 Retriever 객체 반환"""
        if search_kwargs is None:
            search_kwargs = {"k": 8}
        
        return self.vector_store.get_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )


class ComplaintsAgent:
    """상담 사례 전문 에이전트"""
    
    def __init__(self,
                 retriever=None,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = None,
                 max_context_docs: int = 8,
                 similarity_threshold: float = None):
        """
        초기화
        
        Args:
            retriever: 상담 사례 검색기
            model_name (str): GPT 모델명  
            temperature (float): 생성 온도
            max_context_docs (int): 최대 컨텍스트 문서 수
            similarity_threshold (float): 유사도 임계값
        """
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        # 기본값 설정 (상담사례는 약간 더 유연하게)
        if temperature is None:
            temperature = thresholds["consultation_temperature"]
        if similarity_threshold is None:
            similarity_threshold = thresholds["similarity_threshold"]
        
        # 검색기 초기화
        if retriever is None:
            self.retriever = ComplaintsRetriever()
        else:
            self.retriever = retriever
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        # 대화 기록 관리
        self.memory = ComplaintsMemory()
        
        # OpenAI 클라이언트 초기화
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        logger.info(f"ComplaintsAgent initialized with model: {model_name}")
    
    def query_consultation(self, user_query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        상담 사례 질의 처리
        
        Args:
            user_query (str): 사용자 질의
            
        Returns:
            Tuple[str, List[Dict[str, Any]]]: (응답, 참조 문서들)
        """
        try:
            # 1. 상담 사례 전용 검색 컨텍스트 생성
            search_context = {
                "agent_type": "consultation_agent",
                "domain_hints": ["consultation_case", "실무", "절차", "방법", "경험", "사례"],
                "boost_keywords": ["절차", "방법", "실무", "경험", "사례", "신고", "신청", "승인", "처리", "서류", "비용", "기간", "통관", "세관", "관세"],
                "priority_data_sources": ["상담사례DB", "실무가이드", "민원처리사례"]
            }
            
            # 2. 관련 상담 사례 검색
            relevant_docs = self.retriever.search_consultation_cases(
                raw_query=user_query,
                top_k=self.max_context_docs,
                search_context=search_context,
                similarity_threshold=self.similarity_threshold
            )
            
            # 3. 응답 생성
            if relevant_docs:
                response = self._generate_response_with_context(user_query, relevant_docs)
            else:
                response = self._generate_fallback_response(user_query)
            
            # 4. 대화 기록에 추가
            self.memory.add_user_message(user_query, search_context)
            self.memory.add_assistant_message(response, relevant_docs)
            
            return response, relevant_docs
            
        except Exception as e:
            logger.error(f"상담 사례 질의 처리 실패: {e}")
            error_response = "죄송합니다. 상담 사례 정보 조회 중 오류가 발생했습니다."
            return error_response, []
    
    def get_similar_cases(self, category: str, top_k: int = 5) -> List[Dict]:
        """특정 카테고리의 유사한 상담 사례 조회"""
        try:
            search_filters = {
                "data_type": "consultation_case",
                "category": category
            }
            
            retrieved_docs = self.retriever.search_consultation_cases(
                raw_query=f"{category} 상담 사례",
                top_k=top_k,
                filter_by=search_filters
            )
            
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"유사 사례 조회 실패: {e}")
            return []
    
    def _generate_response_with_context(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """문서 컨텍스트를 포함한 응답 생성"""
        try:
            # 대화 히스토리 포함
            conversation_context = self.memory.get_recent_context(3)
            
            # 문서 정보 포맷팅
            context_text = self._format_documents_for_prompt(documents)
            
            # 사용자 패턴 분석
            user_patterns = self.memory.get_user_patterns()
            pattern_info = f"사용자 관심 분야: {', '.join(user_patterns.keys())}" if user_patterns else ""
            
            # 프롬프트 구성
            system_prompt = f"""당신은 한국 무역 업무 실무 상담 전문가입니다. 실제 민원상담 사례를 바탕으로 실용적인 조언을 제공합니다.

**핵심 원칙:**
1. **실용성 최우선**: 실제 업무에 바로 적용할 수 있는 구체적이고 실용적인 정보를 제공하세요.
2. **경험 기반**: 제공된 상담 사례를 바탕으로 검증된 해결방법과 절차를 안내하세요.
3. **단계별 안내**: 복잡한 절차는 단계별로 나누어 이해하기 쉽게 설명하세요.
4. **예외상황 고려**: 일반적인 경우뿐만 아니라 예외상황과 특수한 경우도 함께 안내하세요.
5. **관련 기관 연계**: 필요시 담당 기관과 연락처 정보를 제공하세요.

관련 상담 사례:
{context_text}

{pattern_info}

답변 시 다음을 준수하세요:
1. 실제 상담 사례를 근거로 검증된 해결방법 제시
2. 단계별 실행 방법과 필요 서류 안내
3. 흔한 실수와 주의할 점 미리 안내
4. 담당 기관과 연락처 정보 제공
5. 상담 사례는 참고용이며, 실제 적용 시 관련 기관에 최종 확인 필요함을 안내"""
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_context)
            messages.append({"role": "user", "content": query})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"상담 응답 생성 실패: {e}")
            return "상담 응답 생성 중 오류가 발생했습니다."
    
    def _generate_fallback_response(self, query: str) -> str:
        """문서 없이 일반적인 응답 생성"""
        return f"'{query}'에 대한 구체적인 상담 사례를 찾지 못했습니다. 좀 더 구체적인 질문을 해주시거나 다른 표현으로 다시 질문해 주세요."
    
    def _format_documents_for_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """문서들을 프롬프트용으로 포맷팅"""
        formatted_docs = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            
            # 상담 사례 특화 포맷팅
            doc_info = []
            if metadata.get("case_number"):
                doc_info.append(f"사례번호: {metadata['case_number']}")
            if metadata.get("category"):
                doc_info.append(f"분야: {metadata['category']}")
            if metadata.get("sub_category"):
                doc_info.append(f"세부분야: {metadata['sub_category']}")
            if metadata.get("consultation_type"):
                doc_info.append(f"상담유형: {metadata['consultation_type']}")
            
            doc_header = " | ".join(doc_info) if doc_info else "상담 사례"
            formatted_docs.append(f"[{doc_header}]\n{content}")
        
        return "\n\n".join(formatted_docs)
    
    def get_conversation_summary(self) -> str:
        """현재 상담 대화의 요약 생성"""
        try:
            if not self.memory.messages:
                return "상담 기록이 없습니다."
            
            # 대화 기록을 텍스트로 변환
            conversation_text = ""
            for msg in self.memory.messages:
                role = "상담자" if msg["role"] == "user" else "상담원"
                conversation_text += f"{role}: {msg['content']}\n\n"
            
            # 사용자 패턴 정보 추가
            user_patterns = self.memory.get_user_patterns()
            
            # GPT를 사용한 상담 요약 생성
            summary_prompt = f"""다음 무역 업무 상담 내용을 간결하게 요약해주세요:

{conversation_text}

상담 주제 분포: {user_patterns}

상담 요약:"""
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.2,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"상담 요약 생성 실패: {e}")
            return "상담 요약 생성 중 오류가 발생했습니다."
    
    def reset_conversation(self) -> None:
        """대화 기록 초기화"""
        self.memory.clear_history()
        logger.info("상담 사례 대화 기록 초기화됨")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """에이전트 통계 정보 반환"""
        try:
            retriever_stats = self.retriever.vector_store.get_collection_stats() if hasattr(self.retriever, 'vector_store') else {}
            return {
                "agent_type": "complaints",
                "model_name": self.model_name,
                "temperature": self.temperature,
                "max_context_docs": self.max_context_docs,
                "similarity_threshold": self.similarity_threshold,
                "conversation_stats": {
                    "total_messages": len(self.memory.messages),
                    "context_cases": len(self.memory.case_context),
                    "user_patterns": self.memory.get_user_patterns()
                },
                "retriever_stats": retriever_stats
            }
        except Exception as e:
            logger.error(f"상담 에이전트 통계 조회 실패: {e}")
            return {"error": str(e)}


# 하위 호환성을 위한 별칭
ConsultationCaseAgent = ComplaintsAgent
ConsultationCaseRetriever = ComplaintsRetriever