"""
Shared schemas for model serving endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


class ModelStatus(str, Enum):
    """Model status enumeration"""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


class InferenceRequest(BaseModel):
    """Base inference request schema"""
    inputs: Dict[str, Any] = Field(..., description="Model inputs")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Inference parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "inputs": {
                    "text": "Sample input text",
                    "image_url": "https://example.com/image.jpg"
                },
                "parameters": {
                    "max_tokens": 100,
                    "temperature": 0.7
                }
            }
        }


class InferenceResponse(BaseModel):
    """Base inference response schema"""
    model_name: str
    model_version: str
    predictions: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class BatchInferenceRequest(BaseModel):
    """Batch inference request schema"""
    inputs: List[Dict[str, Any]] = Field(..., description="List of model inputs")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('inputs')
    def validate_inputs(cls, v):
        if not v:
            raise ValueError('inputs cannot be empty')
        if len(v) > 100:  # Max batch size
            raise ValueError('batch size cannot exceed 100')
        return v


class BatchInferenceResponse(BaseModel):
    """Batch inference response schema"""
    model_name: str
    model_version: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    total_items: int
    successful_items: int
    failed_items: int
    processing_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ModelHealthResponse(BaseModel):
    """Model health check response"""
    model_name: str
    status: ModelStatus
    version: str
    uptime_seconds: float
    last_inference: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)