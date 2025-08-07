"""
End-to-end pipeline for customs clearance document processing
"""

import asyncio
from typing import Dict, Any, Optional
import httpx
from fastapi import APIRouter, Form, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


class PipelineRequest(BaseModel):
    declaration_type: str = "import"  # import or export


@router.post("/process-complete-workflow")
async def process_complete_workflow(
    declaration_type: str = Form(...),
    invoice_file: UploadFile = File(...),
    packing_list_file: UploadFile = File(...),
    bill_of_lading_file: UploadFile = File(...)
):
    """Complete workflow: OCR → Report Generation"""
    
    workflow_id = f"workflow_{asyncio.get_event_loop().time()}"
    
    try:
        logger.info(f"Starting complete workflow {workflow_id}")
        
        # Step 1: OCR Analysis
        logger.info("Step 1: Analyzing documents with OCR service")
        
        files = {
            "invoice_file": (invoice_file.filename, await invoice_file.read(), invoice_file.content_type),
            "packing_list_file": (packing_list_file.filename, await packing_list_file.read(), packing_list_file.content_type),
            "bill_of_lading_file": (bill_of_lading_file.filename, await bill_of_lading_file.read(), bill_of_lading_file.content_type)
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            ocr_response = await client.post(
                f"{settings.MODEL_OCR_URL or 'http://localhost:8001'}/ocr/",
                files=files
            )
        
        if ocr_response.status_code != 200:
            raise HTTPException(
                status_code=ocr_response.status_code,
                detail=f"OCR processing failed: {ocr_response.text}"
            )
        
        ocr_data = ocr_response.json()
        logger.info("Step 1 completed: OCR analysis successful")
        
        # Step 2: HS Code Conversion
        logger.info("Step 2: Converting HS Code")
        items = ocr_data.get("items", None)
        
        hsk_code_data = []
        
        if(declaration_type == "import"):
            for item in items or []:
                item_name = item.get("item_name", "")
                hs_code = item.get("hs_code", "")
                hs_code_fixed = hs_code.replace(".", "")

                async with httpx.AsyncClient(timeout=60.0) as client:
                    hs_code_response = await client.post(
                        f"{settings.MODEL_HSCODE_URL or 'http://localhost:8003'}/convert",
                        json={"us_hs_code": hs_code_fixed, "product_name": item_name}
                    )
                if hs_code_response.status_code != 200:
                    logger.error(f"HS Code conversion failed for {item_name}: {hs_code_response.text}")
                    hsk_code_data.append("")
                    continue
                
                hs_code_data = hs_code_response.json()
                hs_code_suggestions = hs_code_data.get("suggestions", [])
                hsk_code_data.append(hs_code_suggestions[0] if hs_code_suggestions else "" )

            # Merge HS Code data with OCR results
            for item, hsk_code in zip(ocr_data.get("items", []), hsk_code_data):
                item["hsk_code_suggestions"] = hsk_code
            
        logger.info("Step 2 completed: HS Code conversion successful")

        # Step 3: Generate Declaration
        logger.info("Step 3: Generating customs declaration")
        
        # Choose endpoint based on declaration type
        endpoint = "/generate-customs-declaration/import" if declaration_type == "import" else "/generate-customs-declaration/export"
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            report_response = await client.post(
                f"{settings.MODEL_REPORT_URL or 'http://localhost:8002'}{endpoint}",
                json={
                    "ocr_data": ocr_data
                }
            )
        
        if report_response.status_code != 200:
            raise HTTPException(
                status_code=report_response.status_code,
                detail=f"Declaration generation failed: {report_response.text}"
            )
        
        declaration_data = report_response.json()
        logger.info("Step 3 completed: Declaration generation successful")
        
        # Return complete workflow result
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Complete workflow processed successfully",
                "workflow_id": workflow_id,
                "declaration_type": declaration_type,
                "pipeline_results": {
                    "step_1_ocr": {
                        "status": "completed",
                        "data": ocr_data
                    },
                    "step_2_hscode_conversion": {
                        "status": "completed",
                        "data": hsk_code_data
                    },
                    "step_3_declaration": {
                        "status": "completed",
                        "data": declaration_data
                    }
                }

            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing failed: {str(e)}"
        )


@router.get("/health/services")
async def check_all_services():
    """Check health of all integrated services"""
    
    services_status = {}
    
    # Check OCR service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ocr_response = await client.get(
                f"{settings.MODEL_OCR_URL or 'http://localhost:8001'}/docs"
            )
        services_status["model-ocr"] = {
            "status": "healthy" if ocr_response.status_code == 200 else "unhealthy",
            "url": settings.MODEL_OCR_URL or "http://localhost:8001"
        }
    except Exception as e:
        services_status["model-ocr"] = {
            "status": "unreachable",
            "error": str(e),
            "url": settings.MODEL_OCR_URL or "http://localhost:8001"
        }
    
    # Check Report service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            report_response = await client.get(
                f"{settings.MODEL_REPORT_URL or 'http://localhost:8002'}/docs"
            )
        services_status["model-report"] = {
            "status": "healthy" if report_response.status_code == 200 else "unhealthy",
            "url": settings.MODEL_REPORT_URL or "http://localhost:8002"
        }
        
    except Exception as e:
        services_status["model-report"] = {
            "status": "unreachable",
            "error": str(e),
            "url": settings.MODEL_REPORT_URL or "http://localhost:8002"
        }
    
    # Check HS Code service
    try:    
        async with httpx.AsyncClient(timeout=5.0) as client:
            hs_code_response = await client.get(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8003'}/health"
            )
        
        services_status["model-hscode"] = {
            "status": hs_code_response.json().get("status", "unhealthy"),
            "url": settings.MODEL_HSCODE_URL or "http://localhost:8003"
        }
    
    except Exception as e:
        services_status["model-hscode"] = {
            "status": "unreachable",
            "error": str(e),
            "url": settings.MODEL_HSCODE_URL or "http://localhost:8003"
        }
        
    
    # Check overall status
    all_healthy = all(
        service["status"] == "healthy" 
        for service in services_status.values()
    )
    
    return {
        "overall_status": "healthy" if all_healthy else "degraded",
        "services": services_status,
        "timestamp": asyncio.get_event_loop().time()
    }