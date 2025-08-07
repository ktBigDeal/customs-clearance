"""
캐시 관리 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import logging
import time

from core.recommender import RecommenderService
from schemas.request import CacheRequest
from schemas.response import CacheResponse, StatusResponse

router = APIRouter()
logger = logging.getLogger(__name__)

def get_recommender_service() -> RecommenderService:
    """의존성 주입을 위한 더미 함수"""
    raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")

@router.get("/info", response_model=dict)
async def get_cache_info(
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    캐시 정보 조회
    
    캐시의 상세 정보를 반환합니다.
    """
    try:
        status = await service.get_status()
        
        cache_info = {
            "cache_status": status.get('cache_status', 'unknown'),
            "total_items": status.get('total_items', 0),
            "data_sources": status.get('data_sources', {}),
            "uptime_seconds": status.get('uptime_seconds', 0),
            "performance": status.get('performance', {})
        }
        
        return {
            "success": True,
            "cache_info": cache_info,
            "message": "캐시 정보를 성공적으로 조회했습니다"
        }
        
    except Exception as e:
        logger.error(f"캐시 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캐시 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/rebuild", response_model=CacheResponse)
async def rebuild_cache(
    background_tasks: BackgroundTasks,
    force: bool = False,
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    캐시 재구축
    
    데이터를 다시 로드하여 캐시를 재구축합니다.
    """
    try:
        logger.info(f"캐시 재구축 요청 (force={force})")
        
        # 비동기로 캐시 재구축 실행
        start_time = time.time()
        success = await service.rebuild_cache()
        rebuild_time = time.time() - start_time
        
        if success:
            # 새로운 상태 정보
            status = await service.get_status()
            
            return CacheResponse(
                success=True,
                action="rebuild",
                message=f"캐시 재구축이 성공적으로 완료되었습니다 ({rebuild_time:.2f}초)",
                details={
                    "rebuild_time_seconds": rebuild_time,
                    "total_items": status.get('total_items', 0),
                    "cache_status": status.get('cache_status', 'unknown'),
                    "timestamp": time.time()
                }
            )
        else:
            return CacheResponse(
                success=False,
                action="rebuild",
                message="캐시 재구축에 실패했습니다",
                details={
                    "rebuild_time_seconds": rebuild_time,
                    "timestamp": time.time()
                }
            )
            
    except Exception as e:
        logger.error(f"캐시 재구축 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캐시 재구축 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/clear", response_model=CacheResponse)
async def clear_cache(
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    캐시 삭제
    
    모든 캐시 파일을 삭제합니다.
    """
    try:
        logger.info("캐시 삭제 요청")
        
        deleted_count = await service.clear_cache()
        
        return CacheResponse(
            success=True,
            action="clear",
            message=f"{deleted_count}개의 캐시 파일을 삭제했습니다",
            details={
                "deleted_files": deleted_count,
                "timestamp": time.time()
            }
        )
        
    except Exception as e:
        logger.error(f"캐시 삭제 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캐시 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/manage", response_model=CacheResponse)
async def manage_cache(
    request: CacheRequest,
    background_tasks: BackgroundTasks,
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    캐시 관리 통합 엔드포인트
    
    다양한 캐시 관리 작업을 통합적으로 처리합니다.
    """
    try:
        if request.action == "info":
            # 캐시 정보 조회
            status = await service.get_status()
            return CacheResponse(
                success=True,
                action="info",
                message="캐시 정보 조회 완료",
                details={
                    "cache_status": status.get('cache_status'),
                    "total_items": status.get('total_items'),
                    "uptime_seconds": status.get('uptime_seconds')
                }
            )
            
        elif request.action == "rebuild":
            # 캐시 재구축
            start_time = time.time()
            success = await service.rebuild_cache()
            rebuild_time = time.time() - start_time
            
            return CacheResponse(
                success=success,
                action="rebuild",
                message=f"캐시 재구축 {'성공' if success else '실패'} ({rebuild_time:.2f}초)",
                details={
                    "rebuild_time_seconds": rebuild_time,
                    "force": request.force
                }
            )
            
        elif request.action == "clear":
            # 캐시 삭제
            deleted_count = await service.clear_cache()
            
            return CacheResponse(
                success=True,
                action="clear",
                message=f"{deleted_count}개 파일 삭제 완료",
                details={
                    "deleted_files": deleted_count,
                    "force": request.force
                }
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 액션: {request.action}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캐시 관리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캐시 관리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats", response_model=dict)
async def get_cache_stats(
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    캐시 통계 정보
    
    캐시 사용량 및 성능 통계를 반환합니다.
    """
    try:
        status = await service.get_status()
        
        stats = {
            "cache_status": status.get('cache_status', 'unknown'),
            "total_items": status.get('total_items', 0),
            "data_sources": status.get('data_sources', {}),
            "performance": status.get('performance', {}),
            "system_info": {
                "uptime_seconds": status.get('uptime_seconds', 0),
                "initialized": status.get('initialized', False),
                "openai_available": status.get('openai_available', False)
            }
        }
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": time.time(),
            "message": "캐시 통계 정보를 성공적으로 캐시했습니다"
        }
        
    except Exception as e:
        logger.error(f"캐시 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캐시 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )
