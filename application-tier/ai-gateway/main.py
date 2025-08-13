"""
한국 관세 통관 시스템을 위한 FastAPI AI 게이트웨이

이 모듈은 AI/ML 모델 서빙과 Spring Boot 백엔드와의 통합을 위한
메인 API 게이트웨이 역할을 수행합니다.

주요 기능:
- AI 모델 서비스 통합 및 관리
- Spring Boot 백엔드와의 연동
- 요청 로깅 및 모니터링
- CORS 및 보안 미들웨어 설정
- 전역 예외 처리
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import AuthMiddleware, RequestLoggingMiddleware
from app.routers import health, models, ai_gateway

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 컨텍스트 매니저
    
    애플리케이션 시작과 종료 시점에 필요한 작업들을 관리합니다.
    - 시작 시: 로깅 설정, 환경 정보 출력
    - 종료 시: 정리 작업 및 종료 로그
    """
    # Startup
    logger.info("Starting AI Gateway application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Gateway application...")


# Create FastAPI application
app = FastAPI(
    title="Customs Clearance AI Gateway",
    description="AI Gateway and Model Serving API for Korean Customs Clearance System",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add security middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(AuthMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    전역 HTTP 예외 처리기
    
    HTTP 예외가 발생했을 때 표준화된 에러 응답을 반환합니다.
    에러 코드, 메시지, 타임스탬프, 요청 경로 등의 정보를 포함합니다.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": str(request.state.timestamp) if hasattr(request.state, 'timestamp') else None,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    전역 일반 예외 처리기
    
    처리되지 않은 모든 예외를 캐치하여 500 Internal Server Error로 변환합니다.
    예외 정보는 로그에 기록되고, 클라이언트에는 안전한 에러 메시지만 반환합니다.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": str(request.state.timestamp) if hasattr(request.state, 'timestamp') else None,
            "path": str(request.url.path)
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
app.include_router(ai_gateway.router, prefix="/api/v1/gateway", tags=["AI Gateway"])

# Include new integration routers
from app.routers import ocr_integration, hs_code_integration, report_integration, pipeline, chatbot_integration
app.include_router(ocr_integration.router, prefix="/api/v1/ocr", tags=["OCR Integration"])
app.include_router(hs_code_integration.router, prefix="/api/v1/hs-code", tags=["HS Code Integration"])
app.include_router(report_integration.router, prefix="/api/v1/report", tags=["Report Integration"])
app.include_router(chatbot_integration.router, prefix="/api/v1/chatbot", tags=["Chatbot Integration"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    루트 엔드포인트
    
    API 게이트웨이의 기본 정보를 반환합니다.
    서비스 이름, 버전, 상태, 실행 환경 등의 정보를 제공합니다.
    
    Returns:
        Dict[str, Any]: 서비스 기본 정보
    """
    return {
        "service": "Customs Clearance AI Gateway",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


def main():
    """메인 실행 함수"""
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None  # Use our custom logging config
    )


if __name__ == "__main__":
    main()