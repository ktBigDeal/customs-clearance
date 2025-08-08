"""
커스텀 예외 및 예외 처리 모듈

FastAPI 애플리케이션에서 사용하는 커스텀 예외와 예외 처리 로직을 정의합니다.
일관된 에러 응답 형식을 제공하고, 적절한 HTTP 상태 코드를 반환합니다.

주요 예외 유형:
- 인증 및 권한 관련 예외
- 데이터베이스 관련 예외
- RAG 시스템 관련 예외
- 비즈니스 로직 예외
"""

import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class CustomHTTPException(HTTPException):
    """커스텀 HTTP 예외 기본 클래스
    
    FastAPI의 HTTPException을 확장하여 추가적인 메타데이터와 
    일관된 에러 응답 형식을 지원합니다.
    
    Attributes:
        status_code: HTTP 상태 코드
        detail: 에러 세부 정보
        error_code: 내부 에러 코드
        user_message: 사용자 친화적 메시지
        metadata: 추가 메타데이터
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        user_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or f"HTTP_{status_code}"
        self.user_message = user_message or detail
        self.metadata = metadata or {}


class AuthenticationError(CustomHTTPException):
    """인증 오류 예외
    
    JWT 토큰 검증 실패, 만료된 토큰, 잘못된 인증 정보 등에 사용됩니다.
    """
    
    def __init__(
        self,
        detail: str = "인증이 필요합니다",
        user_message: str = "로그인이 필요합니다. 다시 로그인해주세요.",
        error_code: str = "AUTH_REQUIRED",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            user_message=user_message,
            metadata=metadata,
            headers={"WWW-Authenticate": "Bearer"}
        )


class TokenExpiredError(AuthenticationError):
    """토큰 만료 예외"""
    
    def __init__(
        self,
        detail: str = "JWT 토큰이 만료되었습니다",
        user_message: str = "로그인이 만료되었습니다. 다시 로그인해주세요.",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            detail=detail,
            user_message=user_message,
            error_code="TOKEN_EXPIRED",
            metadata=metadata
        )


class InvalidTokenError(AuthenticationError):
    """유효하지 않은 토큰 예외"""
    
    def __init__(
        self,
        detail: str = "유효하지 않은 JWT 토큰입니다",
        user_message: str = "인증 정보가 올바르지 않습니다. 다시 로그인해주세요.",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            detail=detail,
            user_message=user_message,
            error_code="INVALID_TOKEN",
            metadata=metadata
        )


class AuthorizationError(CustomHTTPException):
    """권한 부족 예외
    
    인증은 되었으나 특정 작업에 대한 권한이 없는 경우 사용됩니다.
    """
    
    def __init__(
        self,
        detail: str = "접근 권한이 없습니다",
        user_message: str = "해당 작업을 수행할 권한이 없습니다.",
        error_code: str = "ACCESS_DENIED",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            user_message=user_message,
            metadata=metadata
        )


class DatabaseError(CustomHTTPException):
    """데이터베이스 관련 예외
    
    데이터베이스 연결 오류, 쿼리 실행 실패, 트랜잭션 오류 등에 사용됩니다.
    """
    
    def __init__(
        self,
        detail: str = "데이터베이스 오류가 발생했습니다",
        user_message: str = "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        error_code: str = "DATABASE_ERROR",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code,
            user_message=user_message,
            metadata=metadata
        )


class ConversationNotFoundError(CustomHTTPException):
    """대화방 없음 예외"""
    
    def __init__(
        self,
        conversation_id: str,
        user_message: str = "존재하지 않는 대화방입니다.",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"대화방을 찾을 수 없습니다: {conversation_id}",
            error_code="CONVERSATION_NOT_FOUND",
            user_message=user_message,
            metadata=metadata or {"conversation_id": conversation_id}
        )


class MessageNotFoundError(CustomHTTPException):
    """메시지 없음 예외"""
    
    def __init__(
        self,
        message_id: str,
        user_message: str = "존재하지 않는 메시지입니다.",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"메시지를 찾을 수 없습니다: {message_id}",
            error_code="MESSAGE_NOT_FOUND",
            user_message=user_message,
            metadata=metadata or {"message_id": message_id}
        )


class RAGServiceError(CustomHTTPException):
    """RAG 서비스 오류 예외
    
    벡터 검색 실패, OpenAI API 오류, 모델 응답 생성 실패 등에 사용됩니다.
    """
    
    def __init__(
        self,
        detail: str = "AI 서비스 오류가 발생했습니다",
        user_message: str = "답변을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        error_code: str = "RAG_SERVICE_ERROR",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code=error_code,
            user_message=user_message,
            metadata=metadata
        )


class OpenAIAPIError(RAGServiceError):
    """OpenAI API 오류 예외"""
    
    def __init__(
        self,
        detail: str,
        api_error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            detail=f"OpenAI API 오류: {detail}",
            user_message="AI 서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요.",
            error_code="OPENAI_API_ERROR",
            metadata={**(metadata or {}), "api_error_code": api_error_code}
        )


class VectorSearchError(RAGServiceError):
    """벡터 검색 오류 예외"""
    
    def __init__(
        self,
        detail: str = "문서 검색 중 오류가 발생했습니다",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            detail=detail,
            user_message="관련 문서를 찾는 중 오류가 발생했습니다. 다른 방식으로 질문해보세요.",
            error_code="VECTOR_SEARCH_ERROR",
            metadata=metadata
        )


class RateLimitExceededError(CustomHTTPException):
    """속도 제한 초과 예외
    
    API 호출 빈도가 제한을 초과한 경우 사용됩니다.
    """
    
    def __init__(
        self,
        limit: int,
        reset_time: int,
        user_message: str = "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"속도 제한 초과: {limit}회/분",
            error_code="RATE_LIMIT_EXCEEDED",
            user_message=user_message,
            metadata={
                **(metadata or {}),
                "limit": limit,
                "reset_time": reset_time
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Reset": str(reset_time)
            }
        )


class ValidationError(CustomHTTPException):
    """데이터 검증 오류 예외
    
    요청 데이터의 형식이나 값이 올바르지 않은 경우 사용됩니다.
    """
    
    def __init__(
        self,
        detail: str,
        field_errors: Optional[Dict[str, str]] = None,
        user_message: str = "입력 정보를 확인해주세요.",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            user_message=user_message,
            metadata={
                **(metadata or {}),
                "field_errors": field_errors or {}
            }
        )


class ExternalServiceError(CustomHTTPException):
    """외부 서비스 오류 예외
    
    Spring Boot 백엔드, 외부 API 등의 연동 오류에 사용됩니다.
    """
    
    def __init__(
        self,
        service_name: str,
        detail: str,
        user_message: str = "외부 서비스 연동 중 오류가 발생했습니다.",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{service_name} 서비스 오류: {detail}",
            error_code="EXTERNAL_SERVICE_ERROR",
            user_message=user_message,
            metadata={
                **(metadata or {}),
                "service_name": service_name
            }
        )


async def handle_custom_exception(request: Request, exc: CustomHTTPException) -> JSONResponse:
    """커스텀 예외 처리 핸들러
    
    CustomHTTPException을 처리하여 일관된 형식의 JSON 응답을 반환합니다.
    
    Args:
        request (Request): FastAPI 요청 객체
        exc (CustomHTTPException): 발생한 커스텀 예외
        
    Returns:
        JSONResponse: 표준화된 에러 응답
    """
    
    # 요청 정보 로깅
    logger.error(
        f"커스텀 예외 발생 - "
        f"URL: {request.url} | "
        f"Method: {request.method} | "
        f"Error: {exc.error_code} | "
        f"Detail: {exc.detail}"
    )
    
    # 응답 데이터 구성
    response_data = {
        "success": False,
        "error_code": exc.error_code,
        "error": exc.detail,
        "message": exc.user_message,
        "timestamp": settings.get_current_time().isoformat(),
        "path": str(request.url.path)
    }
    
    # 메타데이터 추가 (개발 환경에서만)
    if settings.is_development and exc.metadata:
        response_data["metadata"] = exc.metadata
    
    # 특정 예외 유형별 추가 헤더
    headers = exc.headers or {}
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=headers
    )


def create_error_response(
    status_code: int,
    error_code: str,
    error_message: str,
    user_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """에러 응답 생성 유틸리티
    
    Args:
        status_code (int): HTTP 상태 코드
        error_code (str): 내부 에러 코드
        error_message (str): 에러 메시지
        user_message (Optional[str]): 사용자 친화적 메시지
        metadata (Optional[Dict[str, Any]]): 추가 메타데이터
        
    Returns:
        Dict[str, Any]: 표준화된 에러 응답 데이터
    """
    
    response_data = {
        "success": False,
        "error_code": error_code,
        "error": error_message,
        "message": user_message or error_message,
        "timestamp": settings.get_current_time().isoformat()
    }
    
    if settings.is_development and metadata:
        response_data["metadata"] = metadata
    
    return response_data


def log_exception(
    exc: Exception,
    context: str,
    request_url: Optional[str] = None,
    user_id: Optional[int] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """예외 상세 로깅
    
    Args:
        exc (Exception): 발생한 예외
        context (str): 예외 발생 컨텍스트
        request_url (Optional[str]): 요청 URL
        user_id (Optional[int]): 사용자 ID
        additional_info (Optional[Dict[str, Any]]): 추가 정보
    """
    
    log_data = {
        "context": context,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "timestamp": datetime.now().isoformat()
    }
    
    if request_url:
        log_data["request_url"] = request_url
    
    if user_id:
        log_data["user_id"] = user_id
    
    if additional_info:
        log_data.update(additional_info)
    
    logger.error(f"예외 발생: {log_data}", exc_info=True)


# 예외 처리 데코레이터
def handle_exceptions(context: str):
    """예외 처리 데코레이터
    
    함수에서 발생하는 예외를 자동으로 처리하고 로깅합니다.
    
    Args:
        context (str): 예외 발생 컨텍스트
    """
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except CustomHTTPException:
                # 커스텀 예외는 그대로 전파
                raise
            except Exception as exc:
                # 일반 예외는 로깅 후 내부 서버 오류로 변환
                log_exception(exc, context)
                raise CustomHTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{context}에서 예상치 못한 오류가 발생했습니다",
                    error_code="INTERNAL_ERROR",
                    user_message="서버에서 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                )
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CustomHTTPException:
                raise
            except Exception as exc:
                log_exception(exc, context)
                raise CustomHTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{context}에서 예상치 못한 오류가 발생했습니다",
                    error_code="INTERNAL_ERROR",
                    user_message="서버에서 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                )
        
        # 비동기 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator