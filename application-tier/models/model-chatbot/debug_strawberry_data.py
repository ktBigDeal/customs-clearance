#!/usr/bin/env python3
"""
딸기(Strawberry) 데이터 가용성 디버깅 스크립트
벡터 DB에서 딸기 관련 데이터의 존재 여부와 data_type 분포 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.vector_store import ChromaVectorStore
from src.rag.embeddings import OpenAIEmbedder
from src.utils.config import get_trade_agent_config, load_config

def debug_strawberry_data():
    """딸기 데이터 가용성 디버깅"""
    print("🍓 딸기 데이터 가용성 디버깅 시작...")
    
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
        
        print("✅ 벡터 DB 연결 완료")
        
        # === 1. 전체 데이터 타입 분포 분석 ===
        print(f"\n📊 전체 데이터 타입 분포 분석...")
        stats = vector_store.get_collection_stats()
        
        if 'data_type_distribution' in stats:
            print(f"  📈 데이터 타입별 문서 수:")
            for data_type, count in stats['data_type_distribution'].items():
                print(f"    {data_type}: {count}개")
        
        # === 2. 딸기 키워드로 전체 검색 ===
        print(f"\n🔍 '딸기' 키워드로 전체 데이터 검색...")
        query_embedding = embedder.embed_text("딸기 수입 허용 국가")
        
        all_strawberry_results = vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=20
        )
        
        print(f"  📊 전체 검색 결과: {len(all_strawberry_results)}개")
        
        # 데이터 타입별 분류
        regulation_count = 0
        consultation_count = 0
        animal_plant_count = 0
        other_count = 0
        
        print(f"\n📋 딸기 관련 검색 결과 상세:")
        for i, result in enumerate(all_strawberry_results[:10], 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')[:150]
            similarity = result.get('similarity', 0)
            data_source = metadata.get('data_source', 'N/A')
            data_type = metadata.get('data_type', 'N/A')
            product_name = metadata.get('product_name', 'N/A')
            
            print(f"  {i}. 유사도: {similarity:.3f}")
            print(f"     데이터소스: {data_source}")
            print(f"     데이터타입: {data_type}")
            print(f"     제품명: {product_name}")
            print(f"     내용: {content}...")
            print()
            
            # 카운팅
            if data_type == "trade_regulation":
                regulation_count += 1
            elif data_type == "consultation_case":
                consultation_count += 1
            elif data_source == "동식물허용금지지역":
                animal_plant_count += 1
            else:
                other_count += 1
        
        # === 3. 동식물허용금지지역 데이터에서 딸기 검색 ===
        print(f"\n🐕🌱 동식물허용금지지역 데이터에서 딸기 검색...")
        animal_plant_results = vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=20,
            where={"data_source": "동식물허용금지지역"}
        )
        
        print(f"  📊 동식물허용금지지역 검색 결과: {len(animal_plant_results)}개")
        
        strawberry_exact_matches = 0
        for i, result in enumerate(animal_plant_results[:5], 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')[:100]
            similarity = result.get('similarity', 0)
            product_name = metadata.get('product_name', 'N/A')
            
            print(f"  {i}. 유사도: {similarity:.3f}")
            print(f"     제품명: {product_name}")
            print(f"     내용: {content}...")
            
            # 정확한 딸기 매칭 확인
            if '딸기' in product_name or '딸기' in content:
                strawberry_exact_matches += 1
                print(f"     ✅ 딸기 정확 매칭!")
            print()
        
        # === 4. trade_regulation 데이터에서 딸기 검색 ===
        print(f"\n📋 trade_regulation 데이터에서 딸기 검색...")
        regulation_results = vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=20,
            where={"data_type": "trade_regulation"}
        )
        
        print(f"  📊 trade_regulation 검색 결과: {len(regulation_results)}개")
        
        regulation_strawberry_matches = 0
        for i, result in enumerate(regulation_results[:5], 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')[:100]
            similarity = result.get('similarity', 0)
            data_source = metadata.get('data_source', 'N/A')
            
            print(f"  {i}. 유사도: {similarity:.3f}")
            print(f"     데이터소스: {data_source}")
            print(f"     내용: {content}...")
            
            if '딸기' in content:
                regulation_strawberry_matches += 1
                print(f"     ✅ 딸기 언급!")
            print()
        
        # === 5. consultation_case 데이터에서 딸기 검색 ===
        print(f"\n📞 consultation_case 데이터에서 딸기 검색...")
        consultation_results = vector_store.search_similar(
            query_embedding=query_embedding,
            top_k=20,
            where={"data_type": "consultation_case"}
        )
        
        print(f"  📊 consultation_case 검색 결과: {len(consultation_results)}개")
        
        consultation_strawberry_matches = 0
        for i, result in enumerate(consultation_results[:3], 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')[:100]
            similarity = result.get('similarity', 0)
            data_source = metadata.get('data_source', 'N/A')
            
            print(f"  {i}. 유사도: {similarity:.3f}")
            print(f"     데이터소스: {data_source}")
            print(f"     내용: {content}...")
            
            if '딸기' in content:
                consultation_strawberry_matches += 1
                print(f"     ✅ 딸기 언급!")
            print()
        
        # === 6. 결과 요약 ===
        print(f"\n{'='*60}")
        print(f"🍓 딸기 데이터 분석 요약")
        print(f"{'='*60}")
        print(f"📊 전체 검색 결과 데이터 타입 분포:")
        print(f"  - trade_regulation: {regulation_count}개")
        print(f"  - consultation_case: {consultation_count}개") 
        print(f"  - 동식물허용금지지역: {animal_plant_count}개")
        print(f"  - 기타: {other_count}개")
        print()
        print(f"🔍 타입별 딸기 매칭 결과:")
        print(f"  - 동식물허용금지지역 정확 매칭: {strawberry_exact_matches}개")
        print(f"  - trade_regulation 언급: {regulation_strawberry_matches}개")
        print(f"  - consultation_case 언급: {consultation_strawberry_matches}개")
        print()
        
        if strawberry_exact_matches == 0:
            print("❌ 동식물허용금지지역에 딸기 데이터 없음 - 이것이 문제의 원인!")
        else:
            print("✅ 동식물허용금지지역에 딸기 데이터 존재")
            
        if consultation_strawberry_matches > 0 and strawberry_exact_matches == 0:
            print("⚠️ 규제 데이터는 없지만 상담 사례는 있음 - 혼동의 원인!")
        
        print("✅ 딸기 데이터 분석 완료")
        
    except Exception as e:
        print(f"❌ 디버깅 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_strawberry_data()