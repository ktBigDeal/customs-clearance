#!/usr/bin/env python3
"""
벡터 DB 상태 디버깅 스크립트
동식물 규제 데이터 로딩 상태 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.vector_store import ChromaVectorStore
from src.rag.embeddings import OpenAIEmbedder
from src.utils.config import get_trade_agent_config, load_config

def debug_vector_db():
    """벡터 DB 상태 디버깅"""
    print("🔍 벡터 DB 상태 디버깅 시작...")
    
    try:
        # 환경 설정 로드
        config = load_config()
        trade_config = get_trade_agent_config()
        
        # 임베딩 모델 초기화
        embedder = OpenAIEmbedder()
        
        # 벡터 저장소 초기화
        vector_store = ChromaVectorStore(
            collection_name=trade_config["collection_name"],
            db_path="data/chroma_db"
        )
        
        # 컬렉션 통계 확인
        stats = vector_store.get_collection_stats()
        print(f"\n📊 컬렉션 통계:")
        print(f"  총 문서 수: {stats.get('total_documents', 0)}")
        print(f"  컬렉션 이름: {stats.get('collection_name', 'N/A')}")
        print(f"  DB 경로: {stats.get('db_path', 'N/A')}")
        
        if 'data_type_distribution' in stats:
            print(f"\n📈 데이터 타입 분포:")
            for data_type, count in stats['data_type_distribution'].items():
                print(f"  {data_type}: {count}개")
        
        # 동식물 규제 데이터 검색 테스트
        print(f"\n🔍 동식물 규제 데이터 검색 테스트...")
        
        # 멜론 관련 문서 검색
        query_embedding = embedder.embed_text("멜론 수입 허용 국가")
        melon_results = vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=10,
            where={"data_source": "동식물허용금지지역"}
        )
        
        print(f"\n🍈 멜론 관련 검색 결과 ({len(melon_results)}개):")
        for i, result in enumerate(melon_results[:3], 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')[:100]
            similarity = result.get('similarity', 0)
            
            print(f"  {i}. 유사도: {similarity:.3f}")
            print(f"     품목: {metadata.get('product_name', 'N/A')}")
            print(f"     데이터 소스: {metadata.get('data_source', 'N/A')}")
            print(f"     내용: {content}...")
            print()
        
        # 아보카도 관련 문서 검색
        query_embedding2 = embedder.embed_text("아보카도 수입 허용 국가")
        avocado_results = vector_store.search_similar(
            query_embedding=query_embedding2,
            top_k=10,
            where={"data_source": "동식물허용금지지역"}
        )
        
        print(f"\n🥑 아보카도 관련 검색 결과 ({len(avocado_results)}개):")
        for i, result in enumerate(avocado_results[:3], 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')[:100]
            similarity = result.get('similarity', 0)
            
            print(f"  {i}. 유사도: {similarity:.3f}")
            print(f"     품목: {metadata.get('product_name', 'N/A')}")
            print(f"     데이터 소스: {metadata.get('data_source', 'N/A')}")
            print(f"     내용: {content}...")
            print()
        
        # 전체 검색 (필터 없음)
        print(f"\n🔍 전체 데이터에서 멜론 검색 (필터 없음):")
        query_embedding3 = embedder.embed_text("멜론 수입 허용 국가")
        all_melon_results = vector_store.search_similar(
            query_embedding=query_embedding3,
            top_k=10
        )
        
        for i, result in enumerate(all_melon_results[:5], 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')[:100]
            similarity = result.get('similarity', 0)
            data_source = metadata.get('data_source', 'N/A')
            data_type = metadata.get('data_type', 'N/A')
            
            print(f"  {i}. 유사도: {similarity:.3f}")
            print(f"     데이터 소스: {data_source}")
            print(f"     데이터 타입: {data_type}")
            print(f"     내용: {content}...")
            print()
        
        print("✅ 벡터 DB 디버깅 완료")
        
    except Exception as e:
        print(f"❌ 디버깅 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vector_db()