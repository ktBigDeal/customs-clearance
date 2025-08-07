#!/usr/bin/env python3
"""
ChromaDB Docker 연결 테스트 스크립트

이 스크립트는 application-tier의 model-chatbot이 data-tier의 ChromaDB Docker 서비스와
정상적으로 연결되는지 확인합니다.

사용법:
    python test_docker_chromadb.py [--mode docker] [--host localhost] [--port 8011]

환경변수:
    CHROMADB_MODE=docker          # Docker 모드 활성화
    CHROMADB_HOST=localhost       # ChromaDB 서버 호스트
    CHROMADB_PORT=8011           # ChromaDB 서버 포트
    OPENAI_API_KEY=sk-proj-...   # OpenAI API 키 (임베딩용)
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))

try:
    from utils.config import load_config, get_chromadb_config
    from rag.vector_store import LangChainVectorStore
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import method...")
    # 절대 경로로 import 시도
    import sys
    import os
    sys.path.insert(0, os.path.join(current_dir, "src"))
    
    from utils.config import load_config, get_chromadb_config
    from rag.vector_store import LangChainVectorStore

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_chromadb_connection(mode: str = "docker", host: str = "localhost", port: int = 8011):
    """ChromaDB 연결 테스트"""
    
    print(f"\n🔍 ChromaDB 연결 테스트 시작")
    print(f"📍 모드: {mode}")
    
    try:
        # 환경변수 설정 (테스트용)
        if mode == "docker":
            os.environ["CHROMADB_MODE"] = "docker"
            os.environ["CHROMADB_HOST"] = host
            os.environ["CHROMADB_PORT"] = str(port)
            print(f"🐳 Docker 모드: {host}:{port}")
        else:
            os.environ["CHROMADB_MODE"] = "local"
            print(f"📁 로컬 모드: data/chroma_db")
        
        # 환경 변수 로드
        print("\n📋 환경 변수 로드 중...")
        config = load_config()
        
        # ChromaDB 설정 로드
        chromadb_config = get_chromadb_config()
        print(f"⚙️ ChromaDB 설정: {chromadb_config}")
        
        # 벡터 스토어 초기화
        print("\n🏗️ 벡터 스토어 초기화 중...")
        vector_store = LangChainVectorStore(
            collection_name="test_collection",
            config=chromadb_config
        )
        
        print(f"✅ 벡터 스토어 초기화 성공!")
        print(f"📊 모드: {vector_store.mode}")
        
        # 컬렉션 통계 확인
        print("\n📊 컬렉션 통계 확인 중...")
        stats = vector_store.get_collection_stats()
        print(f"📈 통계: {stats}")
        
        # Docker 모드인 경우 추가 연결 정보 확인
        if mode == "docker" and hasattr(vector_store, 'chroma_client'):
            print("\n🔗 ChromaDB 서버 상세 정보:")
            try:
                client = vector_store.chroma_client
                version = client.get_version()
                collections = client.list_collections()
                
                print(f"  - 버전: {version}")
                print(f"  - 컬렉션 수: {len(collections)}")
                
                for collection in collections:
                    count = collection.count()
                    print(f"    • {collection.name}: {count}개 문서")
                    
            except Exception as e:
                print(f"  ⚠️ 서버 정보 조회 실패: {e}")
        
        # 간단한 검색 테스트 (데이터가 있는 경우)
        print("\n🔍 검색 기능 테스트 중...")
        try:
            results = vector_store.search_similar(
                query_text="관세법",
                top_k=3
            )
            print(f"🎯 검색 결과: {len(results)}개 문서 발견")
            
            if results:
                print("  상위 결과:")
                for i, result in enumerate(results[:3], 1):
                    content_preview = result.get("content", "")[:100] + "..."
                    metadata = result.get("metadata", {})
                    law_name = metadata.get("law_name", "알 수 없음")
                    print(f"    {i}. [{law_name}] {content_preview}")
            
        except Exception as e:
            print(f"  📝 검색 테스트 실패 (데이터 없음 또는 오류): {e}")
        
        print(f"\n🎉 ChromaDB 연결 테스트 완료! ✅")
        return True
        
    except Exception as e:
        print(f"\n❌ ChromaDB 연결 테스트 실패!")
        print(f"🚨 오류: {e}")
        logger.error(f"ChromaDB connection test failed: {e}", exc_info=True)
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="ChromaDB Docker 연결 테스트")
    parser.add_argument("--mode", default="docker", choices=["local", "docker"],
                       help="연결 모드 (기본값: docker)")
    parser.add_argument("--host", default="localhost",
                       help="ChromaDB 서버 호스트 (기본값: localhost)")
    parser.add_argument("--port", type=int, default=8011,
                       help="ChromaDB 서버 포트 (기본값: 8011)")
    
    args = parser.parse_args()
    
    print("🚀 ChromaDB Docker 연결 테스트 도구")
    print("=" * 50)
    
    # 연결 테스트 실행
    success = test_chromadb_connection(
        mode=args.mode,
        host=args.host,
        port=args.port
    )
    
    if success:
        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n📝 다음 단계:")
        print("  1. model-chatbot의 다른 스크립트들이 Docker ChromaDB를 사용하도록 설정")
        print("  2. 환경변수 CHROMADB_MODE=docker를 .env 파일에 추가")
        print("  3. unified_cli.py 또는 다른 RAG 스크립트 실행하여 확인")
        sys.exit(0)
    else:
        print("\n❌ 테스트 실패!")
        print("\n🔧 문제 해결 방법:")
        print("  1. data-tier에서 ChromaDB 컨테이너가 실행 중인지 확인:")
        print("     cd ../../../data-tier && docker-compose ps")
        print("  2. ChromaDB 서비스 재시작:")
        print("     docker-compose restart chromadb")
        print("  3. 포트 8011이 열려있는지 확인:")
        print("     curl http://localhost:8011/api/v2/heartbeat")
        print("  4. .env 파일에 OPENAI_API_KEY가 설정되어 있는지 확인")
        sys.exit(1)


if __name__ == "__main__":
    main()