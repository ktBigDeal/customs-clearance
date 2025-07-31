"""
Configuration settings for the AI Gateway application.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "Customs Clearance AI Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
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
    """Get cached settings instance"""
    return Settings()


# Environment-specific configurations
def get_cors_origins() -> List[str]:
    """Get CORS origins based on environment"""
    settings = get_settings()
    
    if settings.ENVIRONMENT == "production":
        # In production, restrict CORS origins
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
        # Development - allow local origins
        return settings.CORS_ORIGINS