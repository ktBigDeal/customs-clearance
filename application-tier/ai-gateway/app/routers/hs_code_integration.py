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

async def get_hs_code_client():
    """Get HTTP client for Report service"""
    return httpx.AsyncClient(
        base_url=settings.MODEL_HSCODE_URL or "http://localhost:8006",
        timeout=60.0,
        headers={"Content-Type": "application/json"}
    )

class ConvertRequest(BaseModel):
    us_hs_code: str
    product_name: str

@router.get("/")
async def get_hs_code_info():
    """Get HS Code service information"""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.get(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/"            
            )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error fetching HS Code info: {response.text}"
            )
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )

@router.post("/initialize")
async def initialize_hs_code_service():
    """Initialize HS Code service"""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/initialize"
            )
        if response.status_code == 200:
            logger.info("HS Code service initialized successfully")
            initialization_status = response.json()
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "HS Code service initialized successfully",
                    "initialization_status": initialization_status,
                    "processing_time": response.headers.get("X-Processing-Time", "N/A")
                }
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error initializing HS Code service: {response.text}"
            )
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )
    except Exception as e:
        logger.error(f"Error initializing HS Code service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize HS Code service"
        )
    
@router.get("/status")
async def get_hs_code_status():
    """Get HS Code service status"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/status"
            )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error fetching HS Code status: {response.text}"
            )
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )
    

@router.post("/hscode_convert")
async def convert_hs_code(requset: ConvertRequest):    
    try:
        logger.info("Starting hscode prediction via HSCODE service")
        
        # Call Report service for import declaration
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/convert",
                json={
                    "us_hs_code": requset.us_hs_code,
                    "product_name": requset.product_name
                }
            )
        
        if response.status_code == 200:
            hscode_data = response.json()
            logger.info("Import declaration generated successfully")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "hs_code_convert successfully",
                    "hscode_data": hscode_data,
                    "processing_time": response.headers.get("X-Processing-Time", "N/A")
                }
            )
        else:
            logger.error(f"Hscode service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Hscode service error: {response.text}"
            )
            
    except httpx.RequestError as e:
        logger.error(f"Hscode service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hscode service is unavailable"
        )
    except Exception as e:
        logger.error(f"Error in convert hscode: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Convert hs code failed"
        )
    

@router.get("/lookup/{hscode}")
async def lookup_hs_code(hscode: str):
    """Lookup HS Code information"""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.get(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/lookup/{hscode}"
            )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error looking up HS Code: {response.text}"
            )
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )

@router.delete("/cache")
async def clear_hs_code_cache():
    """Clear HS Code service cache"""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.delete(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/cache"
            )
        if response.status_code == 200:
            logger.info("HS Code cache cleared successfully")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "HS Code cache cleared successfully",
                    "processing_time": response.headers.get("X-Processing-Time", "N/A")
                }
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error clearing HS Code cache: {response.text}"
            )
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )
    
@router.get("/hs6/{hs6}/description")
async def get_hs6_description(hs6: str):
    """Get HS Code 6-digit description"""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.get(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/hs6/{hs6}/description"
            )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error fetching HS Code 6-digit description: {response.text}"
            )
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )
    

@router.get("/health")
async def check_hscode_health():
    """Check hscode service health"""
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.MODEL_HSCODE_URL or 'http://localhost:8006'}/health"
            )
        
        return response.json()
            
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )