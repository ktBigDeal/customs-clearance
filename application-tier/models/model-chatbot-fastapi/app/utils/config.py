"""
Configuration Management Module

환경 변수 및 설정 관리를 담당하는 모듈입니다.
python-dotenv를 사용한 자동 로딩으로 개선했습니다.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv # pyright: ignore[reportMissingImports]
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

logger = logging.getLogger(__name__)


def load_config(env_file: Optional[str] = None) -> Dict[str, str]:
    """
    환경 변수를 안전하게 로드하고 검증하는 함수
    
    환경 변수(Environment Variables)란?
    - 운영체제에 저장된 설정값들 (예: API 키, 데이터베이스 주소)
    - 코드에 직접 쓰면 보안 위험, 환경변수로 분리하면 안전
    - .env 파일: 개발자가 쉽게 관리할 수 있는 환경변수 파일
    
    이 함수가 하는 일:
    1. .env 파일을 찾아서 로드 (python-dotenv 라이브러리 사용)
    2. 필수 환경변수(OPENAI_API_KEY) 존재 확인
    3. 선택적 환경변수(HF_TOKEN) 체크
    4. 보안을 위해 API 키는 일부만 출력 (마스킹)
    
    Args:
        env_file (Optional[str]): .env 파일의 경로를 직접 지정
                                  None이면 프로젝트 루트에서 자동으로 찾음
                                  
    Returns:
        Dict[str, str]: 성공적으로 로드된 환경 변수들의 딕셔너리
                        예: {"OPENAI_API_KEY": "sk-proj-...", "HF_TOKEN": "hf_..."}
    
    Raises:
        ValueError: 필수 환경변수가 없을 때 발생
        
    신입 개발자 팁:
    - 절대로 API 키를 코드에 직접 적지 마세요!
    - .env 파일은 .gitignore에 추가해서 Git에 올라가지 않도록 하세요
    - 로그에 민감한 정보가 노출되지 않도록 마스킹 처리합니다
    """
    # 프로젝트 루트 디렉토리 찾기
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent # model-chatbot-fastapi
    
    # .env 파일 경로 결정
    if env_file is None:
        env_file = project_root / ".env"
    else:
        env_file = Path(env_file)
    
    # .env 파일 로드
    if env_file.exists() and HAS_DOTENV:
        load_dotenv(env_file)
        logger.info(f"Environment variables loaded from {env_file}")
        print(f"✅ 환경 변수 로드 완료: {env_file}")
    elif env_file.exists() and not HAS_DOTENV:
        logger.warning("python-dotenv not installed. Please install it with: pip install python-dotenv")
        print("⚠️ python-dotenv가 설치되지 않았습니다.")
        print("  다음 명령으로 설치해주세요: pip install python-dotenv")
        print("  또는 직접 환경 변수를 설정해주세요.")
    else:
        logger.warning(f".env file not found at {env_file}")
        print(f"⚠️ .env 파일을 찾을 수 없습니다: {env_file}")
        print("  .env.example을 참고하여 .env 파일을 생성해주세요.")
    
    # 필수 환경 변수 확인
    required_vars = ["OPENAI_API_KEY"]
    optional_vars = ["HF_TOKEN"]
    
    config = {}
    missing_vars = []
    
    # 필수 변수 체크
    for var in required_vars:
        value = os.getenv(var)
        if value:
            config[var] = value
            # API 키는 일부만 출력
            masked_value = value[:10] + "..." if len(value) > 10 else "***"
            logger.info(f"{var} loaded: {masked_value}")
            print(f"✅ {var}: {masked_value}")
        else:
            missing_vars.append(var)
    
    # 선택적 변수 체크
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            config[var] = value
            masked_value = value[:10] + "..." if len(value) > 10 else "***"
            logger.info(f"{var} loaded: {masked_value}")
            print(f"✅ {var}: {masked_value}")
        else:
            logger.info(f"{var} not provided (optional)")
            print(f"ℹ️ {var}: 설정되지 않음 (선택사항)")
    
    # 필수 변수가 누락된 경우 경고
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        print("  .env 파일에 필수 환경 변수를 설정해주세요.")
        raise ValueError(error_msg)
    
    return config


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 경로 반환 (model-chatbot-fastapi 기준)
    
    Returns:
        Path: model-chatbot-fastapi 프로젝트 루트 경로
    """
    current_dir = Path(__file__).parent
    fastapi_root = current_dir.parent.parent  # model-chatbot-fastapi 루트
    return fastapi_root


