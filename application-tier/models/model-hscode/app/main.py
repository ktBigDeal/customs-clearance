"""
FastAPI 기반 HS 코드 추천 API 서버
기존 hs_recommender 시스템을 RESTful API로 제공
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import sys
from typing import Optional
import asyncio

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from .api.v1.api import api_router
from .core.config import get_settings
from .core.recommender import RecommenderService
from .schemas.response import HealthResponse, StatusResponse

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 글로벌 추천 서비스 인스턴스
recommender_service: Optional[RecommenderService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global recommender_service
    
    logger.info("🚀 HS 코드 추천 API 서버 시작 중...")
    
    # 추천 서비스 초기화
    try:
        settings = get_settings()
        recommender_service = RecommenderService(settings)
        
        # 백그라운드에서 데이터 로드
        logger.info("📊 데이터 로딩 시작...")
        await recommender_service.initialize()
        logger.info("✅ 추천 서비스 초기화 완료")
        
    except Exception as e:
        logger.error(f"❌ 서비스 초기화 실패: {e}")
        raise
    
    yield
    
    # 종료 시 정리
    logger.info("🛑 HS 코드 추천 API 서버 종료")
    if recommender_service:
        await recommender_service.cleanup()

# FastAPI 앱 생성
app = FastAPI(
    title="HS 코드 추천 API",
    description="""
    AI 기반 HS 코드 추천 시스템
    
    ## 주요 기능
    - **하이브리드 검색**: TF-IDF + 의미 검색 결합
    - **다중 데이터 소스**: HSK 분류 + HS 코드 + 표준품명 통합
    - **LLM 분석**: OpenAI 기반 정확도 향상
    - **실시간 캐싱**: 고성능 검색 인덱스
    
    ## 데이터 구조
    - HSK 분류 데이터 중심 (15개 필드)
    - HS 코드 데이터 보조 (5개 필드)
    - 표준품명 데이터 보조 (3개 필드)
    - final_combined_text 기반 통합 검색
    """,
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 설정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

@app.get("/", response_model=dict)
async def root():
    """루트 엔드포인트"""
    return {
        "service": "HS 코드 추천 API",
        "version": "2.1.0",
        "status": "running",
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크 엔드포인트"""
    global recommender_service
    
    if recommender_service is None:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")
    
    health_status = await recommender_service.get_health()
    
    return HealthResponse(
        status="healthy" if health_status["healthy"] else "unhealthy",
        timestamp=health_status["timestamp"],
        version="2.1.0",
        details=health_status
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """서비스 상태 정보"""
    global recommender_service
    
    if recommender_service is None:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다")
    
    status_info = await recommender_service.get_status()
    
    return StatusResponse(
        service_name="HS 코드 추천 서비스",
        version="2.1.0",
        status="active" if status_info["initialized"] else "initializing",
        uptime_seconds=status_info.get("uptime_seconds", 0),
        total_items=status_info.get("total_items", 0),
        cache_status=status_info.get("cache_status", "unknown"),
        openai_available=status_info.get("openai_available", False),
        data_sources=status_info.get("data_sources", {}),
        performance=status_info.get("performance", {})
    )

def get_recommender_service() -> RecommenderService:
    """추천 서비스 의존성 주입"""
    global recommender_service
    if recommender_service is None:
        raise HTTPException(status_code=503, detail="서비스가 아직 초기화되지 않았습니다")
    return recommender_service

# 의존성 등록 (다른 모듈에서 사용)
from .api.v1.endpoints.recommend import get_recommender_service as recommend_get_service
from .api.v1.endpoints.search import get_recommender_service as search_get_service  
from .api.v1.endpoints.health import get_recommender_service as health_get_service
from .api.v1.endpoints.cache import get_recommender_service as cache_get_service

app.dependency_overrides[recommend_get_service] = get_recommender_service
app.dependency_overrides[search_get_service] = get_recommender_service
app.dependency_overrides[health_get_service] = get_recommender_service  
app.dependency_overrides[cache_get_service] = get_recommender_service

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """글로벌 예외 처리"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "내부 서버 오류",
            "message": "요청 처리 중 오류가 발생했습니다.",
            "detail": str(exc) if app.debug else None
        }
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HS 코드 추천 API 서버")
    parser.add_argument("--host", default="0.0.0.0", help="호스트 주소")
    parser.add_argument("--port", type=int, default=8003, help="포트 번호")
    parser.add_argument("--reload", action="store_true", help="개발 모드 (자동 재시작)")
    parser.add_argument("--workers", type=int, default=1, help="워커 프로세스 수")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )