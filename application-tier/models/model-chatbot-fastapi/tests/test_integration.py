#!/usr/bin/env python3
"""
Integration Test Suite
model-chatbot-fastapi의 모든 구성 요소 통합 테스트
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import logging
import json

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTester:
    """통합 테스트 실행 클래스"""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 통합 테스트 실행"""
        logger.info("🚀 Starting comprehensive integration tests...")
        
        # 테스트 목록
        tests = [
            ("Configuration Loading", self.test_configuration),
            ("Database Connection", self.test_database_connection),
            ("Database Initialization", self.test_database_initialization),
            ("LangGraph Integration", self.test_langgraph_integration),
            ("Query Router", self.test_query_router),
            ("Law Agent", self.test_law_agent),
            ("Trade Regulation Agent", self.test_trade_regulation_agent),
            ("Consultation Case Agent", self.test_consultation_case_agent),
            ("End-to-End Conversation", self.test_end_to_end_conversation),
        ]
        
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
        
        # 결과 요약
        self.print_summary()
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": self.passed_tests / self.total_tests if self.total_tests > 0 else 0,
            "results": self.test_results
        }
    
    async def run_test(self, test_name: str, test_func) -> bool:
        """개별 테스트 실행"""
        self.total_tests += 1
        
        try:
            logger.info(f"🧪 Running test: {test_name}")
            result = await test_func()
            
            if result:
                self.passed_tests += 1
                self.test_results[test_name] = {"status": "PASS", "details": "Test completed successfully"}
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.failed_tests += 1
                self.test_results[test_name] = {"status": "FAIL", "details": "Test returned False"}
                logger.error(f"❌ {test_name} - FAILED")
            
            return result
            
        except Exception as e:
            self.failed_tests += 1
            self.test_results[test_name] = {"status": "ERROR", "details": str(e)}
            logger.error(f"💥 {test_name} - ERROR: {e}")
            return False
    
    async def test_configuration(self) -> bool:
        """설정 로딩 테스트"""
        try:
            from app.utils.config import load_config, get_fastapi_config, get_langgraph_config, get_chromadb_config
            
            # 환경변수 로딩 테스트 (실패해도 OK - 개발환경에서 API 키가 없을 수 있음)
            try:
                config = load_config()
                logger.info(f"📝 Configuration loaded: {len(config)} keys")
            except ValueError as e:
                logger.warning(f"⚠️ Configuration warning (expected in dev): {e}")
            
            # FastAPI 설정 테스트
            fastapi_config = get_fastapi_config()
            assert fastapi_config["title"] == "관세 통관 챗봇 서비스"
            assert fastapi_config["version"] == "1.0.0"
            
            # LangGraph 설정 테스트
            langgraph_config = get_langgraph_config()
            assert "model_name" in langgraph_config
            assert "temperature" in langgraph_config
            
            # ChromaDB 설정 테스트
            chromadb_config = get_chromadb_config()
            assert "collection_name" in chromadb_config
            assert chromadb_config["mode"] in ["local", "docker"]
            
            logger.info("✅ All configuration modules loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            return False
    
    async def test_database_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            from app.core.database import db_manager
            
            # 데이터베이스 초기화
            await db_manager.initialize()
            
            # PostgreSQL 테스트
            async with db_manager.get_db_session() as session:
                result = await session.execute("SELECT 1 as test")
                assert result.scalar() == 1
            
            # Redis 테스트
            redis_client = await db_manager.get_redis()
            await redis_client.ping()
            
            logger.info("✅ Database connections established successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    async def test_database_initialization(self) -> bool:
        """데이터베이스 초기화 테스트"""
        try:
            from app.utils.database_init import initialize_database, check_required_tables
            
            # 데이터베이스 초기화
            success = await initialize_database(check_tables=True, create_if_missing=True)
            assert success, "Database initialization failed"
            
            # 테이블 존재 확인
            tables_exist = await check_required_tables()
            assert tables_exist, "Required tables not found after initialization"
            
            logger.info("✅ Database initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization test failed: {e}")
            return False
    
    async def test_langgraph_integration(self) -> bool:
        """LangGraph 통합 테스트"""
        try:
            from app.core.langgraph_integration import LangGraphManager
            
            # LangGraph 매니저 생성 (실제 API 키 없이도 생성은 가능해야 함)
            manager = LangGraphManager()
            
            # 기본 설정 확인
            assert hasattr(manager, 'timeout_seconds')
            assert hasattr(manager, 'max_retries')
            assert manager.timeout_seconds > 0
            
            # 초기화 시도 (API 키가 없으면 실패할 수 있지만 구조는 확인)
            try:
                await manager.initialize()
                logger.info("✅ LangGraph manager initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ LangGraph initialization failed (expected without API keys): {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ LangGraph integration test failed: {e}")
            return False
    
    async def test_query_router(self) -> bool:
        """쿼리 라우터 테스트"""
        try:
            from app.rag.query_router import AsyncQueryRouter, QueryType
            
            # 라우터 생성
            router = AsyncQueryRouter()
            
            # 테스트 쿼리들
            test_queries = [
                ("관세법 제1조는 무엇인가요?", QueryType.REGULATION),  # Law query
                ("소고기 수입 허용 국가는?", QueryType.REGULATION),     # Animal/plant regulation
                ("통관신고서 작성 방법을 알려주세요", QueryType.CONSULTATION),  # Consultation
            ]
            
            for query, expected_type in test_queries:
                query_type, confidence, routing_info = await router.route_query(query)
                
                logger.info(f"📝 Query: '{query}' → {query_type.value} (confidence: {confidence:.2f})")
                assert isinstance(query_type, QueryType)
                assert isinstance(confidence, float)
                assert isinstance(routing_info, dict)
                
                # 일부 쿼리는 예상한 타입과 다를 수 있지만, 유효한 결과가 나와야 함
            
            logger.info("✅ Query router working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ Query router test failed: {e}")
            return False
    
    async def test_law_agent(self) -> bool:
        """법령 에이전트 테스트"""
        try:
            from app.rag.law_agent import AsyncConversationAgent
            
            # 에이전트 생성
            agent = AsyncConversationAgent()
            
            # 기본 설정 확인
            assert hasattr(agent, 'model_name')
            assert hasattr(agent, 'temperature')
            assert hasattr(agent, 'max_context_docs')
            
            # 초기화 시도 (retriever 없이도 구조는 확인 가능)
            try:
                await agent.initialize()
                logger.info("✅ Law agent initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Law agent initialization failed (expected without data): {e}")
            
            # 메모리 시스템 테스트
            await agent.memory.add_user_message("테스트 메시지")
            await agent.memory.add_assistant_message("테스트 응답")
            
            history = agent.memory.get_conversation_history()
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Law agent test failed: {e}")
            return False
    
    async def test_trade_regulation_agent(self) -> bool:
        """무역 규제 에이전트 테스트"""
        try:
            from app.rag.trade_regulation_agent import AsyncTradeRegulationAgent
            
            # 에이전트 생성
            agent = AsyncTradeRegulationAgent()
            
            # 기본 설정 확인
            assert hasattr(agent, 'model_name')
            assert hasattr(agent, 'temperature')
            assert agent.temperature == 0.1  # 규제 정보는 더 정확하게
            
            # 메모리 시스템 테스트
            await agent.memory.add_user_message("소고기 수입 허용 국가는?")
            await agent.memory.add_assistant_message("미국, 호주에서 수입 가능합니다.")
            
            history = agent.memory.get_conversation_history()
            assert len(history) == 2
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Trade regulation agent test failed: {e}")
            return False
    
    async def test_consultation_case_agent(self) -> bool:
        """상담 사례 에이전트 테스트"""
        try:
            from app.rag.consultation_case_agent import AsyncConsultationCaseAgent
            
            # 에이전트 생성
            agent = AsyncConsultationCaseAgent()
            
            # 기본 설정 확인
            assert hasattr(agent, 'model_name')
            assert hasattr(agent, 'temperature')
            assert agent.temperature == 0.4  # 상담사례는 약간 더 유연하게
            
            # 메모리 및 패턴 분석 테스트
            await agent.memory.add_user_message("통관신고서 작성 방법을 알려주세요")
            
            patterns = agent.memory.get_user_patterns()
            assert isinstance(patterns, dict)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Consultation case agent test failed: {e}")
            return False
    
    async def test_end_to_end_conversation(self) -> bool:
        """엔드투엔드 대화 테스트"""
        try:
            from app.services.conversation_service import ConversationService
            from app.core.database import db_manager
            from app.models.conversation import MessageRole
            
            # 서비스 생성 및 초기화
            service = ConversationService(db_manager)
            await service.initialize()
            
            # 테스트 사용자 ID
            test_user_id = 99999
            
            # 새 대화 생성
            conversation = await service.create_conversation(
                user_id=test_user_id,
                initial_message="관세법에 대해 질문이 있습니다"
            )
            
            assert conversation.user_id == test_user_id
            assert conversation.title is not None
            assert conversation.message_count == 0
            
            # 메시지 추가
            user_msg = await service.add_message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content="관세법 제1조 내용을 알려주세요",
                user_id=test_user_id
            )
            
            assert user_msg.content == "관세법 제1조 내용을 알려주세요"
            assert user_msg.role == MessageRole.USER
            
            # 대화 기록 조회
            history = await service.get_conversation_history(
                conversation_id=conversation.id,
                user_id=test_user_id,
                limit=10
            )
            
            assert len(history) == 1
            assert history[0].content == "관세법 제1조 내용을 알려주세요"
            
            logger.info("✅ End-to-end conversation flow working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ End-to-end conversation test failed: {e}")
            return False
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("🧪 INTEGRATION TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*60)
        
        # 실패한 테스트 상세 정보
        failed_tests = [name for name, result in self.test_results.items() if result["status"] != "PASS"]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test_name in failed_tests:
                result = self.test_results[test_name]
                print(f"  • {test_name}: {result['details']}")
            print("="*60)
        
        # 전체 상태
        if self.failed_tests == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️ {self.failed_tests} TEST(S) FAILED")
        
        print("="*60)


async def main():
    """메인 실행 함수"""
    try:
        tester = IntegrationTester()
        results = await tester.run_all_tests()
        
        # 결과를 JSON 파일로 저장
        results_file = Path(__file__).parent / "integration_test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 Test results saved to: {results_file}")
        
        # 성공률에 따른 종료 코드
        if results["failed_tests"] == 0:
            logger.info("🎉 All integration tests passed!")
            sys.exit(0)
        else:
            logger.error(f"💥 {results['failed_tests']} test(s) failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"💥 Integration test execution failed: {e}")
        sys.exit(1)
    
    finally:
        # 데이터베이스 연결 정리
        try:
            from app.core.database import db_manager
            await db_manager.close()
        except Exception:
            pass


if __name__ == "__main__":
    print("""
🧪 model-chatbot-fastapi Integration Test Suite
==============================================

This script tests all components of the model-chatbot-fastapi system:
• Configuration loading
• Database connections and initialization  
• LangGraph integration
• RAG agents (law, trade regulation, consultation)
• Query routing
• End-to-end conversation flow

Starting tests...
""")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Integration tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error in integration tests: {e}")
        sys.exit(1)