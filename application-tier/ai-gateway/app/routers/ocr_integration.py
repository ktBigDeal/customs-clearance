"""
model-ocr 서비스를 위한 OCR 통합 엔드포인트

이 모듈은 Azure Document Intelligence 기반의 OCR 서비스와의 통합을 제공합니다.
관세 문서 (Invoice, Packing List, Bill of Lading) 분석을 지원합니다.
"""

import asyncio
from typing import Dict, Any, List, Optional
import httpx
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse

from ..core.config import get_settings
from ..core.logging import get_logger
from ..schemas.common import ResponseStatus

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


async def get_ocr_client():
    """
    OCR 서비스를 위한 HTTP 클라이언트 반환
    
    model-ocr 서비스와의 통신을 위한 비동기 HTTP 클라이언트를 생성합니다.
    기본 URL과 타임아웃 설정을 포함합니다.
    
    Returns:
        httpx.AsyncClient: OCR 서비스 통신용 HTTP 클라이언트
    """
    return httpx.AsyncClient(
        base_url=settings.MODEL_OCR_URL or "http://localhost:8001",
        timeout=30.0,
        headers={"Content-Type": "application/json"}
    )


@router.post("/analyze-documents")
async def analyze_documents(
    invoice_file: Optional[UploadFile] = File(None),
    packing_list_file: Optional[UploadFile] = File(None),
    bill_of_lading_file: Optional[UploadFile] = File(None),
):
    """
    OCR 서비스를 사용한 관세 문서 분석
    
    세 개의 주요 관세 문서(Invoice, Packing List, Bill of Lading)를
    Azure Document Intelligence를 통해 분석하고 구조화된 데이터를 추출합니다.
    """

    try:
        logger.info("Starting document analysis via OCR service")

        if not any([invoice_file, packing_list_file, bill_of_lading_file]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="적어도 하나의 파일은 업로드해야 합니다."
            )

        files = {}
        if invoice_file:
            files["invoice_file"] = (invoice_file.filename, await invoice_file.read(), invoice_file.content_type)
        if packing_list_file:
            files["packing_list_file"] = (packing_list_file.filename, await packing_list_file.read(), packing_list_file.content_type)
        if bill_of_lading_file:
            files["bill_of_lading_file"] = (bill_of_lading_file.filename, await bill_of_lading_file.read(), bill_of_lading_file.content_type)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.MODEL_OCR_URL or 'http://localhost:8001'}/ocr/",
                files=files
            )

        if response.status_code == 200:
            ocr_data = response.json()
            logger.info("OCR analysis completed successfully")

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Documents analyzed successfully",
                    "ocr_data": ocr_data,
                    "processing_time": response.headers.get("X-Processing-Time", "N/A")
                }
            )
        else:
            logger.error(f"OCR service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OCR service error: {response.text}"
            )

    except httpx.RequestError as e:
        logger.error(f"OCR service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OCR service is unavailable"
        )
    except Exception as e:
        logger.error(f"Error in document analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document analysis failed"
        )


@router.get("/ocr/health")
async def check_ocr_health():
    """Check OCR service health"""
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.MODEL_OCR_URL or 'http://localhost:8001'}/docs"
            )
        
        if response.status_code == 200:
            return {
                "status": "healthy",
                "service": "model-ocr",
                "url": settings.MODEL_OCR_URL or "http://localhost:8001"
            }
        else:
            return {
                "status": "unhealthy",
                "service": "model-ocr",
                "error": f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "model-ocr",
            "error": str(e)
        }