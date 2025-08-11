"""
Report Integration endpoints for model-report service
"""

import asyncio
from typing import Dict, Any
import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logging import get_logger
from ..schemas.common import ResponseStatus

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


class DeclarationRequest(BaseModel):
    ocr_data: Dict[str, Any]

async def get_report_client():
    """Get HTTP client for Report service"""
    return httpx.AsyncClient(
        base_url=settings.MODEL_REPORT_URL or "http://localhost:8002",
        timeout=60.0,
        headers={"Content-Type": "application/json"}
    )


async def convert_us_hs_codes(ocr_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert US HS codes to Korean HS codes using US Converter service"""
    logger.info("Converting US HS codes to Korean HS codes")
    
    # Create a copy of OCR data to modify
    converted_data = ocr_data.copy()
    
    # Convert HS codes in items
    if "items" in converted_data:
        for item in converted_data["items"]:
            if "hs_code" in item and item["hs_code"]:
                us_hs_code = item["hs_code"]
                product_name = item.get("item_name", "")
                
                try:
                    # Call US HS Code Converter service (port 8006)
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        convert_response = await client.post(
                            "http://localhost:8006/convert",
                            json={
                                "us_hs_code": us_hs_code,
                                "product_name": product_name
                            }
                        )
                    
                    if convert_response.status_code == 200:
                        conversion_result = convert_response.json()
                        # Extract Korean HS code from conversion result
                        if "korea_recommendation" in conversion_result:
                            korean_hs = conversion_result["korea_recommendation"].get("hs_code", us_hs_code)
                            item["hs_code"] = korean_hs
                            logger.info(f"Converted US HS {us_hs_code} → Korean HS {korean_hs}")
                        else:
                            logger.warning(f"No Korean recommendation for US HS {us_hs_code}, keeping original")
                    else:
                        logger.warning(f"Failed to convert HS code {us_hs_code}, keeping original")
                        
                except Exception as e:
                    logger.error(f"Error converting HS code {us_hs_code}: {e}")
                    # Keep original HS code if conversion fails
    
    return converted_data

@router.post("/generate-import-declaration")
async def generate_import_declaration(request: DeclarationRequest):
    """Generate import customs declaration with HS code conversion"""
    
    try:
        logger.info("Starting import declaration generation with HS code conversion")
        
        # Step 1: Convert US HS codes to Korean HS codes
        converted_ocr_data = await convert_us_hs_codes(request.ocr_data)
        
        # Step 2: Call Report service for import declaration with converted data
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.MODEL_REPORT_URL or 'http://localhost:8002'}/generate-customs-declaration/import",
                json={
                    "ocr_data": converted_ocr_data
                }
            )
        
        if response.status_code == 200:
            declaration_data = response.json()
            logger.info("Import declaration generated successfully")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Import declaration generated successfully",
                    "declaration_type": "import",
                    "declaration_data": declaration_data,
                    "processing_time": response.headers.get("X-Processing-Time", "N/A")
                }
            )
        else:
            logger.error(f"Report service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Report service error: {response.text}"
            )
            
    except httpx.RequestError as e:
        logger.error(f"Report service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report service is unavailable"
        )
    except Exception as e:
        logger.error(f"Error in import declaration generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Import declaration generation failed"
        )


@router.post("/generate-export-declaration")
async def generate_export_declaration(request: DeclarationRequest):
    """Generate export customs declaration with HS code conversion"""
    
    try:
        logger.info("Starting export declaration generation with HS code conversion")
        
        # Step 1: Convert US HS codes to Korean HS codes
        converted_ocr_data = await convert_us_hs_codes(request.ocr_data)
        
        # Step 2: Call Report service for export declaration with converted data
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.MODEL_REPORT_URL or 'http://localhost:8002'}/generate-customs-declaration/export",
                json={
                    "ocr_data": converted_ocr_data
                }
            )
        
        if response.status_code == 200:
            declaration_data = response.json()
            logger.info("Export declaration generated successfully")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Export declaration generated successfully",
                    "declaration_type": "export",
                    "declaration_data": declaration_data,
                    "processing_time": response.headers.get("X-Processing-Time", "N/A")
                }
            )
        else:
            logger.error(f"Report service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Report service error: {response.text}"
            )
            
    except httpx.RequestError as e:
        logger.error(f"Report service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report service is unavailable"
        )
    except Exception as e:
        logger.error(f"Error in export declaration generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export declaration generation failed"
        )


@router.get("/health")
async def check_report_health():
    """Check Report service health"""
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.MODEL_REPORT_URL or 'http://localhost:8002'}/docs"
            )
        
        if response.status_code == 200:
            return {
                "status": "healthy",
                "service": "model-report",
                "url": settings.MODEL_REPORT_URL or "http://localhost:8002"
            }
        else:
            return {
                "status": "unhealthy",
                "service": "model-report",
                "error": f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "model-report",
            "error": str(e)
        }