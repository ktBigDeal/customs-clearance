"""
Similar Law Retriever Module

관세법 문서에서 유사한 조문을 검색하고 내부 참조를 활용한 확장 검색 기능
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
import re
from .embeddings import LangChainEmbedder
from .vector_store import ChromaVectorStore
from .query_normalizer import QueryNormalizer, AdvancedQueryProcessor

logger = logging.getLogger(__name__)


class SimilarLawRetriever:
    """유사한 법률 조문 검색 및 내부 참조 추적 클래스"""
    
    def __init__(self,
                 embedder: LangChainEmbedder,
                 vector_store: ChromaVectorStore,
                 query_normalizer: QueryNormalizer):
        """
        초기화
        
        Args:
            embedder (LangChainEmbedder): 임베딩 생성기
            vector_store (ChromaVectorStore): 벡터 저장소
            query_normalizer (QueryNormalizer): 쿼리 정규화기
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.query_normalizer = query_normalizer
        self.query_processor = AdvancedQueryProcessor(query_normalizer)
        
        # 내부 문서 캐시 (성능 최적화용)
        self._document_cache = {}
        
        logger.info("SimilarLawRetriever initialized")
    
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
            # 1. 복합 쿼리 처리
            processed_query = self.query_processor.process_complex_query(raw_query)
            
            # 2. 사용할 쿼리 결정
            if expand_with_synonyms:
                search_query = processed_query["expanded_query"]
            else:
                search_query = processed_query["normalized_query"]
            
            logger.info(f"🔍 검색 쿼리: {search_query}")
            
            # 3. 쿼리 임베딩 생성
            query_embedding = self.embedder.embed_text(search_query)
            
            # 4. 벡터 유사도 검색
            logger.info(f"🔍 벡터 검색 시작 (top_k: {top_k})")
            primary_results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=top_k
            )
            logger.info(f"📊 벡터 검색 결과: {len(primary_results)}개")
            
            # 5. 내부 참조 확장 검색
            if include_references:
                expanded_results = self._expand_with_references(primary_results, top_k)
            else:
                expanded_results = primary_results
            
            # 6. 결과 후처리 및 정렬
            final_results = self._post_process_results(expanded_results, processed_query)
            
            # 7. 유사도 임계값 필터링
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
    
    def search_by_article_reference(self, article_ref: str) -> Optional[Dict[str, Any]]:
        """
        조문 참조를 통한 직접 검색
        
        Args:
            article_ref (str): 조문 참조 (예: "제1조", "제5조제2항")
            
        Returns:
            Optional[Dict[str, Any]]: 해당 조문 정보
        """
        try:
            # 벡터 저장소에서 검색 (where 절 없이)
            results = self.vector_store.search_similar(
                query_embedding=[0.0] * self.embedder.embedding_dim,  # 더미 임베딩
                top_k=200  # 더 많은 결과를 가져와서 필터링
            )
            
            # 정확한 매치 또는 부분 매치 찾기
            exact_matches = []
            partial_matches = []
            
            for result in results:
                result_index = result.get("index", "") or result.get("metadata", {}).get("index", "")
                
                if result_index == article_ref:
                    # 정확한 매치
                    exact_matches.append(result)
                elif article_ref in result_index or result_index in article_ref:
                    # 부분 매치 (예: "제1조" 검색 시 "제1조제1항" 매치)
                    partial_matches.append(result)
            
            # 정확한 매치 우선 반환
            if exact_matches:
                return exact_matches[0]
            elif partial_matches:
                return partial_matches[0]
            
            return None
            
        except Exception as e:
            logger.error(f"조문 참조 검색 실패: {e}")
            return None
    
    def get_related_articles(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        특정 문서와 관련된 조문들 조회 (내부 참조 기반)
        
        Args:
            document (Dict[str, Any]): 기준 문서
            
        Returns:
            List[Dict[str, Any]]: 관련 조문 리스트
        """
        related_articles = []
        
        try:
            # 메타데이터에서 내부 참조 정보 추출
            metadata = document.get("metadata", {})
            
            # JSON 문자열로 저장된 내부 참조 정보 파싱
            internal_refs_raw = metadata.get("internal_law_references", "{}")
            if isinstance(internal_refs_raw, str):
                import json
                internal_refs = json.loads(internal_refs_raw)
            else:
                internal_refs = internal_refs_raw
            
            # 각 참조 유형별로 관련 조문 검색
            for ref_type, ref_list in internal_refs.items():
                if not ref_list:
                    continue
                
                for ref in ref_list:  # 모든 참조 처리
                    related_doc = self.search_by_article_reference(ref)
                    if related_doc and related_doc not in related_articles:
                        related_doc["reference_type"] = ref_type
                        related_articles.append(related_doc)
            
            logger.debug(f"발견된 관련 조문: {len(related_articles)}개")
            return related_articles
            
        except Exception as e:
            logger.error(f"관련 조문 조회 실패: {e}")
            return []
    
    def search_with_context_expansion(self, 
                                    query: str, 
                                    context_documents: List[Dict[str, Any]],
                                    top_k: int = 5) -> List[Dict[str, Any]]:
        """
        기존 컨텍스트를 고려한 확장 검색
        
        Args:
            query (str): 검색 쿼리
            context_documents (List[Dict[str, Any]]): 기존 컨텍스트 문서들
            top_k (int): 반환할 결과 수
            
        Returns:
            List[Dict[str, Any]]: 컨텍스트 고려된 검색 결과
        """
        try:
            # 1. 기본 검색 수행
            basic_results = self.search_similar_laws(query, top_k)
            
            # 2. 컨텍스트 문서들의 관련 조문들 수집
            context_related = []
            for context_doc in context_documents:
                related = self.get_related_articles(context_doc)
                context_related.extend(related)
            
            # 3. 결과 통합 및 중복 제거
            all_results = basic_results + context_related
            unique_results = self._remove_duplicates(all_results)
            
            # 4. 컨텍스트 관련성에 따른 점수 부여
            scored_results = self._score_with_context(unique_results, context_documents)
            
            # 5. 점수 기준 정렬 및 상위 결과 반환
            sorted_results = sorted(scored_results, 
                                  key=lambda x: x.get("context_score", 0), 
                                  reverse=True)
            
            return sorted_results[:top_k]
            
        except Exception as e:
            logger.error(f"컨텍스트 확장 검색 실패: {e}")
            return self.search_similar_laws(query, top_k)
    
    def _expand_with_references(self, 
                              primary_results: List[Dict[str, Any]], 
                              max_total: int) -> List[Dict[str, Any]]:
        """
        내부 참조를 활용한 검색 결과 확장
        
        Args:
            primary_results (List[Dict[str, Any]]): 기본 검색 결과
            max_total (int): 최대 반환 결과 수
            
        Returns:
            List[Dict[str, Any]]: 확장된 검색 결과
        """
        expanded_results = primary_results.copy()
        seen_ids = {result["id"] for result in primary_results}
        
        # 상위 결과들의 내부 참조 따라가기 (모든 결과 확장)
        for result in primary_results:
            try:
                related_articles = self.get_related_articles(result)
                
                for related in related_articles:
                    if related["id"] not in seen_ids and len(expanded_results) < max_total:
                        # 참조 관련성 점수 추가
                        related["reference_boost"] = 0.1
                        related["referenced_from"] = result["id"]
                        expanded_results.append(related)
                        seen_ids.add(related["id"])
                        
            except Exception as e:
                logger.warning(f"참조 확장 중 오류: {e}")
                continue
        
        return expanded_results
    
    def _post_process_results(self, 
                            results: List[Dict[str, Any]], 
                            processed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        검색 결과 후처리 및 최적화
        
        Args:
            results (List[Dict[str, Any]]): 원본 검색 결과
            processed_query (Dict[str, Any]): 처리된 쿼리 정보
            
        Returns:
            List[Dict[str, Any]]: 후처리된 검색 결과
        """
        # 1. 점수 재계산
        for result in results:
            base_score = result.get("similarity", 0)
            
            # 참조 부스트 적용
            reference_boost = result.get("reference_boost", 0)
            
            # 의도 매칭 점수
            intent_score = self._calculate_intent_score(result, processed_query["intent"])
            
            # 최종 점수 계산
            final_score = base_score + reference_boost + intent_score * 0.1
            result["final_score"] = final_score
        
        # 2. 점수 기준 정렬
        sorted_results = sorted(results, key=lambda x: x.get("final_score", 0), reverse=True)
        
        # 3. 결과 포맷팅
        formatted_results = []
        for result in sorted_results:
            # 다중 경로에서 index와 subtitle 추출 (우선순위: 최상위 > metadata > 기본값)
            index = (result.get("index") or 
                    result.get("metadata", {}).get("index") or "")
            subtitle = (result.get("subtitle") or 
                       result.get("metadata", {}).get("subtitle") or "")
            
            formatted_result = {
                "id": result["id"],
                "content": result["content"],
                "metadata": result["metadata"],
                "index": index,  # 최상위 레벨로 추가
                "subtitle": subtitle,  # 최상위 레벨로 추가
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
        """
        의도 매칭 점수 계산
        
        Args:
            result (Dict[str, Any]): 검색 결과
            intent (Dict[str, Any]): 추출된 의도
            
        Returns:
            float: 의도 매칭 점수
        """
        score = 0.0
        content = result.get("content", "").lower()
        
        # 핵심 개념 매칭
        key_concepts = intent.get("key_concepts", [])
        for concept in key_concepts:
            if concept.lower() in content:
                score += 0.2
        
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
                        score += 0.3
                        break
        
        return min(score, 1.0)  # 최대 1.0으로 제한
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        중복 결과 제거
        
        Args:
            results (List[Dict[str, Any]]): 검색 결과 리스트
            
        Returns:
            List[Dict[str, Any]]: 중복 제거된 결과
        """
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get("id")
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results
    
    def _score_with_context(self, 
                          results: List[Dict[str, Any]], 
                          context_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        컨텍스트 고려한 점수 부여
        
        Args:
            results (List[Dict[str, Any]]): 검색 결과
            context_docs (List[Dict[str, Any]]): 컨텍스트 문서들
            
        Returns:
            List[Dict[str, Any]]: 점수가 부여된 결과
        """
        # 컨텍스트 문서들의 주요 키워드 추출
        context_keywords = set()
        for doc in context_docs:
            content = doc.get("content", "")
            # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용 가능)
            words = re.findall(r'\w+', content)
            context_keywords.update(words[:10])  # 상위 10개 단어
        
        # 각 결과에 컨텍스트 점수 부여
        for result in results:
            content = result.get("content", "")
            words = set(re.findall(r'\w+', content))
            
            # 컨텍스트와의 키워드 overlap 계산
            overlap = len(context_keywords & words)
            context_score = overlap / max(len(context_keywords), 1)
            
            result["context_score"] = context_score
        
        return results