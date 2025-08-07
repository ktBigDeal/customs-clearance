#!/usr/bin/env python3
"""
ChromaDB 연결 테스트 스크립트

Docker 컨테이너 내부와 외부에서 ChromaDB 서버 연결을 테스트합니다.
"""

import os
import sys
import time
import requests
import traceback
from typing import Optional

def test_chromadb_connection(host: str = "localhost", port: int = 8000, timeout: int = 30) -> bool:
    """ChromaDB 서버 연결 테스트"""
    base_url = f"http://{host}:{port}"
    
    print(f"🔍 ChromaDB 연결 테스트 시작...")
    print(f"   대상 서버: {base_url}")
    print(f"   타임아웃: {timeout}초")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # 헬스체크 엔드포인트 테스트
            response = requests.get(f"{base_url}/api/v1/heartbeat", timeout=5)
            
            if response.status_code == 200:
                print("✅ ChromaDB 서버 연결 성공!")
                
                # 버전 정보 확인
                try:
                    version_response = requests.get(f"{base_url}/api/v1/version", timeout=5)
                    if version_response.status_code == 200:
                        version_data = version_response.json()
                        print(f"   버전: {version_data}")
                except Exception as e:
                    print(f"   버전 정보 확인 실패: {e}")
                
                return True
            else:
                print(f"❌ ChromaDB 서버 응답 오류: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("⏳ ChromaDB 서버 대기 중...")
            time.sleep(2)
            continue
            
        except Exception as e:
            print(f"❌ 연결 테스트 중 오류: {e}")
            traceback.print_exc()
            return False
    
    print(f"❌ ChromaDB 서버 연결 실패 (타임아웃: {timeout}초)")
    return False

def test_chromadb_api(host: str = "localhost", port: int = 8000) -> bool:
    """ChromaDB API 기능 테스트"""
    base_url = f"http://{host}:{port}"
    
    print(f"\n🧪 ChromaDB API 기능 테스트...")
    
    try:
        # 컬렉션 목록 조회
        response = requests.get(f"{base_url}/api/v1/collections", timeout=10)
        
        if response.status_code == 200:
            collections = response.json()
            print(f"✅ 컬렉션 목록 조회 성공 - 총 {len(collections)}개 컬렉션")
            
            for collection in collections:
                print(f"   - {collection.get('name', 'Unknown')}")
            
            return True
        else:
            print(f"❌ 컬렉션 목록 조회 실패: HTTP {response.status_code}")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API 테스트 중 오류: {e}")
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    print("🚀 ChromaDB Docker 연결 테스트 시작")
    print("=" * 50)
    
    # 환경 변수에서 설정 읽기
    host = os.environ.get('CHROMA_TEST_HOST', 'localhost')
    port = int(os.environ.get('CHROMA_TEST_PORT', '8011'))
    timeout = int(os.environ.get('CHROMA_TEST_TIMEOUT', '30'))
    
    # 연결 테스트
    connection_success = test_chromadb_connection(host, port, timeout)
    
    if connection_success:
        # API 기능 테스트
        api_success = test_chromadb_api(host, port)
        
        if api_success:
            print("\n🎉 모든 테스트 통과!")
            sys.exit(0)
        else:
            print("\n❌ API 테스트 실패")
            sys.exit(1)
    else:
        print("\n❌ 연결 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()