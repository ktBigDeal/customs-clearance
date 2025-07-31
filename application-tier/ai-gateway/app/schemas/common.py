"""
Common schemas used across the application.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"


class BaseResponse(BaseModel):
    """Base response schema"""
    status: ResponseStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class ErrorResponse(BaseResponse):
    """Error response schema"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    uptime: float
    checks: Dict[str, Any] = Field(default_factory=dict)


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseModel):
    """Paginated response schema"""
    items: List[Any]
    page: int
    size: int
    total: int
    pages: int