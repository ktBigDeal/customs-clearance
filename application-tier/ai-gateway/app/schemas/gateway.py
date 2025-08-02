"""
Schemas for AI Gateway endpoints - integration with Spring Boot backend.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, validator

from .common import BaseResponse


class DocumentType(str, Enum):
    """Document types for customs clearance"""
    INVOICE = "invoice"
    PACKING_LIST = "packing_list"
    BILL_OF_LADING = "bill_of_lading"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"
    CUSTOMS_DECLARATION = "customs_declaration"
    PERMIT = "permit"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Processing status for documents"""
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    REVIEW_REQUIRED = "review_required"


class DocumentProcessingRequest(BaseModel):
    """Request schema for document processing"""
    document_id: Optional[str] = Field(None, description="Optional document identifier")
    document_type: DocumentType = Field(..., description="Type of document")
    document_url: Optional[str] = Field(None, description="URL to document file")
    document_content: Optional[str] = Field(None, description="Base64 encoded document content")
    language: str = Field(default="ko", description="Document language")
    options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")
    
    @validator('document_url', 'document_content')
    def validate_document_source(cls, v, values):
        document_url = values.get('document_url')
        document_content = values.get('document_content')
        
        if not document_url and not document_content:
            raise ValueError('Either document_url or document_content must be provided')
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "invoice",
                "document_url": "https://example.com/document.pdf",
                "language": "ko",
                "options": {
                    "extract_tables": True,
                    "ocr_confidence_threshold": 0.8
                }
            }
        }


class ExtractedField(BaseModel):
    """Extracted field information"""
    field_name: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    location: Optional[Dict[str, Any]] = None  # Coordinates in document


class DocumentProcessingResponse(BaseResponse):
    """Response schema for document processing"""
    document_id: str
    document_type: DocumentType
    processing_status: ProcessingStatus
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    extracted_fields: List[ExtractedField] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_time: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class RiskAssessmentRequest(BaseModel):
    """Request schema for risk assessment"""
    declaration_id: str = Field(..., description="Declaration identifier")
    declaration_data: Dict[str, Any] = Field(..., description="Declaration data")
    historical_data: Optional[Dict[str, Any]] = Field(None, description="Historical trader data")
    options: Dict[str, Any] = Field(default_factory=dict)


class RiskFactor(BaseModel):
    """Risk factor information"""
    factor_name: str
    risk_level: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    score: float = Field(ge=0.0, le=1.0)
    description: str
    recommendations: List[str] = Field(default_factory=list)


class RiskAssessmentResponse(BaseResponse):
    """Response schema for risk assessment"""
    declaration_id: str
    overall_risk_level: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    overall_risk_score: float = Field(ge=0.0, le=1.0)
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    requires_inspection: bool = False
    processing_time: Optional[float] = None


class ValidationRequest(BaseModel):
    """Request schema for customs validation"""
    declaration_data: Dict[str, Any] = Field(..., description="Declaration data to validate")
    validation_rules: Optional[List[str]] = Field(None, description="Specific validation rules to apply")
    options: Dict[str, Any] = Field(default_factory=dict)


class ValidationError(BaseModel):
    """Validation error information"""
    field_name: str
    error_code: str
    error_message: str
    severity: str = Field(..., pattern="^(WARNING|ERROR|CRITICAL)$")
    suggested_fix: Optional[str] = None


class ValidationResponse(BaseResponse):
    """Response schema for validation"""
    is_valid: bool
    validation_errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    processing_time: Optional[float] = None