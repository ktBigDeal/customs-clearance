"""
FastAPI용 관세법 전문 대화형 RAG 에이전트
기존 model-chatbot의 ConversationAgent를 비동기 버전으로 포팅
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# OpenAI 클라이언트 import
try:
    from openai import AsyncOpenAI
except ImportError:
    # 하위 호환성을 위한 fallback
    AsyncOpenAI = None

# 로컬 모듈들 import
from .law_retriever import SimilarLawRetriever
from .embeddings import LangChainEmbedder
from .vector_store import LangChainVectorStore
from .query_normalizer import LawQueryNormalizer
from ..utils.config import get_law_chromadb_config

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    AI와 사용자 간의 대화 기록을 관리하는 클래스 (비동기 호환)
    
    기존 model-chatbot의 ConversationMemory와 동일한 기능을 제공하면서
    FastAPI 환경에서 비동기적으로 사용할 수 있도록 설계
    
    주요 기능:
    - 사용자 메시지 및 AI 응답 저장
    - 대화 기록 조회 및 컨텍스트 관리
    - 메모리 크기 제한을 통한 성능 최적화
    """
    
    def __init__(self, max_history: int = 10):
        """
        대화 메모리 초기화
        
        Args:
            max_history: 저장할 최대 대화 기록 수 (기본값: 10턴)
        """
        self.max_history = max_history
        self.messages = []
        self.context_documents = []
        
    async def add_user_message(self, message: str) -> None:
        """사용자 메시지 추가 (비동기)"""
        self.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        await self._trim_history()
    
    async def add_assistant_message(self, 
                                   message: str, 
                                   source_documents: Optional[List[Dict]] = None) -> None:
        """어시스턴트 메시지 추가 (비동기)"""
        self.messages.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "source_documents": source_documents or []
        })
        
        # 참조된 문서들을 컨텍스트에 추가
        if source_documents:
            for doc in source_documents:
                if doc not in self.context_documents:
                    self.context_documents.append(doc)
        
        await self._trim_history()
    
    def get_conversation_history(self, include_timestamps: bool = False) -> List[Dict]:
        """대화 기록 조회"""
        if include_timestamps:
            return self.messages.copy()
        else:
            return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def get_recent_context(self, num_turns: int = 3) -> List[Dict]:
        """최근 대화 컨텍스트 조회"""
        recent_messages = self.messages[-num_turns*2:] if self.messages else []
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    
    async def clear_history(self) -> None:
        """대화 기록 초기화 (비동기)"""
        self.messages.clear()
        self.context_documents.clear()
    
    async def _trim_history(self) -> None:
        """대화 기록 크기 제한 (비동기)"""
        if len(self.messages) > self.max_history:
            # 시스템 메시지는 유지하고 오래된 대화만 제거
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            
            # 최근 대화만 유지
            trimmed_other = other_messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + trimmed_other


