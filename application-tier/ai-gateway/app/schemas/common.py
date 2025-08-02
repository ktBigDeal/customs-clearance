"""
애플리케이션 전체에서 사용되는 공통 스키마

이 모듈은 여러 모듈에서 공통으로 사용되는 Pydantic 모델들을 정의합니다.
기본 응답, 오류 처리, 페이지네이션, 헬스 체크 등의 스키마를 포함합니다.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    """
    응답 상태 열거형
    
    API 응답의 전반적인 상태를 나타내는 열거형입니다.
    성공, 오류, 처리 중 상태를 구분합니다.
    """
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"


class BaseResponse(BaseModel):
    """
    기본 응답 스키마
    
    모든 API 응답에서 공통으로 사용되는 기본 필드들을 정의합니다.
    상태, 메시지, 타임스탬프, 요청 ID 등을 포함합니다.
    """
    status: ResponseStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class ErrorResponse(BaseResponse):
    """
    오류 응답 스키마
    
    API 오류 상황에서 사용되는 응답 스키마입니다.
    오류 코드와 상세 정보를 추가로 포함합니다.
    """
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthStatus(str, Enum):
    """
    헬스 체크 상태 열거형
    
    애플리케이션의 건강 상태를 나타내는 열거형입니다.
    정상, 비정상, 성능 저하 상태를 구분합니다.
    """
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """
    헬스 체크 응답 스키마
    
    애플리케이션의 건강 상태 체크 결과를 나타내는 스키마입니다.
    상태, 버전, 업타임, 세부 체크 결과를 포함합니다.
    """
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    uptime: float
    checks: Dict[str, Any] = Field(default_factory=dict)


class PaginationParams(BaseModel):
    """
    페이지네이션 매개변수
    
    목록 조회 API에서 사용되는 페이지네이션 매개변수를 정의합니다.
    페이지 번호와 페이지 크기에 대한 유효성 검사를 포함합니다.
    """
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseModel):
    """
    페이지네이션 응답 스키마
    
    페이지네이션이 적용된 목록 조회 결과를 나타내는 스키마입니다.
    아이템 목록과 함께 페이지 정보를 포함합니다.
    """
    items: List[Any]
    page: int
    size: int
    total: int
    pages: int