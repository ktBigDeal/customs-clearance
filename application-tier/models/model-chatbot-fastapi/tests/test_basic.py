#!/usr/bin/env python3
"""
Basic Functionality Test
데이터베이스 연결 없이 실행할 수 있는 기본 기능 테스트
"""

import sys
import logging
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
except ImportError:
    print("python-dotenv not available, using system environment variables")
except Exception as e:
    print(f"Failed to load .env file: {e}")

# OpenAI API 키 확인
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print("OpenAI API key loaded successfully")
else:
    print("WARNING: OpenAI API key not found in environment")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """모든 주요 모듈 import 테스트"""
    logger.info("[SEARCH] Testing module imports...")
    
    try:
        # Core modules
        from app.utils.config import get_fastapi_config, get_langgraph_config
        logger.info("[OK] Configuration modules imported")
        
        from app.core.langgraph_integration import LangGraphManager
        logger.info("[OK] LangGraph integration imported")
        
        # RAG agents
        from app.rag.query_router import AsyncQueryRouter, QueryType
        from app.rag.law_agent import AsyncConversationAgent
        from app.rag.trade_regulation_agent import AsyncTradeRegulationAgent
        from app.rag.consultation_case_agent import AsyncConsultationCaseAgent
        logger.info("[OK] All RAG agents imported")
        
        # Database models
        from app.models.conversation import ConversationORM, MessageORM, MessageRole
        logger.info("[OK] Database models imported")
        
        # Services
        from app.services.conversation_service import ConversationService
        logger.info("[OK] Services imported")
        
        logger.info("[SUCCESS] All imports successful!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """설정 모듈 기본 테스트"""
    logger.info("[CONFIG] Testing configuration...")
    
    try:
        from app.utils.config import get_fastapi_config, get_langgraph_config, get_chromadb_config
        
        # FastAPI 설정
        fastapi_config = get_fastapi_config()
        assert fastapi_config["title"] == "관세 통관 챗봇 서비스"
        assert fastapi_config["version"] == "1.0.0"
        assert "cors_origins" in fastapi_config
        
        # LangGraph 설정
        langgraph_config = get_langgraph_config()
        assert "model_name" in langgraph_config
        assert "temperature" in langgraph_config
        assert "timeout_seconds" in langgraph_config
        
        # ChromaDB 설정
        chromadb_config = get_chromadb_config()
        assert "collection_name" in chromadb_config
        assert chromadb_config["mode"] in ["local", "docker"]
        
        logger.info("[OK] Configuration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_query_router_basic():
    """쿼리 라우터 기본 기능 테스트"""
    logger.info("[ROUTE] Testing query router...")
    
    try:
        from app.rag.query_router import AsyncQueryRouter, QueryType
        
        # 라우터 생성
        router = AsyncQueryRouter()
        
        # 키워드 로딩 확인
        assert len(router.regulation_keywords) > 0
        assert len(router.consultation_keywords) > 0
        assert len(router.law_keywords) > 0
        assert len(router.animal_plant_products) > 0
        
        # 기본 분석 함수 테스트
        normalized = router._normalize_query("관세법 제1조는 무엇인가요?")
        assert normalized == "관세법 제1조는 무엇인가요"  # 물음표 제거됨
        
        law_score = router._calculate_law_score("관세법 제1조")
        assert law_score > 0
        
        regulation_score = router._calculate_regulation_score("수입 규제 정보")
        assert regulation_score > 0
        
        consultation_score = router._calculate_consultation_score("신고 방법 알려주세요")
        assert consultation_score > 0
        
        logger.info("[OK] Query router basic tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Query router test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


def test_agents_creation():
    """에이전트 생성 테스트"""
    logger.info("[AGENT] Testing agent creation...")
    
    try:
        from app.rag.law_agent import AsyncConversationAgent
        from app.rag.trade_regulation_agent import AsyncTradeRegulationAgent
        from app.rag.consultation_case_agent import AsyncConsultationCaseAgent
        
        # 법령 에이전트
        law_agent = AsyncConversationAgent()
        assert law_agent.model_name == "gpt-4.1-mini"
        assert law_agent.temperature == 0.2
        assert hasattr(law_agent, 'memory')
        
        # 무역 규제 에이전트
        trade_agent = AsyncTradeRegulationAgent()
        assert trade_agent.temperature == 0.1  # 더 정확하게
        assert hasattr(trade_agent, 'memory')
        
        # 상담 사례 에이전트
        consultation_agent = AsyncConsultationCaseAgent()
        assert consultation_agent.temperature == 0.4  # 더 유연하게
        assert hasattr(consultation_agent, 'memory')
        
        logger.info("[OK] Agent creation tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Agent creation test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


def test_memory_systems():
    """메모리 시스템 테스트"""
    logger.info("[MEMORY] Testing memory systems...")
    
    try:
        import asyncio
        
        from app.rag.law_agent import ConversationMemory
        from app.rag.trade_regulation_agent import AsyncTradeRegulationMemory
        from app.rag.consultation_case_agent import AsyncConsultationCaseMemory
        
        async def test_async_memory():
            # 법령 에이전트 메모리 (동기)
            law_memory = ConversationMemory(max_history=5)
            await law_memory.add_user_message("테스트 질문")
            await law_memory.add_assistant_message("테스트 답변", [])
            
            history = law_memory.get_conversation_history()
            assert len(history) == 2
            
            # 무역 규제 에이전트 메모리 (비동기)
            trade_memory = AsyncTradeRegulationMemory(max_history=5)
            await trade_memory.add_user_message("수입 규제 질문")
            await trade_memory.add_assistant_message("규제 답변", [])
            
            history = trade_memory.get_conversation_history()
            assert len(history) == 2
            
            # 상담 사례 에이전트 메모리 (비동기 + 패턴 분석)
            consultation_memory = AsyncConsultationCaseMemory(max_history=10)
            await consultation_memory.add_user_message("통관신고 방법을 알려주세요")
            await consultation_memory.add_assistant_message("신고 방법 안내", [])
            
            history = consultation_memory.get_conversation_history()
            assert len(history) == 2
            
            patterns = consultation_memory.get_user_patterns()
            assert isinstance(patterns, dict)
            
        asyncio.run(test_async_memory())
        
        logger.info("[OK] Memory system tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory system test failed: {e}")
        return False


def test_data_models():
    """데이터 모델 테스트"""
    logger.info("[DATA] Testing data models...")
    
    try:
        from app.models.conversation import (
            MessageRole, AgentType, RoutingInfo, MessageReference,
            ConversationUtils, ConversationValidator
        )
        
        # Enum 테스트
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert AgentType.CONVERSATION == "conversation_agent"
        
        # 유틸리티 함수 테스트
        conv_id = ConversationUtils.generate_conversation_id()
        assert conv_id.startswith("conv_")
        assert len(conv_id) == 17  # "conv_" + 12자리 hex
        
        msg_id = ConversationUtils.generate_message_id()
        assert msg_id.startswith("msg_")
        assert len(msg_id) == 16  # "msg_" + 12자리 hex
        
        title = ConversationUtils.generate_conversation_title("관세법에 대한 질문입니다")
        assert title == "관세법에 대한 질문입니다"
        
        # 검증 함수 테스트
        assert ConversationValidator.validate_message_content("유효한 메시지")
        assert not ConversationValidator.validate_message_content("")
        assert not ConversationValidator.validate_message_content("a" * 10001)  # 너무 긴 메시지
        
        assert ConversationValidator.validate_conversation_title("유효한 제목")
        assert not ConversationValidator.validate_conversation_title("")
        assert not ConversationValidator.validate_conversation_title("a" * 201)  # 너무 긴 제목
        
        logger.info("[OK] Data model tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data model test failed: {e}")
        return False


def main():
    """메인 테스트 실행"""
    logger.info("[START] Starting basic functionality tests...")
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Query Router Basic", test_query_router_basic),
        ("Agent Creation", test_agents_creation),
        ("Memory Systems", test_memory_systems),
        ("Data Models", test_data_models),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n[RUN] Running: {test_name}")
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"[ERROR] {test_name} failed with exception: {e}")
            failed += 1
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "="*50)
    print("[TEST] BASIC FUNCTIONALITY TEST RESULTS")
    print("="*50)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print("="*50)
    
    if failed == 0:
        print("[SUCCESS] ALL BASIC TESTS PASSED!")
        print("[OK] Core functionality is working correctly")
        print("💡 You can now try running the full integration tests")
    else:
        print(f"⚠️ {failed} TEST(S) FAILED")
        print("❌ Please check the error messages above")
    
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    print("""
[TEST] model-chatbot-fastapi Basic Functionality Test
====================================================

This script tests core functionality without requiring database connections:
- Module imports and structure
- Configuration loading
- Query routing logic
- Agent creation and memory systems
- Data models and validation

Starting tests...
""")
    
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)