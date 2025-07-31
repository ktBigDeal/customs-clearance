"""
Logging configuration for the AI Gateway application.
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
    """Setup application logging configuration"""
    
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
    """Get logging configuration dictionary"""
    
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
    """Get a structured logger instance"""
    return structlog.get_logger(name)