"""
검색 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import time
import logging

from app.core.recommender import RecommenderService
from app.schemas.request import SearchRequest
from app.schemas.response import SearchResponse, HSCodeRecommendation, SearchInfo

router = APIRouter()
logger = logging.getLogger(__name__)

def get_recommender_service() -> RecommenderService:
    """의존성 주입을 위한 더미 함수"""
    raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")

@router.get("/", response_model=SearchResponse)
async def search_hs_codes(
    q: str = Query(..., description="검색어"),
    material: Optional[str] = Query(None, description="재질"),
    usage: Optional[str] = Query(None, description="용도"),
    limit: int = Query(10, ge=1, le=50, description="결과 개수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    include_scores: bool = Query(False, description="점수 포함 여부"),
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    HS 코드 검색
    
    GET 방식으로 간단한 검색을 수행합니다.
    """
    try:
        start_time = time.time()
        logger.info(f"검색 요청: {q}")
        
        # 검색 실행
        result = await service.search(
            query=q,
            material=material or "",
            usage=usage or "",
            limit=limit
        )
        
        search_time = (time.time() - start_time) * 1000
        
        # 결과 변환
        results = []
        if result and 'recommendations' in result:
            for rec in result['recommendations'][offset:offset+limit]:
                hs_rec = HSCodeRecommendation(
                    hs_code=rec.get('hs_code', ''),
                    name_kr=rec.get('name_kr', ''),
                    name_en=rec.get('name_en', ''),
                    description=rec.get('description', ''),
                    confidence=rec.get('confidence', 0.0),
                    chapter=rec.get('chapter', ''),
                    data_source=rec.get('data_source', '')
                )
                
                if include_scores:
                    hs_rec.keyword_score = rec.get('keyword_score')
                    hs_rec.semantic_score = rec.get('semantic_score')
                    hs_rec.hybrid_score = rec.get('hybrid_score')
                
                results.append(hs_rec)
        
        # 페이징 정보
        total_count = len(result.get('recommendations', [])) if result else 0
        page_info = {
            "limit": limit,
            "offset": offset,
            "total": total_count,
            "has_more": offset + limit < total_count
        }
        
        # 검색 정보
        search_info = SearchInfo(
            query=q,
            material=material or "",
            usage=usage or "",
            search_time_ms=search_time,
            total_candidates=total_count,
            method="basic_search"
        )
        
        return SearchResponse(
            success=True,
            message=f"{len(results)}개의 검색 결과를 찾았습니다",
            results=results,
            total_count=total_count,
            page_info=page_info,
            search_info=search_info
        )
        
    except Exception as e:
        logger.error(f"검색 실행 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"검색 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/", response_model=SearchResponse)
async def search_hs_codes_post(
    request: SearchRequest,
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    HS 코드 검색 (POST)
    
    더 복잡한 검색 조건을 POST로 처리합니다.
    """
    try:
        start_time = time.time()
        logger.info(f"POST 검색 요청: {request.query}")
        
        # 검색 실행
        result = await service.search(
            query=request.query,
            material=request.material,
            usage=request.usage,
            limit=request.limit
        )
        
        search_time = (time.time() - start_time) * 1000
        
        # 결과 변환
        results = []
        if result and 'recommendations' in result:
            start_idx = request.offset
            end_idx = start_idx + request.limit
            
            for rec in result['recommendations'][start_idx:end_idx]:
                hs_rec = HSCodeRecommendation(
                    hs_code=rec.get('hs_code', ''),
                    name_kr=rec.get('name_kr', ''),
                    name_en=rec.get('name_en', ''),
                    description=rec.get('description', ''),
                    confidence=rec.get('confidence', 0.0),
                    chapter=rec.get('chapter', ''),
                    data_source=rec.get('data_source', '')
                )
                
                if request.include_scores:
                    hs_rec.keyword_score = rec.get('keyword_score')
                    hs_rec.semantic_score = rec.get('semantic_score')
                    hs_rec.hybrid_score = rec.get('hybrid_score')
                
                results.append(hs_rec)
        
        # 페이징 정보
        total_count = len(result.get('recommendations', [])) if result else 0
        page_info = {
            "limit": request.limit,
            "offset": request.offset,
            "total": total_count,
            "has_more": request.offset + request.limit < total_count
        }
        
        # 검색 정보
        search_info = SearchInfo(
            query=request.query,
            material=request.material,
            usage=request.usage,
            search_time_ms=search_time,
            total_candidates=total_count,
            method="post_search"
        )
        
        return SearchResponse(
            success=True,
            message=f"{len(results)}개의 검색 결과를 찾았습니다",
            results=results,
            total_count=total_count,
            page_info=page_info,
            search_info=search_info
        )
        
    except Exception as e:
        logger.error(f"POST 검색 실행 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"검색 처리 중 오류가 발생했습니다: {str(e)}"
        )

