
"""
AI 게이트웨이 애플리케이션을 위한 설정 관리 모듈

이 모듈은 환경 변수와 기본값을 통해 애플리케이션의 모든 설정을 관리합니다.
Pydantic BaseSettings를 사용하여 설정 값들의 타입 안전성과 검증을 보장합니다.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    
    환경 변수 또는 .env 파일에서 설정 값들을 읽어와서 애플리케이션 전체에서
    사용할 수 있는 설정 객체를 생성합니다. 모든 설정 값들은 타입 힌트와 기본값을
    가지고 있어 안전하게 사용할 수 있습니다.
    """
    
    # Application settings
    APP_NAME: str = "Customs Clearance AI Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:8080",  # Spring Boot backend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # Database settings (optional for model metadata)
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Spring Boot backend integration
    SPRING_BOOT_BASE_URL: str = "http://localhost:8080"
    SPRING_BOOT_API_KEY: Optional[str] = None
    
    # Model services configuration
    MODEL_OCR_URL: str = "http://localhost:8001"
    MODEL_REPORT_URL: str = "http://localhost:8002"
    MODEL_HSCODE_URL: str = "http://localhost:8003"
    MODEL_CHATBOT_URL: str = "http://localhost:8004"
    
    # AI Model settings
    MODEL_STORAGE_PATH: str = "./models"
    DEFAULT_MODEL_TIMEOUT: int = 30
    MAX_BATCH_SIZE: int = 100
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Cache settings
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    캐시된 설정 인스턴스 반환
    
    설정 객체를 싱글톤 패턴으로 관리하여 메모리 효율성을 높이고
    설정 값 읽기 성능을 최적화합니다.
    
    Returns:
        Settings: 애플리케이션 설정 객체
    """
    return Settings()


def get_cors_origins() -> List[str]:
    """
    환경별 CORS 허용 출처 목록 반환
    
    실행 환경(development, staging, production)에 따라 적절한
    CORS 허용 출처 목록을 반환합니다. 프로덕션 환경에서는 보안을 위해
    허용 출처를 제한합니다.
    
    Returns:
        List[str]: CORS 허용 출처 URL 목록
    """
    settings = get_settings()
    
    if settings.ENVIRONMENT == "production":
        # 프로덕션 환경에서는 CORS 출처를 제한
        return [
            "https://your-production-frontend.com",
            "https://your-production-backend.com"
        ]
    elif settings.ENVIRONMENT == "staging":
        return [
            "https://staging-frontend.com", 
            "https://staging-backend.com",
            "http://localhost:3000",
            "http://localhost:8080"
        ]
    else:
        # 개발 환경 - 로컬 출처 허용
        return settings.CORS_ORIGINS