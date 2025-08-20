"""
AI 게이트웨이를 위한 헬스 체크 엔드포인트

이 모듈은 애플리케이션의 상태를 모니터링하기 위한 헬스 체크 엔드포인트를 제공합니다.
시스템 리소스, 외부 의존성, Kubernetes 통합을 지원합니다.
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

# 업타임 계산을 위한 애플리케이션 시작 시간
start_time = time.time()


async def get_system_info() -> Dict[str, Any]:
    """
    헬스 체크를 위한 시스템 정보 수집
    
    CPU, 메모리, 디스크 사용량 등의 시스템 리소스 정보를 수집합니다.
    psutil 라이브러리를 사용하여 실시간 시스템 메트릭을 수집합니다.
    
    Returns:
        Dict[str, Any]: 시스템 리소스 정보 딕셔너리
    """
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
    """
    외부 의존성 체크
    
    Spring Boot 백엔드, 데이터베이스, Redis 등의 외부 서비스 상태를 체크합니다.
    각 서비스에 대해 연결 상태와 응답 시간을 측정합니다.
    
    Returns:
        Dict[str, Any]: 외부 의존성 체크 결과
    """
    settings = get_settings()
    checks = {}
    
    # Check Spring Boot backend
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SPRING_BOOT_BASE_URL}/api/v1/actuator/health",
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
    """
    기본 헬스 체크 엔드포인트
    
    애플리케이션의 전반적인 상태를 체크합니다.
    시스템 리소스, 외부 의존성, 업타임 등의 정보를 종합하여
    전체적인 건강 상태를 평가합니다.
    
    Returns:
        HealthResponse: 종합적인 헬스 체크 결과
    """
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
    """
    Kubernetes를 위한 준비 상태 체크 엔드포인트
    
    애플리케이션이 요청을 받을 준비가 되었는지 확인합니다.
    주요 외부 의존성(예: Spring Boot)이 사용 가능한지 검증합니다.
    
    Returns:
        dict: 준비 상태 정보
        
    Raises:
        HTTPException: 서비스가 준비되지 않은 경우
    """
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
    """
    Kubernetes를 위한 활성 상태 체크 엔드포인트
    
    애플리케이션이 아직 살아있는지 확인합니다.
    간단한 상태 체크로 프로세스가 동작 중인지 확인합니다.
    
    Returns:
        dict: 활성 상태 정보
    """
    settings = get_settings()
    
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "version": settings.VERSION,
        "uptime": time.time() - start_time
    }