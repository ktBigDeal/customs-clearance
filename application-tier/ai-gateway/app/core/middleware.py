"""
AI 게이트웨이 애플리케이션을 위한 커스텀 미들웨어

이 모듈은 요청 로깅, 인증, 레이트 리미팅 등의 미들웨어를 제공합니다.
모든 HTTP 요청에 대해 로깅, 보안, 성능 처리를 수행합니다.
"""

import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
security = HTTPBearer(auto_error=False)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    요청 및 응답 로깅 미들웨어
    
    모든 HTTP 요청과 응답에 대한 정보를 로그로 기록합니다.
    요청 ID, 처리 시간, 상태 코드 등의 정보를 추적합니다.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.timestamp = time.time()
        
        # Log request
        logger.info(
            "Request received",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            "Response sent",
            request_id=request_id,
            status_code=response.status_code,
            process_time=process_time,
        )
        
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """
    기본 인증 미들웨어
    
    HTTP Bearer 토큰을 사용한 기본적인 인증 기능을 제공합니다.
    공개 엔드포인트는 인증을 건너뛰고, 디버그 모드에서는 인증을 비활성화합니다.
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/health/",
        "/health/ready",
        "/health/live",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip authentication in debug mode
        if settings.DEBUG:
            return await call_next(request)
        
        # Get authorization header
        credentials: Optional[HTTPAuthorizationCredentials] = await security(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate token (basic implementation)
        if not self._validate_token(credentials.credentials):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Add user info to request state (if needed)
        request.state.user = self._get_user_from_token(credentials.credentials)
        
        return await call_next(request)
    
    def _validate_token(self, token: str) -> bool:
        """
        인증 토큰 유효성 검사
        
        주어진 토큰의 유효성을 검사합니다.
        개발 환경에서는 상시 true를 반환하고,
        프로덕션에서는 실제 JWT 검증 등을 수행해야 합니다.
        
        Args:
            token (str): 검사할 인증 토큰
            
        Returns:
            bool: 토큰 유효성 여부
        """
        # TODO: Implement proper token validation
        # This is a basic implementation for development
        if settings.DEBUG:
            return True
        
        # In production, validate against your auth service
        # Example: JWT validation, database lookup, etc.
        return token == settings.SECRET_KEY
    
    def _get_user_from_token(self, token: str) -> dict:
        """
        토큰에서 사용자 정보 추출
        
        인증 토큰에서 사용자 정보를 추출합니다.
        개발 환경에서는 기본 사용자 정보를 반환하고,
        프로덕션에서는 JWT 디코딩 등을 통해 실제 사용자 정보를 추출해야 합니다.
        
        Args:
            token (str): 사용자 정보를 포함하는 토큰
            
        Returns:
            dict: 사용자 정보 딕셔너리
        """
        # TODO: Implement proper user extraction
        # This is a basic implementation for development
        return {
            "id": "system",
            "username": "system_user",
            "roles": ["api_user"]
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    요청 빈도 제한 미들웨어
    
    클라이언트 IP별로 분당 요청 수를 제한하여 API 남용을 방지합니다.
    메모리 기반의 간단한 구현이며, 프로덕션에서는 Redis 등을 사용해야 합니다.
    """
    
    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}  # In production, use Redis or similar
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        # Clean old entries
        self.requests = {
            key: value for key, value in self.requests.items()
            if key[1] >= minute_window - 1
        }
        
        # Check rate limit
        request_count = sum(
            1 for key in self.requests.keys()
            if key[0] == client_ip and key[1] == minute_window
        )
        
        if request_count >= self.calls_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Record request
        self.requests[(client_ip, minute_window)] = current_time
        
        return await call_next(request)