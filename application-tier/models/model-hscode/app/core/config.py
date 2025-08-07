"""
API 서버 설정 관리
"""

from pydantic import BaseSettings, Field
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
import os
import sys

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# 기존 설정 가져오기
try:
    from config import (
        FILE_PATHS, SYSTEM_CONFIG, DATA_INTEGRATION_CONFIG,
        SEARCH_ENGINE_CONFIG, CACHE_CONFIG, LLM_CONFIG,
        PERFORMANCE_CONFIG
    )
except ImportError as e:
    print(f"기존 설정 파일 로드 실패: {e}")
    # 기본값 설정
    FILE_PATHS = {}
    SYSTEM_CONFIG = {}
    DATA_INTEGRATION_CONFIG = {}
    SEARCH_ENGINE_CONFIG = {}
    CACHE_CONFIG = {}
    LLM_CONFIG = {}
    PERFORMANCE_CONFIG = {}

class Settings(BaseSettings):
    """API 서버 설정"""
    
    # API 서버 기본 설정
    app_name: str = Field(default="HS 코드 추천 API", description="애플리케이션 이름")
    app_version: str = Field(default="2.1.0", description="API 버전")
    debug: bool = Field(default=False, description="디버그 모드")
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", description="서버 호스트")
    port: int = Field(default=8003, description="서버 포트")
    workers: int = Field(default=1, description="워커 프로세스 수")
    
    # CORS 설정
    cors_origins: list = Field(default=["*"], description="CORS 허용 도메인")
    cors_methods: list = Field(default=["*"], description="CORS 허용 메서드")
    
    # 캐시 설정
    cache_dir: str = Field(
        default=str(PROJECT_ROOT / "cache" / "hs_code_cache"),
        description="캐시 디렉토리 경로"
    )
    cache_ttl: int = Field(default=3600, description="캐시 TTL (초)")
    
    # 추천 시스템 설정
    semantic_model: str = Field(
        default=SYSTEM_CONFIG.get('semantic_model', 'jhgan/ko-sroberta-multitask'),
        description="의미 검색 모델명"
    )
    top_k: int = Field(
        default=SYSTEM_CONFIG.get('top_k', 30),
        description="검색 결과 최대 개수"
    )
    
    # OpenAI 설정
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API 키")
    openai_api_file: str = Field(
        default=str(PROJECT_ROOT / "docs" / "Aivle-api.txt"),
        description="OpenAI API 키 파일 경로"
    )
    openai_model: str = Field(
        default=LLM_CONFIG.get('default_model', 'gpt-4.1-mini'),
        description="OpenAI 모델명"
    )
    
    # 성능 설정
    max_request_size: int = Field(default=10 * 1024 * 1024, description="최대 요청 크기 (바이트)")
    request_timeout: int = Field(default=30, description="요청 타임아웃 (초)")
    
    # 로깅 설정
    log_level: str = Field(default="INFO", description="로그 레벨")
    log_file: Optional[str] = Field(default=None, description="로그 파일 경로")
    
    # 데이터 파일 경로
    @property
    def file_paths(self) -> Dict[str, str]:
        """데이터 파일 경로 반환"""
        return FILE_PATHS
    
    @property
    def system_config(self) -> Dict[str, Any]:
        """시스템 설정 반환"""
        return SYSTEM_CONFIG
    
    @property
    def search_config(self) -> Dict[str, Any]:
        """검색 엔진 설정 반환"""
        return SEARCH_ENGINE_CONFIG
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """LLM 설정 반환"""
        return LLM_CONFIG
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

class DevelopmentSettings(Settings):
    """개발 환경 설정"""
    debug: bool = True
    log_level: str = "DEBUG"
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

class ProductionSettings(Settings):
    """프로덕션 환경 설정"""
    debug: bool = False
    log_level: str = "INFO"
    workers: int = 4
    cors_origins: list = []  # 프로덕션에서는 구체적으로 설정

class TestSettings(Settings):
    """테스트 환경 설정"""
    debug: bool = True
    cache_dir: str = str(PROJECT_ROOT / "test_cache")
    log_level: str = "DEBUG"

@lru_cache()
def get_settings() -> Settings:
    """환경에 따른 설정 반환"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()

# 전역 설정 인스턴스
settings = get_settings()