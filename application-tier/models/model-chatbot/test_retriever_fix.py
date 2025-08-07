#!/usr/bin/env python3
"""
Test TradeInfoRetriever _build_where_condition fix
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

def test_build_where_condition():
    """_build_where_condition 메서드 테스트"""
    try:
        print("🧪 _build_where_condition 테스트")
        
        from src.rag.embeddings import OpenAIEmbedder
        from src.rag.vector_store import ChromaVectorStore
        from src.rag.query_normalizer import LawQueryNormalizer
        from src.rag.trade_info_retriever import TradeInfoRetriever
        from src.utils.config import get_trade_agent_config
        
        # 설정 로드
        trade_config = get_trade_agent_config()
        
        # 구성요소 초기화
        embedder = OpenAIEmbedder()
        vector_store = ChromaVectorStore(
            collection_name=trade_config["collection_name"],
            db_path="data/chroma_db"
        )
        query_normalizer = LawQueryNormalizer()
        retriever = TradeInfoRetriever(
            embedder=embedder,
            vector_store=vector_store,
            query_normalizer=query_normalizer,
            collection_name=trade_config["collection_name"]
        )
        
        # 테스트 케이스들
        test_cases = [
            {
                "name": "단일 조건",
                "filter": {"data_type": "trade_regulation"},
                "expected": {"data_type": {"$eq": "trade_regulation"}}
            },
            {
                "name": "다중 조건",
                "filter": {
                    "data_type": "trade_regulation",
                    "data_source": "동식물허용금지지역"
                },
                "expected": {"$and": [
                    {"data_type": {"$eq": "trade_regulation"}},
                    {"data_source": {"$eq": "동식물허용금지지역"}}
                ]}
            },
            {
                "name": "빈 조건",
                "filter": {},
                "expected": None
            },
            {
                "name": "지원하지 않는 필드",
                "filter": {"unsupported_field": "value"},
                "expected": None
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🔍 테스트: {test_case['name']}")
            print(f"입력: {test_case['filter']}")
            
            result = retriever._build_where_condition(test_case['filter'])
            print(f"결과: {result}")
            print(f"기대: {test_case['expected']}")
            
            if result == test_case['expected']:
                print("✅ 성공!")
            else:
                print("❌ 실패!")
        
        # 실제 딸기 검색 테스트
        print(f"\n{'='*50}")
        print("🍓 실제 딸기 검색 테스트")
        
        filter_by = {
            "data_type": "trade_regulation",
            "data_source": "동식물허용금지지역"
        }
        
        where_condition = retriever._build_where_condition(filter_by)
        print(f"생성된 where 조건: {where_condition}")
        
        # 실제 검색 실행
        print("\n🔍 딸기 검색 실행...")
        results = retriever.search_trade_info(
            raw_query="딸기 수입 허용 국가",
            top_k=5,
            filter_by=filter_by
        )
        
        print(f"📊 검색 결과: {len(results)}개")
        for i, doc in enumerate(results, 1):
            metadata = doc.get("metadata", {})
            product_name = metadata.get("product_name", "")
            data_source = metadata.get("data_source", "")
            similarity = doc.get("similarity", 0)
            
            print(f"  {i}. {product_name} ({data_source}) - 유사도: {similarity:.3f}")
            if "딸기" in product_name:
                print("     🍓 딸기 매칭 성공!")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return
    
    success = test_build_where_condition()
    
    if success:
        print("\n✅ _build_where_condition 테스트 완료!")
    else:
        print("\n❌ 테스트 중 문제가 발생했습니다.")

if __name__ == "__main__":
    main()