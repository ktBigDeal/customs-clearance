"""
PostgreSQL 데이터베이스 연결 및 모델 관리 모듈

FastAPI 애플리케이션의 PostgreSQL 데이터베이스 연결을 관리합니다.
SQLAlchemy 2.0 비동기 ORM을 사용하여 대화 이력을 저장하고 관리합니다.

주요 기능:
- 비동기 데이터베이스 연결 관리
- 세션 팩토리 및 컨텍스트 관리
- 데이터베이스 테이블 자동 생성
- 연결 풀 관리 및 최적화
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    AsyncEngine, 
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 데이터베이스 객체
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
    """SQLAlchemy 기본 모델 클래스
    
    모든 데이터베이스 모델이 상속받을 기본 클래스입니다.
    공통 필드와 메서드를 정의할 수 있습니다.
    """
    pass


def create_database_engine() -> AsyncEngine:
    """비동기 데이터베이스 엔진 생성
    
    PostgreSQL 데이터베이스에 대한 비동기 엔진을 생성합니다.
    연결 풀과 타임아웃 설정을 포함합니다.
    
    Returns:
        AsyncEngine: SQLAlchemy 비동기 엔진
        
    Raises:
        SQLAlchemyError: 데이터베이스 연결 생성 실패
    """
    try:
        # 개발 환경에서는 쿼리 로깅 활성화
        echo_queries = settings.is_development and settings.DATABASE_ECHO
        
        # 연결 풀 설정 (운영 환경에서는 더 보수적으로)
        if settings.is_production:
            pool_size = 10
            max_overflow = 20
            pool_recycle = 3600
            pool_pre_ping = True
        else:
            pool_size = 5
            max_overflow = 10
            pool_recycle = 7200
            pool_pre_ping = False
        
        engine = create_async_engine(
            settings.postgres_url,
            echo=echo_queries,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            # 연결 타임아웃 설정
            connect_args={
                "server_settings": {
                    "application_name": settings.APP_NAME,
                    "timezone": "Asia/Seoul",
                }
            }
        )
        
        logger.info(f"✅ PostgreSQL 엔진 생성 완료: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        return engine
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL 엔진 생성 실패: {e}")
        raise SQLAlchemyError(f"데이터베이스 엔진 생성 실패: {e}")


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """비동기 세션 팩토리 생성
    
    데이터베이스 세션을 생성하는 팩토리를 만듭니다.
    자동 커밋 및 플러시 설정을 포함합니다.
    
    Args:
        engine (AsyncEngine): 데이터베이스 엔진
        
    Returns:
        async_sessionmaker[AsyncSession]: 세션 팩토리
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,  # 명시적 flush 제어
        autocommit=False  # 트랜잭션 수동 제어
    )


async def init_db() -> None:
    """데이터베이스 초기화
    
    데이터베이스 엔진과 세션 팩토리를 초기화하고,
    필요한 테이블을 생성합니다.
    
    Raises:
        SQLAlchemyError: 데이터베이스 초기화 실패
    """
    global _engine, _session_factory
    
    try:
        # 엔진 생성
        _engine = create_database_engine()
        
        # 세션 팩토리 생성
        _session_factory = create_session_factory(_engine)
        
        # 연결 테스트
        async with _engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        logger.info("✅ 데이터베이스 연결 테스트 완료")
        
        # 테이블 생성 (개발 환경에서만)
        if settings.is_development:
            async with _engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ 데이터베이스 테이블 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        raise SQLAlchemyError(f"데이터베이스 초기화 실패: {e}")


