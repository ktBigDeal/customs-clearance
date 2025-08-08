#!/usr/bin/env python3
"""
Database Setup Script
PostgreSQL 데이터베이스 테이블 및 인덱스 생성을 위한 스크립트
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager, create_tables, DatabaseConfig
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_database_connection():
    """데이터베이스 연결 확인"""
    try:
        logger.info("🔍 Checking database connection...")
        await db_manager.initialize()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def setup_database():
    """데이터베이스 초기 설정"""
    try:
        logger.info("🚀 Starting database setup...")
        
        # 1. 데이터베이스 연결 초기화
        if not await check_database_connection():
            logger.error("❌ Cannot proceed without database connection")
            return False
        
        # 2. 테이블 생성
        logger.info("📋 Creating database tables...")
        await create_tables()
        
        # 3. 연결 테스트
        logger.info("🧪 Testing database functionality...")
        await test_database_functionality()
        
        logger.info("✅ Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False
    
    finally:
        # 연결 종료
        await db_manager.close()


async def test_database_functionality():
    """데이터베이스 기능 테스트"""
    try:
        # PostgreSQL 테스트
        async with db_manager.get_pg_connection() as conn:
            # 테이블 존재 확인
            result = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('conversations', 'messages')
            """)
            
            table_names = [row['table_name'] for row in result]
            logger.info(f"📋 Found tables: {table_names}")
            
            if 'conversations' not in table_names or 'messages' not in table_names:
                raise Exception("Required tables not found")
            
            # 인덱스 확인
            result = await conn.fetch("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename IN ('conversations', 'messages')
                ORDER BY indexname
            """)
            
            index_names = [row['indexname'] for row in result]
            logger.info(f"🔍 Found indexes: {len(index_names)} indexes created")
            
        # Redis 테스트
        redis_client = await db_manager.get_redis()
        await redis_client.ping()
        logger.info("✅ Redis connection test passed")
        
        logger.info("✅ All database functionality tests passed")
        
    except Exception as e:
        logger.error(f"❌ Database functionality test failed: {e}")
        raise


def print_environment_info():
    """환경 변수 정보 출력"""
    config = DatabaseConfig()
    
    logger.info("🔧 Database Configuration:")
    logger.info(f"  PostgreSQL Host: {config.postgres_host}:{config.postgres_port}")
    logger.info(f"  PostgreSQL Database: {config.postgres_db}")
    logger.info(f"  PostgreSQL User: {config.postgres_user}")
    logger.info(f"  Redis Host: {config.redis_host}:{config.redis_port}")
    logger.info(f"  Redis Database: {config.redis_db}")
    logger.info(f"  Connection Pool Size: {config.postgres_pool_size}")
    

def print_usage():
    """사용법 출력"""
    print("""
Database Setup Script for model-chatbot-fastapi

Usage:
    python scripts/setup_database.py [options]

Options:
    --help, -h       Show this help message
    --info, -i       Show database configuration
    --test, -t       Test database connection only
    --setup, -s      Setup database (default)

Environment Variables:
    POSTGRES_HOST     PostgreSQL host (default: localhost)
    POSTGRES_PORT     PostgreSQL port (default: 5432)
    POSTGRES_DB       PostgreSQL database (default: conversations)
    POSTGRES_USER     PostgreSQL username (default: postgres)
    POSTGRES_PASSWORD PostgreSQL password (default: password)
    REDIS_HOST        Redis host (default: localhost)
    REDIS_PORT        Redis port (default: 6379)
    REDIS_DB          Redis database (default: 0)

Examples:
    # Setup database with default settings
    python scripts/setup_database.py

    # Check connection only
    python scripts/setup_database.py --test

    # Show configuration
    python scripts/setup_database.py --info
""")


async def main():
    """메인 함수"""
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print_usage()
        return
    
    if '--info' in args or '-i' in args:
        print_environment_info()
        return
    
    if '--test' in args or '-t' in args:
        logger.info("🧪 Testing database connection only...")
        success = await check_database_connection()
        if success:
            logger.info("✅ Database connection test passed")
            await db_manager.close()
        else:
            logger.error("❌ Database connection test failed")
        return
    
    # 기본: 데이터베이스 설정
    logger.info("🚀 Starting database setup process...")
    print_environment_info()
    
    success = await setup_database()
    
    if success:
        logger.info("🎉 Database setup completed successfully!")
        logger.info("📝 You can now start the FastAPI application")
        sys.exit(0)
    else:
        logger.error("💥 Database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️  Database setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)