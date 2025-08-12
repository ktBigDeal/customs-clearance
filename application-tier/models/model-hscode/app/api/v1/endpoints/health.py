"""
헬스체크 API 엔드포인트
"""

from fastapi import APIRouter, Depends
import logging

from app.core.recommender import RecommenderService
from app.schemas.response import HealthResponse

router = APIRouter()
logger = logging.getLogger(__name__)

def get_recommender_service() -> RecommenderService:
    """의존성 주입을 위한 더미 함수"""
    from fastapi import HTTPException
    raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")

@router.get("/", response_model=HealthResponse)
async def health_check(
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    기본 헬스체크
    
    서비스의 기본적인 상태를 확인합니다.
    """
    health_info = await service.get_health()
    
    return HealthResponse(
        status="healthy" if health_info["healthy"] else "unhealthy",
        timestamp=health_info["timestamp"],
        version="2.1.0",
        details=health_info
    )

@router.get("/live", response_model=dict)
async def liveness_probe():
    """
    라이브니스 프로브
    
    Kubernetes 등에서 사용하는 라이브니스 체크용 엔드포인트입니다.
    """
    return {
        "status": "alive",
        "timestamp": __import__('time').time()
    }

@router.get("/ready", response_model=dict)
async def readiness_probe(
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    레디니스 프로브
    
    서비스가 요청을 처리할 준비가 되었는지 확인합니다.
    """
    try:
        health_info = await service.get_health()
        
        if health_info["healthy"] and health_info.get("data_loaded", False):
            return {
                "status": "ready",
                "timestamp": health_info["timestamp"],
                "data_loaded": True
            }
        else:
            return {
                "status": "not_ready",
                "timestamp": health_info["timestamp"],
                "reason": "서비스가 아직 초기화 중입니다"
            }
            
    except Exception as e:
        logger.error(f"레디니스 체크 실패: {e}")
        return {
            "status": "not_ready",
            "timestamp": __import__('time').time(),
            "reason": f"서비스 오류: {str(e)}"
        }

@router.get("/startup", response_model=dict)
async def startup_probe(
    service: RecommenderService = Depends(get_recommender_service)
):
    """
    스타트업 프로브
    
    서비스가 시작되었는지 확인합니다.
    """
    try:
        status = await service.get_status()
        
        return {
            "status": "started" if status["initialized"] else "starting",
            "uptime_seconds": status["uptime_seconds"],
            "initialized": status["initialized"]
        }
        
    except Exception as e:
        logger.error(f"스타트업 체크 실패: {e}")
        return {
            "status": "failed",
            "timestamp": __import__('time').time(),
            "error": str(e)
        }
