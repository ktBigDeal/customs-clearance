"""
Custom middleware for the AI Gateway application.
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
    """Middleware to log all requests and responses"""
    
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
    """Basic authentication middleware"""
    
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
        """Validate authentication token"""
        # TODO: Implement proper token validation
        # This is a basic implementation for development
        if settings.DEBUG:
            return True
        
        # In production, validate against your auth service
        # Example: JWT validation, database lookup, etc.
        return token == settings.SECRET_KEY
    
    def _get_user_from_token(self, token: str) -> dict:
        """Extract user information from token"""
        # TODO: Implement proper user extraction
        # This is a basic implementation for development
        return {
            "id": "system",
            "username": "system_user",
            "roles": ["api_user"]
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
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