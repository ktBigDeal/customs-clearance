"""
LangGraph Integration Module for FastAPI
기존 model-chatbot의 LangGraph 시스템을 FastAPI용 비동기 버전으로 포팅
"""

import asyncio
import logging
import os
import sys
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
from contextlib import asynccontextmanager

# 로컬 모듈들 import
try:
    from ..rag.langgraph_orchestrator import LangGraphOrchestrator
    from ..rag.langgraph_factory import LangGraphAgentFactory
    from ..rag.law_agent import AsyncConversationAgent
    from ..rag.trade_regulation_agent import AsyncTradeRegulationAgent
    from ..rag.consultation_case_agent import AsyncConsultationCaseAgent
    from ..utils.config import get_trade_agent_config, get_chromadb_config
except ImportError as e:
    logging.error(f"Failed to import local modules: {e}")
    # 개발 중에는 임포트 에러를 무시하고 기본 클래스들 정의
    pass

logger = logging.getLogger(__name__)


class LangGraphManager:
    """
    FastAPI용 비동기 LangGraph 매니저
    
    기존 model-chatbot의 LangGraph 시스템을 FastAPI 환경에서
    비동기적으로 사용할 수 있도록 래핑하는 매니저 클래스
    
    주요 기능:
    - 비동기 메시지 처리
    - 에이전트별 라우팅 관리
    - 대화 컨텍스트 유지
    - 에러 처리 및 복구
    """
    
    def __init__(self):
        self.orchestrator: Optional[LangGraphOrchestrator] = None
        self.factory: Optional[LangGraphAgentFactory] = None
        self.is_initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # 성능 설정
        self.default_model = "gpt-4.1-mini"
        self.default_temperature = 0.1
        self.max_retries = 3
        self.timeout_seconds = 60
        
        logger.info("LangGraphManager created")
    
    async def initialize(self, 
                        model_name: Optional[str] = None,
                        temperature: Optional[float] = None,
                        force_rebuild: bool = False) -> None:
        """
        LangGraph 시스템 비동기 초기화
        
        Args:
            model_name: 사용할 언어 모델 (기본값: gpt-4.1-mini)
            temperature: 모델 온도 설정 (기본값: 0.1)
            force_rebuild: 강제 재초기화 여부
        """
        async with self._initialization_lock:
            if self.is_initialized and not force_rebuild:
                logger.info("LangGraph system already initialized")
                return
            
            try:
                logger.info("🚀 Initializing LangGraph system...")
                
                # 환경 변수 검증
                await self._validate_environment()
                
                # 팩토리 생성 (동기적으로)
                self.factory = LangGraphAgentFactory()
                
                # 오케스트레이터 생성 (동기적으로)
                model = model_name or self.default_model
                temp = temperature if temperature is not None else self.default_temperature
                
                self.orchestrator = self.factory.create_orchestrated_system(
                    model_name=model,
                    temperature=temp,
                    force_rebuild=force_rebuild
                )
                
                self.is_initialized = True
                logger.info("✅ LangGraph system initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize LangGraph system: {e}")
                self.is_initialized = False
                raise RuntimeError(f"LangGraph initialization failed: {str(e)}")
    
    async def process_message(self, 
                            user_message: str,
                            conversation_history: Optional[List[Dict[str, Any]]] = None,
                            include_routing_info: bool = True) -> Dict[str, Any]:
        """
        사용자 메시지를 비동기적으로 처리
        
        Args:
            user_message: 사용자 메시지
            conversation_history: 이전 대화 기록 (선택적)
            include_routing_info: 라우팅 정보 포함 여부
            
        Returns:
            처리 결과 딕셔너리
            {
                "response": "AI 응답",
                "agent_used": "사용된 에이전트명",
                "routing_info": {...},
                "references": [...],
                "metadata": {...}
            }
        """
        if not self.is_initialized:
            await self.initialize()
        
        if not self.orchestrator:
            raise RuntimeError("LangGraph orchestrator not available")
        
        try:
            logger.info(f"🧠 Processing message with LangGraph: {user_message[:100]}...")
            
            # 컨텍스트가 있으면 포함해서 처리
            enhanced_input = self._prepare_input_with_context(
                user_message, 
                conversation_history
            )
            
            # 타임아웃과 함께 비동기 실행
            result = await asyncio.wait_for(
                self._run_orchestrator_async(enhanced_input),
                timeout=self.timeout_seconds
            )
            
            # 결과 파싱
            parsed_result = self._parse_langgraph_result(result, include_routing_info)
            
            logger.info(f"✅ Message processed successfully with agent: {parsed_result.get('agent_used', 'unknown')}")
            
            return parsed_result
            
        except asyncio.TimeoutError:
            logger.error("❌ LangGraph processing timeout")
            return self._create_error_response("요청 처리 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            
        except Exception as e:
            logger.error(f"❌ LangGraph processing failed: {e}")
            return self._create_error_response(f"처리 중 오류가 발생했습니다: {str(e)}")
    
    async def get_agent_stats(self) -> Dict[str, Any]:
        """에이전트 시스템 상태 정보 조회"""
        if not self.is_initialized:
            return {
                "orchestrator_available": False,
                "agents": {},
                "error": "System not initialized"
            }
        
        try:
            stats = {
                "orchestrator_available": self.orchestrator is not None,
                "agents": {
                    "conversation_agent": self.factory.conversation_agent is not None,
                    "regulation_agent": self.factory.regulation_agent is not None,
                    "consultation_agent": self.factory.consultation_agent is not None,
                },
                "model_name": self.default_model,
                "temperature": self.default_temperature,
                "is_initialized": self.is_initialized
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get agent stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """시스템 헬스 체크"""
        try:
            if not self.is_initialized:
                return {
                    "status": "unhealthy",
                    "error": "System not initialized"
                }
            
            # 간단한 테스트 메시지 처리
            test_result = await self.process_message(
                "관세법 테스트", 
                include_routing_info=False
            )
            
            if "error" in test_result:
                return {
                    "status": "unhealthy",
                    "error": test_result["error"]
                }
            
            return {
                "status": "healthy",
                "orchestrator": "available",
                "test_response_length": len(test_result.get("response", ""))
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _validate_environment(self) -> None:
        """환경 변수 및 설정 검증"""
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        logger.info("✅ Environment variables validated")
    
    async def _run_orchestrator_async(self, enhanced_input: str) -> Dict[str, Any]:
        """
        LangGraph 오케스트레이터를 비동기로 실행
        (실제로는 동기 함수를 thread pool에서 실행)
        """
        loop = asyncio.get_event_loop()
        
        # CPU-bound 작업을 별도 스레드에서 실행
        result = await loop.run_in_executor(
            None,  # 기본 executor 사용
            self.orchestrator.invoke,
            enhanced_input
        )
        
        return result
    
    def _prepare_input_with_context(self, 
                                   current_message: str, 
                                   context_messages: Optional[List[Dict[str, Any]]]) -> str:
        """대화 컨텍스트를 포함한 입력 준비"""
        if not context_messages:
            return current_message
        
        # 최근 5개 메시지만 컨텍스트로 사용
        recent_messages = context_messages[-5:] if len(context_messages) > 5 else context_messages
        
        context_str = ""
        for msg in recent_messages:
            role = "사용자" if msg.get("role") == "user" else "AI"
            content = msg.get("content", "")[:100]  # 100자로 제한
            context_str += f"{role}: {content}...\n"
        
        if context_str:
            return f"[이전 대화]\n{context_str}\n[현재 질문]\n{current_message}"
        
        return current_message
    
    def _parse_langgraph_result(self, 
                               result: Dict[str, Any], 
                               include_routing_info: bool = True) -> Dict[str, Any]:
        """LangGraph 결과를 FastAPI 응답 형식으로 파싱"""
        try:
            # 메시지 추출
            messages = result.get("messages", [])
            ai_response = ""
            if messages:
                last_message = messages[-1]
                ai_response = getattr(last_message, 'content', str(last_message))
            
            parsed = {
                "response": ai_response or "죄송합니다. 응답을 생성할 수 없습니다.",
                "agent_used": "unknown",
                "references": [],
                "metadata": {
                    "processing_time": result.get("processing_time", 0),
                    "total_messages": len(messages)
                }
            }
            
            # 라우팅 정보 추출
            if include_routing_info:
                routing_history = result.get("routing_history", [])
                if routing_history:
                    latest_routing = routing_history[-1]
                    parsed["agent_used"] = latest_routing.get("selected_agent", "unknown")
                    parsed["routing_info"] = {
                        "selected_agent": latest_routing.get("selected_agent"),
                        "complexity": latest_routing.get("complexity", 0.0),
                        "reasoning": latest_routing.get("reasoning", ""),
                        "requires_multiple_agents": latest_routing.get("requires_multiple", False)
                    }
            
            # 참조 문서 추출
            agent_responses = result.get("agent_responses", {})
            references = []
            for agent_name, agent_data in agent_responses.items():
                docs = agent_data.get("docs", [])
                for doc in docs[:3]:  # 최대 3개
                    references.append({
                        "source": agent_name,
                        "title": doc.get("title", ""),
                        "similarity": doc.get("similarity", 0.0),
                        "metadata": doc.get("metadata", {})
                    })
            
            parsed["references"] = references
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse LangGraph result: {e}")
            return self._create_error_response("결과 파싱 중 오류가 발생했습니다.")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "response": error_message,
            "agent_used": "error_handler",
            "references": [],
            "metadata": {"error": True},
            "error": error_message
        }


# 싱글톤 인스턴스 관리
_langgraph_manager: Optional[LangGraphManager] = None


async def get_langgraph_manager() -> LangGraphManager:
    """
    LangGraphManager 싱글톤 인스턴스 반환
    FastAPI의 Dependency Injection에서 사용
    """
    global _langgraph_manager
    
    if _langgraph_manager is None:
        _langgraph_manager = LangGraphManager()
        await _langgraph_manager.initialize()
    
    return _langgraph_manager


async def initialize_langgraph_system() -> None:
    """시스템 시작 시 LangGraph 초기화"""
    try:
        logger.info("Initializing LangGraph system at startup...")
        manager = await get_langgraph_manager()
        await manager.initialize()
        logger.info("✅ LangGraph system initialization completed")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LangGraph system: {e}")
        raise


async def cleanup_langgraph_system() -> None:
    """시스템 종료 시 정리"""
    global _langgraph_manager
    
    if _langgraph_manager:
        logger.info("Cleaning up LangGraph system...")
        # 필요시 정리 작업 수행
        _langgraph_manager = None
        logger.info("✅ LangGraph system cleanup completed")


# FastAPI 생명주기 관리용 컨텍스트 매니저
@asynccontextmanager
async def langgraph_lifespan():
    """FastAPI 애플리케이션 생명주기에서 LangGraph 관리"""
    # 시작
    try:
        await initialize_langgraph_system()
        yield
    finally:
        # 종료
        await cleanup_langgraph_system()