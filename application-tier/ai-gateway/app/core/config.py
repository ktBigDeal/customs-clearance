"""
AI 게이트웨이 애플리케이션 설정 모듈
환경 변수와 기본값을 사용하여 설정을 로드하며, 타입 안전성을 보장합니다.
"""

import osfrom functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json


class Settings(BaseSettings):
    # OpenAI API
    OPENAI_API_KEY: str
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
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # CORS settings
    CORS_ORIGINS: List[str] = []

    # Database settings
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Spring Boot backend
    SPRING_BOOT_BASE_URL: str
    SPRING_BOOT_API_KEY: Optional[str] = None

    # Model services
    MODEL_OCR_URL: str
    MODEL_REPORT_URL: str
    MODEL_HSCODE_URL: str
    MODEL_CHATBOT_URL: str

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
    CACHE_TTL: int = 300

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_cors_origins() -> List[str]:
    settings = get_settings()
    if settings.ENVIRONMENT == "production":
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
    return settings.CORS_ORIGINS
