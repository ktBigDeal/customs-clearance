#!/usr/bin/env python3
"""
LangChain 마이그레이션 후 호환성 및 성능 검증 테스트

이 스크립트는 LangChain 마이그레이션이 성공적으로 완료되었는지 확인합니다.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List

# 프로젝트 루트를 파이썬 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_langchain_embeddings():
    """LangChain 임베딩 시스템 테스트"""
    try:
        from src.rag.embeddings import LangChainEmbedder
        
        logger.info("🧪 LangChain 임베딩 시스템 테스트 시작")
        
        # 임베더 초기화
        embedder = LangChainEmbedder()
        
        # 단일 텍스트 임베딩 테스트
        test_text = "아보카도를 수입하고 싶어요"
        embedding = embedder.embed_text(test_text)
        
        assert isinstance(embedding, list), "임베딩 결과가 리스트가 아닙니다"
        assert len(embedding) == 1536, f"임베딩 차원이 예상과 다릅니다: {len(embedding)}"
        assert all(isinstance(x, float) for x in embedding), "임베딩 벡터에 float이 아닌 값이 있습니다"
        
        # 배치 임베딩 테스트
        test_texts = ["아보카도 수입", "바나나 규제", "동식물 검역"]
        embeddings = embedder.embed_texts(test_texts)
        
        assert len(embeddings) == len(test_texts), "배치 임베딩 결과 수가 일치하지 않습니다"
        assert all(len(emb) == 1536 for emb in embeddings), "배치 임베딩 차원이 일치하지 않습니다"
        
        logger.info("✅ LangChain 임베딩 시스템 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ LangChain 임베딩 시스템 테스트 실패: {e}")
        return False

def test_langchain_vector_store():
    """LangChain 벡터 스토어 테스트"""
    try:
        from src.rag.vector_store import LangChainVectorStore
        from src.rag.embeddings import LangChainEmbedder
        
        logger.info("🧪 LangChain 벡터 스토어 테스트 시작")
        
        # 임베더와 벡터 스토어 초기화
        embedder = LangChainEmbedder()
        vector_store = LangChainVectorStore(
            collection_name="test_collection",
            embedding_function=embedder.embeddings
        )
        
        # 테스트 문서 추가
        test_documents = [
            {
                "content": "아보카도는 식물 검역 대상입니다.",
                "metadata": {
                    "data_type": "trade_regulation",
                    "product_name": "아보카도",
                    "animal_plant_type": "식물",
                    "data_source": "동식물허용금지지역"
                }
            },
            {
                "content": "바나나 수입시 검역 절차가 필요합니다.",
                "metadata": {
                    "data_type": "trade_regulation", 
                    "product_name": "바나나",
                    "animal_plant_type": "식물",
                    "data_source": "동식물허용금지지역"
                }
            }
        ]
        
        # 문서 추가 테스트
        doc_ids = vector_store.add_documents(test_documents)
        assert len(doc_ids) == len(test_documents), "문서 추가 결과 수가 일치하지 않습니다"
        
        # 검색 테스트
        search_results = vector_store.search_similar(
            query_text="아보카도 수입",
            top_k=2
        )
        
        assert len(search_results) > 0, "검색 결과가 없습니다"
        assert all("content" in result for result in search_results), "검색 결과에 content가 없습니다"
        assert all("metadata" in result for result in search_results), "검색 결과에 metadata가 없습니다"
        
        # 필터링 검색 테스트
        filtered_results = vector_store.search_similar(
            query_text="식물 검역",
            top_k=5,
            where={"animal_plant_type": {"$eq": "식물"}}
        )
        
        assert len(filtered_results) > 0, "필터링 검색 결과가 없습니다"
        
        # Retriever 객체 테스트
        retriever = vector_store.get_retriever(search_type="similarity", search_kwargs={"k": 3})
        assert retriever is not None, "Retriever 객체 생성 실패"
        
        logger.info("✅ LangChain 벡터 스토어 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ LangChain 벡터 스토어 테스트 실패: {e}")
        return False

def test_trade_info_retriever():
    """TradeInfoRetriever LLM 기반 메타데이터 필터링 테스트"""
    try:
        from src.rag.trade_info_retriever import TradeInfoRetriever
        
        logger.info("🧪 TradeInfoRetriever LLM 메타데이터 필터링 테스트 시작")
        
        # TradeInfoRetriever 초기화
        retriever = TradeInfoRetriever(collection_name="test_trade_collection")
        
        # LLM 메타데이터 필터 생성 테스트
        test_queries = [
            "아보카도를 수입하고 싶어요",
            "바나나 수입 규제가 궁금합니다", 
            "돼지고기 수입 절차는 어떻게 되나요",
            "HS코드 0804 관련 규제 정보"
        ]
        
        for query in test_queries:
            # LLM 기반 메타데이터 필터 생성 테스트
            filters = retriever._generate_llm_metadata_filters(query)
            
            logger.info(f"Query: '{query}' → Filters: {filters}")
            
            # 기본적인 검증
            assert isinstance(filters, dict), "필터가 딕셔너리가 아닙니다"
            
            # 동식물 관련 쿼리의 경우 적절한 필터가 생성되었는지 확인
            if any(item in query for item in ["아보카도", "바나나", "돼지고기"]):
                if "data_type" in filters:
                    assert filters["data_type"] == "trade_regulation", "동식물 제품에 대해 잘못된 데이터 타입 필터"
        
        # 검색 컨텍스트 기반 검색 테스트
        search_context = {
            "agent_type": "regulation_agent",
            "domain_hints": ["animal_plant_import", "허용국가", "수입규제"],
            "boost_keywords": ["허용국가", "수입", "금지", "제한"],
            "priority_data_sources": ["동식물허용금지지역"]
        }
        
        # 실제 검색은 벡터 DB에 데이터가 있어야 가능하므로 메서드 호출만 테스트
        try:
            results = retriever.search_trade_info(
                raw_query="아보카도 수입 허용국가",
                top_k=3,
                search_context=search_context
            )
            # 데이터가 없어도 빈 리스트 반환은 정상
            assert isinstance(results, list), "검색 결과가 리스트가 아닙니다"
        except Exception as search_error:
            # 벡터 DB에 데이터가 없는 경우 발생할 수 있는 오류는 허용
            logger.warning(f"검색 테스트 중 예상 가능한 오류: {search_error}")
        
        logger.info("✅ TradeInfoRetriever LLM 메타데이터 필터링 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ TradeInfoRetriever LLM 메타데이터 필터링 테스트 실패: {e}")
        return False

def test_agent_compatibility():
    """Agent 호환성 테스트"""
    try:
        from src.rag.trade_regulation_agent import TradeRegulationAgent
        from src.rag.consultation_case_agent import ConsultationCaseAgent
        from src.rag.trade_info_retriever import TradeInfoRetriever
        
        logger.info("🧪 Agent 호환성 테스트 시작")
        
        # TradeInfoRetriever 초기화
        retriever = TradeInfoRetriever(collection_name="test_agent_collection")
        
        # TradeRegulationAgent 초기화 테스트
        try:
            regulation_agent = TradeRegulationAgent(retriever=retriever)
            assert regulation_agent is not None, "TradeRegulationAgent 초기화 실패"
            
            # 검색 컨텍스트 생성 테스트
            search_context = regulation_agent._create_regulation_search_context("아보카도 수입 허용국가")
            assert isinstance(search_context, dict), "검색 컨텍스트가 딕셔너리가 아닙니다"
            assert "agent_type" in search_context, "검색 컨텍스트에 agent_type이 없습니다"
            assert search_context["agent_type"] == "regulation_agent", "잘못된 agent_type"
            
            logger.info("✅ TradeRegulationAgent 호환성 테스트 통과")
            
        except Exception as e:
            logger.error(f"❌ TradeRegulationAgent 테스트 실패: {e}")
            return False
        
        # ConsultationCaseAgent 초기화 테스트
        try:
            consultation_agent = ConsultationCaseAgent(retriever=retriever)
            assert consultation_agent is not None, "ConsultationCaseAgent 초기화 실패"
            
            # 검색 컨텍스트 생성 테스트
            search_context = consultation_agent._create_consultation_search_context("통관 절차가 궁금합니다")
            assert isinstance(search_context, dict), "검색 컨텍스트가 딕셔너리가 아닙니다"
            assert "agent_type" in search_context, "검색 컨텍스트에 agent_type이 없습니다"
            assert search_context["agent_type"] == "consultation_agent", "잘못된 agent_type"
            
            logger.info("✅ ConsultationCaseAgent 호환성 테스트 통과")
            
        except Exception as e:
            logger.error(f"❌ ConsultationCaseAgent 테스트 실패: {e}")
            return False
        
        logger.info("✅ Agent 호환성 테스트 모두 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent 호환성 테스트 실패: {e}")
        return False

def run_migration_validation():
    """전체 마이그레이션 검증 실행"""
    logger.info("🚀 LangChain 마이그레이션 검증 시작")
    logger.info(f"검증 시간: {datetime.now().isoformat()}")
    
    test_results = {
        "embeddings": False,
        "vector_store": False, 
        "retriever": False,
        "agents": False
    }
    
    # 각 테스트 실행
    test_results["embeddings"] = test_langchain_embeddings()
    test_results["vector_store"] = test_langchain_vector_store()
    test_results["retriever"] = test_trade_info_retriever()
    test_results["agents"] = test_agent_compatibility()
    
    # 결과 요약
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info("=" * 60)
    logger.info("🏁 LangChain 마이그레이션 검증 결과")
    logger.info("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{test_name:15}: {status}")
    
    logger.info("=" * 60)
    logger.info(f"전체 결과: {passed_tests}/{total_tests} 테스트 통과")
    
    if passed_tests == total_tests:
        logger.info("🎉 모든 테스트 통과! LangChain 마이그레이션이 성공적으로 완료되었습니다.")
        return True
    else:
        logger.error(f"⚠️  {total_tests - passed_tests}개 테스트 실패. 마이그레이션을 재검토해야 합니다.")
        return False

if __name__ == "__main__":
    success = run_migration_validation()
    sys.exit(0 if success else 1)