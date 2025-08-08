"""
Database Initialization Utilities
FastAPI 애플리케이션 시작 시 데이터베이스 초기화를 위한 유틸리티
"""

import logging
from typing import Optional
import asyncio

from ..core.database import db_manager, create_tables, DatabaseConfig

logger = logging.getLogger(__name__)


async def initialize_database(check_tables: bool = True, create_if_missing: bool = True) -> bool:
    """
    데이터베이스 초기화 및 테이블 생성
    
    Args:
        check_tables: 기존 테이블 존재 여부 확인
        create_if_missing: 테이블이 없으면 생성
        
    Returns:
        bool: 초기화 성공 여부
    """
    try:
        logger.info("🚀 Initializing database...")
        
        # 1. 데이터베이스 연결 초기화
        await db_manager.initialize()
        logger.info("✅ Database connection established")
        
        # 2. 테이블 존재 확인
        if check_tables:
            tables_exist = await check_required_tables()
            
            if not tables_exist:
                if create_if_missing:
                    logger.info("📋 Creating missing database tables...")
                    await create_tables()
                    logger.info("✅ Database tables created successfully")
                else:
                    logger.warning("⚠️ Required tables are missing but auto-creation is disabled")
                    return False
            else:
                logger.info("✅ All required database tables exist")
        else:
            # 테이블 확인 없이 생성 (멱등성 보장)
            await create_tables()
            logger.info("✅ Database tables ensured")
        
        # 3. 기본 확인
        await verify_database_health()
        
        logger.info("🎉 Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


async def check_required_tables() -> bool:
    """필수 테이블 존재 여부 확인"""
    try:
        async with db_manager.get_pg_connection() as conn:
            result = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('conversations', 'messages')
                ORDER BY table_name
            """)
            
            table_names = [row['table_name'] for row in result]
            required_tables = {'conversations', 'messages'}
            existing_tables = set(table_names)
            
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                logger.warning(f"⚠️ Missing tables: {missing_tables}")
                return False
            else:
                logger.info(f"✅ Found all required tables: {existing_tables}")
                return True
                
    except Exception as e:
        logger.error(f"❌ Table check failed: {e}")
        return False


async def verify_database_health() -> bool:
    """데이터베이스 상태 확인"""
    try:
        # PostgreSQL 연결 테스트
        async with db_manager.get_db_session() as session:
            result = await session.execute("SELECT 1 as test")
            assert result.scalar() == 1
        
        # Redis 연결 테스트
        redis_client = await db_manager.get_redis()
        await redis_client.ping()
        
        logger.info("✅ Database health check passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False


async def get_database_info() -> dict:
    """데이터베이스 정보 조회"""
    try:
        async with db_manager.get_pg_connection() as conn:
            # 데이터베이스 버전 확인
            version_result = await conn.fetchrow("SELECT version() as version")
            
            # 테이블 정보 확인
            tables_result = await conn.fetch("""
                SELECT 
                    schemaname, 
                    tablename, 
                    tableowner,
                    tablespace
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            
            # 인덱스 정보 확인
            indexes_result = await conn.fetch("""
                SELECT 
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            # 데이터 수 확인
            conv_count = 0
            msg_count = 0
            
            try:
                conv_result = await conn.fetchrow("SELECT COUNT(*) as count FROM conversations")
                conv_count = conv_result['count'] if conv_result else 0
                
                msg_result = await conn.fetchrow("SELECT COUNT(*) as count FROM messages")
                msg_count = msg_result['count'] if msg_result else 0
            except Exception:
                # 테이블이 없을 수 있음
                pass
            
            config = DatabaseConfig()
            
            return {
                "database_version": version_result['version'] if version_result else "Unknown",
                "connection_info": {
                    "host": config.postgres_host,
                    "port": config.postgres_port,
                    "database": config.postgres_db,
                    "user": config.postgres_user
                },
                "tables": [
                    {
                        "schema": row['schemaname'],
                        "name": row['tablename'],
                        "owner": row['tableowner']
                    }
                    for row in tables_result
                ],
                "indexes": [
                    {
                        "table": row['tablename'],
                        "name": row['indexname'],
                        "definition": row['indexdef']
                    }
                    for row in indexes_result
                ],
                "data_counts": {
                    "conversations": conv_count,
                    "messages": msg_count
                },
                "redis_info": {
                    "host": config.redis_host,
                    "port": config.redis_port,
                    "database": config.redis_db
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get database info: {e}")
        return {"error": str(e)}


class DatabaseReadinessChecker:
    """데이터베이스 준비상태 확인 클래스"""
    
    def __init__(self, max_retries: int = 5, retry_delay: float = 2.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def wait_for_database(self) -> bool:
        """데이터베이스 준비될 때까지 대기"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔍 Database readiness check (attempt {attempt}/{self.max_retries})")
                
                # 연결 시도
                await db_manager.initialize()
                
                # 간단한 쿼리 실행
                await verify_database_health()
                
                logger.info("✅ Database is ready")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Database not ready (attempt {attempt}): {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"⏳ Waiting {self.retry_delay}s before retry...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("❌ Database readiness check failed after all retries")
                    return False
        
        return False


async def ensure_database_ready() -> bool:
    """데이터베이스가 준비될 때까지 대기하고 초기화"""
    checker = DatabaseReadinessChecker()
    
    # 1. 데이터베이스 준비 대기
    if not await checker.wait_for_database():
        logger.error("❌ Database is not ready")
        return False
    
    # 2. 테이블 초기화
    if not await initialize_database():
        logger.error("❌ Database initialization failed")
        return False
    
    return True


# FastAPI 시작 시 사용할 수 있는 편의 함수
async def startup_database_init() -> None:
    """FastAPI 애플리케이션 시작 시 데이터베이스 초기화"""
    try:
        success = await ensure_database_ready()
        if not success:
            raise RuntimeError("Database initialization failed during startup")
        logger.info("🚀 FastAPI database startup initialization completed")
    except Exception as e:
        logger.error(f"💥 FastAPI database startup failed: {e}")
        raise


async def shutdown_database() -> None:
    """FastAPI 애플리케이션 종료 시 데이터베이스 연결 정리"""
    try:
        await db_manager.close()
        logger.info("✅ Database connections closed during shutdown")
    except Exception as e:
        logger.error(f"❌ Database shutdown error: {e}")


# 헬스체크용 함수 (FastAPI health endpoint에서 사용 가능)
async def database_health_check() -> dict:
    """데이터베이스 상태 확인 (헬스체크용)"""
    try:
        # PostgreSQL 확인
        async with db_manager.get_db_session() as session:
            pg_result = await session.execute("SELECT 1")
            pg_healthy = pg_result.scalar() == 1
        
        # Redis 확인
        redis_client = await db_manager.get_redis()
        await redis_client.ping()
        redis_healthy = True
        
        return {
            "status": "healthy" if pg_healthy and redis_healthy else "unhealthy",
            "checks": {
                "postgresql": "healthy" if pg_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy"
            },
            "timestamp": logger.info("Database health check completed")
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": logger.error(f"Database health check failed: {e}")
        }