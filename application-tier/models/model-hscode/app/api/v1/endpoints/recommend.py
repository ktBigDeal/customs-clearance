"""
HS 코드 추천 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
import time
import logging

from ....core.recommender import RecommenderService
from ....schemas.request import RecommendRequest, BatchRecommendRequest
from ....schemas.response import (
    RecommendResponse, BatchRecommendResponse, 
    HSCodeRecommendation, SearchInfo
)

router = APIRouter()
logger = logging.getLogger(__name__)

def get_recommender_service() -> RecommenderService:
    """의존성 주입을 위한 더미 함수 (main.py에서 오버라이드됨)"""
    raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")

@router.post("/", response_model=RecommendResponse)
async def recommend_hs_code(
    request: RecommendRequest,
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    HS 코드 추천
    
    상품명을 입력받아 가장 적합한 HS 코드를 추천합니다.
    """
    try:
        start_time = time.time()
        logger.info(f"추천 요청: {request.query}")
        
        # 추천 실행
        result = await service.recommend(
            query=request.query,
            material=request.material,
            usage=request.usage,
            use_llm=request.use_llm,
            final_count=request.top_k
        )
        
        search_time = (time.time() - start_time) * 1000
        
        # 응답 데이터 변환
        recommendations = []
        if result and 'recommendations' in result:
            for rec in result['recommendations']:
                recommendations.append(HSCodeRecommendation(
                    hs_code=rec.get('hs_code', ''),
                    name_kr=rec.get('name_kr', ''),
                    name_en=rec.get('name_en', ''),
                    description=rec.get('description', ''),
                    confidence=rec.get('confidence', 0.0),
                    keyword_score=rec.get('keyword_score'),
                    semantic_score=rec.get('semantic_score'),
                    hybrid_score=rec.get('hybrid_score'),
                    chapter=rec.get('chapter', ''),
                    heading=rec.get('heading', ''),
                    subheading=rec.get('subheading', ''),
                    data_source=rec.get('data_source', ''),
                    is_standard_match=rec.get('is_standard_match', False),
                    llm_analysis=rec.get('llm_analysis')
                ))
        
        # 검색 정보
        search_info = None
        if result and 'search_info' in result:
            info = result['search_info']
            search_info = SearchInfo(
                query=request.query,
                expanded_query=info.get('expanded_query', ''),
                material=request.material,
                usage=request.usage,
                search_time_ms=search_time,
                total_candidates=info.get('total_candidates'),
                method=info.get('method', ''),
                llm_used=request.use_llm,
                llm_candidates=info.get('llm_candidates'),
                search_candidates=info.get('search_candidates')
            )
        
        return RecommendResponse(
            success=True,
            message=f"{len(recommendations)}개의 HS 코드를 추천했습니다",
            recommendations=recommendations,
            search_info=search_info,
            metadata={
                "request_mode": request.mode,
                "include_details": request.include_details,
                "processing_time_ms": search_time
            }
        )
        
    except Exception as e:
        logger.error(f"추천 실행 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"추천 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/batch", response_model=BatchRecommendResponse)
async def batch_recommend(
    request: BatchRecommendRequest,
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    배치 HS 코드 추천
    
    여러 상품명을 한 번에 처리하여 각각의 HS 코드를 추천합니다.
    """
    try:
        start_time = time.time()
        logger.info(f"배치 추천 요청: {len(request.requests)}개")
        
        results = []
        successful_count = 0
        
        if request.parallel_processing:
            # 병렬 처리 (현재는 순차 처리로 구현, 추후 asyncio.gather 사용 가능)
            import asyncio
            
            async def process_single_request(req):
                try:
                    result = await service.recommend(
                        query=req.query,
                        material=req.material,
                        usage=req.usage,
                        use_llm=req.use_llm,
                        final_count=req.top_k
                    )
                    return result, None
                except Exception as e:
                    return None, str(e)
            
            # 병렬 실행
            tasks = [process_single_request(req) for req in request.requests]
            batch_results = await asyncio.gather(*tasks)
            
            for i, (result, error) in enumerate(batch_results):
                req = request.requests[i]
                
                if error:
                    results.append(RecommendResponse(
                        success=False,
                        message=f"처리 실패: {error}",
                        recommendations=[]
                    ))
                else:
                    successful_count += 1
                    # 개별 응답 생성 (위의 코드와 동일한 로직)
                    recommendations = []
                    if result and 'recommendations' in result:
                        for rec in result['recommendations']:
                            recommendations.append(HSCodeRecommendation(
                                hs_code=rec.get('hs_code', ''),
                                name_kr=rec.get('name_kr', ''),
                                name_en=rec.get('name_en', ''),
                                description=rec.get('description', ''),
                                confidence=rec.get('confidence', 0.0),
                                chapter=rec.get('chapter', ''),
                                data_source=rec.get('data_source', ''),
                                is_standard_match=rec.get('is_standard_match', False)
                            ))
                    
                    results.append(RecommendResponse(
                        success=True,
                        message=f"{len(recommendations)}개 추천",
                        recommendations=recommendations
                    ))
        
        else:
            # 순차 처리
            for req in request.requests:
                try:
                    result = await service.recommend(
                        query=req.query,
                        material=req.material,
                        usage=req.usage,
                        use_llm=req.use_llm,
                        final_count=req.top_k
                    )
                    
                    successful_count += 1
                    recommendations = []
                    if result and 'recommendations' in result:
                        for rec in result['recommendations']:
                            recommendations.append(HSCodeRecommendation(
                                hs_code=rec.get('hs_code', ''),
                                name_kr=rec.get('name_kr', ''),
                                name_en=rec.get('name_en', ''),
                                description=rec.get('description', ''),
                                confidence=rec.get('confidence', 0.0)
                            ))
                    
                    results.append(RecommendResponse(
                        success=True,
                        message=f"{len(recommendations)}개 추천",
                        recommendations=recommendations
                    ))
                    
                except Exception as e:
                    results.append(RecommendResponse(
                        success=False,
                        message=f"처리 실패: {str(e)}",
                        recommendations=[]
                    ))
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchRecommendResponse(
            success=successful_count > 0,
            total_requests=len(request.requests),
            successful_requests=successful_count,
            results=results,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"배치 추천 실행 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"배치 추천 처리 중 오류가 발생했습니다: {str(e)}"
        )

