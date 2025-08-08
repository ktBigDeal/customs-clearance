"""
Customs Law Agent Module

관세법 조문 전문 에이전트 - 법령 검색 및 응답 생성 통합
"""

import logging
import openai
from typing import List, Dict, Any, Optional, Tuple
import json
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationMemory:
    """대화 기록 관리 클래스"""
    
    def __init__(self, max_history: int = 10):
        """
        초기화
        
        Args:
            max_history (int): 최대 대화 기록 수
        """
        self.max_history = max_history
        self.messages = []
        self.context_documents = []  # 대화에서 참조된 문서들
        
    def add_user_message(self, message: str) -> None:
        """사용자 메시지 추가"""
        self.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
    
    def add_assistant_message(self, message: str, source_documents: List[Dict] = None) -> None:
        """어시스턴트 메시지 추가"""
        self.messages.append({
            "role": "assistant", 
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "source_documents": source_documents or []
        })
        
        # 참조된 문서들을 컨텍스트에 추가
        if source_documents:
            for doc in source_documents:
                if doc not in self.context_documents:
                    self.context_documents.append(doc)
        
        self._trim_history()
    
    def get_conversation_history(self, include_timestamps: bool = False) -> List[Dict]:
        """대화 기록 조회"""
        if include_timestamps:
            return self.messages.copy()
        else:
            return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def get_recent_context(self, num_turns: int = 3) -> List[Dict]:
        """최근 대화 컨텍스트 조회"""
        recent_messages = self.messages[-num_turns*2:] if self.messages else []
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    
    def clear_history(self) -> None:
        """대화 기록 초기화"""
        self.messages.clear()
        self.context_documents.clear()
    
    def _trim_history(self) -> None:
        """대화 기록 크기 제한"""
        if len(self.messages) > self.max_history:
            # 시스템 메시지는 유지하고 오래된 대화만 제거
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            
            # 최근 대화만 유지
            trimmed_other = other_messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + trimmed_other


