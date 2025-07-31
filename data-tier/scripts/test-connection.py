#!/usr/bin/env python3
"""
MySQL 연결 테스트 스크립트
"""
import os
import sys
import mysql.connector
from mysql.connector import Error
import time

def test_connection():
    """MySQL 데이터베이스 연결 테스트"""
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME', 'customs_clearance'),
        'user': os.getenv('DB_USER', 'customs_user'),
        'password': os.getenv('DB_PASSWORD', 'customs_pass'),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        'autocommit': True
    }
    
    print("=== MySQL 연결 테스트 ===")
    print(f"호스트: {config['host']}:{config['port']}")
    print(f"데이터베이스: {config['database']}")
    print(f"사용자: {config['user']}")
    print("-" * 40)
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"연결 시도 {attempt}/{max_retries}...")
            
            # 데이터베이스 연결
            connection = mysql.connector.connect(**config)
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                # 버전 정보 확인
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                print(f"✅ MySQL 연결 성공!")
                print(f"   버전: {version}")
                
                # 문자셋 확인
                cursor.execute("SHOW VARIABLES LIKE 'character_set%'")
                charset_info = cursor.fetchall()
                print(f"   문자셋 설정:")
                for var_name, var_value in charset_info:
                    if 'utf8mb4' in var_value:
                        print(f"   ✅ {var_name}: {var_value}")
                    else:
                        print(f"   ⚠️  {var_name}: {var_value}")
                
                # 테이블 목록 확인
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"   테이블 개수: {len(tables)}")
                for table in tables:
                    print(f"   - {table[0]}")
                
                # 사용자 데이터 확인
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                print(f"   사용자 수: {user_count}")
                
                # 신고서 데이터 확인
                cursor.execute("SELECT COUNT(*) FROM declarations")
                declaration_count = cursor.fetchone()[0]
                print(f"   신고서 수: {declaration_count}")
                
                # 연결 종료
                cursor.close()
                connection.close()
                print("✅ 모든 테스트 완료!")
                return True
                
        except Error as e:
            print(f"❌ 연결 실패 (시도 {attempt}): {e}")
            if attempt < max_retries:
                print(f"   {retry_delay}초 후 재시도...")
                time.sleep(retry_delay)
            else:
                print("❌ 최대 재시도 횟수 초과")
                return False
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False
    
    return False

def test_queries():
    """기본 쿼리 테스트"""
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME', 'customs_clearance'),
        'user': os.getenv('DB_USER', 'customs_user'),
        'password': os.getenv('DB_PASSWORD', 'customs_pass'),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        print("\n=== 쿼리 테스트 ===")
        
        # 신고서 상태별 통계
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM declarations 
            GROUP BY status
        """)
        stats = cursor.fetchall()
        print("신고서 상태별 통계:")
        for stat in stats:
            print(f"  {stat['status']}: {stat['count']}건")
        
        # 최근 신고서 조회
        cursor.execute("""
            SELECT declaration_number, company_name, status, created_at
            FROM declarations 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()
        print("\n최근 신고서:")
        for decl in recent:
            print(f"  {decl['declaration_number']}: {decl['company_name']} ({decl['status']})")
        
        cursor.close()
        connection.close()
        print("✅ 쿼리 테스트 완료!")
        
    except Error as e:
        print(f"❌ 쿼리 테스트 실패: {e}")

if __name__ == "__main__":
    print("관세청 통관시스템 - MySQL 연결 테스트")
    print("=" * 50)
    
    if test_connection():
        test_queries()
        sys.exit(0)
    else:
        sys.exit(1)