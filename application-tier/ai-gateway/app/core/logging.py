"""
AI 게이트웨이 애플리케이션을 위한 로깅 설정 모듈

이 모듈은 구조화된 로그와 표준 로그를 모두 지원하는 로깅 시스템을 설정합니다.
JSON 형태의 구조화된 로그를 통해 로그 분석과 모니터링을 용이하게 합니다.
"""

import logging
import logging.config
import sys
from typing import Dict, Any

import structlog
from pythonjsonlogger import jsonlogger

from .config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """
    애플리케이션 로깅 설정 초기화
    
    structlog과 표준 logging을 모두 설정하여 구조화된 로그와
    일반 로그를 모두 지원합니다. JSON 형태의 로그 출력으로
    로그 분석과 모니터링을 최적화합니다.
    """
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    log_config = get_logging_config()
    logging.config.dictConfig(log_config)


def get_logging_config() -> Dict[str, Any]:
    """
    로깅 설정 딕셔너리 반환
    
    환경 설정에 따라 적절한 로그 포맷터와 핸들러를 구성합니다.
    콘솔 출력과 파일 출력을 모두 지원하며, 로그 로테이션도 설정됩니다.
    
    Returns:
        Dict[str, Any]: 로깅 설정 딕셔너리
    """
    
    formatters = {
        "json": {
            "()": jsonlogger.JsonFormatter,
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    }
    
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
            "level": settings.LOG_LEVEL
        }
    }
    
    # Add file handler if log file is specified
    if settings.LOG_FILE:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": settings.LOG_FILE,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
            "level": settings.LOG_LEVEL
        }
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": {
            "": {  # Root logger
                "handlers": list(handlers.keys()),
                "level": settings.LOG_LEVEL,
                "propagate": False
            },
            "uvicorn": {
                "handlers": list(handlers.keys()),
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": list(handlers.keys()),
                "level": "INFO",
                "propagate": False
            },
            "fastapi": {
                "handlers": list(handlers.keys()),
                "level": "INFO",
                "propagate": False
            }
        }
    }


def get_logger(name: str) -> structlog.BoundLogger:
    """
    구조화된 로거 인스턴스 반환
    
    주어진 이름으로 structlog 로거를 생성합니다.
    이 로거는 구조화된 로그 메시지를 JSON 형태로 출력합니다.
    
    Args:
        name (str): 로거 이름
        
    Returns:
        structlog.BoundLogger: 구조화된 로거 인스턴스
    """
    return structlog.get_logger(name)