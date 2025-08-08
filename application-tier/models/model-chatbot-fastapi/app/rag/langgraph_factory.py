"""
LangGraph Factory Module

기존 에이전트들과 LangGraph 오케스트레이터의 통합을 담당하는 팩토리 클래스
"""

import logging
from typing import Optional, Dict, Any
import os

from .langgraph_orchestrator import LangGraphOrchestrator
from .law_agent import AsyncConversationAgent
from .trade_regulation_agent import AsyncTradeRegulationAgent
from .consultation_case_agent import AsyncConsultationCaseAgent
from .embeddings import LangChainEmbedder
from .vector_store import LangChainVectorStore, ChromaVectorStore
from .query_normalizer import LawQueryNormalizer
from .law_retriever import SimilarLawRetriever
from .trade_info_retriever import TradeInfoRetriever
from ..utils.config import get_trade_agent_config

logger = logging.getLogger(__name__)


class LangGraphAgentFactory:
    """LangGraph 기반 멀티 에이전트 시스템 팩토리"""
    
    def __init__(self):
        """팩토리 초기화"""
        self.orchestrator = None
        self.conversation_agent = None
        self.regulation_agent = None
        self.consultation_agent = None
        
        # 공통 구성요소
        self.embedder = None
        self.law_vector_store = None
        self.trade_vector_store = None
        self.query_normalizer = None
        
        logger.info("LangGraphAgentFactory initialized")
    
    def create_orchestrated_system(self, 
                                  model_name: str = "gpt-4.1-mini",
                                  temperature: float = 0.1,
                                  force_rebuild: bool = False) -> LangGraphOrchestrator:
        """
        완전한 LangGraph 오케스트레이션 시스템 생성
        
        Args:
            model_name: 사용할 언어 모델
            temperature: 모델 온도 설정
            force_rebuild: 강제 재구성 여부
            
        Returns:
            설정된 LangGraphOrchestrator
        """
        try:
            logger.info(f"🏗️ Building LangGraph orchestrated system...")
            
            # API 키 확인
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # 기존 오케스트레이터가 있고 재구성이 필요하지 않으면 반환
            if self.orchestrator and not force_rebuild:
                logger.info("Using existing orchestrator")
                return self.orchestrator
            
            # 1. 공통 구성요소 초기화
            self._initialize_common_components()
            
            # 2. 개별 에이전트 생성
            self._create_conversation_agent()
            self._create_regulation_agent(model_name, temperature)
            self._create_consultation_agent(model_name, temperature)
            
            # 3. LangGraph 오케스트레이터 생성
            self.orchestrator = LangGraphOrchestrator(
                model_name=model_name,
                temperature=temperature
            )
            
            # 4. 에이전트들을 오케스트레이터에 연결
            self.orchestrator.set_agents(
                conversation_agent=self.conversation_agent,
                regulation_agent=self.regulation_agent,
                consultation_agent=self.consultation_agent
            )
            
            logger.info("✅ LangGraph orchestrated system created successfully")
            return self.orchestrator
            
        except Exception as e:
            logger.error(f"Failed to create orchestrated system: {e}")
            raise
    
    def _initialize_common_components(self):
        """공통 구성요소 초기화"""
        try:
            logger.info("🔧 Initializing common components...")
            
            # 임베딩 모델
            if not self.embedder:
                self.embedder = LangChainEmbedder()
                logger.info("  - LangChain Embedder initialized")
            
            # 쿼리 정규화기
            if not self.query_normalizer:
                self.query_normalizer = LawQueryNormalizer()
                logger.info("  - Query Normalizer initialized")
            
            # 벡터 저장소들
            if not self.law_vector_store:
                self.law_vector_store = ChromaVectorStore(
                    collection_name="customs_law_collection",
                    db_path="data/chroma_db"
                )
                logger.info("  - Law Vector Store initialized")
            
            if not self.trade_vector_store:
                trade_config = get_trade_agent_config()
                self.trade_vector_store = ChromaVectorStore(
                    collection_name=trade_config["collection_name"],
                    db_path="data/chroma_db"
                )
                logger.info("  - Trade Vector Store initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize common components: {e}")
            raise
    
    def _create_conversation_agent(self):
        """관세법 RAG 에이전트 생성"""
        try:
            if self.conversation_agent:
                return
            
            logger.info("🏛️ Creating AsyncConversationAgent...")
            
            # 법령 검색기 생성
            law_retriever = SimilarLawRetriever(
                embedder=self.embedder,
                vector_store=self.law_vector_store,
                query_normalizer=self.query_normalizer
            )
            
            # 대화 에이전트 생성
            self.conversation_agent = AsyncConversationAgent(
                retriever=law_retriever,
                max_context_docs=5,
                similarity_threshold=0.0
            )
            
            logger.info("  ✅ AsyncConversationAgent created")
            
        except Exception as e:
            logger.error(f"Failed to create AsyncConversationAgent: {e}")
            raise
    
    def _create_regulation_agent(self, model_name: str, temperature: float):
        """무역 규제 전문 에이전트 생성"""
        try:
            if self.regulation_agent:
                return
            
            logger.info("⚖️ Creating TradeRegulationAgent...")
            
            # 무역 정보 검색기 생성
            trade_retriever = TradeInfoRetriever(
                embedder=self.embedder,
                vector_store=self.trade_vector_store,
                query_normalizer=self.query_normalizer,
                collection_name=get_trade_agent_config()["collection_name"]
            )
            
            # 규제 전문 에이전트 생성
            self.regulation_agent = AsyncTradeRegulationAgent(
                retriever=trade_retriever,
                model_name=model_name,
                temperature=0.1,  # 규제 정보는 더 정확하게
                max_context_docs=12,  # 더 많은 규제 문서 참조
                similarity_threshold=get_trade_agent_config()["similarity_threshold"]
            )
            
            logger.info("  ✅ TradeRegulationAgent created")
            
        except Exception as e:
            logger.error(f"Failed to create TradeRegulationAgent: {e}")
            raise
    
    def _create_consultation_agent(self, model_name: str, temperature: float):
        """상담 사례 전문 에이전트 생성"""
        try:
            if self.consultation_agent:
                return
            
            logger.info("💼 Creating ConsultationCaseAgent...")
            
            # 무역 정보 검색기 재사용 (같은 데이터베이스 사용)
            trade_retriever = TradeInfoRetriever(
                embedder=self.embedder,
                vector_store=self.trade_vector_store,
                query_normalizer=self.query_normalizer,
                collection_name=get_trade_agent_config()["collection_name"]
            )
            
            # 상담 전문 에이전트 생성
            self.consultation_agent = AsyncConsultationCaseAgent(
                retriever=trade_retriever,
                model_name=model_name,
                temperature=0.4,  # 상담사례는 약간 더 유연하게
                max_context_docs=8,  # 적당한 수의 상담사례 참조
                similarity_threshold=get_trade_agent_config()["similarity_threshold"]
            )
            
            logger.info("  ✅ ConsultationCaseAgent created")
            
        except Exception as e:
            logger.error(f"Failed to create ConsultationCaseAgent: {e}")
            raise
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """에이전트 통계 정보 반환"""
        stats = {
            "factory_type": "LangGraphAgentFactory",
            "orchestrator_available": self.orchestrator is not None,
            "agents": {
                "conversation_agent": self.conversation_agent is not None,
                "regulation_agent": self.regulation_agent is not None,
                "consultation_agent": self.consultation_agent is not None
            }
        }
        
        # 개별 에이전트 통계 추가
        if self.conversation_agent:
            try:
                stats["conversation_agent_stats"] = self.conversation_agent.get_statistics()
            except:
                pass
        
        if self.regulation_agent:
            try:
                stats["regulation_agent_stats"] = self.regulation_agent.get_statistics()
            except:
                pass
        
        if self.consultation_agent:
            try:
                stats["consultation_agent_stats"] = self.consultation_agent.get_statistics()
            except:
                pass
        
        if self.orchestrator:
            try:
                stats["orchestrator_stats"] = self.orchestrator.get_routing_stats()
            except:
                pass
        
        return stats
    
    def reset(self):
        """팩토리 상태 초기화"""
        logger.info("🔄 Resetting LangGraphAgentFactory...")
        
        self.orchestrator = None
        self.conversation_agent = None
        self.regulation_agent = None
        self.consultation_agent = None
        
        # 공통 구성요소는 유지 (재사용 가능)
        
        logger.info("✅ Factory reset completed")


# 글로벌 팩토리 인스턴스 (싱글톤 패턴)
_factory_instance = None

def get_langgraph_factory() -> LangGraphAgentFactory:
    """글로벌 LangGraph 팩토리 인스턴스 반환"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = LangGraphAgentFactory()
    return _factory_instance


def create_orchestrated_system(model_name: str = "gpt-4.1-mini", 
                              temperature: float = 0.1,
                              force_rebuild: bool = False) -> LangGraphOrchestrator:
    """
    편의 함수: 완전한 LangGraph 오케스트레이션 시스템 생성
    
    Args:
        model_name: 사용할 언어 모델
        temperature: 모델 온도 설정
        force_rebuild: 강제 재구성 여부
        
    Returns:
        설정된 LangGraphOrchestrator
    """
    factory = get_langgraph_factory()
    return factory.create_orchestrated_system(
        model_name=model_name,
        temperature=temperature,
        force_rebuild=force_rebuild
    )