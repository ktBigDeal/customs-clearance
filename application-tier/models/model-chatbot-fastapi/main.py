"""
FastAPI 메인 애플리케이션
LangGraph 기반 대화기록 연속성 시스템
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn

# 기존 model-chatbot 모듈 경로 추가
current_dir = Path(__file__).parent
model_chatbot_path = current_dir.parent / "model-chatbot"
sys.path.insert(0, str(model_chatbot_path))

# 내부 모듈 import
from app.core.database import db_manager, create_tables
from app.routers.conversations import router as conversations_router


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI 애플리케이션 생명주기 관리
    시작 시 데이터베이스 초기화, 종료 시 정리
    """
    # 시작 시 초기화
    logger.info("🚀 Starting FastAPI Chatbot Service...")
    
    try:
        # 환경변수 검증
        required_vars = ["OPENAI_API_KEY", "POSTGRES_USER", "POSTGRES_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            raise RuntimeError(f"Missing environment variables: {missing_vars}")
        
        # 데이터베이스 연결 초기화
        await db_manager.initialize()
        
        # 테이블 생성
        await create_tables()
        
        logger.info("✅ Database initialization completed")
        
        # 기존 LangGraph 시스템 초기화 (필요시)
        try:
            from src.rag.langgraph_factory import get_langgraph_factory
            langgraph_factory = get_langgraph_factory()
            logger.info("✅ LangGraph factory initialized")
        except Exception as e:
            logger.warning(f"⚠️ LangGraph initialization failed: {e}")
        
        logger.info("🎉 FastAPI Chatbot Service started successfully")
        
        yield  # 애플리케이션 실행
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    finally:
        # 종료 시 정리
        logger.info("🔄 Shutting down FastAPI Chatbot Service...")
        
        try:
            await db_manager.close()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
        
        logger.info("👋 FastAPI Chatbot Service shutdown completed")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="관세 통관 챗봇 서비스",
    description="""
    ## 🤖 LangGraph 기반 관세법 전문 챗봇

    ### 주요 기능
    - **🧠 지능형 AI 라우팅**: LangGraph 오케스트레이터를 통한 멀티 에이전트 시스템
    - **📚 전문 지식**: 관세법, 무역규제, 상담사례 3개 전문 에이전트
    - **💬 대화 연속성**: PostgreSQL 기반 대화기록 관리 및 컨텍스트 유지
    - **🔍 전문검색**: PostgreSQL GIN 인덱스를 활용한 고속 검색
    - **⚡ 고성능**: Redis 캐싱과 비동기 처리를 통한 최적화

    ### 아키텍처
    - **Frontend**: Next.js 14.2 + TypeScript
    - **Backend**: FastAPI + LangGraph + PostgreSQL + Redis
    - **AI**: OpenAI GPT + ChromaDB 벡터 저장소
    - **Authentication**: presentation-tier/backend와 연동

    ### 사용 방법
    1. **대화 시작**: `POST /api/v1/conversations/chat` 
    2. **기록 조회**: `GET /api/v1/conversations/`
    3. **검색**: `POST /api/v1/conversations/search`
    """,
    version="1.0.0",
    contact={
        "name": "관세 통관 시스템 개발팀",
        "url": "https://github.com/customs-clearance",
        "email": "support@customs-clearance.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    # 개발 모드에서는 docs 활성화
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 개발 서버
        "http://localhost:8080",  # Spring Boot 백엔드
        "https://customs-clearance.com",  # 프로덕션 도메인
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# GZip 압축 미들웨어
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 라우터 등록
app.include_router(conversations_router)

# 헬스 체크 엔드포인트
@app.get("/health", tags=["health"])
async def health_check():
    """
    헬스 체크 엔드포인트
    서비스 상태 및 의존성 확인
    """
    try:
        # 데이터베이스 연결 확인
        redis_client = await db_manager.get_redis()
        await redis_client.ping()
        
        # PostgreSQL 연결 확인 (간단한 쿼리)
        async with db_manager.get_db_session() as session:
            await session.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "fastapi-chatbot",
            "version": "1.0.0",
            "database": "connected",
            "redis": "connected",
            "timestamp": "2025-01-06T10:30:00Z"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": "fastapi-chatbot",
                "error": str(e),
                "timestamp": "2025-01-06T10:30:00Z"
            }
        )


@app.get("/health/detailed", tags=["health"])
async def detailed_health_check():
    """
    상세 헬스 체크 엔드포인트
    모든 의존성 상태 확인
    """
    health_status = {
        "service": "fastapi-chatbot",
        "version": "1.0.0",
        "status": "healthy",
        "checks": {}
    }
    
    # PostgreSQL 확인
    try:
        async with db_manager.get_db_session() as session:
            await session.execute("SELECT 1")
        health_status["checks"]["postgresql"] = {"status": "up", "response_time": "< 50ms"}
    except Exception as e:
        health_status["checks"]["postgresql"] = {"status": "down", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Redis 확인
    try:
        redis_client = await db_manager.get_redis()
        await redis_client.ping()
        health_status["checks"]["redis"] = {"status": "up", "response_time": "< 10ms"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "down", "error": str(e)}
        health_status["status"] = "degraded"
    
    # LangGraph 확인
    try:
        from src.rag.langgraph_factory import get_langgraph_factory
        factory = get_langgraph_factory()
        health_status["checks"]["langgraph"] = {"status": "up", "agents": "3"}
    except Exception as e:
        health_status["checks"]["langgraph"] = {"status": "down", "error": str(e)}
        health_status["status"] = "degraded"
    
    # OpenAI API 확인 (선택적)
    if os.getenv("OPENAI_API_KEY"):
        health_status["checks"]["openai"] = {"status": "configured"}
    else:
        health_status["checks"]["openai"] = {"status": "not_configured"}
        health_status["status"] = "degraded"
    
    status_code = status.HTTP_200_OK
    if health_status["status"] == "degraded":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(status_code=status_code, content=health_status)


# 전역 예외 처리기
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "timestamp": "2025-01-06T10:30:00Z"
        }
    )


# 커스텀 OpenAPI 스키마
def custom_openapi():
    """커스텀 OpenAPI 스키마 생성"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="관세 통관 챗봇 API",
        version="1.0.0",
        description="LangGraph 기반 관세법 전문 챗봇 서비스",
        routes=app.routes,
    )
    
    # 추가 정보
    openapi_schema["info"]["x-logo"] = {
        "url": "https://customs-clearance.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# 메인 실행 (개발용)
if __name__ == "__main__":
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )