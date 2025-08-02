"""
Spring Boot 백엔드와의 통합을 위한 AI 게이트웨이 엔드포인트

이 모듈은 Spring Boot 백엔드와 AI 모델 서비스 간의 통합을 담당합니다.
문서 처리, 위험 평가, 검증 등의 AI 기반 서비스를 제공합니다.
"""

import asyncio
from typing import Dict, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
import httpx

from ..core.config import get_settings
from ..core.logging import get_logger
from ..schemas.gateway import (
    DocumentProcessingRequest, DocumentProcessingResponse,
    RiskAssessmentRequest, RiskAssessmentResponse,
    ValidationRequest, ValidationResponse,
    ProcessingStatus, ExtractedField, RiskFactor, ValidationError
)
from ..schemas.common import ResponseStatus

logger = get_logger(__name__)
router = APIRouter()


async def get_spring_boot_client():
    """
    Spring Boot 백엔드를 위한 HTTP 클라이언트 반환
    
    설정된 기본 URL과 인증 헤더를 사용하여 비동기 HTTP 클라이언트를 생성합니다.
    타임아웃과 API 키 설정을 포함합니다.
    
    Returns:
        httpx.AsyncClient: Spring Boot 백엔드 통신용 HTTP 클라이언트
    """
    settings = get_settings()
    return httpx.AsyncClient(
        base_url=settings.SPRING_BOOT_BASE_URL,
        timeout=30.0,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": settings.SPRING_BOOT_API_KEY or "development-key"
        }
    )


@router.post("/process-document", response_model=DocumentProcessingResponse)
async def process_document(
    request: DocumentProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    AI 모델을 사용한 관세 통관 문서 처리
    
    주어진 문서에서 텍스트를 추출하고, 버화된 데이터를 생성합니다.
    처리 결과는 백그라운드로 Spring Boot 백엔드에 전송됩니다.
    
    Args:
        request (DocumentProcessingRequest): 문서 처리 요청 데이터
        background_tasks (BackgroundTasks): 백그라운드 작업 처리용
        
    Returns:
        DocumentProcessingResponse: 문서 처리 결과
        
    Raises:
        HTTPException: 문서 처리 실패 시
    """
    
    document_id = request.document_id or str(uuid4())
    
    try:
        logger.info(f"Starting document processing for {document_id}")
        
        # Simulate document processing workflow
        extracted_data = await _process_document_workflow(request)
        
        # Extract structured fields
        extracted_fields = [
            ExtractedField(
                field_name="invoice_number",
                value="INV-2024-001",
                confidence=0.95,
                location={"page": 1, "x": 100, "y": 200}
            ),
            ExtractedField(
                field_name="total_amount",
                value=15000.00,
                confidence=0.92,
                location={"page": 1, "x": 300, "y": 400}
            ),
            ExtractedField(
                field_name="shipper_name",
                value="ABC Trading Co., Ltd.",
                confidence=0.88
            )
        ]
        
        # Send results to Spring Boot backend (async)
        background_tasks.add_task(
            _notify_spring_boot_backend,
            document_id,
            extracted_data
        )
        
        return DocumentProcessingResponse(
            status=ResponseStatus.SUCCESS,
            message="Document processed successfully",
            document_id=document_id,
            document_type=request.document_type,
            processing_status=ProcessingStatus.COMPLETED,
            extracted_data=extracted_data,
            extracted_fields=extracted_fields,
            confidence_score=0.91,
            processing_time=2.5,
            warnings=["Low confidence on some text regions"],
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        
        return DocumentProcessingResponse(
            status=ResponseStatus.ERROR,
            message="Document processing failed",
            document_id=document_id,
            document_type=request.document_type,
            processing_status=ProcessingStatus.ERROR,
            errors=[str(e)]
        )


@router.post("/assess-risk", response_model=RiskAssessmentResponse)
async def assess_risk(request: RiskAssessmentRequest):
    """Assess risk level for customs declarations"""
    
    try:
        logger.info(f"Starting risk assessment for declaration {request.declaration_id}")
        
        # Simulate risk assessment
        risk_factors = await _assess_risk_factors(request.declaration_data)
        
        # Calculate overall risk
        overall_score = sum(factor.score for factor in risk_factors) / len(risk_factors)
        
        if overall_score >= 0.8:
            overall_risk_level = "CRITICAL"
        elif overall_score >= 0.6:
            overall_risk_level = "HIGH"
        elif overall_score >= 0.4:
            overall_risk_level = "MEDIUM"
        else:
            overall_risk_level = "LOW"
        
        recommendations = [
            "Verify shipper credentials",
            "Check commodity classification",
            "Review declared values against market prices"
        ]
        
        return RiskAssessmentResponse(
            status=ResponseStatus.SUCCESS,
            message="Risk assessment completed",
            declaration_id=request.declaration_id,
            overall_risk_level=overall_risk_level,
            overall_risk_score=overall_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            requires_inspection=overall_score >= 0.7,
            processing_time=1.2
        )
        
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Risk assessment failed"
        )


@router.post("/validate", response_model=ValidationResponse)
async def validate_declaration(request: ValidationRequest):
    """Validate customs declaration data"""
    
    try:
        logger.info("Starting customs validation")
        
        # Simulate validation logic
        validation_errors = await _validate_declaration_data(request.declaration_data)
        
        # Separate errors and warnings
        errors = [err for err in validation_errors if err.severity in ["ERROR", "CRITICAL"]]
        warnings = [err for err in validation_errors if err.severity == "WARNING"]
        
        is_valid = len(errors) == 0
        
        return ValidationResponse(
            status=ResponseStatus.SUCCESS,
            message="Validation completed",
            is_valid=is_valid,
            validation_errors=errors,
            warnings=warnings,
            processing_time=0.8
        )
        
    except Exception as e:
        logger.error(f"Error in validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed"
        )


async def _process_document_workflow(request: DocumentProcessingRequest) -> Dict[str, Any]:
    """Simulate document processing workflow"""
    
    # Simulate AI model processing
    await asyncio.sleep(1.0)  # Simulate processing time
    
    # Mock extracted data based on document type
    if request.document_type.value == "invoice":
        return {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "total_amount": 15000.00,
            "currency": "USD",
            "shipper": {
                "name": "ABC Trading Co., Ltd.",
                "address": "123 Main St, Seoul, Korea",
                "contact": "+82-2-1234-5678"
            },
            "consignee": {
                "name": "XYZ Import Corp.",
                "address": "456 Oak Ave, Busan, Korea"
            },
            "items": [
                {
                    "description": "Electronic Components",
                    "quantity": 100,
                    "unit_price": 150.00,
                    "hs_code": "8541.10.00"
                }
            ]
        }
    
    elif request.document_type.value == "packing_list":
        return {
            "packing_date": "2024-01-14",
            "total_packages": 5,
            "total_weight": 250.5,
            "weight_unit": "kg",
            "items": [
                {
                    "package_number": 1,
                    "contents": "Electronic Components",
                    "weight": 50.1,
                    "dimensions": "40x30x20 cm"
                }
            ]
        }
    
    else:
        return {
            "document_type": request.document_type.value,
            "processed": True,
            "confidence": 0.85
        }


async def _assess_risk_factors(declaration_data: Dict[str, Any]) -> list[RiskFactor]:
    """Simulate risk factor assessment"""
    
    await asyncio.sleep(0.5)  # Simulate processing
    
    return [
        RiskFactor(
            factor_name="Shipper History",
            risk_level="LOW",
            score=0.2,
            description="Known reliable shipper with good compliance record",
            recommendations=["Continue monitoring"]
        ),
        RiskFactor(
            factor_name="Commodity Classification",
            risk_level="MEDIUM",
            score=0.6,
            description="Complex electronic components requiring detailed inspection",
            recommendations=["Verify HS codes", "Check technical specifications"]
        ),
        RiskFactor(
            factor_name="Value Declaration",
            risk_level="HIGH",
            score=0.8,
            description="Declared value significantly below market average",
            recommendations=["Verify invoices", "Check comparable transactions"]
        )
    ]


async def _validate_declaration_data(declaration_data: Dict[str, Any]) -> list[ValidationError]:
    """Simulate validation logic"""
    
    await asyncio.sleep(0.3)  # Simulate processing
    
    errors = []
    
    # Check required fields
    if not declaration_data.get("shipper_name"):
        errors.append(ValidationError(
            field_name="shipper_name",
            error_code="REQUIRED_FIELD_MISSING",
            error_message="Shipper name is required",
            severity="ERROR",
            suggested_fix="Enter valid shipper name"
        ))
    
    # Check value consistency
    total_value = declaration_data.get("total_value", 0)
    if total_value <= 0:
        errors.append(ValidationError(
            field_name="total_value",
            error_code="INVALID_VALUE",
            error_message="Total value must be greater than zero",
            severity="ERROR",
            suggested_fix="Enter valid total value"
        ))
    
    # Check HS codes
    if not declaration_data.get("hs_code"):
        errors.append(ValidationError(
            field_name="hs_code",
            error_code="HS_CODE_MISSING",
            error_message="HS code is required for classification",
            severity="WARNING",
            suggested_fix="Provide appropriate HS code"
        ))
    
    return errors


async def _notify_spring_boot_backend(document_id: str, extracted_data: Dict[str, Any]):
    """Notify Spring Boot backend about processed document"""
    
    try:
        async with await get_spring_boot_client() as client:
            response = await client.post(
                "/api/v1/documents/ai-processed",
                json={
                    "document_id": document_id,
                    "extracted_data": extracted_data,
                    "processed_at": str(asyncio.get_event_loop().time())
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully notified Spring Boot about document {document_id}")
            else:
                logger.warning(f"Failed to notify Spring Boot: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error notifying Spring Boot backend: {e}")