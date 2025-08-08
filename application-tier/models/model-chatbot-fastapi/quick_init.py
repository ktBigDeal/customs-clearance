#!/usr/bin/env python3
"""
빠른 데이터베이스 초기화
원라이너 명령어 대신 사용할 수 있는 간단한 스크립트
"""

import asyncio
import os
from app.core.database import db_manager, create_tables

async def quick_init():
    """빠른 데이터베이스 초기화"""
    try:
        print("🚀 데이터베이스 초기화 시작...")
        
        # 환경변수 확인
        if not os.getenv("POSTGRES_USER") or not os.getenv("POSTGRES_PASSWORD"):
            print("❌ POSTGRES_USER 또는 POSTGRES_PASSWORD 환경변수가 설정되지 않았습니다")
            return False
            
        # 데이터베이스 매니저 초기화
        await db_manager.initialize()
        print("✅ 데이터베이스 연결 초기화 완료")
        
        # 테이블 생성
        await create_tables()
        print("✅ 테이블 생성 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return False
    finally:
        # 연결 정리
        await db_manager.close()
        print("🔄 연결 정리 완료")

if __name__ == "__main__":
    success = asyncio.run(quick_init())
    exit(0 if success else 1)