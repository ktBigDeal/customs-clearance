"""
Regulations Agent Module

무역 규제 전문 에이전트 - 규제 정보 검색 및 응답 생성 통합
"""

import logging
import openai
from typing import List, Dict, Any, Optional, Tuple
import json
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class TradeRegulationRetriever:
    """무역 규제 정보 검색 및 관련 데이터 추적 클래스 (통합)"""
    
    def __init__(self,
                 embedder=None,
                 vector_store=None,
                 query_normalizer=None,
                 collection_name: str = "trade_info_collection"):
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
        
        # HS코드 패턴 매칭 (기존 호환성 유지)
        self.hs_code_pattern = re.compile(r'\\b\\d{4,10}\\b')
        
        logger.info(f"TradeRegulationRetriever initialized with collection: {collection_name}")
    
    def search_trade_info(self, 
                         raw_query: str, 
                         top_k: int = 5,
                         include_related: bool = True,
                         expand_with_synonyms: bool = True,
                         similarity_threshold: float = 0.0,
                         filter_by: Optional[Dict[str, Any]] = None,
                         search_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        무역 정보 검색
        
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
            
            # 1. LLM 기반 메타데이터 필터 생성
            llm_filters = self._generate_llm_metadata_filters(raw_query, search_context)
            
            # 2. 기존 필터와 LLM 필터 병합
            combined_filters = self._merge_filters(filter_by, llm_filters)
            
            if combined_filters:
                if not filter_by:
                    filter_by = {}
                filter_by.update(combined_filters)
            
            # 3. 쿼리 정규화 및 확장
            normalized_query = self.query_normalizer.normalize(raw_query, search_context)
            if expand_with_synonyms:
                expanded_query = self.query_normalizer.expand_query_with_synonyms(normalized_query)
            else:
                expanded_query = normalized_query
            
            logger.info(f"🔍 Query: '{raw_query}' → '{expanded_query}'")
            logger.info(f"🏷️ LLM Filters: {llm_filters}")
            
            # 4. HS코드 감지 및 특별 처리
            hs_codes = self._extract_hs_codes(raw_query)
            if hs_codes:
                logger.info(f"🔢 감지된 HS코드: {hs_codes}")
                return self._search_by_hs_code(hs_codes, top_k, include_related)
            
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
                expanded_results = self._expand_with_related_info(primary_results, top_k)
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
            logger.error(f"무역 정보 검색 실패: {e}")
            return []
    
    def _extract_hs_codes(self, query: str) -> List[str]:
        """쿼리에서 HS코드 추출"""
        matches = self.hs_code_pattern.findall(query)
        hs_codes = [match for match in matches if len(match) >= 4]
        return hs_codes
    
    def _search_by_hs_code(self, hs_codes: List[str], top_k: int, include_related: bool) -> List[Dict[str, Any]]:
        """HS코드 기반 검색"""
        all_results = []
        
        for hs_code in hs_codes:
            try:
                where_condition = {"hs_code": {"$eq": hs_code}}
                query = f"HS코드 {hs_code} 제품 규제 수출 수입"
                query_embedding = self.embedder.embed_text(query)
                
                results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    where=where_condition
                )
                
                for result in results:
                    result["hs_code_match"] = hs_code
                    result["match_type"] = "exact_hs_code"
                
                all_results.extend(results)
                
                if include_related and len(hs_code) >= 6:
                    related_results = self._search_related_hs_codes(hs_code[:6], top_k // 2)
                    all_results.extend(related_results)
                    
            except Exception as e:
                logger.error(f"HS코드 {hs_code} 검색 실패: {e}")
                continue
        
        # 중복 제거 및 정렬
        from ..utils.tools import smart_deduplicate
        unique_results = smart_deduplicate(all_results, id_key="id", preserve_higher_score=True)
        return unique_results[:top_k]
    
    def _search_related_hs_codes(self, hs_prefix: str, top_k: int) -> List[Dict[str, Any]]:
        """관련 HS코드 검색"""
        try:
            query = f"HS코드 {hs_prefix} 관련 제품"
            query_embedding = self.embedder.embed_text(query)
            
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            for result in results:
                result["match_type"] = "related_hs_code"
                result["hs_prefix_match"] = hs_prefix
            
            return results
            
        except Exception as e:
            logger.error(f"관련 HS코드 검색 실패: {e}")
            return []
    
    def _build_where_condition(self, filter_by: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """필터링 조건 구성"""
        if not filter_by:
            return None
        
        supported_fields = [
            "category", "country", "regulation_type", "status", "hs_code", "product_category", 
            "data_type", "data_source", "consultation_type", "case_number", "product_name",
            "affected_country", "regulating_country", "animal_plant_type", "management_number"
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
    
    def _expand_with_related_info(self, results: List[Dict[str, Any]], max_total: int) -> List[Dict[str, Any]]:
        """관련 정보로 검색 결과 확장"""
        expanded_results = results.copy()
        seen_ids = {result.get("id", "") for result in results}
        
        for result in results[:3]:
            metadata = result.get("metadata", {})
            
            # HS코드 기반 확장
            hs_code = metadata.get("hs_code", "")
            if hs_code and len(hs_code) >= 6:
                related_hs = self._search_related_hs_codes(hs_code[:6], 2)
                for related in related_hs:
                    if related.get("id", "") not in seen_ids:
                        related["reference_info"] = {"is_related": True, "related_to": result.get("id", "")}
                        expanded_results.append(related)
                        seen_ids.add(related.get("id", ""))
        
        return expanded_results[:max_total]
    
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
        
        # 동식물 수입 규제 데이터 최우선 처리
        data_source = metadata.get("data_source", "")
        if data_source == "동식물허용금지지역":
            score += 0.5
            
            priority = metadata.get("priority", 0)
            regulation_intensity = metadata.get("regulation_intensity", "")
            
            try:
                priority_int = int(priority) if priority else 0
            except (ValueError, TypeError):
                priority_int = 0
            
            if priority_int >= 2:
                score += 0.2
            if regulation_intensity == "high":
                score += 0.15
            if metadata.get("has_global_prohibition", False):
                score += 0.1
                
        elif "규제" in data_source:
            score += 0.3
        
        # 규제 유형별 가중치
        regulation_type = metadata.get("regulation_type", "")
        if regulation_type == "import_regulations":
            score += 0.25
        elif "restrictions" in regulation_type:
            score += 0.2
        elif "prohibitions" in regulation_type:
            score += 0.3
        
        # HS코드 매칭 가중치
        if result.get("match_type") == "exact_hs_code":
            score += 0.4
        elif result.get("match_type") == "related_hs_code":
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_llm_metadata_filters(self, query: str, search_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """LLM을 사용해서 쿼리에 맞는 메타데이터 필터를 지능적으로 생성"""
        try:
            intent_info = self.query_normalizer.extract_intent(query)
            filters = {}
            
            # 데이터 타입 결정
            if intent_info.get("intent_type") == "동식물검역":
                filters["data_type"] = "trade_regulation"
                filters["data_source"] = "동식물허용금지지역"
            elif intent_info.get("trade_category") == "동식물수입규제":
                filters["data_type"] = "trade_regulation"
                filters["data_source"] = "동식물허용금지지역"
            elif search_context and search_context.get("agent_type") == "regulation_agent":
                filters["data_type"] = "trade_regulation"
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
            search_kwargs = {"k": 5}
        
        return self.vector_store.get_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )


class RegulationsAgent:
    """무역 규제 전문 에이전트"""
    
    def __init__(self,
                 retriever=None,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = None,
                 max_context_docs: int = 8,
                 similarity_threshold: float = None):
        """
        초기화
        
        Args:
            retriever: 무역 정보 검색기
            model_name (str): GPT 모델명  
            temperature (float): 생성 온도
            max_context_docs (int): 최대 컨텍스트 문서 수
            similarity_threshold (float): 유사도 임계값
        """
        from ..config.config import get_quality_thresholds
        thresholds = get_quality_thresholds()
        
        # 기본값 설정
        if temperature is None:
            temperature = thresholds["regulation_temperature"]
        if similarity_threshold is None:
            similarity_threshold = thresholds["similarity_threshold"]
        
        # 검색기 초기화
        if retriever is None:
            self.retriever = TradeRegulationRetriever()
        else:
            self.retriever = retriever
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        # OpenAI 클라이언트 초기화
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        logger.info(f"RegulationsAgent initialized with model: {model_name}")
    
    def query_regulation(self, user_query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        무역 규제 질의 처리
        
        Args:
            user_query (str): 사용자 질의
            
        Returns:
            Tuple[str, List[Dict[str, Any]]]: (응답, 참조 문서들)
        """
        try:
            # 1. 관련 규제 정보 검색
            search_context = {
                "agent_type": "regulation_agent",
                "domain_hints": ["trade_regulation", "import_export"],
                "priority_data_sources": ["동식물허용금지지역", "수입규제DB_전체"]
            }
            
            relevant_docs = self.retriever.search_trade_info(
                raw_query=user_query,
                top_k=self.max_context_docs,
                search_context=search_context,
                similarity_threshold=self.similarity_threshold
            )
            
            # 2. 응답 생성
            if relevant_docs:
                response = self._generate_response_with_context(user_query, relevant_docs)
            else:
                response = self._generate_fallback_response(user_query)
            
            return response, relevant_docs
            
        except Exception as e:
            logger.error(f"무역 규제 질의 처리 실패: {e}")
            error_response = "죄송합니다. 무역 규제 정보 조회 중 오류가 발생했습니다."
            return error_response, []
    
    def _generate_response_with_context(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """문서 컨텍스트를 포함한 응답 생성"""
        try:
            context_text = self._format_documents_for_prompt(documents)
            
            system_prompt = f"""당신은 무역 규제 전문가입니다. 다음 무역 규제 정보를 참조하여 정확하고 실무적인 답변을 제공하세요.

관련 규제 정보:
{context_text}

답변 시 다음을 준수하세요:
1. HS코드나 제품명을 명확히 제시
2. 해당 국가의 구체적인 규제 내용 설명
3. 수입/수출 시 필요한 절차나 주의사항 안내
4. 관련된 다른 규제가 있다면 함께 안내
5. 동식물 검역의 경우 특별 주의사항 강조"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=1200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"규제 응답 생성 실패: {e}")
            return "규제 정보 응답 생성 중 오류가 발생했습니다."
    
    def _generate_fallback_response(self, query: str) -> str:
        """문서 없이 일반적인 응답 생성"""
        return f"'{query}'에 대한 구체적인 무역 규제 정보를 찾지 못했습니다. HS코드나 구체적인 제품명, 국가명을 포함해서 다시 질문해 주세요."
    
    def _format_documents_for_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """문서들을 프롬프트용으로 포맷팅"""
        formatted_docs = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            
            # 규제 정보 특화 포맷팅
            doc_info = []
            if metadata.get("hs_code"):
                doc_info.append(f"HS코드: {metadata['hs_code']}")
            if metadata.get("country"):
                doc_info.append(f"국가: {metadata['country']}")
            if metadata.get("product_name"):
                doc_info.append(f"제품: {metadata['product_name']}")
            if metadata.get("regulation_type"):
                doc_info.append(f"규제유형: {metadata['regulation_type']}")
            
            doc_header = " | ".join(doc_info) if doc_info else "규제 정보"
            formatted_docs.append(f"[{doc_header}]\n{content}")
        
        return "\n\n".join(formatted_docs)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """에이전트 통계 정보 반환"""
        try:
            retriever_stats = self.retriever.vector_store.get_collection_stats() if hasattr(self.retriever, 'vector_store') else {}
            return {
                "agent_type": "regulations",
                "model_name": self.model_name,
                "temperature": self.temperature,
                "max_context_docs": self.max_context_docs,
                "similarity_threshold": self.similarity_threshold,
                "retriever_stats": retriever_stats
            }
        except Exception as e:
            logger.error(f"규제 에이전트 통계 조회 실패: {e}")
            return {"error": str(e)}


# 하위 호환성을 위한 별칭
TradeRegulationAgent = RegulationsAgent
TradeInfoRetriever = TradeRegulationRetriever