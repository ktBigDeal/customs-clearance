"""
Trade Information Retriever Module

무역 정보 CSV 데이터에서 관련 정보를 검색하고 HS코드, 국가별 규제 등을 활용한 확장 검색 기능
"""

import logging
from typing import List, Dict, Any, Optional
import re
from .embeddings import LangChainEmbedder
from .vector_store import LangChainVectorStore
from .query_normalizer import QueryNormalizer, AdvancedQueryProcessor, TradeQueryNormalizer

logger = logging.getLogger(__name__)


class TradeInfoRetriever:
    """무역 정보 검색 및 관련 데이터 추적 클래스"""
    
    def __init__(self,
                 embedder: Optional[LangChainEmbedder] = None,
                 vector_store: Optional[LangChainVectorStore] = None,
                 query_normalizer: Optional[QueryNormalizer] = None,
                 collection_name: str = "trade_info_collection"):
        """
        초기화 (LangChain 표준 사용)
        
        Args:
            embedder (Optional[LangChainEmbedder]): LangChain 임베딩 생성기
            vector_store (Optional[LangChainVectorStore]): LangChain 벡터 저장소
            query_normalizer (Optional[QueryNormalizer]): 쿼리 정규화기
            collection_name (str): 사용할 컬렉션 이름
        """
        # 기본값 설정 (자동 초기화)
        if embedder is None:
            self.embedder = LangChainEmbedder()  # 기본 text-embedding-3-small 사용
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
            # TradeQueryNormalizer 사용으로 동식물 수입 의도 감지 개선
            self.query_normalizer = TradeQueryNormalizer()
        else:
            self.query_normalizer = query_normalizer
            
        self.query_processor = AdvancedQueryProcessor(self.query_normalizer)
        self.collection_name = collection_name
        
        # 내부 문서 캐시 (성능 최적화용)
        self._document_cache = {}
        
        # HS코드 패턴 매칭 (기존 호환성 유지)
        self.hs_code_pattern = re.compile(r'\b\d{4,10}\b')  # 4-10자리 숫자를 HS코드로 인식
        
        logger.info(f"LangChain TradeInfoRetriever initialized with collection: {collection_name}")
    
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
            # 1. LLM 기반 메타데이터 필터 생성 (핵심 개선 기능)
            llm_filters = self._generate_llm_metadata_filters(raw_query, search_context)
            
            # 2. 기존 필터와 LLM 필터 병합
            combined_filters = self._merge_filters(filter_by, llm_filters)
            
            # 병합된 필터를 실제 검색에 사용
            if combined_filters:
                if not filter_by:
                    filter_by = {}
                filter_by.update(combined_filters)
            
            # 3. 쿼리 정규화 및 확장 (TradeQueryNormalizer 사용)
            normalized_query = self.query_normalizer.normalize(raw_query, search_context)
            if expand_with_synonyms:
                expanded_query = self.query_normalizer.expand_query_with_synonyms(normalized_query)
            else:
                expanded_query = normalized_query
            
            logger.info(f"🔍 Query: '{raw_query}' → '{expanded_query}'")
            logger.info(f"🏷️ LLM Filters: {llm_filters}")
            
            # 4. HS코드 감지 및 특별 처리 (기존 로직 유지)
            hs_codes = self._extract_hs_codes(raw_query)
            if hs_codes:
                logger.info(f"🔢 감지된 HS코드: {hs_codes}")
                return self._search_by_hs_code(hs_codes, top_k, include_related)
            
            # 2.5. 검색 컨텍스트 기반 특별 처리
            if search_context and search_context.get("domain_hints"):
                logger.info(f"🎯 검색 컨텍스트 적용: {search_context.get('domain_hints')}")
                # 컨텍스트 기반 검색 쿼리 보강
                context_keywords = search_context.get("boost_keywords", [])
                if context_keywords:
                    enhanced_query = f"{raw_query} {' '.join(context_keywords)}"
                    processed_query = self.query_processor.process_complex_query(enhanced_query)
                else:
                    processed_query = self.query_processor.process_complex_query(raw_query)
            else:
                processed_query = self.query_processor.process_complex_query(raw_query)
            
            # 3. 사용할 쿼리 결정 (이미 위에서 processed_query 생성됨)
            if expand_with_synonyms:
                search_query = processed_query["expanded_query"]
            else:
                search_query = processed_query["normalized_query"]
            
            logger.info(f"🔍 검색 쿼리: {search_query}")
            
            # 4. 쿼리 임베딩 생성
            query_embedding = self.embedder.embed_text(search_query)
            
            # 5. 벡터 유사도 검색
            logger.info(f"🔍 벡터 검색 시작 (top_k: {top_k})")
            
            # 필터링 조건 적용
            where_condition = self._build_where_condition(filter_by)
            
            primary_results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                where=where_condition
            )
            logger.info(f"📊 벡터 검색 결과: {len(primary_results)}개")
            
            # 6. 관련 데이터 확장 검색
            if include_related:
                expanded_results = self._expand_with_related_info(primary_results, top_k)
            else:
                expanded_results = primary_results
            
            # 7. 결과 후처리 및 정렬 (search_context 포함)
            final_results = self._post_process_results(expanded_results, processed_query, search_context)
            
            # 8. 유사도 임계값 필터링
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
    
    def search_by_country(self, country: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        특정 국가의 무역 규제 정보 검색
        
        Args:
            country (str): 국가명
            top_k (int): 반환할 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            # 국가명 정규화
            normalized_country = self._normalize_country_name(country)
            
            # 메타데이터 필터링으로 검색
            where_condition = {"country": {"$eq": normalized_country}}
            
            # 국가 관련 쿼리로 임베딩 검색
            query = f"{normalized_country} 무역 규제 수출 수입 제한"
            query_embedding = self.embedder.embed_text(query)
            
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                where=where_condition
            )
            
            logger.info(f"🌍 {country} 관련 {len(results)}개 결과 발견")
            return results
            
        except Exception as e:
            logger.error(f"국가별 검색 실패: {e}")
            return []
    
    def search_by_product_category(self, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        제품 카테고리별 정보 검색
        
        Args:
            category (str): 제품 카테고리
            top_k (int): 반환할 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            # 카테고리 관련 쿼리
            query = f"{category} 제품 무역 규제 수출 수입"
            query_embedding = self.embedder.embed_text(query)
            
            # 제품 카테고리 필터링
            where_condition = {"product_category": {"$eq": category}}
            
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                where=where_condition
            )
            
            logger.info(f"📦 {category} 카테고리 {len(results)}개 결과 발견")
            return results
            
        except Exception as e:
            logger.error(f"카테고리별 검색 실패: {e}")
            return []
    
    def _extract_hs_codes(self, query: str) -> List[str]:
        """쿼리에서 HS코드 추출"""
        matches = self.hs_code_pattern.findall(query)
        # 4자리 이상의 숫자만 HS코드로 간주
        hs_codes = [match for match in matches if len(match) >= 4]
        return hs_codes
    
    def _search_by_hs_code(self, hs_codes: List[str], top_k: int, include_related: bool) -> List[Dict[str, Any]]:
        """HS코드 기반 검색"""
        all_results = []
        
        for hs_code in hs_codes:
            try:
                # 정확한 HS코드 매칭
                where_condition = {"hs_code": {"$eq": hs_code}}
                
                # HS코드로 쿼리 생성
                query = f"HS코드 {hs_code} 제품 규제 수출 수입"
                query_embedding = self.embedder.embed_text(query)
                
                results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    where=where_condition
                )
                
                # HS코드 매칭 정보 추가
                for result in results:
                    result["hs_code_match"] = hs_code
                    result["match_type"] = "exact_hs_code"
                
                all_results.extend(results)
                
                # 관련 HS코드 검색 (앞 6자리가 같은 경우)
                if include_related and len(hs_code) >= 6:
                    related_results = self._search_related_hs_codes(hs_code[:6], top_k // 2)
                    all_results.extend(related_results)
                    
            except Exception as e:
                logger.error(f"HS코드 {hs_code} 검색 실패: {e}")
                continue
        
        # 중복 제거 및 정렬
        unique_results = self._deduplicate_results(all_results)
        return unique_results[:top_k]
    
    def _search_related_hs_codes(self, hs_prefix: str, top_k: int) -> List[Dict[str, Any]]:
        """관련 HS코드 검색 (앞자리가 같은 제품들)"""
        try:
            # HS코드 앞자리가 같은 제품들 검색
            query = f"HS코드 {hs_prefix} 관련 제품"
            query_embedding = self.embedder.embed_text(query)
            
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            # 관련 제품 정보 추가
            for result in results:
                result["match_type"] = "related_hs_code"
                result["hs_prefix_match"] = hs_prefix
            
            return results
            
        except Exception as e:
            logger.error(f"관련 HS코드 검색 실패: {e}")
            return []
    
    def _normalize_country_name(self, country: str) -> str:
        """국가명 정규화"""
        # 일반적인 국가명 매핑
        country_mapping = {
            "미국": "미국", "USA": "미국", "United States": "미국",
            "중국": "중국", "China": "중국",
            "일본": "일본", "Japan": "일본",
            "독일": "독일", "Germany": "독일",
            "영국": "영국", "UK": "영국", "United Kingdom": "영국",
            "프랑스": "프랑스", "France": "프랑스",
            "이탈리아": "이탈리아", "Italy": "이탈리아",
            "캐나다": "캐나다", "Canada": "캐나다",
            "호주": "호주", "Australia": "호주",
            "인도": "인도", "India": "인도"
        }
        
        return country_mapping.get(country, country)
    
    def _build_where_condition(self, filter_by: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """필터링 조건 구성 (data_type 지원 강화)"""
        if not filter_by:
            return None
        
        # 지원되는 메타데이터 필드 확장
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
            # 여러 조건을 $and로 결합
            return {"$and": conditions}
    
    def _expand_with_related_info(self, results: List[Dict[str, Any]], max_total: int) -> List[Dict[str, Any]]:
        """관련 정보로 검색 결과 확장"""
        expanded_results = results.copy()
        
        # 기존 결과에서 HS코드나 국가 정보 추출하여 관련 문서 찾기
        seen_ids = {result.get("id", "") for result in results}
        
        for result in results[:3]:  # 상위 3개 결과만 확장
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
            
            # 국가 기반 확장
            country = metadata.get("country", "")
            if country:
                related_country = self.search_by_country(country, 2)
                for related in related_country:
                    if related.get("id", "") not in seen_ids:
                        related["reference_info"] = {"is_related": True, "related_to": result.get("id", "")}
                        expanded_results.append(related)
                        seen_ids.add(related.get("id", ""))
        
        return expanded_results[:max_total]
    
    def _post_process_results(self, results: List[Dict[str, Any]], processed_query: Dict[str, Any], search_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """검색 결과 후처리 (search_context 기반 부스팅 포함)"""
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
            x.get("importance_score", 0) * 0.3 + 
            x.get("similarity", 0) * 0.7
        ), reverse=True)
        
        return results
    
    def _apply_search_context_boost(self, result: Dict[str, Any], search_context: Dict[str, Any]) -> float:
        """검색 컨텍스트 기반 부스팅 점수 계산"""
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
        
        return min(boost_score, 0.5)  # 최대 0.5로 제한
    
    def _calculate_importance_score(self, result: Dict[str, Any], processed_query: Dict[str, Any]) -> float:
        """문서 중요도 점수 계산"""
        score = 0.0
        metadata = result.get("metadata", {})
        
        # 동식물 수입 규제 데이터 최우선 처리
        data_source = metadata.get("data_source", "")
        if data_source == "동식물허용금지지역":
            score += 0.5  # 동식물 규제는 최고 중요도
            
            # 동식물 관련 추가 가중치
            priority = metadata.get("priority", 0)
            regulation_intensity = metadata.get("regulation_intensity", "")
            
            # 🔧 타입 안전성: priority를 정수로 변환
            try:
                priority_int = int(priority) if priority else 0
            except (ValueError, TypeError):
                priority_int = 0
            
            if priority_int >= 2:  # 높은 우선순위
                score += 0.2
            if regulation_intensity == "high":  # 높은 규제 강도
                score += 0.15
            if metadata.get("has_global_prohibition", False):  # 전역 금지
                score += 0.1
                
        elif "규제" in data_source:
            score += 0.3  # 일반 규제 정보
        
        # 규제 유형별 가중치
        regulation_type = metadata.get("regulation_type", "")
        if regulation_type == "import_regulations":
            score += 0.25  # 수입 규제는 높은 중요도
        elif "restrictions" in regulation_type:
            score += 0.2
        elif "prohibitions" in regulation_type:
            score += 0.3  # 금지 품목은 매우 중요
        
        # HS코드 매칭 가중치
        if result.get("match_type") == "exact_hs_code":
            score += 0.4
        elif result.get("match_type") == "related_hs_code":
            score += 0.2
        
        # 상태별 가중치
        is_active = metadata.get("is_active", False)
        if is_active:
            score += 0.15  # 활성 규제는 중요도 높음
            
        status = metadata.get("status", "")
        if "규제중" in status:
            score += 0.2  # 실제 적용 중인 규제
        elif "조사중" in status:
            score += 0.1
        
        # 데이터 타입별 가중치
        data_type = metadata.get("data_type", "")
        if data_type == "trade_regulation":
            score += 0.1  # 무역 규제 데이터
        
        return min(score, 1.0)  # 최대 1.0으로 제한
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 결과 제거"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get("id", "")
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """검색 통계 정보 반환"""
        try:
            stats = self.vector_store.get_collection_stats()
            stats["retriever_type"] = "LangChain_TradeInfoRetriever"
            return stats
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {e}")
            return {"error": str(e)}
    
    def _generate_llm_metadata_filters(self, query: str, search_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        LLM을 사용해서 쿼리에 맞는 메타데이터 필터를 지능적으로 생성
        
        Args:
            query (str): 사용자 질의
            search_context (Optional[Dict[str, Any]]): 에이전트별 검색 컨텍스트
            
        Returns:
            Dict[str, Any]: 생성된 메타데이터 필터
        """
        try:
            # 1. 의도 분석으로 필터 힌트 추출
            intent_info = self.query_normalizer.extract_intent(query)
            
            filters = {}
            
            # 2. 데이터 타입 결정
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
            
            # 3. 동물/식물 타입 결정
            key_concepts = intent_info.get("key_concepts", [])
            detected_items = []
            
            # 농산물/식물 키워드 감지
            plant_keywords = ['아보카도', '바나나', '딸기', '사과', '배', '포도', '체리', '복숭아', 
                            '오렌지', '레몬', '라임', '키위', '망고', '파인애플', '멜론', '수박',
                            '쌀', '밀', '옥수수', '콩', '팥', '녹두', '감자', '고구마', '양파', '마늘']
            
            # 동물/축산물 키워드 감지  
            animal_keywords = ['돼지고기', '소고기', '닭고기', '오리고기', '양고기', '생선', '새우', '게',
                             '우유', '치즈', '버터', '요구르트', '계란', '꿀']
            
            for concept in key_concepts:
                if concept in plant_keywords:
                    detected_items.append(concept)
                    filters["animal_plant_type"] = "식물"
                    filters["product_category"] = "식물"
                elif concept in animal_keywords:
                    detected_items.append(concept)
                    filters["animal_plant_type"] = "동물"
                    filters["product_category"] = "동물"
            
            # 4. 제품명 정확 매칭 필터
            if detected_items:
                # 가장 가능성 높은 제품명으로 정확 매칭 시도
                primary_product = detected_items[0]
                logger.info(f"🎯 제품명 정확 매칭 필터: {primary_product}")
            
            # 5. 컨텍스트 기반 추가 필터
            if search_context:
                priority_sources = search_context.get("priority_data_sources", [])
                if priority_sources:
                    # 첫 번째 우선순위 소스 사용
                    filters["data_source"] = priority_sources[0]
                
                domain_hints = search_context.get("domain_hints", [])
                if "animal_plant_import" in domain_hints:
                    filters["data_type"] = "trade_regulation"
                    filters["regulation_type"] = "import_regulations"
            
            logger.debug(f"🤖 LLM 생성 필터: {filters}")
            return filters
            
        except Exception as e:
            logger.error(f"LLM 메타데이터 필터 생성 실패: {e}")
            return {}
    
    def _merge_filters(self, user_filters: Optional[Dict[str, Any]], llm_filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자 제공 필터와 LLM 생성 필터를 지능적으로 병합
        
        Args:
            user_filters: 사용자가 명시적으로 제공한 필터
            llm_filters: LLM이 생성한 필터
            
        Returns:
            Dict[str, Any]: 병합된 필터
        """
        if not user_filters:
            return llm_filters
        
        if not llm_filters:
            return user_filters or {}
        
        # 사용자 필터가 우선순위를 가지되, LLM 필터로 보완
        merged = llm_filters.copy()
        merged.update(user_filters)  # 사용자 필터로 덮어쓰기
        
        return merged
    
    def get_langchain_retriever(self, 
                               search_type: str = "similarity",
                               search_kwargs: Optional[Dict[str, Any]] = None):
        """
        LangChain 표준 Retriever 객체 반환 (체인 연결용)
        
        Args:
            search_type (str): 검색 타입 ("similarity", "mmr", "similarity_score_threshold")
            search_kwargs (Optional[Dict[str, Any]]): 검색 파라미터
            
        Returns:
            Retriever: LangChain Retriever 객체
        """
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vector_store.get_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