class CustomsLawRetriever:
    """관세법 조문 검색 및 내부 참조 추적 클래스 (통합)"""
    
    def __init__(self,
                 embedder=None,
                 vector_store=None,
                 query_normalizer=None,
                 collection_name: str = "law_collection"):
        """
        초기화
        
        Args:
            embedder: 임베딩 생성기
            vector_store: 벡터 저장소
            query_normalizer: 쿼리 정규화기
            collection_name (str): 컬렉션 이름
        """
        # 통합된 import 시스템 사용
        from ..utils.embeddings import LangChainEmbedder
        from ..utils.db_connect import LangChainVectorStore
        # Query normalizer removed - using basic string processing
        
        # LangChain 구성요소 초기화
        if embedder is None:
            self.embedder = LangChainEmbedder()
        else:
            self.embedder = embedder
            
        if vector_store is None:
            self.vector_store = LangChainVectorStore(collection_name=collection_name)
        else:
            self.vector_store = vector_store
            
        if query_normalizer is None:
            from ..utils.query_normalizer import get_query_normalizer
            self.query_normalizer = get_query_normalizer("law")
        else:
            self.query_normalizer = query_normalizer
            
        # 내부 문서 캐시 (성능 최적화용)
        self._document_cache = {}
        
        logger.info("CustomsLawRetriever initialized")
    
    def search_similar_laws(self, 
                           raw_query: str, 
                           top_k: int = 5,
                           include_references: bool = True,
                           expand_with_synonyms: bool = True,
                           similarity_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        유사한 법률 조문 검색
        
        Args:
            raw_query (str): 원본 사용자 질의
            top_k (int): 반환할 상위 결과 수
            include_references (bool): 내부 참조 문서 포함 여부
            expand_with_synonyms (bool): 동의어 확장 사용 여부
            similarity_threshold (float): 유사도 임계값 (0.0-1.0)
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 리스트
        """
        try:
            # Simple query processing
            search_query = raw_query.strip()
            logger.info(f"🔍 검색 쿼리: {search_query}")
            
            # 3. LangChain 벡터 검색 수행
            logger.info(f"🔍 LangChain 벡터 검색 시작 (top_k: {top_k})")
            primary_results = self.vector_store.search_similar(
                query_text=search_query,
                top_k=top_k
            )
            logger.info(f"📊 벡터 검색 결과: {len(primary_results)}개")
            
            # 4. 내부 참조 확장 검색
            if include_references:
                expanded_results = self._expand_with_references(primary_results, top_k)
            else:
                expanded_results = primary_results
            
            # 5. 결과 후처리 및 정렬
            final_results = self._post_process_results(expanded_results, processed_query)
            
            # 6. 유사도 임계값 필터링
            if similarity_threshold > 0.0:
                filtered_results = [result for result in final_results 
                                  if result.get("similarity", 0) >= similarity_threshold]
                logger.info(f"🎯 유사도 임계값 {similarity_threshold}로 필터링: {len(final_results)} → {len(filtered_results)}개")
                final_results = filtered_results
            
            logger.info(f"✅ {len(final_results)}개 결과 반환 (요청된 top_k: {top_k})")
            return final_results
            
        except Exception as e:
            logger.error(f"검색 실패: {e}")
            return []
    
    def _expand_with_references(self, 
                              primary_results: List[Dict[str, Any]], 
                              max_total: int) -> List[Dict[str, Any]]:
        """내부 참조를 활용한 검색 결과 확장"""
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        expanded_results = primary_results.copy()
        seen_ids = {result["id"] for result in primary_results}
        
        # 상위 결과들의 내부 참조 따라가기
        for result in primary_results:
            try:
                related_articles = self._get_related_articles(result)
                
                for related in related_articles:
                    if related["id"] not in seen_ids and len(expanded_results) < max_total:
                        related["reference_boost"] = thresholds["reference_boost"]
                        related["referenced_from"] = result["id"]
                        expanded_results.append(related)
                        seen_ids.add(related["id"])
                        
            except Exception as e:
                logger.warning(f"참조 확장 중 오류: {e}")
                continue
        
        return expanded_results
    
    def _get_related_articles(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """특정 문서와 관련된 조문들 조회 (내부 참조 기반)"""
        related_articles = []
        
        try:
            # 메타데이터에서 내부 참조 정보 추출
            metadata = document.get("metadata", {})
            
            # JSON 문자열로 저장된 내부 참조 정보 파싱
            internal_refs_raw = metadata.get("internal_law_references", "{}")
            if isinstance(internal_refs_raw, str):
                internal_refs = json.loads(internal_refs_raw)
            else:
                internal_refs = internal_refs_raw
            
            # 각 참조 유형별로 관련 조문 검색
            for ref_type, ref_list in internal_refs.items():
                if not ref_list:
                    continue
                
                for ref in ref_list:
                    related_doc = self._search_by_article_reference(ref)
                    if related_doc and related_doc not in related_articles:
                        related_doc["reference_type"] = ref_type
                        related_articles.append(related_doc)
            
            logger.debug(f"발견된 관련 조문: {len(related_articles)}개")
            return related_articles
            
        except Exception as e:
            logger.error(f"관련 조문 조회 실패: {e}")
            return []
    
    def _search_by_article_reference(self, article_ref: str) -> Optional[Dict[str, Any]]:
        """조문 참조를 통한 직접 검색"""
        try:
            # 벡터 저장소에서 검색
            results = self.vector_store.search_similar(
                query_text="법령 조문",
                top_k=200
            )
            
            # 정확한 매치 또는 부분 매치 찾기
            exact_matches = []
            partial_matches = []
            
            for result in results:
                result_index = result.get("index", "") or result.get("metadata", {}).get("index", "")
                
                if result_index == article_ref:
                    exact_matches.append(result)
                elif article_ref in result_index or result_index in article_ref:
                    partial_matches.append(result)
            
            if exact_matches:
                return exact_matches[0]
            elif partial_matches:
                return partial_matches[0]
            
            return None
            
        except Exception as e:
            logger.error(f"조문 참조 검색 실패: {e}")
            return None
    
    def _post_process_results(self, 
                            results: List[Dict[str, Any]], 
                            processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """검색 결과 후처리 및 최적화"""
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        # 1. 점수 재계산
        for result in results:
            base_score = result.get("similarity", 0)
            reference_boost = result.get("reference_boost", 0)
            intent_score = self._calculate_intent_score(result, processed_query["intent"])
            
            # 최종 점수 계산
            final_score = base_score + reference_boost + intent_score * thresholds["intent_weight"]
            result["final_score"] = final_score
        
        # 2. 점수 기준 정렬
        sorted_results = sorted(results, key=lambda x: x.get("final_score", 0), reverse=True)
        
        # 3. 결과 포맷팅
        formatted_results = []
        for result in sorted_results:
            # 다중 경로에서 index와 subtitle 추출
            index = (result.get("index") or 
                    result.get("metadata", {}).get("index") or "")
            subtitle = (result.get("subtitle") or 
                       result.get("metadata", {}).get("subtitle") or "")
            
            formatted_result = {
                "id": result["id"],
                "content": result["content"],
                "metadata": result["metadata"],
                "index": index,
                "subtitle": subtitle,
                "similarity": result.get("similarity", 0),
                "final_score": result.get("final_score", 0),
                "reference_info": {
                    "is_referenced": result.get("reference_boost", 0) > 0,
                    "referenced_from": result.get("referenced_from"),
                    "reference_type": result.get("reference_type")
                }
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _calculate_intent_score(self, result: Dict[str, Any], intent: Dict[str, Any]) -> float:
        """의도 매칭 점수 계산"""
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        score = 0.0
        content = result.get("content", "").lower()
        
        # 핵심 개념 매칭
        key_concepts = intent.get("key_concepts", [])
        for concept in key_concepts:
            if concept.lower() in content:
                score += thresholds["concept_score"]
        
        # 법령 영역 매칭
        law_area = intent.get("law_area", "")
        if law_area != "일반":
            area_keywords = {
                "수입": ["수입", "반입", "들여오"],
                "수출": ["수출", "반출", "내보내"],
                "통관": ["통관", "세관"],
                "관세": ["관세", "세금", "부과"],
                "검사": ["검사", "검증", "확인"]
            }
            
            if law_area in area_keywords:
                for keyword in area_keywords[law_area]:
                    if keyword in content:
                        score += thresholds["area_score"]
                        break
        
        return min(score, 1.0)
    
    def get_langchain_retriever(self, search_type: str = "similarity", search_kwargs: Optional[Dict[str, Any]] = None):
        """LangChain 표준 Retriever 객체 반환"""
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        return self.vector_store.get_retriever(search_type=search_type, search_kwargs=search_kwargs)


class CustomsLawAgent:
    """관세법 조문 전문 에이전트"""
    
    def __init__(self,
                 embedder=None,
                 vector_store=None,
                 query_normalizer=None,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = None,
                 max_context_docs: int = 5,
                 similarity_threshold: float = None):
        """
        초기화
        
        Args:
            embedder: 임베딩 생성기 
            vector_store: 벡터 저장소
            query_normalizer: 쿼리 정규화기
            model_name (str): GPT 모델명
            temperature (float): 생성 온도
            max_context_docs (int): 최대 컨텍스트 문서 수
            similarity_threshold (float): 유사도 임계값
        """
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        # 기본값 설정
        if temperature is None:
            temperature = thresholds["model_temperature"] 
        if similarity_threshold is None:
            similarity_threshold = thresholds["similarity_threshold"]
        
        # 검색기 초기화
        self.retriever = CustomsLawRetriever(
            embedder=embedder,
            vector_store=vector_store, 
            query_normalizer=query_normalizer
        )
        
        # 모델 설정
        self.model_name = model_name
        self.temperature = temperature
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        # 대화 기록 관리
        self.memory = ConversationMemory()
        
        # OpenAI 클라이언트 초기화
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        logger.info(f"CustomsLawAgent initialized with model: {model_name}")
    
    def query_law(self, user_query: str, include_context: bool = True) -> Tuple[str, List[Dict[str, Any]]]:
        """
        관세법 질의 처리
        
        Args:
            user_query (str): 사용자 질의
            include_context (bool): 대화 컨텍스트 포함 여부
            
        Returns:
            Tuple[str, List[Dict[str, Any]]]: (응답, 참조 문서들)
        """
        try:
            # 1. 관련 문서 검색
            relevant_docs = self.retriever.search_similar_laws(
                raw_query=user_query,
                top_k=self.max_context_docs,
                similarity_threshold=self.similarity_threshold
            )
            
            # 2. 대화 컨텍스트 고려한 확장 검색
            if include_context and self.memory.context_documents:
                context_docs = self.memory.context_documents[-3:]  # 최근 3개 문서
                expanded_docs = self.retriever._expand_with_context(user_query, context_docs, self.max_context_docs)
                
                # 중복 제거하며 통합
                from ..utils.tools import deduplicate_by_id
                all_docs = relevant_docs + expanded_docs
                relevant_docs = deduplicate_by_id(all_docs, id_key="id")
            
            # 3. 프롬프트 생성 및 응답 생성
            if relevant_docs:
                response = self._generate_response_with_context(user_query, relevant_docs)
            else:
                response = self._generate_fallback_response(user_query)
            
            # 4. 대화 기록에 추가
            self.memory.add_user_message(user_query)
            self.memory.add_assistant_message(response, relevant_docs)
            
            return response, relevant_docs
            
        except Exception as e:
            logger.error(f"관세법 질의 처리 실패: {e}")
            error_response = "죄송합니다. 질의 처리 중 오류가 발생했습니다. 다시 시도해 주세요."
            return error_response, []
    
    def _generate_response_with_context(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """문서 컨텍스트를 포함한 응답 생성"""
        try:
            # 대화 히스토리 포함
            conversation_context = self.memory.get_recent_context(2)
            
            # 문서 정보 포맷팅
            context_text = self._format_documents_for_prompt(documents)
            
            # 프롬프트 구성
            system_prompt = f"""당신은 관세법 전문가입니다. 다음 관세법 조문들을 참조하여 정확하고 상세한 답변을 제공하세요.

관련 법령 조문:
{context_text}

답변 시 다음을 준수하세요:
1. 구체적인 조문 번호를 인용하여 근거를 명확히 제시
2. 법령의 내용을 정확히 해석하여 설명  
3. 실무적인 적용 방법도 함께 안내
4. 관련된 다른 조문이 있다면 함께 안내"""
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_context)
            messages.append({"role": "user", "content": query})
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            return "응답 생성 중 오류가 발생했습니다."
    
    def _generate_fallback_response(self, query: str) -> str:
        """문서 없이 일반적인 응답 생성"""
        return f"'{query}'에 대한 구체적인 관세법 조문을 찾지 못했습니다. 더 구체적인 질문을 해주시거나 다른 표현으로 다시 질문해 주세요."
    
    def _format_documents_for_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """문서들을 프롬프트용으로 포맷팅"""
        formatted_docs = []
        
        for doc in documents:
            index = doc.get("index", "")
            subtitle = doc.get("subtitle", "")
            content = doc.get("content", "")
            
            if index and content:
                doc_text = f"[{index}] {subtitle}\n{content}"
                formatted_docs.append(doc_text)
        
        return "\n\n".join(formatted_docs)
    
    def reset_conversation(self) -> None:
        """대화 기록 초기화"""
        self.memory.clear_history()
        logger.info("관세법 에이전트 대화 기록 초기화됨")
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """대화 통계 정보 반환"""
        return {
            "total_messages": len(self.memory.messages),
            "context_documents": len(self.memory.context_documents),
            "agent_type": "customs_law",
            "model_name": self.model_name,
            "temperature": self.temperature
        }


# 하위 호환성을 위한 별칭
ConversationAgent = CustomsLawAgent
SimilarLawRetriever = CustomsLawRetriever