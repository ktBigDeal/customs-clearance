#!/usr/bin/env python3
"""
ChromaDB Query Test
ChromaDB 쿼리 형식 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

def test_chromadb_where_conditions():
    """ChromaDB where 조건 형식 테스트"""
    try:
        print("🧪 ChromaDB Where 조건 테스트 시작")
        
        from src.rag.embeddings import OpenAIEmbedder
        from src.rag.vector_store import ChromaVectorStore
        from src.utils.config import get_trade_agent_config
        
        # 설정 로드
        trade_config = get_trade_agent_config()
        
        # 구성요소 초기화
        embedder = OpenAIEmbedder()
        vector_store = ChromaVectorStore(
            collection_name=trade_config["collection_name"],
            db_path="data/chroma_db"
        )
        
        # 딸기 임베딩 생성
        query_embedding = embedder.embed_text("딸기 수입 허용 국가")
        
        # 테스트 케이스 1: 단일 조건
        print("\n🔍 테스트 1: 단일 조건 (data_type)")
        try:
            where_single = {"data_type": {"$eq": "trade_regulation"}}
            results1 = vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=5,
                where=where_single
            )
            print(f"✅ 단일 조건 성공: {len(results1)}개 결과")
        except Exception as e:
            print(f"❌ 단일 조건 실패: {e}")
        
        # 테스트 케이스 2: 잘못된 다중 조건 (기존 방식)
        print("\n🔍 테스트 2: 잘못된 다중 조건")
        try:
            where_wrong = {
                "data_type": {"$eq": "trade_regulation"},
                "data_source": {"$eq": "동식물허용금지지역"}
            }
            results2 = vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=5,
                where=where_wrong
            )
            print(f"✅ 잘못된 다중 조건 성공: {len(results2)}개 결과")
        except Exception as e:
            print(f"❌ 잘못된 다중 조건 실패: {e}")
        
        # 테스트 케이스 3: 올바른 다중 조건 ($and 사용)
        print("\n🔍 테스트 3: 올바른 다중 조건 ($and)")
        try:
            where_correct = {"$and": [
                {"data_type": {"$eq": "trade_regulation"}},
                {"data_source": {"$eq": "동식물허용금지지역"}}
            ]}
            results3 = vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=5,
                where=where_correct
            )
            print(f"✅ 올바른 다중 조건 성공: {len(results3)}개 결과")
            
            # 결과 분석
            if results3:
                print("📋 검색 결과 분석:")
                for i, doc in enumerate(results3, 1):
                    metadata = doc.get("metadata", {})
                    product_name = metadata.get("product_name", "")
                    data_source = metadata.get("data_source", "")
                    data_type = metadata.get("data_type", "")
                    similarity = doc.get("similarity", 0)
                    
                    print(f"  {i}. 제품: {product_name}")
                    print(f"     소스: {data_source}")
                    print(f"     타입: {data_type}")
                    print(f"     유사도: {similarity:.3f}")
                    
                    if "딸기" in product_name:
                        print("     🍓 딸기 매칭!")
                    print()
            
        except Exception as e:
            print(f"❌ 올바른 다중 조건 실패: {e}")
        
        # 테스트 케이스 4: 딸기만 검색 (data_source만)
        print("\n🔍 테스트 4: 동식물허용금지지역만 검색")
        try:
            where_animal_plant = {"data_source": {"$eq": "동식물허용금지지역"}}
            results4 = vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=10,
                where=where_animal_plant
            )
            print(f"✅ 동식물 데이터 검색 성공: {len(results4)}개 결과")
            
            # 딸기 관련 결과 찾기
            strawberry_count = 0
            for doc in results4:
                metadata = doc.get("metadata", {})
                product_name = metadata.get("product_name", "")
                if "딸기" in product_name:
                    strawberry_count += 1
                    print(f"  🍓 발견: {product_name}")
            
            print(f"🍓 딸기 관련 제품: {strawberry_count}개")
            
        except Exception as e:
            print(f"❌ 동식물 데이터 검색 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return
    
    # 테스트 실행
    success = test_chromadb_where_conditions()
    
    if success:
        print("\n✅ ChromaDB 쿼리 테스트 완료!")
    else:
        print("\n❌ 테스트 중 문제가 발생했습니다.")

if __name__ == "__main__":
    main()