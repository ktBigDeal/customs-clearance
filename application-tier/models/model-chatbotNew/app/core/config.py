"""
애플리케이션 설정 관리 모듈

FastAPI 애플리케이션의 전역 설정을 관리합니다.
환경 변수, 데이터베이스 설정, JWT 설정, Redis 설정 등을 중앙 집중식으로 관리합니다.

주요 기능:
- 환경별 설정 (개발/테스트/운영)
- 데이터베이스 연결 설정 (PostgreSQL)
- Redis 캐시 설정
- JWT 토큰 검증 설정 (Spring Boot 연동)
- CORS 및 보안 설정
"""

import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any, Dict
from functools import lru_cache
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스
    
    환경 변수와 기본값을 통해 애플리케이션 설정을 관리합니다.
    Pydantic BaseSettings를 상속받아 자동 타입 검증과 환경 변수 로딩을 지원합니다.
    
    환경 변수 우선순위:
    1. 시스템 환경 변수
    2. .env 파일
    3. 기본값 (default)
    """
    
    # 기본 애플리케이션 설정
    APP_NAME: str = Field(default="관세법 RAG 챗봇 API", description="애플리케이션 이름")
    APP_VERSION: str = Field(default="1.0.0", description="애플리케이션 버전")
    ENVIRONMENT: str = Field(default="development", description="환경 구분 (development/production)")
    DEBUG: bool = Field(default=True, description="디버그 모드")
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", description="서버 호스트")
    PORT: int = Field(default=8000, description="서버 포트")
    
    # PostgreSQL 데이터베이스 설정
    POSTGRES_HOST: str = Field(default="172.30.1.20", description="PostgreSQL 호스트")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL 포트")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL 사용자명")
    POSTGRES_PASSWORD: str = Field(default="postgres123", description="PostgreSQL 비밀번호")
    POSTGRES_DB: str = Field(default="conversations", description="PostgreSQL 데이터베이스명")
    DATABASE_ECHO: bool = Field(default=False, description="SQLAlchemy 쿼리 로깅")
    
    # Redis 캐시 설정
    REDIS_HOST: str = Field(default="172.30.1.30", description="Redis 호스트")
    REDIS_PORT: int = Field(default=6379, description="Redis 포트")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis 비밀번호")
    REDIS_DB: int = Field(default=0, description="Redis 데이터베이스 번호")
    CACHE_TTL: int = Field(default=3600, description="캐시 기본 TTL (초)")
    SESSION_TTL: int = Field(default=86400, description="세션 TTL (초)")
    
    # ChromaDB 벡터 저장소 설정
    CHROMA_HOST: str = Field(default="172.30.1.40", description="ChromaDB 호스트")
    CHROMA_PORT: int = Field(default=8000, description="ChromaDB 포트")
    
    # JWT 토큰 설정 (Spring Boot 연동)
    JWT_SECRET: str = Field(default="mySecretKey", description="JWT 서명 검증 키")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 알고리즘")
    JWT_TOKEN_PREFIX: str = Field(default="Bearer", description="JWT 토큰 접두사")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT 토큰 만료 시간 (시간)")
    
    # Spring Boot 백엔드 연동 설정
    BACKEND_BASE_URL: str = Field(default="http://localhost:8080/api/v1", description="Spring Boot 백엔드 URL")
    BACKEND_TIMEOUT: int = Field(default=30, description="백엔드 API 타임아웃 (초)")
    
    # OpenAI API 설정
    OPENAI_API_KEY: str = Field(description="OpenAI API 키")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="사용할 OpenAI 모델")
    OPENAI_TEMPERATURE: float = Field(default=0.3, description="OpenAI 모델 temperature")
    OPENAI_MAX_TOKENS: int = Field(default=4000, description="최대 토큰 수")
    OPENAI_TIMEOUT: int = Field(default=60, description="OpenAI API 타임아웃 (초)")
    
    # CORS 설정
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], 
        description="허용된 CORS 오리진"
    )
    TRUSTED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"], 
        description="신뢰할 수 있는 호스트"
    )
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", description="로깅 레벨")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="로그 포맷"
    )
    
    # RAG 시스템 설정
    MAX_CONTEXT_DOCS: int = Field(default=8, description="최대 컨텍스트 문서 수")
    SIMILARITY_THRESHOLD: float = Field(default=0.2, description="유사도 임계값")
    MAX_CHAT_HISTORY: int = Field(default=20, description="최대 채팅 이력 수")
    
    # 비동기 처리 설정
    ASYNC_WORKER_COUNT: int = Field(default=4, description="비동기 워커 수")
    TASK_TIMEOUT: int = Field(default=300, description="작업 타임아웃 (초)")
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """환경 값 검증"""
        if v not in ["development", "testing", "production"]:
            raise ValueError("ENVIRONMENT는 development, testing, production 중 하나여야 합니다")
        return v
    
    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v):
        """JWT 시크릿 키 검증"""
        if len(v) < 8:
            raise ValueError("JWT_SECRET은 최소 8자 이상이어야 합니다")
        return v
    
    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v):
        """OpenAI API 키 검증"""
        if not v.startswith("sk-"):
            raise ValueError("유효하지 않은 OpenAI API 키 형식입니다")
        return v
    
    @property
    def postgres_url(self) -> str:
        """PostgreSQL 연결 URL 생성
        
        비동기 PostgreSQL 드라이버(asyncpg)를 사용한 연결 문자열을 반환합니다.
        
        Returns:
            str: PostgreSQL 연결 URL
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def redis_url(self) -> str:
        """Redis 연결 URL 생성
        
        Redis 연결 문자열을 반환합니다. 비밀번호가 설정된 경우 포함합니다.
        
        Returns:
            str: Redis 연결 URL
        """
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def chroma_url(self) -> str:
        """ChromaDB 연결 URL 생성
        
        Returns:
            str: ChromaDB 연결 URL
        """
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"
    
    @property
    def is_development(self) -> bool:
        """개발 환경 여부 확인
        
        Returns:
            bool: 개발 환경인지 여부
        """
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """운영 환경 여부 확인
        
        Returns:
            bool: 운영 환경인지 여부
        """
        return self.ENVIRONMENT == "production"
    
    def get_current_time(self) -> datetime:
        """현재 시간 반환 (KST)
        
        한국 표준시 기준의 현재 시간을 반환합니다.
        
        Returns:
            datetime: 현재 시간 (KST)
        """
        kst = timezone(timedelta(hours=9))
        return datetime.now(kst)
    
    def get_log_config(self) -> Dict[str, Any]:
        """로깅 설정 딕셔너리 반환
        
        Returns:
            Dict[str, Any]: 로깅 설정
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": self.LOG_FORMAT
                },
            },
            "handlers": {
                "default": {
                    "level": self.LOG_LEVEL,
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                },
                "file": {
                    "level": self.LOG_LEVEL,
                    "formatter": "standard",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "app/logs/chatbot_api.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": self.LOG_LEVEL,
                    "propagate": False
                }
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (싱글톤)
    
    애플리케이션 전체에서 동일한 설정 인스턴스를 사용하도록 캐싱합니다.
    환경 변수가 변경되면 애플리케이션을 다시 시작해야 합니다.
    
    Returns:
        Settings: 애플리케이션 설정 인스턴스
    """
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()


