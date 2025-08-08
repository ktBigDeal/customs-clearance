#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
독립적으로 실행 가능한 데이터베이스 테이블 생성 스크립트
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from app.core.database import db_manager, create_tables

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_database():
    """
    데이터베이스 초기화
    1. 데이터베이스 매니저 초기화
    2. 테이블 생성
    3. 연결 확인
    """
    try:
        logger.info("🚀 Starting database initialization...")
        
        # 환경변수 검증
        required_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.info("💡 Please set the following environment variables:")
            for var in missing_vars:
                logger.info(f"   export {var}=your_value")
            return False
        
        # 데이터베이스 연결 초기화
        logger.info("🔧 Initializing database connections...")
        await db_manager.initialize()
        
        # 테이블 생성
        logger.info("📋 Creating database tables...")
        await create_tables()
        
        # 연결 테스트
        logger.info("🔍 Testing database connectivity...")
        from sqlalchemy import text
        async with db_manager.get_db_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM conversations"))
            count = result.scalar()
            logger.info(f"✅ Conversations table accessible, current count: {count}")
        
        # Redis 테스트
        redis_client = await db_manager.get_redis()
        await redis_client.ping()
        logger.info("✅ Redis connectivity confirmed")
        
        logger.info("🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.exception("Full error details:")
        return False
    
    finally:
        # 연결 정리
        try:
            await db_manager.close()
            logger.info("🔄 Database connections closed")
        except Exception as e:
            logger.error(f"⚠️ Error during cleanup: {e}")


async def check_database_status():
    """
    데이터베이스 상태 확인만 수행
    """
    try:
        logger.info("🔍 Checking database status...")
        
        # 데이터베이스 매니저 초기화
        await db_manager.initialize()
        
        # PostgreSQL 상태 확인
        async with db_manager.get_pg_connection() as conn:
            version_result = await conn.fetchval("SELECT version()")
            logger.info(f"📊 PostgreSQL version: {version_result}")
            
            # 테이블 존재 확인
            tables_result = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            if tables_result:
                logger.info("📋 Existing tables:")
                for row in tables_result:
                    logger.info(f"   - {row['table_name']}")
            else:
                logger.info("📋 No tables found - database needs initialization")
        
        # Redis 상태 확인
        redis_client = await db_manager.get_redis()
        redis_info = await redis_client.info()
        logger.info(f"🔴 Redis version: {redis_info.get('redis_version', 'unknown')}")
        
        logger.info("✅ Database status check completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database status check failed: {e}")
        return False
    
    finally:
        try:
            await db_manager.close()
        except:
            pass


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--action",
        choices=["init", "status"],
        default="init",
        help="Action to perform (default: init)"
    )
    parser.add_argument(
        "--env-file",
        help="Path to .env file (optional)"
    )
    
    args = parser.parse_args()
    
    # .env 파일 로드 (지정된 경우)
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
        logger.info(f"📁 Loaded environment from: {args.env_file}")
    
    # 현재 환경변수 출력
    logger.info("🌐 Database configuration:")
    logger.info(f"   POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'localhost')}")
    logger.info(f"   POSTGRES_PORT: {os.getenv('POSTGRES_PORT', '5432')}")
    logger.info(f"   POSTGRES_DB: {os.getenv('POSTGRES_DB', 'conversations')}")
    logger.info(f"   POSTGRES_USER: {os.getenv('POSTGRES_USER', 'NOT_SET')}")
    logger.info(f"   POSTGRES_PASSWORD: {'***' if os.getenv('POSTGRES_PASSWORD') else 'NOT_SET'}")
    logger.info(f"   REDIS_HOST: {os.getenv('REDIS_HOST', 'localhost')}")
    logger.info(f"   REDIS_PORT: {os.getenv('REDIS_PORT', '6379')}")
    
    # 액션 실행
    if args.action == "init":
        success = asyncio.run(initialize_database())
    else:  # status
        success = asyncio.run(check_database_status())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()