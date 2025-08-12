"""
Trade Information Retriever Module

무역 정보 CSV 데이터에서 관련 정보를 검색하고 HS코드, 국가별 규제 등을 활용한 확장 검색 기능
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
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
        
        # 🚀 LLM 분류 결과 캐시 (성능 최적화)
        self._llm_classification_cache = {}  # query → classification 결과
        self._cache_max_size = 100  # 최대 캐시 크기
        self._cache_ttl = 3600  # 1시간 TTL
        
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
            # 🎯 입력 쿼리 로깅 및 정규화
            logger.info(f"\n🔍 ===== 무역 정보 검색 시작 ===== ")
            logger.info(f"📝 원본 쿼리: '{raw_query}'")
            logger.info(f"⚙️ 검색 파라미터: top_k={top_k}, threshold={similarity_threshold}")
            if filter_by:
                logger.info(f"🎯 사용자 제공 필터: {filter_by}")
            if search_context:
                logger.info(f"🎨 검색 컨텍스트: {search_context}")
            
            # 1. LLM 기반 메타데이터 필터 생성 (핵심 개선 기능)
            logger.info(f"🤖 LLM 메타데이터 필터 생성 중...")
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
            logger.info(f"🧠 LLM 필터 결과: {llm_filters}")
            logger.info(f"🎯 최종 적용 필터: {filter_by}")
            
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
            
            # 5. 동적 벡터 검색 (스마트 top_k 조정)
            optimized_top_k, search_strategy = self._optimize_search_parameters(top_k, filter_by, processed_query)
            logger.info(f"🔍 최적화된 검색 시작 (top_k: {optimized_top_k}, 전략: {search_strategy})")
            
            # 필터링 조건 적용
            where_condition = self._build_where_condition(filter_by)
            
            logger.info(f"🚀 벡터 검색 실행...")
            primary_results = self._execute_smart_search(
                query_embedding=query_embedding,
                top_k=optimized_top_k,
                where_condition=where_condition,
                search_strategy=search_strategy,
                original_query=raw_query
            )
            
            # 검색 결과 상세 로깅
            logger.info(f"📊 벡터 검색 결과: {len(primary_results)}개 문서")
            if primary_results:
                # 데이터 소스별 분포 로깅
                source_distribution = {}
                for result in primary_results:
                    source = result.get('metadata', {}).get('data_source', 'unknown')
                    source_distribution[source] = source_distribution.get(source, 0) + 1
                logger.info(f"📈 데이터 소스 분포: {source_distribution}")
                
                # 상위 3개 결과의 similarity 점수 로깅
                top_scores = [r.get('similarity', 0.0) for r in primary_results[:3]]
                logger.info(f"🎯 상위 유사도 점수: {top_scores}")
            else:
                logger.warning(f"⚠️ 벡터 검색 결과 없음 - fallback 필요")
            
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
            
            # 최종 결과 요약 로깅
            logger.info(f"📊 ===== 검색 완료: {len(final_results)}개 결과 ===== ")
            if final_results:
                # 최종 결과 품질 평가
                avg_similarity = sum(r.get('similarity', 0.0) for r in final_results) / len(final_results)
                logger.info(f"📈 평균 유사도: {avg_similarity:.3f}")
                
                # regulation_type 분포
                reg_types = {}
                for result in final_results:
                    reg_type = result.get('metadata', {}).get('regulation_type', 'unknown')
                    reg_types[reg_type] = reg_types.get(reg_type, 0) + 1
                logger.info(f"🏷️ 규제 타입 분포: {reg_types}")
            
            logger.info(f"===== 검색 프로세스 종료 ===== \n")
            logger.info(f"✅ {len(final_results)}개 결과 반환 (요청된 top_k: {top_k})")
            
            # 7.5. 결과 품질 평가 및 적응형 검색 확장
            quality_score = self._evaluate_result_quality(final_results, processed_query)
            logger.info(f"📊 결과 품질 평가: {quality_score:.2f} (결과 수: {len(final_results)})")
            
            # 품질 기반 확장 검색 결정
            needs_expansion = (
                len(final_results) < max(3, top_k // 2) or  # 결과 수 부족
                quality_score < 0.6 or  # 품질 점수 낮음
                (len(final_results) < top_k and quality_score < 0.8)  # 요청 수량 미달이면서 품질 보통
            )
            
            if needs_expansion and search_strategy != "expanded":
                logger.info(f"🔄 확장 검색 필요 (결과: {len(final_results)}개, 품질: {quality_score:.2f})")
                expanded_results = self._execute_comprehensive_fallback_search(
                    raw_query, top_k, filter_by, processed_query, quality_score
                )
                
                # 확장된 결과가 더 나은지 평가
                if len(expanded_results) > 0:
                    expanded_quality = self._evaluate_result_quality(expanded_results, processed_query)
                    if len(expanded_results) > len(final_results) or expanded_quality > quality_score:
                        logger.info(f"📈 확장 검색 성공: {len(expanded_results)}개 결과, 품질: {expanded_quality:.2f}")
                        return expanded_results[:top_k]
            
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
        LLM을 사용해서 쿼리에 맞는 메타데이터 필터를 지능적으로 생성 (강화된 버전)
        
        Args:
            query (str): 사용자 질의
            search_context (Optional[Dict[str, Any]]): 에이전트별 검색 컨텍스트
            
        Returns:
            Dict[str, Any]: 생성된 메타데이터 필터
        """
        try:
            # 1. LLM 의도 분석으로 필터 힌트 추출
            intent_info = self.query_normalizer.extract_intent(query)
            
            # 2. 컨텍스트 기반 우선순위 필터 (search_context가 제공한 힌트 우선 적용)
            filters = self._apply_context_based_filters(search_context)
            
            # 3. LLM 의도 분석을 통한 스마트 필터 매핑
            smart_filters = self._generate_smart_filter_mapping(intent_info, query)
            
            # 4. 필터 병합 (컨텍스트 > 스마트 매핑 > 기본값 순)
            final_filters = self._merge_filter_priorities(filters, smart_filters, search_context)
            
            # 5. 제품별 특화 필터 추가
            product_filters = self._extract_product_specific_filters(intent_info)
            final_filters.update(product_filters)
            
            logger.info(f"🤖 스마트 필터 생성: {final_filters}")
            return final_filters
            
        except Exception as e:
            logger.error(f"LLM 메타데이터 필터 생성 실패: {e}")
            # 기본 규제 데이터로 fallback
            return {"data_type": "trade_regulation"}
    
    def _apply_context_based_filters(self, search_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        검색 컨텍스트를 기반으로 우선순위 필터 적용
        
        Args:
            search_context: 에이전트별 검색 컨텍스트
            
        Returns:
            Dict[str, Any]: 컨텍스트 기반 필터
        """
        filters = {}
        
        if not search_context:
            return filters
        
        # 에이전트 타입별 기본 필터
        agent_type = search_context.get("agent_type")
        if agent_type == "regulation_agent":
            filters["data_type"] = "trade_regulation"
        elif agent_type == "consultation_agent":
            filters["data_type"] = "consultation_case"
        
        # 우선순위 데이터 소스 적용
        priority_sources = search_context.get("priority_data_sources", [])
        if priority_sources:
            filters["data_source"] = priority_sources[0]
        
        # 규제 타입 힌트 적용 (최우선)
        regulation_type_hint = search_context.get("regulation_type_hint")
        if regulation_type_hint:
            filters["regulation_type"] = regulation_type_hint
            logger.info(f"🎯 컨텍스트 규제 타입: {regulation_type_hint}")
        
        return filters
    
    def _generate_smart_filter_mapping(self, intent_info: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        🚀 통합 LLM 기반 지능형 필터 매핑 (하드코딩 매핑 완전 제거)
        
        Args:
            intent_info: LLM이 추출한 의도 정보 (사용하지 않음, 호환성 유지)
            query: 원본 질의
            
        Returns:
            Dict[str, Any]: 완전한 지능형 필터
        """
        try:
            # 🧠 모든 규제 유형을 LLM이 한 번에 분류
            llm_classification = self._classify_regulation_query_with_llm(query)
            
            # fallback이 필요한 경우 처리
            if llm_classification.get("fallback_needed") or llm_classification.get("regulation_category") in ["error", "unclear"]:
                logger.warning(f"🔄 LLM 분류 실패, 기본 규제 데이터로 fallback: {llm_classification.get('reasoning', '')}")
                return self._apply_basic_fallback_filters(query)
            
            # 직접 data_source와 regulation_type 매핑
            data_source = llm_classification.get("data_source")
            regulation_type = llm_classification.get("regulation_type")
            confidence = llm_classification.get("confidence", 0.0)
            
            # 신뢰도가 너무 낮은 경우 fallback
            if confidence < 0.3:
                logger.warning(f"🔄 LLM 분류 신뢰도 부족 ({confidence:.2f}), fallback 적용")
                return self._apply_basic_fallback_filters(query)
            
            if not data_source or not regulation_type:
                logger.warning(f"🤖 LLM 분류 불완전: data_source={data_source}, regulation_type={regulation_type}")
                return self._apply_basic_fallback_filters(query)
            
            # 기본 필터 구성
            filters = {
                "data_type": "trade_regulation",
                "data_source": data_source,
                "regulation_type": regulation_type
            }
            
            # 추가 메타데이터 필터 적용
            detected_country = llm_classification.get("detected_country")
            if detected_country and detected_country.lower() != "null":
                regulation_category = llm_classification.get("regulation_category", "")
                if "foreign" in regulation_category:
                    # 외국 규제의 경우 regulating_country 필터 추가
                    filters["regulating_country"] = detected_country
                elif regulation_category in ["export_restrictions", "export_prohibitions"]:
                    # 수출제한/금지는 품목 기준 규제이므로 국가 필터 불필요
                    # affected_country 메타데이터가 존재하지 않아 필터링 시 0개 결과 발생 방지
                    pass
                
            # 동식물 제품 특별 필터
            product_info = llm_classification.get("product_info", {})
            if product_info.get("is_animal_plant"):
                filters["animal_plant_type"] = "동물|식물"  # 동식물 구분
            
            # HS코드 언급 시 HS코드 필터 활성화 (향후 확장용)
            if product_info.get("hs_code_mentioned"):
                filters["has_hs_code"] = True
            
            category = llm_classification.get("regulation_category", "unknown")
            reasoning = llm_classification.get("reasoning", "")
            
            logger.info(f"🚀 통합 LLM 분류 성공: {category} → {data_source} (신뢰도: {confidence:.2f})")
            logger.info(f"📊 분류 근거: {reasoning[:100]}..." if len(reasoning) > 100 else f"📊 분류 근거: {reasoning}")
            
            return filters
            
        except Exception as e:
            logger.error(f"통합 LLM 필터 매핑 실패: {e}")
            # 기본 fallback
            return self._apply_basic_fallback_filters(query)
    
    def _classify_regulation_query_with_llm(self, query: str) -> Dict[str, Any]:
        """
        🚀 완전 통합 LLM 기반 무역 규제 분류 시스템
        
        모든 규제 유형을 한 번에 분류하여 하드코딩 매핑 제거
        
        Args:
            query: 사용자 질의
            
        Returns:
            Dict[str, Any]: 완전한 분류 및 필터 정보
        """
        try:
            # 🚀 캐시 확인 (성능 최적화)
            cache_key = query.lower().strip()
            if cache_key in self._llm_classification_cache:
                cached_result = self._llm_classification_cache[cache_key]
                # TTL 검사
                import time
                if time.time() - cached_result.get("cached_at", 0) < self._cache_ttl:
                    logger.info(f"💾 LLM 분류 캐시 적중: {cache_key[:30]}...")
                    return cached_result["classification"]
                else:
                    # 만료된 캐시 제거
                    del self._llm_classification_cache[cache_key]
            
            classification_prompt = f"""
다음 무역 규제 질의를 정확히 분석하여 최적의 데이터 소스와 필터를 결정해주세요:

질의: "{query}"

## 🎯 분류할 규제 유형 (data_source 매핑):

1. **외국 규제** → "수입규제DB_전체"
   - 외국이 한국 제품에 거는 규제: 반덤핑, 세이프가드, 수입제한 등
   - 키워드: [국가명] + "거는", "규제", "반덤핑", "세이프가드", "수입제한"
   - 예: "베트남이 한국에 거는 규제", "인도 반덤핑", "미국 세이프가드"

2. **한국 수출제한** → "수출제한품목"  
   - 한국이 특정 품목의 수출을 제한
   - 키워드: "수출제한", "수출 제한", "내보낼 수 없는", "수출 규제"
   - 예: "HS코드 수출제한", "광물 수출제한"

3. **한국 수출금지** → "수출금지품목"
   - 한국이 특정 품목의 수출을 완전 금지  
   - 키워드: "수출금지", "수출 금지", "수출 불가", "수출 차단"
   - 예: "고래고기 수출금지", "멸종위기종 수출금지"

4. **한국 수입제한** → "수입제한품목"
   - 한국이 특정 품목의 수입을 제한 (승인 필요)
   - 키워드: "수입제한", "수입 제한", "승인 필요", "수입 규제"
   - 예: "항공기 부품 수입제한", "플라스틱 수입제한"

5. **동식물 수입규제** → "동식물허용금지지역"
   - 동물, 식물, 농축산품 수입 허용/금지 국가 정보
   - 키워드: 동물/식물명, "수입 허용", "검역", "농산물", "축산물"
   - 예: "딸기 수입", "소고기 허용국가", "아보카도 검역"

## 🎯 분석 요소:
- **주체 국가**: 규제하는 국가 (외국 vs 한국)
- **대상 품목**: 구체적 품목명, HS코드, 카테고리
- **규제 강도**: 제한 vs 금지 vs 허용 조건
- **방향성**: 수출 vs 수입 + 한국↔외국 방향

응답 JSON 형식:
{{
    "regulation_category": "foreign_regulation|export_restrictions|export_prohibitions|import_restrictions|animal_plant_import",
    "data_source": "수입규제DB_전체|수출제한품목|수출금지품목|수입제한품목|동식물허용금지지역", 
    "regulation_type": "export_destination_restrictions|export_restrictions|export_prohibitions|import_restrictions|import_regulations",
    "detected_country": "국가명 또는 null",
    "product_info": {{
        "is_animal_plant": true/false,
        "hs_code_mentioned": true/false,
        "product_category": "추정 카테고리 또는 null"
    }},
    "regulation_direction": "foreign_to_korea|korea_export|korea_import|unclear",
    "confidence": 0.0-1.0,
    "reasoning": "분류 근거 설명"
}}

## 🔍 분류 예시:
- "마다가스카르가 현재 행하는 규제들" 
  → {{"regulation_category": "foreign_regulation", "data_source": "수입규제DB_전체"}}
  
- "딸기 수입할 때 주의사항"
  → {{"regulation_category": "animal_plant_import", "data_source": "동식물허용금지지역"}}
  
- "HS코드 2505 수출제한 있나요?"
  → {{"regulation_category": "export_restrictions", "data_source": "수출제한품목"}}

정확한 분류를 위해 키워드, 문맥, 주체-객체 관계를 종합 분석하세요.
"""

            response = self.query_normalizer.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 추출 시도
            import json
            import re
            
            # JSON 부분만 추출
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                
                # 🚀 캐시에 저장 (성능 최적화)
                import time
                cached_entry = {
                    "classification": result_json,
                    "cached_at": time.time()
                }
                
                # 캐시 크기 제한 관리
                if len(self._llm_classification_cache) >= self._cache_max_size:
                    # 가장 오래된 엔트리 제거 (FIFO)
                    oldest_key = min(self._llm_classification_cache.keys(), 
                                    key=lambda k: self._llm_classification_cache[k].get("cached_at", 0))
                    del self._llm_classification_cache[oldest_key]
                
                self._llm_classification_cache[cache_key] = cached_entry
                
                logger.info(f"🤖 LLM 규제 분류: {result_json.get('regulation_category', 'unknown')} → {result_json.get('data_source', 'none')}")
                return result_json
            else:
                logger.warning(f"LLM 응답에서 JSON 추출 실패: {result_text}")
                # 더 나은 기본값 반환
                return {
                    "regulation_category": "unclear",
                    "data_source": None,
                    "regulation_type": None,
                    "confidence": 0.0,
                    "reasoning": "JSON 파싱 실패"
                }
                
        except Exception as e:
            logger.error(f"LLM 규제 분류 실패: {e}")
            # 더 나은 fallback 처리
            return {
                "regulation_category": "error",
                "data_source": None,
                "regulation_type": None,
                "confidence": 0.0,
                "reasoning": f"LLM 분류 오류: {str(e)}",
                "fallback_needed": True
            }
    
    def _apply_basic_fallback_filters(self, query: str) -> Dict[str, Any]:
        """
        🔄 LLM 분류 실패 시 기본 fallback 필터 적용
        
        간단한 키워드 매칭으로 최소한의 분류 수행
        
        Args:
            query: 원본 질의
            
        Returns:
            Dict[str, Any]: 기본 fallback 필터
        """
        query_lower = query.lower()
        
        # 🔍 키워드 기반 기본 분류 (LLM 대비 정확도 낮음)
        if any(keyword in query_lower for keyword in ['수출금지', '수출 금지', '금지품목']):
            logger.info(f"📋 키워드 기반 fallback: 수출금지품목")
            return {
                "data_type": "trade_regulation",
                "data_source": "수출금지품목",
                "regulation_type": "export_prohibitions"
            }
        elif any(keyword in query_lower for keyword in ['수출제한', '수출 제한']):
            logger.info(f"📋 키워드 기반 fallback: 수출제한품목")
            return {
                "data_type": "trade_regulation",
                "data_source": "수출제한품목",
                "regulation_type": "export_restrictions"
            }
        elif any(keyword in query_lower for keyword in ['동식물', '농산물', '축산물', '검역', '아보카도', '딸기', '소고기']):
            logger.info(f"📋 키워드 기반 fallback: 동식물허용금지지역")
            return {
                "data_type": "trade_regulation",
                "data_source": "동식물허용금지지역",
                "regulation_type": "import_regulations"
            }
        elif any(keyword in query_lower for keyword in ['수입제한', '수입 제한']):
            logger.info(f"📋 키워드 기반 fallback: 수입제한품목")
            return {
                "data_type": "trade_regulation",
                "data_source": "수입제한품목",
                "regulation_type": "import_restrictions"
            }
        elif any(keyword in query_lower for keyword in ['반덤핑', '세이프가드', '규제', '외국', '미국', '중국', '일본', '베트남']):
            logger.info(f"📋 키워드 기반 fallback: 수입규제DB_전체")
            return {
                "data_type": "trade_regulation",
                "data_source": "수입규제DB_전체",
                "regulation_type": "export_destination_restrictions"
            }
        else:
            # 최종 기본값
            logger.info(f"📋 최종 기본값 fallback: trade_regulation 전체")
            return {"data_type": "trade_regulation"}
    
    def _apply_enhanced_fallback_search(self, query: str, filters: Dict[str, Any]) -> List[Dict]:
        """
        🔄 강화된 Fallback 검색 시스템 - 단계적 필터 완화
        
        Args:
            query: 검색 쿼리
            filters: 원본 필터
            
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            # 단계적 fallback 전략
            fallback_filters = [
                filters,  # 원본 필터
                {k: v for k, v in filters.items() if k in ["data_type", "data_source"]},  # 기본 필터만
                {"data_type": "trade_regulation"},  # 최소 필터
            ]
            
            for i, fallback_filter in enumerate(fallback_filters, 1):
                try:
                    query_embedding = self.embedder.embed_text(query)
                    results = self.vector_store.search_similar(
                        query_embedding=query_embedding,
                        top_k=12,
                        where=fallback_filter
                    )
                    
                    if results:
                        logger.info(f"✅ Fallback 검색 성공 (단계 {i}): {len(results)}개 결과")
                        logger.debug(f"📊 적용된 필터: {fallback_filter}")
                        return results
                    else:
                        logger.warning(f"⚠️ Fallback 단계 {i} 실패: 0개 결과")
                        
                except Exception as step_error:
                    logger.error(f"❌ Fallback 단계 {i} 오류: {step_error}")
                    continue
            
            logger.error(f"❌ 모든 Fallback 검색 실패")
            return []
            
        except Exception as e:
            logger.error(f"❌ Fallback 검색 시스템 오류: {e}")
            return []
    
    def _get_category_based_filters(self, trade_category: str) -> Dict[str, Any]:
        """⚠️ DEPRECATED: 기존 카테고리 기반 필터 매핑 (LLM 통합 분류로 대체됨)"""
        logger.warning(f"⚠️ DEPRECATED 함수 호출: _get_category_based_filters({trade_category}) - LLM 분류 시스템 사용 권장")
        
        # 기존 호환성을 위해 유지하되 새로운 fallback으로 리다이렉트
        return self._apply_basic_fallback_filters(trade_category)
    
    def _extract_product_specific_filters(self, intent_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED: 제품별 특화 필터 추출 (LLM 통합 분류로 대체됨)
        
        LLM이 모든 제품 분류를 담당하므로 이 함수는 더 이상 필요하지 않음
        
        Args:
            intent_info: LLM 의도 분석 결과 (사용하지 않음)
            
        Returns:
            Dict[str, Any]: 빈 딕셔너리 (LLM이 모든 분류 처리)
        """
        logger.debug(f"⚠️ DEPRECATED 함수 호출: _extract_product_specific_filters - LLM 분류가 모든 제품 분류 처리")
        
        # LLM이 모든 제품 분류를 처리하므로 빈 딕셔너리 반환
        return {}
    
    def _merge_filter_priorities(self, context_filters: Dict[str, Any], 
                               smart_filters: Dict[str, Any],
                               search_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        여러 소스의 필터를 우선순위에 따라 병합 (개선된 우선순위 로직)
        
        🎯 NEW 우선순위: 스마트 매핑(LLM) > 컨텍스트 힌트 > 기본값
        
        Args:
            context_filters: 컨텍스트 기반 필터
            smart_filters: LLM 스마트 매핑 필터
            search_context: 원본 검색 컨텍스트
            
        Returns:
            Dict[str, Any]: 우선순위 적용된 최종 필터
        """
        # 🎯 1. 스마트 매핑(LLM)을 기본으로 시작 (가장 높은 우선순위)
        merged = smart_filters.copy()
        
        # 2. 컨텍스트 필터는 스마트 필터가 없는 경우에만 적용
        for key, value in context_filters.items():
            if key not in merged or not merged[key]:  # LLM이 분류하지 못한 경우만
                merged[key] = value
                logger.debug(f"🔧 컨텍스트 필터 보완: {key} = {value}")
        
        # 3. 최소한 data_type은 보장
        if "data_type" not in merged or not merged["data_type"]:
            agent_type = search_context.get("agent_type") if search_context else None
            if agent_type == "regulation_agent":
                merged["data_type"] = "trade_regulation"
            elif agent_type == "consultation_agent":
                merged["data_type"] = "consultation_case"
            else:
                merged["data_type"] = "trade_regulation"  # 기본값
        
        # 4. 필터 품질 검증
        if merged.get("data_source") and merged.get("regulation_type"):
            logger.info(f"✅ 고품질 필터 병합 완료: {merged.get('data_source')} + {merged.get('regulation_type')}")
        else:
            logger.warning(f"⚠️ 부분적 필터 병합: data_source={merged.get('data_source')}, regulation_type={merged.get('regulation_type')}")
        
        return merged
    
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
    
    def _optimize_search_parameters(self, base_top_k: int, 
                                  filter_conditions: Optional[Dict[str, Any]], 
                                  processed_query: Dict[str, Any]) -> Tuple[int, str]:
        """
        쿼리 복잡도와 필터 조건을 기반으로 검색 매개변수를 동적 최적화
        
        Args:
            base_top_k: 기본 top_k 값
            filter_conditions: 적용된 필터 조건
            processed_query: 처리된 쿼리 정보
            
        Returns:
            Tuple[int, str]: (최적화된 top_k, 검색 전략)
        """
        try:
            # 1. 필터 신뢰도 평가
            filter_confidence = self._evaluate_filter_confidence(filter_conditions)
            
            # 2. 쿼리 복잡도 평가  
            query_complexity = self._evaluate_query_complexity(processed_query)
            
            # 3. 동적 top_k 계산
            if filter_confidence > 0.8:
                # 필터가 매우 정확한 경우 - 적은 수의 정확한 결과
                optimized_top_k = max(base_top_k, 8)
                search_strategy = "precision"
            elif filter_confidence > 0.6:
                # 필터가 어느 정도 정확한 경우 - 기본값
                optimized_top_k = base_top_k
                search_strategy = "balanced"
            else:
                # 필터 신뢰도가 낮은 경우 - 더 많은 결과를 가져와서 후처리
                optimized_top_k = min(base_top_k * 2, 20)
                search_strategy = "recall"
            
            # 4. 복잡한 쿼리는 더 많은 결과 필요
            if query_complexity > 0.7:
                optimized_top_k = min(optimized_top_k + 5, 25)
                
            logger.debug(f"🎯 검색 최적화: 필터신뢰도={filter_confidence:.2f}, 쿼리복잡도={query_complexity:.2f}, top_k={base_top_k}→{optimized_top_k}")
            
            return optimized_top_k, search_strategy
            
        except Exception as e:
            logger.warning(f"검색 매개변수 최적화 실패: {e}")
            return base_top_k, "standard"
    
    def _evaluate_filter_confidence(self, filters: Optional[Dict[str, Any]]) -> float:
        """
        적용된 필터의 신뢰도 평가
        
        Args:
            filters: 적용된 필터 조건들
            
        Returns:
            float: 필터 신뢰도 (0.0-1.0)
        """
        if not filters:
            return 0.0
        
        confidence = 0.0
        
        # data_source가 특정되어 있으면 높은 신뢰도
        if "data_source" in filters:
            confidence += 0.4
        
        # regulation_type이 특정되어 있으면 높은 신뢰도  
        if "regulation_type" in filters:
            confidence += 0.3
        
        # 제품별 필터가 있으면 추가 신뢰도
        if "animal_plant_type" in filters or "product_category" in filters:
            confidence += 0.2
        
        # data_type은 기본 필터이므로 낮은 신뢰도
        if "data_type" in filters:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _evaluate_query_complexity(self, processed_query: Dict[str, Any]) -> float:
        """
        쿼리 복잡도 평가
        
        Args:
            processed_query: 처리된 쿼리 정보
            
        Returns:
            float: 쿼리 복잡도 (0.0-1.0)
        """
        complexity = 0.0
        
        # 의도 복잡도
        intent = processed_query.get("intent", {})
        if intent.get("specificity") == "구체적":
            complexity += 0.3
        
        # 키 개념 수
        key_concepts = len(intent.get("key_concepts", []))
        complexity += min(key_concepts * 0.1, 0.3)
        
        # 쿼리 길이
        query_length = len(processed_query.get("normalized_query", ""))
        if query_length > 20:
            complexity += 0.2
        
        # 확장된 쿼리와 원본 쿼리 차이
        original_len = len(processed_query.get("normalized_query", ""))
        expanded_len = len(processed_query.get("expanded_query", ""))
        if expanded_len > original_len * 1.5:
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def _execute_smart_search(self, query_embedding: List[float], 
                             top_k: int, 
                             where_condition: Optional[Dict[str, Any]],
                             search_strategy: str,
                             original_query: str) -> List[Dict[str, Any]]:
        """
        검색 전략에 따른 스마트 검색 실행
        
        Args:
            query_embedding: 쿼리 임베딩
            top_k: 검색할 결과 수
            where_condition: 필터 조건
            search_strategy: 검색 전략
            original_query: 원본 쿼리
            
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            # LangChainVectorStore는 search_type 매개변수를 지원하지 않으므로 
            # 전략에 따라 다른 방식으로 처리
            
            if search_strategy == "precision":
                # 정밀도 우선 - 유사도 검색 후 높은 임계값 필터링
                results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=min(top_k * 2, 20),  # 더 많이 가져와서 필터링
                    where=where_condition
                )
                # 높은 점수만 유지 (정밀도 우선)
                filtered_results = [r for r in results if r.get("score", 0) >= 0.7]
                return filtered_results[:top_k] if filtered_results else results[:top_k]
                
            elif search_strategy == "recall":
                # 재현율 우선 - 더 많은 결과 수집 후 다양성 확보
                results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=min(top_k * 3, 30),  # 더 많은 결과 수집
                    where=where_condition
                )
                # 다양성 보장을 위해 다른 data_source에서 결과 분산 선택
                return self._ensure_result_diversity(results, top_k)
                
            else:
                # 균형 잡힌 검색 - 기본 유사도 검색
                return self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    where=where_condition
                )
            
        except Exception as e:
            logger.warning(f"스마트 검색 실행 실패: {e}")
            # 기본 검색으로 fallback
            return self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                where=where_condition
            )
    
    def _execute_fallback_search(self, query: str, 
                               expanded_top_k: int,
                               original_filters: Optional[Dict[str, Any]],
                               processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        결과가 부족할 때 실행하는 확장 검색 (점진적 필터 완화)
        
        Args:
            query: 원본 쿼리
            expanded_top_k: 확장된 top_k
            original_filters: 원본 필터
            processed_query: 처리된 쿼리 정보
            
        Returns:
            List[Dict[str, Any]]: 확장 검색 결과
        """
        try:
            logger.info("🔄 확장 검색 전략 실행: 점진적 필터 완화")
            
            # 1단계: regulation_type 제거하고 재검색
            relaxed_filters = original_filters.copy() if original_filters else {}
            if "regulation_type" in relaxed_filters:
                del relaxed_filters["regulation_type"]
                logger.info("📉 1단계: regulation_type 필터 완화")
                
                query_embedding = self.embedder.embed_text(processed_query["normalized_query"])
                where_condition = self._build_where_condition(relaxed_filters)
                
                results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=expanded_top_k,
                    where=where_condition
                )
                
                if len(results) >= 3:
                    return results
            
            # 2단계: data_source도 제거하고 재검색
            if "data_source" in relaxed_filters:
                del relaxed_filters["data_source"]
                logger.info("📉 2단계: data_source 필터 완화")
                
                where_condition = self._build_where_condition(relaxed_filters)
                results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=expanded_top_k,
                    where=where_condition
                )
                
                if len(results) >= 3:
                    return results
            
            # 3단계: data_type만 유지하고 전체 검색
            minimal_filters = {"data_type": "trade_regulation"}
            logger.info("📉 3단계: 최소 필터로 전체 검색")
            
            where_condition = self._build_where_condition(minimal_filters)
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=expanded_top_k,
                where=where_condition
            )
            
            return results
            
        except Exception as e:
            logger.error(f"확장 검색 실패: {e}")
            return []
    
    def _evaluate_result_quality(self, results: List[Dict[str, Any]], processed_query: Dict[str, Any]) -> float:
        """
        검색 결과의 품질을 평가
        
        Args:
            results: 검색 결과 리스트
            processed_query: 처리된 쿼리 정보
            
        Returns:
            float: 품질 점수 (0.0-1.0)
        """
        if not results:
            return 0.0
        
        total_score = 0.0
        
        for result in results:
            score = 0.0
            metadata = result.get("metadata", {})
            
            # 1. 중요도 점수 반영 (40%)
            importance = result.get("importance_score", 0.0)
            score += importance * 0.4
            
            # 2. 유사도 점수 반영 (30%) 
            similarity = result.get("score", 0.0)
            score += similarity * 0.3
            
            # 3. 메타데이터 완성도 평가 (15%)
            metadata_completeness = self._evaluate_metadata_completeness(metadata)
            score += metadata_completeness * 0.15
            
            # 4. 컨텍스트 부스팅 반영 (15%)
            context_boost = result.get("context_boost", 0.0)
            score += min(context_boost, 0.15)
            
            total_score += score
        
        # 평균 품질 점수 계산
        average_quality = total_score / len(results)
        
        # 결과 다양성 보너스
        diversity_bonus = self._evaluate_result_diversity(results)
        final_quality = min(average_quality + diversity_bonus, 1.0)
        
        return final_quality
    
    def _evaluate_metadata_completeness(self, metadata: Dict[str, Any]) -> float:
        """메타데이터 완성도 평가"""
        essential_fields = ["data_source", "data_type"]
        important_fields = ["regulation_type", "product_name", "country"]
        optional_fields = ["hs_code", "status", "priority"]
        
        score = 0.0
        
        # 필수 필드 체크 (60%)
        for field in essential_fields:
            if metadata.get(field):
                score += 0.3
        
        # 중요 필드 체크 (30%)
        for field in important_fields:
            if metadata.get(field):
                score += 0.1
        
        # 선택 필드 체크 (10%)
        for field in optional_fields:
            if metadata.get(field):
                score += 0.033
        
        return min(score, 1.0)
    
    def _evaluate_result_diversity(self, results: List[Dict[str, Any]]) -> float:
        """결과 다양성 평가"""
        if len(results) < 2:
            return 0.0
        
        unique_sources = set()
        unique_types = set()
        
        for result in results:
            metadata = result.get("metadata", {})
            unique_sources.add(metadata.get("data_source", ""))
            unique_types.add(metadata.get("regulation_type", ""))
        
        # 다양성 점수 계산
        source_diversity = min(len(unique_sources) / len(results), 1.0) * 0.05
        type_diversity = min(len(unique_types) / len(results), 1.0) * 0.05
        
        return source_diversity + type_diversity
    
    def _execute_comprehensive_fallback_search(self, query: str, 
                                             target_top_k: int,
                                             original_filters: Optional[Dict[str, Any]],
                                             processed_query: Dict[str, Any],
                                             current_quality: float) -> List[Dict[str, Any]]:
        """
        포괄적인 확장 검색 전략 (품질 기반 적응형 접근)
        
        Args:
            query: 원본 쿼리
            target_top_k: 목표 결과 수
            original_filters: 원본 필터
            processed_query: 처리된 쿼리 정보
            current_quality: 현재 결과 품질
            
        Returns:
            List[Dict[str, Any]]: 확장 검색 결과
        """
        try:
            logger.info(f"🔄 포괄적 확장 검색 시작 (현재 품질: {current_quality:.2f})")
            
            # 품질에 따른 확장 전략 선택
            if current_quality < 0.3:
                # 품질이 매우 낮음 - 전면적 재검색
                return self._execute_comprehensive_search(query, target_top_k, processed_query)
            elif current_quality < 0.6:
                # 품질이 낮음 - 점진적 확장 + 동의어 강화
                return self._execute_progressive_expansion(query, target_top_k * 2, original_filters, processed_query)
            else:
                # 품질이 보통 - 관련 검색으로 보완
                return self._execute_related_search_expansion(query, target_top_k, original_filters, processed_query)
            
        except Exception as e:
            logger.error(f"포괄적 확장 검색 실패: {e}")
            return []
    
    def _execute_comprehensive_search(self, query: str, target_top_k: int, processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """전면적 재검색 - 품질이 매우 낮을 때"""
        logger.info("📡 전면적 재검색 실행")
        
        # 동의어 확장된 쿼리로 필터 없이 검색
        expanded_query = processed_query.get("expanded_query", query)
        query_embedding = self.embedder.embed_text(expanded_query)
        
        # data_type만 유지하고 광범위 검색
        minimal_filters = {"data_type": "trade_regulation"}
        where_condition = self._build_where_condition(minimal_filters)
        
        results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=target_top_k * 2,  # 더 많은 결과 가져와서 후처리
            where=where_condition,
            # search_type="mmr"  # 다양성 확보
        )
        
        return results
    
    def _execute_progressive_expansion(self, query: str, 
                                     expanded_top_k: int,
                                     original_filters: Optional[Dict[str, Any]],
                                     processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """점진적 확장 검색 - 단계별 필터 완화 + 쿼리 확장"""
        logger.info("🔄 점진적 확장 검색 실행")
        
        best_results = []
        query_embedding = self.embedder.embed_text(processed_query.get("normalized_query", query))
        
        # 1단계: 쿼리 확장 + 원본 필터
        if original_filters:
            logger.info("📈 1단계: 쿼리 확장 + 원본 필터")
            expanded_query = processed_query.get("expanded_query", query)
            expanded_embedding = self.embedder.embed_text(expanded_query)
            
            where_condition = self._build_where_condition(original_filters)
            results = self.vector_store.search_similar(
                query_embedding=expanded_embedding,
                top_k=expanded_top_k,
                where=where_condition
            )
            
            if len(results) >= 3:
                return results
            best_results.extend(results)
        
        # 2단계: 관련 키워드 확장 검색
        logger.info("📈 2단계: 관련 키워드 확장")
        related_results = self._search_with_related_keywords(query, expanded_top_k, processed_query)
        best_results.extend(related_results)
        
        # 3단계: 카테고리 기반 확장
        logger.info("📈 3단계: 카테고리 기반 확장")
        category_results = self._search_by_inferred_category(processed_query, expanded_top_k)
        best_results.extend(category_results)
        
        # 중복 제거 및 품질순 정렬
        unique_results = self._deduplicate_results(best_results)
        return unique_results[:expanded_top_k]
    
    def _search_with_related_keywords(self, query: str, top_k: int, processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """관련 키워드를 사용한 확장 검색"""
        try:
            intent = processed_query.get("intent", {})
            key_concepts = intent.get("key_concepts", [])
            
            # 키 개념들로 확장 쿼리 생성
            if key_concepts:
                extended_query = f"{query} {' '.join(key_concepts[:3])}"  # 상위 3개 개념만 사용
                query_embedding = self.embedder.embed_text(extended_query)
                
                # 제한적 필터로 검색
                basic_filters = {"data_type": "trade_regulation"}
                where_condition = self._build_where_condition(basic_filters)
                
                return self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    where=where_condition
                )
            
            return []
            
        except Exception as e:
            logger.warning(f"관련 키워드 검색 실패: {e}")
            return []
    
    def _search_by_inferred_category(self, processed_query: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """추론된 카테고리 기반 검색"""
        try:
            intent = processed_query.get("intent", {})
            trade_category = intent.get("trade_category", "")
            
            if not trade_category or trade_category == "일반":
                return []
            
            # 카테고리별 일반화된 쿼리 생성
            category_queries = {
                "수출제한": "수출 제한 품목 규제",
                "수입규제": "수입 규제 제한 품목",
                "동식물수입규제": "동식물 수입 허용 국가 규제",
                "반덤핑": "반덤핑 관세 규제",
                "세이프가드": "세이프가드 긴급수입제한"
            }
            
            category_query = category_queries.get(trade_category)
            if category_query:
                query_embedding = self.embedder.embed_text(category_query)
                
                return self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    where={"data_type": {"$eq": "trade_regulation"}}
                )
            
            return []
            
        except Exception as e:
            logger.warning(f"카테고리 기반 검색 실패: {e}")
            return []
    
    def _execute_related_search_expansion(self, query: str,
                                        target_top_k: int,
                                        original_filters: Optional[Dict[str, Any]],
                                        processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """관련 검색으로 결과 보완 - 품질이 보통일 때"""
        logger.info("🔗 관련 검색 확장 실행")
        
        results = []
        
        # 현재 쿼리의 주요 키워드 추출
        key_concepts = processed_query.get("intent", {}).get("key_concepts", [])
        
        # 각 키 개념별로 관련 검색 수행
        for concept in key_concepts[:2]:  # 상위 2개 개념만
            concept_query = f"{concept} 관련 규제 정보"
            query_embedding = self.embedder.embed_text(concept_query)
            
            # 완화된 필터 사용
            relaxed_filters = original_filters.copy() if original_filters else {}
            if "regulation_type" in relaxed_filters:
                del relaxed_filters["regulation_type"]
            
            where_condition = self._build_where_condition(relaxed_filters)
            
            concept_results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=target_top_k // 2,
                where=where_condition
            )
            
            # 관련성 표시
            for result in concept_results:
                result["expansion_type"] = "concept_related"
                result["related_concept"] = concept
            
            results.extend(concept_results)
        
        return self._deduplicate_results(results)
    
    
    def _ensure_result_diversity(self, results: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """
        결과의 다양성을 보장하여 다양한 데이터 소스에서 결과 선택
        
        Args:
            results: 전체 검색 결과
            target_count: 목표 결과 수
            
        Returns:
            List[Dict[str, Any]]: 다양성이 보장된 결과
        """
        if not results or len(results) <= target_count:
            return results[:target_count]
        
        # 데이터 소스별로 그룹화
        source_groups = {}
        for result in results:
            data_source = result.get("metadata", {}).get("data_source", "unknown")
            if data_source not in source_groups:
                source_groups[data_source] = []
            source_groups[data_source].append(result)
        
        # 각 소스에서 균등하게 선택
        selected_results = []
        sources = list(source_groups.keys())
        
        # 라운드 로빈 방식으로 선택
        source_index = 0
        while len(selected_results) < target_count and any(source_groups.values()):
            current_source = sources[source_index % len(sources)]
            
            if source_groups[current_source]:
                selected_results.append(source_groups[current_source].pop(0))
            
            source_index += 1
            
            # 무한 루프 방지
            if source_index > target_count * len(sources):
                break
        
        return selected_results[:target_count]
    
