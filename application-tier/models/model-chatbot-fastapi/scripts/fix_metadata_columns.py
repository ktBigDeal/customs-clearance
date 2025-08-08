#!/usr/bin/env python3
"""
컬럼명 불일치 수정 스크립트
metadata -> extra_metadata로 컬럼명 변경
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from app.core.database import db_manager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fix_metadata_columns():
    """
    metadata -> extra_metadata 컬럼명 수정
    1. 기존 테이블 스키마 확인
    2. 컬럼명 변경 수행
    3. 인덱스 재생성
    """
    try:
        logger.info("🚀 Starting metadata column fix...")
        
        # 데이터베이스 연결 초기화
        await db_manager.initialize()
        
        async with db_manager.get_pg_connection() as conn:
            # 1. 현재 테이블 구조 확인
            logger.info("🔍 Checking current table structure...")
            
            conversations_columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conversations' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """)
            
            messages_columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'messages' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """)
            
            logger.info("📊 Current conversations columns:")
            for col in conversations_columns:
                logger.info(f"   - {col['column_name']}: {col['data_type']}")
            
            logger.info("📊 Current messages columns:")
            for col in messages_columns:
                logger.info(f"   - {col['column_name']}: {col['data_type']}")
            
            # 2. conversations 테이블 수정
            conv_has_metadata = any(col['column_name'] == 'metadata' for col in conversations_columns)
            conv_has_extra_metadata = any(col['column_name'] == 'extra_metadata' for col in conversations_columns)
            
            if conv_has_metadata and not conv_has_extra_metadata:
                logger.info("🔧 Renaming conversations.metadata -> extra_metadata...")
                await conn.execute("""
                    ALTER TABLE conversations 
                    RENAME COLUMN metadata TO extra_metadata;
                """)
                logger.info("✅ conversations.metadata renamed to extra_metadata")
            elif not conv_has_metadata and not conv_has_extra_metadata:
                logger.info("🔧 Adding extra_metadata column to conversations...")
                await conn.execute("""
                    ALTER TABLE conversations 
                    ADD COLUMN extra_metadata JSONB DEFAULT '{}'::jsonb;
                """)
                logger.info("✅ conversations.extra_metadata column added")
            else:
                logger.info("✅ conversations.extra_metadata already exists")
            
            # 3. messages 테이블 수정
            msg_has_metadata = any(col['column_name'] == 'metadata' for col in messages_columns)
            msg_has_extra_metadata = any(col['column_name'] == 'extra_metadata' for col in messages_columns)
            
            if msg_has_metadata and not msg_has_extra_metadata:
                logger.info("🔧 Renaming messages.metadata -> extra_metadata...")
                await conn.execute("""
                    ALTER TABLE messages 
                    RENAME COLUMN metadata TO extra_metadata;
                """)
                logger.info("✅ messages.metadata renamed to extra_metadata")
            elif not msg_has_metadata and not msg_has_extra_metadata:
                logger.info("🔧 Adding extra_metadata column to messages...")
                await conn.execute("""
                    ALTER TABLE messages 
                    ADD COLUMN extra_metadata JSONB DEFAULT '{}'::jsonb;
                """)
                logger.info("✅ messages.extra_metadata column added")
            else:
                logger.info("✅ messages.extra_metadata already exists")
            
            # 4. 연결 테스트
            logger.info("🧪 Testing database operations...")
            
            # 테스트 데이터 삽입
            test_conv_id = "test_conv_fix_123"
            test_msg_id = "test_msg_fix_456"
            
            # 기존 테스트 데이터 삭제
            await conn.execute("DELETE FROM conversations WHERE id = $1", test_conv_id)
            
            # 새로운 대화 삽입
            await conn.execute("""
                INSERT INTO conversations 
                (id, user_id, title, extra_metadata) 
                VALUES ($1, $2, $3, $4)
            """, test_conv_id, 1, "테스트 대화", '{"test": "success"}')
            
            # 새로운 메시지 삽입
            await conn.execute("""
                INSERT INTO messages 
                (id, conversation_id, role, content, extra_metadata) 
                VALUES ($1, $2, $3, $4, $5)
            """, test_msg_id, test_conv_id, "user", "테스트 메시지", '{"test": "success"}')
            
            # 데이터 조회 테스트
            conv_result = await conn.fetchrow("""
                SELECT id, title, extra_metadata 
                FROM conversations 
                WHERE id = $1
            """, test_conv_id)
            
            msg_result = await conn.fetchrow("""
                SELECT id, content, extra_metadata 
                FROM messages 
                WHERE id = $1
            """, test_msg_id)
            
            logger.info(f"✅ Conversation test: {conv_result}")
            logger.info(f"✅ Message test: {msg_result}")
            
            # 테스트 데이터 정리
            await conn.execute("DELETE FROM conversations WHERE id = $1", test_conv_id)
            
            logger.info("🎉 Metadata column fix completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Metadata column fix failed: {e}")
        logger.exception("Full error details:")
        return False
    
    finally:
        # 연결 정리
        try:
            await db_manager.close()
            logger.info("🔄 Database connections closed")
        except Exception as e:
            logger.error(f"⚠️ Error during cleanup: {e}")


async def verify_fix():
    """수정 결과 검증"""
    try:
        logger.info("🔍 Verifying metadata column fix...")
        
        await db_manager.initialize()
        
        async with db_manager.get_pg_connection() as conn:
            # 최종 테이블 구조 확인
            conversations_columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conversations' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """)
            
            messages_columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'messages' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """)
            
            logger.info("📊 Final conversations columns:")
            for col in conversations_columns:
                logger.info(f"   - {col['column_name']}: {col['data_type']}")
            
            logger.info("📊 Final messages columns:")
            for col in messages_columns:
                logger.info(f"   - {col['column_name']}: {col['data_type']}")
            
            # extra_metadata 컬럼 존재 확인
            conv_has_extra = any(col['column_name'] == 'extra_metadata' for col in conversations_columns)
            msg_has_extra = any(col['column_name'] == 'extra_metadata' for col in messages_columns)
            
            if conv_has_extra and msg_has_extra:
                logger.info("✅ Verification successful: Both tables have extra_metadata columns")
                return True
            else:
                logger.error(f"❌ Verification failed: conv={conv_has_extra}, msg={msg_has_extra}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False
    
    finally:
        try:
            await db_manager.close()
        except:
            pass


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix metadata column names")
    parser.add_argument(
        "--action",
        choices=["fix", "verify"],
        default="fix",
        help="Action to perform (default: fix)"
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
    
    # 액션 실행
    if args.action == "fix":
        success = asyncio.run(fix_metadata_columns())
    else:  # verify
        success = asyncio.run(verify_fix())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()