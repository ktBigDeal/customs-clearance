"""
Database Configuration and Connection Management
PostgreSQL을 사용한 대화기록 저장소 구성
"""

import os
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON, func, text
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """데이터베이스 설정 관리 - Railway 및 로컬 환경 지원"""
    
    def __init__(self):
        # 환경 감지
        self.is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Railway PostgreSQL 설정 (자동 감지)
        if self.is_railway:
            self._setup_railway_postgres()
        else:
            self._setup_local_postgres()
        
        # Railway Redis 설정 (자동 감지)
        if self.is_railway:
            self._setup_railway_redis()
        else:
            self._setup_local_redis()
        
        # 연결 풀 설정 (환경별 최적화)
        self._setup_connection_pools()
        
        logger.info(f"🔧 Database config initialized for {'Railway' if self.is_railway else 'Local'} environment")
    
    def _setup_railway_postgres(self):
        """Railway PostgreSQL 설정"""
        # Railway는 DATABASE_URL을 제공
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # DATABASE_URL 파싱 (Railway 표준)
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            self.postgres_host = parsed.hostname
            self.postgres_port = parsed.port or 5432
            self.postgres_db = parsed.path[1:]  # 첫 번째 '/' 제거
            self.postgres_user = parsed.username
            self.postgres_password = parsed.password
        else:
            # 개별 환경변수 사용
            self.postgres_host = os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "localhost"))
            self.postgres_port = int(os.getenv("PGPORT", os.getenv("POSTGRES_PORT", "5432")))
            self.postgres_db = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "conversations"))
            self.postgres_user = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres"))
            self.postgres_password = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "password"))
    
    def _setup_local_postgres(self):
        """로컬 PostgreSQL 설정"""
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.getenv("POSTGRES_PORT", "5433"))  # Docker는 5433
        self.postgres_db = os.getenv("POSTGRES_DB", "conversations")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "password")
    
    def _setup_railway_redis(self):
        """Railway Redis 설정"""
        # Railway Redis URL 지원
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            from urllib.parse import urlparse
            parsed = urlparse(redis_url)
            self.redis_host = parsed.hostname
            self.redis_port = parsed.port or 6379
            self.redis_password = parsed.password
            self.redis_db = 0  # Railway Redis는 일반적으로 DB 0
        else:
            # 개별 환경변수 사용
            self.redis_host = os.getenv("REDIS_HOST", "localhost")
            self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
            self.redis_password = os.getenv("REDIS_PASSWORD", None)
            self.redis_db = int(os.getenv("REDIS_DB", "0"))
    
    def _setup_local_redis(self):
        """로컬 Redis 설정"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6380"))  # Docker는 6380
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
    
    def _setup_connection_pools(self):
        """환경별 연결 풀 설정"""
        if self.is_railway:
            # Railway는 더 보수적인 풀 크기 사용
            self.postgres_pool_size = int(os.getenv("POSTGRES_POOL_SIZE", "5"))
            self.postgres_max_overflow = int(os.getenv("POSTGRES_MAX_OVERFLOW", "10"))
            self.redis_max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
        else:
            # 로컬은 더 큰 풀 크기 사용 가능
            self.postgres_pool_size = int(os.getenv("POSTGRES_POOL_SIZE", "10"))
            self.postgres_max_overflow = int(os.getenv("POSTGRES_MAX_OVERFLOW", "20"))
            self.redis_max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
    
    @property
    def postgres_url(self) -> str:
        """PostgreSQL 연결 URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def postgres_direct_url(self) -> str:
        """asyncpg 직접 연결 URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class Base(DeclarativeBase):
    """SQLAlchemy Base Model"""
    pass


class DatabaseManager:
    """데이터베이스 연결 및 세션 관리"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pg_engine = None
        self.pg_session_factory = None
        self.redis_client = None
        self.pg_pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self) -> None:
        """데이터베이스 연결 초기화"""
        try:
            # PostgreSQL SQLAlchemy 엔진
            self.pg_engine = create_async_engine(
                self.config.postgres_url,
                pool_size=self.config.postgres_pool_size,
                max_overflow=self.config.postgres_max_overflow,
                pool_pre_ping=True,
                echo=False  # 프로덕션에서는 False
            )
            
            # 세션 팩토리
            self.pg_session_factory = async_sessionmaker(
                self.pg_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # asyncpg 연결 풀 (Raw SQL 쿼리용)
            self.pg_pool = await asyncpg.create_pool(
                self.config.postgres_direct_url,
                min_size=5,
                max_size=15,
                command_timeout=30
            )
            
            # Redis 연결 (Railway/로컬 환경 대응)
            redis_config = {
                "host": self.config.redis_host,
                "port": self.config.redis_port,
                "db": self.config.redis_db,
                "decode_responses": True,
                "max_connections": self.config.redis_max_connections,
                "retry_on_timeout": True,
                "socket_timeout": 30,
                "socket_connect_timeout": 10
            }
            
            # Railway Redis 패스워드 지원
            if hasattr(self.config, 'redis_password') and self.config.redis_password:
                redis_config["password"] = self.config.redis_password
            
            self.redis_client = redis.Redis(**redis_config)
            
            # 연결 테스트
            await self._test_connections()
            
            logger.info("✅ Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def close(self) -> None:
        """데이터베이스 연결 종료"""
        try:
            if self.pg_engine:
                await self.pg_engine.dispose()
            
            if self.pg_pool:
                await self.pg_pool.close()
            
            if self.redis_client:
                await self.redis_client.aclose()
            
            logger.info("✅ Database connections closed")
            
        except Exception as e:
            logger.error(f"❌ Database close failed: {e}")
    
    async def _test_connections(self) -> None:
        """연결 상태 테스트"""
        # PostgreSQL 테스트
        async with self.pg_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        # Redis 테스트
        await self.redis_client.ping()
        
        logger.info("🔍 Database connection tests passed")
    
    @asynccontextmanager
    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """데이터베이스 세션 컨텍스트 매니저"""
        async with self.pg_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    @asynccontextmanager
    async def get_pg_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """PostgreSQL 직접 연결 컨텍스트 매니저"""
        async with self.pg_pool.acquire() as connection:
            yield connection
    
    async def get_redis(self) -> redis.Redis:
        """Redis 클라이언트 반환"""
        return self.redis_client


# 전역 데이터베이스 매니저 인스턴스
db_config = DatabaseConfig()
db_manager = DatabaseManager(db_config)


async def get_database_manager() -> DatabaseManager:
    """FastAPI 의존성 주입용 데이터베이스 매니저"""
    return db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성 주입용 데이터베이스 세션"""
    async with db_manager.get_db_session() as session:
        yield session


async def get_redis_client() -> redis.Redis:
    """FastAPI 의존성 주입용 Redis 클라이언트"""
    return await db_manager.get_redis()


# 데이터베이스 생성 스크립트
CREATE_TABLES_SQL = """
-- 대화 세션 테이블
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    last_agent_used VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    extra_metadata JSONB DEFAULT '{}'::jsonb
);

-- 메시지 테이블
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    agent_used VARCHAR(50),
    routing_info JSONB DEFAULT '{}'::jsonb,
    "references" JSONB DEFAULT '[]'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extra_metadata JSONB DEFAULT '{}'::jsonb
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(user_id, is_active, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_time ON messages(conversation_id, timestamp DESC);

-- JSON 필드 인덱스
CREATE INDEX IF NOT EXISTS idx_messages_agent_used ON messages(agent_used) WHERE agent_used IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_routing_info_complexity ON messages USING BTREE (CAST(routing_info->>'complexity' AS FLOAT));

-- 전문검색 인덱스는 나중에 필요시 수동으로 생성
-- CREATE INDEX IF NOT EXISTS idx_messages_content_search ON messages 
-- USING GIN (to_tsvector('simple', content));

-- 트리거: conversations 테이블 updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET updated_at = NOW() 
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_timestamp
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();
"""


async def create_tables():
    """데이터베이스 테이블 생성"""
    try:
        async with db_manager.get_pg_connection() as conn:
            await conn.execute(CREATE_TABLES_SQL)
        
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Table creation failed: {e}")
        raise