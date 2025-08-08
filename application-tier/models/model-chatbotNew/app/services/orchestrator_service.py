"""
LangGraph 오케스트레이터 서비스 래퍼

기존 LangGraph 기반 멀티 에이전트 RAG 시스템을 FastAPI와 연동하는 서비스입니다.
비동기 처리와 캐싱, 세션 관리를 지원하여 웹 API로 제공합니다.

주요 기능:
- 기존 orchestrator.py를 비동기로 래핑
- 멀티 에이전트 대화 처리 (관세법, 규제, 민원상담)
- Redis 캐싱을 통한 응답 최적화
- 대화 컨텍스트 관리
- 토큰 사용량 추적
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import json
import sys
from pathlib import Path

# 기존 RAG 시스템 임포트를 위한 경로 추가
current_dir = Path(__file__).parent.parent.parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from app.core.config import settings
from app.core.redis_client import redis_manager
from app.core.exceptions import (
    RAGServiceError, 
    OpenAIAPIError, 
    VectorSearchError,
    handle_exceptions
)

# 기존 RAG 시스템 컴포넌트 임포트
try:
    from orchestrator.orchestrator import MultiAgentOrchestrator
    from utils.db_connect import ChromaDBManager
    from config.config import load_config, get_quality_thresholds
except ImportError as e:
    logging.error(f"기존 RAG 시스템 임포트 실패: {e}")
    MultiAgentOrchestrator = None
    ChromaDBManager = None


logger = logging.getLogger(__name__)


class OrchestratorService:
    """LangGraph 오케스트레이터 서비스 래퍼 클래스
    
    기존 MultiAgentOrchestrator를 비동기 환경에서 사용할 수 있도록 래핑합니다.
    캐싱, 세션 관리, 에러 처리 등의 웹 서비스 기능을 추가합니다.
    
    Attributes:
        orchestrator: 기존 MultiAgentOrchestrator 인스턴스
        db_manager: ChromaDB 연결 관리자
        is_initialized: 초기화 완료 여부
    """
    
    def __init__(self):
        self.orchestrator: Optional[MultiAgentOrchestrator] = None
        self.db_manager: Optional[ChromaDBManager] = None
        self.is_initialized: bool = False
        self._initialization_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """오케스트레이터 초기화
        
        기존 RAG 시스템의 컴포넌트들을 초기화합니다.
        여러 번 호출되어도 한 번만 초기화됩니다.
        
        Raises:
            RAGServiceError: 초기화 실패 시
        """
        if self.is_initialized:
            return
        
        async with self._initialization_lock:
            if self.is_initialized:
                return
            
            try:
                logger.info("🤖 LangGraph 오케스트레이터 초기화 시작")
                
                # 기존 설정 로드
                await asyncio.get_event_loop().run_in_executor(
                    None, load_config
                )
                
                # ChromaDB 매니저 초기화
                if ChromaDBManager is None:
                    raise RAGServiceError(
                        detail="ChromaDBManager 클래스를 가져올 수 없습니다",
                        error_code="IMPORT_ERROR"
                    )
                
                self.db_manager = ChromaDBManager(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT
                )
                
                # 오케스트레이터 초기화
                if MultiAgentOrchestrator is None:
                    raise RAGServiceError(
                        detail="MultiAgentOrchestrator 클래스를 가져올 수 없습니다",
                        error_code="IMPORT_ERROR"
                    )
                
                self.orchestrator = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: MultiAgentOrchestrator(
                        db_manager=self.db_manager,
                        model_name=settings.OPENAI_MODEL,
                        temperature=settings.OPENAI_TEMPERATURE
                    )
                )
                
                self.is_initialized = True
                logger.info("✅ LangGraph 오케스트레이터 초기화 완료")
                
            except Exception as e:
                logger.error(f"❌ 오케스트레이터 초기화 실패: {e}")
                raise RAGServiceError(
                    detail=f"RAG 시스템 초기화 실패: {str(e)}",
                    error_code="INITIALIZATION_FAILED",
                    metadata={"error": str(e)}
                )
    
    @handle_exceptions("오케스트레이터 대화 처리")
    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        user_id: int,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """사용자 메시지 처리
        
        사용자의 질문을 받아 적절한 에이전트를 선택하고 응답을 생성합니다.
        캐싱을 통해 동일한 질문의 재처리를 방지합니다.
        
        Args:
            user_message (str): 사용자 질문
            conversation_id (str): 대화 ID
            user_id (int): 사용자 ID
            conversation_history (Optional[List[Dict[str, Any]]]): 대화 이력
            
        Returns:
            Dict[str, Any]: 처리 결과
            
        Raises:
            RAGServiceError: RAG 처리 실패 시
        """
        if not self.is_initialized:
            await self.initialize()
        
        # 캐시 키 생성 (사용자 질문 기반)
        cache_key = redis_manager.generate_query_hash(user_message, user_id)
        
        # 캐시에서 응답 확인
        cached_response = await redis_manager.get_cached_rag_response(cache_key)
        if cached_response:
            logger.info(f"✅ 캐시된 응답 반환: {cache_key}")
            cached_response["from_cache"] = True
            return cached_response
        
        # 시작 시간 기록
        start_time = time.time()
        
        try:
            logger.info(f"🤖 메시지 처리 시작 - 사용자: {user_id}, 대화: {conversation_id}")
            
            # 대화 이력을 오케스트레이터 형식으로 변환
            formatted_history = self._format_conversation_history(conversation_history or [])
            
            # 오케스트레이터를 통한 응답 생성 (별도 스레드에서 실행)
            response_data = await asyncio.get_event_loop().run_in_executor(
                None,
                self._process_with_orchestrator,
                user_message,
                formatted_history
            )
            
            # 처리 시간 계산
            processing_time = time.time() - start_time
            
            # 응답 데이터 구성
            result = {
                "response": response_data.get("response", "답변을 생성할 수 없습니다."),
                "agent_type": response_data.get("agent_type", "unknown"),
                "processing_time": processing_time,
                "token_usage": response_data.get("token_usage", {}),
                "retrieved_documents": response_data.get("retrieved_documents", []),
                "confidence_score": response_data.get("confidence_score", 0.0),
                "from_cache": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # 응답 캐싱 (성공한 경우에만)
            if result["response"] and not result["response"].startswith("오류"):
                await redis_manager.cache_rag_response(cache_key, result, ttl=3600)
                logger.info(f"✅ 응답 캐싱 완료: {cache_key}")
            
            logger.info(f"✅ 메시지 처리 완료 - 시간: {processing_time:.2f}초, 에이전트: {result['agent_type']}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ 메시지 처리 실패 - 시간: {processing_time:.2f}초, 오류: {e}")
            
            # OpenAI API 오류인지 확인
            if "openai" in str(e).lower() or "api" in str(e).lower():
                raise OpenAIAPIError(
                    detail=str(e),
                    metadata={"processing_time": processing_time}
                )
            
            # 벡터 검색 오류인지 확인
            if "chroma" in str(e).lower() or "vector" in str(e).lower():
                raise VectorSearchError(
                    detail=str(e),
                    metadata={"processing_time": processing_time}
                )
            
            # 일반적인 RAG 서비스 오류
            raise RAGServiceError(
                detail=str(e),
                metadata={
                    "processing_time": processing_time,
                    "conversation_id": conversation_id,
                    "user_id": user_id
                }
            )
    
    def _process_with_orchestrator(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """오케스트레이터를 통한 메시지 처리 (동기 함수)
        
        별도 스레드에서 실행되는 동기 함수입니다.
        기존 오케스트레이터의 동기 API를 호출합니다.
        
        Args:
            user_message (str): 사용자 질문
            conversation_history (List[Dict[str, str]]): 대화 이력
            
        Returns:
            Dict[str, Any]: 오케스트레이터 응답
        """
        try:
            # 기존 오케스트레이터 호출
            response = self.orchestrator.process_query(
                query=user_message,
                conversation_history=conversation_history
            )
            
            # 응답 형식 통일
            if isinstance(response, str):
                return {
                    "response": response,
                    "agent_type": "unknown",
                    "token_usage": {},
                    "retrieved_documents": [],
                    "confidence_score": 0.0
                }
            elif isinstance(response, dict):
                return {
                    "response": response.get("response", response.get("answer", str(response))),
                    "agent_type": response.get("agent_type", response.get("agent", "unknown")),
                    "token_usage": response.get("token_usage", {}),
                    "retrieved_documents": response.get("retrieved_documents", response.get("sources", [])),
                    "confidence_score": response.get("confidence_score", response.get("confidence", 0.0))
                }
            else:
                return {
                    "response": str(response),
                    "agent_type": "unknown",
                    "token_usage": {},
                    "retrieved_documents": [],
                    "confidence_score": 0.0
                }
                
        except Exception as e:
            logger.error(f"오케스트레이터 처리 오류: {e}")
            raise
    
    def _format_conversation_history(
        self, 
        conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """대화 이력을 오케스트레이터 형식으로 변환
        
        PostgreSQL에서 가져온 대화 이력을 기존 오케스트레이터가 
        이해할 수 있는 형식으로 변환합니다.
        
        Args:
            conversation_history (List[Dict[str, Any]]): DB 대화 이력
            
        Returns:
            List[Dict[str, str]]: 오케스트레이터 형식 대화 이력
        """
        formatted_history = []
        
        for message in conversation_history:
            if isinstance(message, dict):
                formatted_message = {
                    "role": message.get("role", "user"),
                    "content": message.get("content", str(message))
                }
                formatted_history.append(formatted_message)
        
        # 최근 대화만 유지 (성능 최적화)
        max_history = settings.MAX_CHAT_HISTORY
        if len(formatted_history) > max_history:
            formatted_history = formatted_history[-max_history:]
        
        return formatted_history
    
    async def get_available_agents(self) -> List[Dict[str, Any]]:
        """사용 가능한 에이전트 목록 반환
        
        Returns:
            List[Dict[str, Any]]: 에이전트 정보 목록
        """
        if not self.is_initialized:
            await self.initialize()
        
        return [
            {
                "type": "law",
                "name": "관세법 에이전트",
                "description": "관세법, 시행령, 시행규칙에 대한 전문적인 상담을 제공합니다.",
                "specialties": ["관세법", "관세율", "과세가격", "원산지", "품목분류"]
            },
            {
                "type": "regulation", 
                "name": "규제 에이전트",
                "description": "수출입 제한/금지 품목과 무역 규제 정보를 제공합니다.",
                "specialties": ["수입제한", "수출금지", "무역규제", "허가/승인", "검역"]
            },
            {
                "type": "consultation",
                "name": "민원상담 에이전트", 
                "description": "실제 민원 상담 사례를 바탕으로 해결방안을 제공합니다.",
                "specialties": ["민원사례", "실무처리", "문제해결", "절차안내", "FAQ"]
            }
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """오케스트레이터 헬스체크
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        try:
            if not self.is_initialized:
                return {
                    "status": "not_initialized",
                    "message": "오케스트레이터가 초기화되지 않았습니다"
                }
            
            # 간단한 테스트 질문으로 동작 확인
            test_result = await asyncio.wait_for(
                self.process_message(
                    user_message="안녕하세요",
                    conversation_id="health_check",
                    user_id=0,
                    conversation_history=[]
                ),
                timeout=10.0
            )
            
            return {
                "status": "healthy",
                "message": "오케스트레이터가 정상 동작중입니다",
                "test_response_time": test_result.get("processing_time", 0),
                "available_agents": len(await self.get_available_agents())
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "message": "오케스트레이터 응답 시간 초과 (10초)"
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "message": f"오케스트레이터 오류: {str(e)}"
            }
    
    async def cleanup(self) -> None:
        """리소스 정리
        
        애플리케이션 종료 시 호출되어 리소스를 정리합니다.
        """
        try:
            if self.db_manager:
                # ChromaDB 연결 정리
                if hasattr(self.db_manager, 'cleanup'):
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.db_manager.cleanup
                    )
            
            self.orchestrator = None
            self.db_manager = None
            self.is_initialized = False
            
            logger.info("✅ 오케스트레이터 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"❌ 오케스트레이터 리소스 정리 실패: {e}")


# 전역 오케스트레이터 서비스 인스턴스
orchestrator_service = OrchestratorService()


async def get_orchestrator_service() -> OrchestratorService:
    """오케스트레이터 서비스 인스턴스 반환 (의존성 주입용)
    
    Returns:
        OrchestratorService: 오케스트레이터 서비스 인스턴스
    """
    if not orchestrator_service.is_initialized:
        await orchestrator_service.initialize()
    
    return orchestrator_service