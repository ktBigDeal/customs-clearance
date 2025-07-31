"""
Schemas for AI model management and serving.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, validator

from .common import BaseResponse, ResponseStatus


class ModelType(str, Enum):
    """AI model types"""
    DOCUMENT_CLASSIFIER = "document_classifier"
    TEXT_EXTRACTOR = "text_extractor"
    FORM_PARSER = "form_parser"
    CUSTOMS_VALIDATOR = "customs_validator"
    RISK_ASSESSOR = "risk_assessor"


class ModelStatus(str, Enum):
    """Model status enumeration"""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    UPDATING = "updating"
    DISABLED = "disabled"


class ModelInfo(BaseModel):
    """Model information schema"""
    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    type: ModelType = Field(..., description="Model type")
    version: str = Field(..., description="Model version")
    status: ModelStatus = Field(..., description="Current model status")
    description: Optional[str] = Field(None, description="Model description")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "customs-doc-classifier-v1",
                "name": "Customs Document Classifier",
                "type": "document_classifier",
                "version": "1.0.0",
                "status": "ready",
                "description": "Classifies customs clearance documents",
                "metadata": {
                    "accuracy": 0.95,
                    "supported_languages": ["ko", "en"],
                    "input_formats": ["pdf", "jpg", "png"]
                }
            }
        }


class ModelRequest(BaseModel):
    """Base model request schema"""
    model_id: str = Field(..., description="Model identifier")
    input_data: Dict[str, Any] = Field(..., description="Input data for the model")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Processing options")
    
    @validator('input_data')
    def validate_input_data(cls, v):
        if not v:
            raise ValueError('input_data cannot be empty')
        return v


class ModelResponse(BaseResponse):
    """Model inference response schema"""
    model_id: str
    predictions: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchModelRequest(BaseModel):
    """Batch model request schema"""
    model_id: str = Field(..., description="Model identifier")
    inputs: List[Dict[str, Any]] = Field(..., description="List of input data")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('inputs')
    def validate_inputs(cls, v):
        if not v:
            raise ValueError('inputs cannot be empty')
        if len(v) > 100:  # Max batch size
            raise ValueError('batch size cannot exceed 100')
        return v


class BatchModelResponse(BaseResponse):
    """Batch model inference response schema"""
    model_id: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    total_items: int
    successful_items: int
    failed_items: int
    processing_time: Optional[float] = None


class ModelUpdateRequest(BaseModel):
    """Model update request schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ModelStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelListResponse(BaseResponse):
    """Model list response schema"""
    models: List[ModelInfo] = Field(default_factory=list)
    total: int = 0