async def close_db() -> None:
    """데이터베이스 연결 종료
    
    데이터베이스 엔진을 정리하고 연결을 종료합니다.
    """
    global _engine, _session_factory
    
    try:
        if _engine:
            await _engine.dispose()
            logger.info("✅ 데이터베이스 연결 종료 완료")
        
        _engine = None
        _session_factory = None
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 종료 실패: {e}")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 컨텍스트 매니저
    
    데이터베이스 세션을 생성하고 자동으로 정리합니다.
    트랜잭션 관리와 예외 처리를 포함합니다.
    
    Yields:
        AsyncSession: 데이터베이스 세션
        
    Raises:
        RuntimeError: 데이터베이스가 초기화되지 않은 경우
        SQLAlchemyError: 세션 생성 또는 사용 중 오류
        
    Example:
        ```python
        async with get_db_session() as session:
            result = await session.execute(select(User))
            await session.commit()
        ```
    """
    if not _session_factory:
        raise RuntimeError("데이터베이스가 초기화되지 않았습니다. init_db()를 먼저 호출하세요.")
    
    session = _session_factory()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ 데이터베이스 세션 오류 (롤백됨): {e}")
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성 주입용 데이터베이스 세션
    
    FastAPI의 Depends()와 함께 사용되는 데이터베이스 세션 의존성입니다.
    각 요청마다 새로운 세션을 생성하고 요청 완료 후 정리합니다.
    
    Yields:
        AsyncSession: 데이터베이스 세션
        
    Example:
        ```python
        @router.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    async with get_db_session() as session:
        yield session


class DatabaseManager:
    """데이터베이스 관리 클래스
    
    데이터베이스 연결 상태 확인, 헬스체크, 마이그레이션 등의 
    관리 기능을 제공합니다.
    """
    
    @staticmethod
    async def health_check() -> dict:
        """데이터베이스 헬스체크
        
        데이터베이스 연결 상태와 기본 쿼리 실행을 확인합니다.
        
        Returns:
            dict: 헬스체크 결과
        """
        if not _engine:
            return {
                "status": "unhealthy",
                "message": "데이터베이스 엔진이 초기화되지 않음"
            }
        
        try:
            async with _engine.begin() as conn:
                result = await conn.execute(text("SELECT version(), current_timestamp"))
                row = result.first()
                
                return {
                    "status": "healthy",
                    "database": "PostgreSQL",
                    "version": row[0] if row else "unknown",
                    "timestamp": row[1].isoformat() if row and row[1] else None,
                    "connection_pool": {
                        "size": _engine.pool.size(),
                        "checked_in": _engine.pool.checkedin(),
                        "checked_out": _engine.pool.checkedout(),
                        "overflow": _engine.pool.overflow(),
                    }
                }
                
        except Exception as e:
            logger.error(f"데이터베이스 헬스체크 실패: {e}")
            return {
                "status": "unhealthy",
                "message": str(e)
            }
    
    @staticmethod
    async def get_connection_info() -> dict:
        """데이터베이스 연결 정보 반환
        
        Returns:
            dict: 연결 정보
        """
        if not _engine:
            return {"status": "not_initialized"}
        
        return {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB,
            "user": settings.POSTGRES_USER,
            "url": settings.postgres_url.replace(settings.POSTGRES_PASSWORD, "***"),
            "pool_size": _engine.pool.size() if _engine else None,
            "echo": _engine.echo if _engine else None,
        }
    
    @staticmethod
    async def execute_raw_query(query: str) -> dict:
        """원시 SQL 쿼리 실행 (개발/관리용)
        
        Args:
            query (str): 실행할 SQL 쿼리
            
        Returns:
            dict: 쿼리 실행 결과
            
        Warning:
            운영 환경에서는 사용하지 마세요. SQL 인젝션 위험이 있습니다.
        """
        if settings.is_production:
            raise RuntimeError("운영 환경에서는 원시 쿼리 실행이 금지됩니다")
        
        if not _engine:
            raise RuntimeError("데이터베이스가 초기화되지 않았습니다")
        
        try:
            async with _engine.begin() as conn:
                result = await conn.execute(text(query))
                
                if result.returns_rows:
                    rows = result.fetchall()
                    return {
                        "success": True,
                        "rows": [dict(row._mapping) for row in rows],
                        "row_count": len(rows)
                    }
                else:
                    return {
                        "success": True,
                        "affected_rows": result.rowcount,
                        "message": "쿼리가 성공적으로 실행되었습니다"
                    }
                    
        except Exception as e:
            logger.error(f"원시 쿼리 실행 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()