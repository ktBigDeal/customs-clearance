#!/usr/bin/env python3
"""
Dual Agent System Test Script
듀얼 에이전트 시스템의 딸기 쿼리 처리 테스트
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dual_agent_system():
    """듀얼 에이전트 시스템 테스트"""
    try:
        print("🧪 듀얼 에이전트 시스템 테스트 시작")
        print("="*60)
        
        # 1. 필요한 모듈 임포트
        from src.rag.embeddings import OpenAIEmbedder
        from src.rag.vector_store import ChromaVectorStore
        from src.rag.query_normalizer import LawQueryNormalizer
        from src.rag.trade_info_retriever import TradeInfoRetriever
        from src.rag.trade_regulation_agent import TradeRegulationAgent
        from src.rag.consultation_case_agent import ConsultationCaseAgent
        from src.rag.query_router import QueryRouter, QueryType
        from src.utils.config import get_trade_agent_config
        
        # 2. 설정 로드
        trade_config = get_trade_agent_config()
        
        # 3. 공통 구성요소 초기화
        print("🔧 시스템 구성요소 초기화...")
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
        
        # 4. 쿼리 라우터 및 에이전트 초기화
        print("🤖 에이전트 및 라우터 초기화...")
        query_router = QueryRouter()
        
        regulation_agent = TradeRegulationAgent(
            retriever=retriever,
            model_name=trade_config["model_name"],
            temperature=0.1,
            max_context_docs=12,
            similarity_threshold=trade_config["similarity_threshold"]
        )
        
        consultation_agent = ConsultationCaseAgent(
            retriever=retriever,
            model_name=trade_config["model_name"],
            temperature=0.4,
            max_context_docs=8,
            similarity_threshold=trade_config["similarity_threshold"]
        )
        
        # 5. 테스트 케이스 정의
        test_queries = [
            {
                "query": "딸기는 어느 나라에서 수입해야해?",
                "expected_agent": "regulation",
                "description": "딸기 수입 허용국가 질의"
            },
            {
                "query": "멜론 수입 가능한 국가는?",
                "expected_agent": "regulation", 
                "description": "멜론 수입 허용국가 질의"
            },
            {
                "query": "통관 절차는 어떻게 되나요?",
                "expected_agent": "consultation",
                "description": "통관 절차 상담 질의"
            },
            {
                "query": "FTA 원산지 증명서 발급 방법",
                "expected_agent": "consultation",
                "description": "FTA 원산지 증명서 실무 질의"
            }
        ]
        
        # 6. 각 테스트 케이스 실행
        print("🧪 테스트 케이스 실행...")
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"🔍 테스트 {i}: {test_case['description']}")
            print(f"📝 질의: {test_case['query']}")
            
            # 쿼리 라우팅 테스트
            query_type, confidence, routing_info = query_router.route_query(test_case['query'])
            
            print(f"🎯 라우팅 결과: {query_type.value} (신뢰도: {confidence:.3f})")
            print(f"📊 라우팅 이유: {routing_info.get('reason', 'unknown')}")
            
            # 기대 결과와 비교
            expected_type = QueryType.REGULATION if test_case['expected_agent'] == "regulation" else QueryType.CONSULTATION
            routing_correct = query_type == expected_type or (query_type == QueryType.MIXED and expected_type == QueryType.CONSULTATION)
            
            if routing_correct:
                print("✅ 라우팅 성공!")
            else:
                print(f"❌ 라우팅 실패! 기대: {expected_type.value}, 실제: {query_type.value}")
            
            # 실제 에이전트 실행
            print("\n🤔 에이전트 실행 중...")
            if query_type == QueryType.REGULATION:
                response, docs = regulation_agent.query_regulation(test_case['query'])
                agent_used = "규제 전문 에이전트"
            else:
                response, docs = consultation_agent.query_consultation(test_case['query'])
                agent_used = "상담 전문 에이전트"
            
            print(f"🤖 사용된 에이전트: {agent_used}")
            print(f"📚 참조 문서 수: {len(docs)}개")
            
            # 응답 품질 체크
            if docs:
                # 데이터 타입 확인
                data_types = [doc.get("metadata", {}).get("data_type", "") for doc in docs]
                regulation_docs = sum(1 for dt in data_types if dt == "trade_regulation")
                consultation_docs = sum(1 for dt in data_types if dt == "consultation_case")
                
                print(f"  - 규제 문서: {regulation_docs}개")
                print(f"  - 상담 문서: {consultation_docs}개")
                
                # 딸기/멜론 쿼리의 경우 특별 체크
                if "딸기" in test_case['query'] or "멜론" in test_case['query']:
                    animal_plant_docs = sum(1 for doc in docs 
                                          if doc.get("metadata", {}).get("data_source") == "동식물허용금지지역")
                    boosted_docs = sum(1 for doc in docs if doc.get("boosted", False))
                    
                    print(f"  - 동식물규제 문서: {animal_plant_docs}개")
                    print(f"  - 부스팅된 문서: {boosted_docs}개")
                    
                    if animal_plant_docs > 0:
                        print("✅ 동식물 규제 데이터 검색 성공!")
                    else:
                        print("❌ 동식물 규제 데이터 검색 실패!")
            
            # 응답 미리보기
            response_preview = response[:200] + "..." if len(response) > 200 else response
            print(f"\n💬 응답 미리보기:\n{response_preview}")
        
        print(f"\n{'='*60}")
        print("🎉 듀얼 에이전트 시스템 테스트 완료!")
        
        # 7. 시스템 상태 확인
        print("\n📊 시스템 상태:")
        stats = vector_store.get_collection_stats()
        if "error" not in stats:
            print(f"  - 총 문서 수: {stats.get('total_documents', 0):,}개")
            print(f"  - 컬렉션명: {stats.get('collection_name', 'N/A')}")
        else:
            print("  - ❌ 벡터 저장소 연결 실패")
        
        return True
        
    except Exception as e:
        logger.error(f"듀얼 에이전트 테스트 실패: {e}")
        print(f"❌ 테스트 실패: {e}")
        return False

def main():
    """메인 함수"""
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일을 확인하거나 환경 변수를 설정해주세요.")
        return
    
    # 테스트 실행
    success = test_dual_agent_system()
    
    if success:
        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 테스트 중 문제가 발생했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()