def validate_settings() -> bool:
    """설정 유효성 검사
    
    필수 설정값들이 올바르게 설정되었는지 확인합니다.
    데이터베이스 연결, API 키 등의 필수 요소를 검증합니다.
    
    Returns:
        bool: 설정이 유효한지 여부
        
    Raises:
        ValueError: 필수 설정이 누락되거나 잘못된 경우
    """
    try:
        # OpenAI API 키 존재 확인
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다")
        
        # 데이터베이스 URL 생성 테스트
        postgres_url = settings.postgres_url
        redis_url = settings.redis_url
        
        if not postgres_url or not redis_url:
            raise ValueError("데이터베이스 연결 설정이 올바르지 않습니다")
        
        # JWT 시크릿 검증
        if len(settings.JWT_SECRET) < 8:
            raise ValueError("JWT_SECRET이 너무 짧습니다 (최소 8자)")
        
        return True
        
    except Exception as e:
        raise ValueError(f"설정 검증 실패: {e}")


def create_env_file() -> bool:
    """환경 변수 예제 파일 생성
    
    .env.example 파일을 생성하여 필수 환경 변수 목록을 제공합니다.
    개발자가 쉽게 환경을 설정할 수 있도록 도움을 줍니다.
    
    Returns:
        bool: 파일 생성 성공 여부
    """
    try:
        env_example_content = '''# FastAPI RAG 챗봇 환경 변수 설정

# 애플리케이션 기본 설정
APP_NAME="관세법 RAG 챗봇 API"
APP_VERSION="1.0.0"
ENVIRONMENT="development"
DEBUG=true
HOST="0.0.0.0"
PORT=8000

# PostgreSQL 데이터베이스 설정 (대화 이력 저장)
POSTGRES_HOST="172.30.1.20"
POSTGRES_PORT=5432
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres123"
POSTGRES_DB="conversations"
DATABASE_ECHO=false

# Redis 캐시 설정
REDIS_HOST="172.30.1.30"
REDIS_PORT=6379
REDIS_PASSWORD=""
REDIS_DB=0
CACHE_TTL=3600
SESSION_TTL=86400

# ChromaDB 벡터 저장소 설정
CHROMA_HOST="172.30.1.40"
CHROMA_PORT=8000

# JWT 토큰 설정 (Spring Boot와 동일하게 설정)
JWT_SECRET="your-secret-key-here-min-8-chars"
JWT_ALGORITHM="HS256"
JWT_TOKEN_PREFIX="Bearer"
JWT_EXPIRATION_HOURS=24

# Spring Boot 백엔드 연동
BACKEND_BASE_URL="http://localhost:8080/api/v1"
BACKEND_TIMEOUT=30

# OpenAI API 설정 (필수)
OPENAI_API_KEY="sk-proj-your-openai-api-key-here"
OPENAI_MODEL="gpt-4o-mini"
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=60

# CORS 설정
CORS_ORIGINS='["http://localhost:3000", "http://127.0.0.1:3000"]'
TRUSTED_HOSTS='["localhost", "127.0.0.1", "0.0.0.0"]'

# 로깅 설정
LOG_LEVEL="INFO"

# RAG 시스템 설정
MAX_CONTEXT_DOCS=8
SIMILARITY_THRESHOLD=0.2
MAX_CHAT_HISTORY=20

# 비동기 처리 설정
ASYNC_WORKER_COUNT=4
TASK_TIMEOUT=300
'''
        
        env_file_path = Path(".env.example")
        
        if env_file_path.exists():
            return True  # 이미 존재하면 성공으로 간주
            
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.write(env_example_content)
            
        return True
        
    except Exception as e:
        print(f"❌ .env.example 파일 생성 실패: {e}")
        return False


# 애플리케이션 시작 시 설정 검증
if __name__ == "__main__":
    try:
        validate_settings()
        print("✅ 설정 검증 완료")
        print(f"📊 환경: {settings.ENVIRONMENT}")
        print(f"🗄️ PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        print(f"🗂️ Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"🔍 ChromaDB: {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
    except ValueError as e:
        print(f"❌ 설정 오류: {e}")
        create_env_file()
        print("📄 .env.example 파일을 참고하여 환경 변수를 설정해주세요.")