class AsyncConversationAgent:
    """
    FastAPI용 비동기 관세법 전문 대화형 RAG 에이전트
    
    기존 ConversationAgent의 모든 기능을 비동기로 구현:
    - 관세법 조문 검색
    - GPT를 통한 자연어 답변 생성
    - 대화 기록 관리
    - 참조 문서 추적
    """
    
    def __init__(self,
                 retriever: Optional['SimilarLawRetriever'] = None,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = 0.2,
                 max_context_docs: int = 5,
                 similarity_threshold: float = 0.0,
                 openai_api_key: Optional[str] = None):
        """
        비동기 대화 에이전트 초기화
        
        Args:
            retriever: 관세법 검색 엔진 (None이면 나중에 초기화)
            model_name: OpenAI 모델명
            temperature: 생성 온도 (0.0-2.0)
            max_context_docs: 최대 컨텍스트 문서 수
            similarity_threshold: 유사도 임계값
            openai_api_key: OpenAI API 키 (None이면 환경변수 사용)
        """
        self.retriever = retriever
        self.model_name = model_name
        self.temperature = temperature
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        # OpenAI 비동기 클라이언트 초기화
        if AsyncOpenAI:
            self.client = AsyncOpenAI(api_key=openai_api_key)
        else:
            self.client = None
            logger.warning("AsyncOpenAI not available, using synchronous fallback")
        
        # 대화 메모리 초기화
        self.memory = ConversationMemory()
        
        # 시스템 프롬프트
        self.system_prompt = """당신은 관세법 전문가입니다. 사용자의 관세법 관련 질문에 대해 정확하고 이해하기 쉬운 답변을 제공해주세요.

답변 시 다음 사항을 준수해주세요:
1. 제공된 관세법 조문을 기반으로 정확한 정보를 제공하세요
2. 복잡한 법률 용어는 쉽게 설명해주세요
3. 구체적인 조문 번호와 내용을 인용하세요
4. 실무적인 적용 방법도 함께 안내해주세요
5. 불확실한 내용은 명시하고 전문가 상담을 권유하세요

답변 형식:
- 핵심 답변을 먼저 제시
- 관련 조문 및 근거 제시
- 실무 적용 시 주의사항 안내"""
        
        self.is_initialized = False
        logger.info("AsyncConversationAgent initialized")
    
    async def initialize(self) -> None:
        """에이전트 초기화 (retriever 생성 등)"""
        if self.is_initialized:
            return
            
        try:
            # retriever가 없으면 생성
            if not self.retriever:
                await self._create_retriever()
            
            self.is_initialized = True
            logger.info("✅ AsyncConversationAgent fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AsyncConversationAgent: {e}")
            raise
    
    async def _create_retriever(self) -> None:
        """관세법 검색 엔진 생성"""
        try:
            # 기존 model-chatbot 모듈들을 사용하여 retriever 생성
            embedder = LangChainEmbedder()
            
            config = get_law_chromadb_config()
            vector_store = LangChainVectorStore(
                collection_name=config["collection_name"],
                config=config
            )
            
            query_normalizer = LawQueryNormalizer()
            
            self.retriever = SimilarLawRetriever(
                embedder=embedder,
                vector_store=vector_store,
                query_normalizer=query_normalizer
            )
            
            logger.info("✅ Law retriever created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create retriever: {e}")
            self.retriever = None
    
    async def chat(self, user_input: str) -> Tuple[str, List[Dict]]:
        """
        사용자 입력에 대한 대화 처리
        
        Args:
            user_input: 사용자 메시지
            
        Returns:
            Tuple[str, List[Dict]]: (AI 응답, 참조 문서 목록)
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 사용자 메시지를 메모리에 추가
            await self.memory.add_user_message(user_input)
            
            # 관련 문서 검색
            relevant_docs = await self._search_relevant_documents(user_input)
            
            # AI 응답 생성
            response = await self._generate_response(user_input, relevant_docs)
            
            # 응답을 메모리에 추가
            await self.memory.add_assistant_message(response, relevant_docs)
            
            logger.info(f"✅ Chat completed for user input: {user_input[:50]}...")
            
            return response, relevant_docs
            
        except Exception as e:
            logger.error(f"❌ Chat processing failed: {e}")
            error_response = f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"
            return error_response, []
    
    async def _search_relevant_documents(self, query: str) -> List[Dict]:
        """관련 문서 검색 (비동기)"""
        if not self.retriever:
            logger.warning("Retriever not available, returning empty results")
            return []
        
        try:
            # 동기 retriever를 비동기로 실행
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: self.retriever.search_similar_laws(
                    raw_query=query, 
                    top_k=self.max_context_docs,
                    similarity_threshold=self.similarity_threshold
                )
            )
            
            logger.info(f"Retrieved {len(docs)} relevant documents")
            return docs
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []
    
    async def _generate_response(self, query: str, documents: List[Dict]) -> str:
        """AI 응답 생성 (비동기)"""
        try:
            # 대화 컨텍스트 구성
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # 최근 대화 기록 추가
            conversation_history = self.memory.get_recent_context(num_turns=3)
            messages.extend(conversation_history[:-1])  # 현재 사용자 메시지 제외
            
            # 검색된 문서들을 컨텍스트에 추가
            context_text = self._format_documents_for_context(documents)
            
            user_message = f"""사용자 질문: {query}

관련 관세법 조문:
{context_text}

위 조문들을 참고하여 사용자 질문에 정확하고 이해하기 쉽게 답변해주세요."""
            
            messages.append({"role": "user", "content": user_message})
            
            # OpenAI API 호출
            if self.client:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=2000
                )
                
                return response.choices[0].message.content
            else:
                # Fallback for synchronous client
                import openai
                response = openai.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=2000
                )
                
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _format_documents_for_context(self, documents: List[Dict]) -> str:
        """검색된 문서들을 컨텍스트 형태로 포맷"""
        if not documents:
            return "관련된 관세법 조문을 찾지 못했습니다."
        
        formatted_docs = []
        for i, doc in enumerate(documents, 1):
            # 문서 정보 추출
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            index = (doc.get("index") or 
                    metadata.get("index") or 
                    "").strip()
            subtitle = (doc.get("subtitle") or 
                       metadata.get("subtitle") or 
                       "").strip()
            law_name = metadata.get("law_name", "관세법")
            similarity = abs(doc.get("similarity", 0))
            
            # 문서 제목 구성
            title_parts = []
            if index and index != "N/A":
                title_parts.append(index)
            if subtitle:
                title_parts.append(subtitle)
            
            title = " ".join(title_parts) if title_parts else "관련 조문"
            
            formatted_docs.append(f"""
[문서 {i}] {law_name} - {title} (유사도: {similarity:.3f})
{content[:800]}{'...' if len(content) > 800 else ''}
""")
        
        return "\n".join(formatted_docs)
    
    async def reset_conversation(self) -> None:
        """대화 기록 초기화"""
        await self.memory.clear_history()
        logger.info("Conversation history reset")
    
    def get_conversation_history(self) -> List[Dict]:
        """현재 대화 기록 반환"""
        return self.memory.get_conversation_history(include_timestamps=True)


# 싱글톤 인스턴스 관리를 위한 전역 변수
_law_agent_instance: Optional[AsyncConversationAgent] = None


async def get_law_agent() -> AsyncConversationAgent:
    """
    법령 에이전트 싱글톤 인스턴스 반환
    FastAPI dependency injection용
    """
    global _law_agent_instance
    
    if _law_agent_instance is None:
        _law_agent_instance = AsyncConversationAgent()
        await _law_agent_instance.initialize()
    
    return _law_agent_instance


async def create_law_agent(**kwargs) -> AsyncConversationAgent:
    """
    새로운 법령 에이전트 인스턴스 생성
    
    Args:
        **kwargs: AsyncConversationAgent 생성자 파라미터
        
    Returns:
        초기화된 AsyncConversationAgent 인스턴스
    """
    agent = AsyncConversationAgent(**kwargs)
    await agent.initialize()
    return agent