"""
Health check endpoints for the AI Gateway.
"""

import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
import psutil

from ..core.config import get_settings
from ..core.logging import get_logger
from ..schemas.common import HealthResponse, HealthStatus

logger = get_logger(__name__)
router = APIRouter()

# Application start time for uptime calculation
start_time = time.time()


async def get_system_info() -> Dict[str, Any]:
    """Get system information for health checks"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
    except Exception as e:
        logger.warning(f"Failed to get system info: {e}")
        return {}


async def check_dependencies() -> Dict[str, Any]:
    """Check external dependencies"""
    settings = get_settings()
    checks = {}
    
    # Check Spring Boot backend
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SPRING_BOOT_BASE_URL}/health",
                timeout=5.0
            )
            checks["spring_boot"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
    except Exception as e:
        checks["spring_boot"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check database (if configured)
    if settings.DATABASE_URL:
        checks["database"] = {"status": "not_implemented"}
    
    # Check Redis (if configured)
    if settings.REDIS_URL:
        checks["redis"] = {"status": "not_implemented"}
    
    return checks


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    settings = get_settings()
    uptime = time.time() - start_time
    
    system_info = await get_system_info()
    dependencies = await check_dependencies()
    
    # Determine overall health status
    status = HealthStatus.HEALTHY
    
    # Check system resources
    if system_info:
        memory_percent = system_info.get("memory", {}).get("percent", 0)
        cpu_percent = system_info.get("cpu_percent", 0)
        disk_percent = system_info.get("disk", {}).get("percent", 0)
        
        if memory_percent > 90 or cpu_percent > 90 or disk_percent > 90:
            status = HealthStatus.DEGRADED
        elif memory_percent > 95 or cpu_percent > 95 or disk_percent > 95:
            status = HealthStatus.UNHEALTHY
    
    # Check dependencies
    for dep_name, dep_info in dependencies.items():
        if dep_info.get("status") == "unhealthy":
            status = HealthStatus.DEGRADED
    
    return HealthResponse(
        status=status,
        version=settings.VERSION,
        uptime=uptime,
        checks={
            "system": system_info,
            "dependencies": dependencies
        }
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    settings = get_settings()
    dependencies = await check_dependencies()
    
    # Check critical dependencies
    ready = True
    for dep_name, dep_info in dependencies.items():
        if dep_name == "spring_boot" and dep_info.get("status") == "unhealthy":
            ready = False
            break
    
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready"
        )
    
    return {
        "status": "ready",
        "timestamp": datetime.now(),
        "version": settings.VERSION
    }


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint for Kubernetes"""
    settings = get_settings()
    
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "version": settings.VERSION,
        "uptime": time.time() - start_time
    }