def get_trade_agent_config() -> Dict[str, Any]:
    """
    무역 정보 에이전트의 동작 설정을 반환하는 함수
    
    Returns:
        Dict[str, Any]: 에이전트 설정 딕셔너리
    """
    return {
        "collection_name": "trade_info_collection",
        "model_name": "gpt-4.1-mini",
        "temperature": 0.3,
        "max_context_docs": 8,
        "similarity_threshold": 0.0,
        "animal_plant_threshold": 0.1,
        "rerank_threshold": 0.2,
        "max_history": 10,
        "search_filters": {
            "default_expand_synonyms": True,
            "default_include_related": True,
            "supported_countries": [
                "미국", "중국", "일본", "독일", "영국", "프랑스", 
                "이탈리아", "캐나다", "호주", "인도", "인도네시아",
                "말레이시아", "필리핀", "튀르키예", "이집트", "EU"
            ],
            "supported_categories": [
                "철강", "플라스틱", "고무", "화학품", "기계", "전기기기",
                "농산물", "섬유", "의류", "신발", "가구", "완구"
            ]
        }
    }


def get_setting(key_path: str, default: Any = None) -> Any:
    """설정값 조회
    
    Args:
        key_path (str): 점으로 구분된 설정 키 경로
        default (Any): 기본값
        
    Returns:
        Any: 설정값
    """
    # 기본 설정값들
    DEFAULT_SETTINGS = {
        "chunk_strategy": {
            "paragraph_threshold": 3,
            "max_content_length": 2000,
            "min_content_length": 10
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    keys = key_path.split('.')
    value = DEFAULT_SETTINGS
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def get_chromadb_config() -> Dict[str, Any]:
    """
    ChromaDB 연결 설정을 반환하는 함수 (FastAPI용)
    
    기존 model-chatbot의 ChromaDB 설정을 FastAPI 환경에 맞게 적응
    
    환경변수:
    - CHROMADB_MODE: "local" (기본값) 또는 "docker"
    - CHROMADB_HOST: Docker 모드일 때 ChromaDB 서버 호스트 (기본값: "localhost")
    - CHROMADB_PORT: Docker 모드일 때 ChromaDB 서버 포트 (기본값: "8011")
    
    Returns:
        Dict[str, Any]: ChromaDB 연결 설정
    """
    mode = os.getenv("CHROMADB_MODE", "local").lower()
    
    config = {
        "collection_name": "trade_info_collection"
    }
    
    if mode == "docker":
        config.update({
            "mode": "docker",
            "host": os.getenv("CHROMADB_HOST", "localhost"),
            "port": int(os.getenv("CHROMADB_PORT", "8011"))
        })
        logger.info(f"ChromaDB Docker mode: {config['host']}:{config['port']}")
    else:
        config.update({
            "mode": "local",
            "persist_directory": str("chroma_db")
        })
        logger.info(f"ChromaDB local mode: {config['persist_directory']}")
    
    return config


def get_law_chromadb_config() -> Dict[str, Any]:
    """관세법 전용 ChromaDB 설정"""
    config = get_chromadb_config()
    config["collection_name"] = "customs_law_collection"
    return config

def get_fastapi_config() -> Dict[str, Any]:
    """FastAPI 서버 전용 설정"""
    return {
        "title": "관세 통관 챗봇 서비스",
        "description": "LangGraph 기반 관세법 전문 챗봇 API",
        "version": "1.0.0",
        "host": "0.0.0.0",
        "port": int(os.getenv("FASTAPI_PORT", "8004")),
        "reload": os.getenv("FASTAPI_RELOAD", "true").lower() == "true",
        "workers": int(os.getenv("FASTAPI_WORKERS", "1")),
        "cors_origins": [
            "http://localhost:3000",  # Next.js 개발 서버
            "http://localhost:8080",  # Spring Boot 백엔드
            "https://customs-clearance.com",  # 프로덕션 도메인
        ]
    }


def get_langgraph_config() -> Dict[str, Any]:
    """LangGraph 시스템 설정"""
    return {
        "model_name": os.getenv("LANGGRAPH_MODEL", "gpt-4.1-mini"),
        "temperature": float(os.getenv("LANGGRAPH_TEMPERATURE", "0.1")),
        "max_retries": int(os.getenv("LANGGRAPH_MAX_RETRIES", "3")),
        "timeout_seconds": int(os.getenv("LANGGRAPH_TIMEOUT", "60")),
        "enable_caching": os.getenv("LANGGRAPH_ENABLE_CACHING", "true").lower() == "true",
        "cache_ttl": int(os.getenv("LANGGRAPH_CACHE_TTL", "3600"))
    }