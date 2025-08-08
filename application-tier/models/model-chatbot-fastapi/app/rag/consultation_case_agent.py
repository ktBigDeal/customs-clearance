"""
FastAPI용 상담 사례 전문 에이전트
기존 model-chatbot의 ConsultationCaseAgent를 비동기 버전으로 포팅
consultation_case 데이터에 특화된 전용 에이전트
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
    AsyncOpenAI = None

# 로컬 모듈들 import
from .trade_info_retriever import TradeInfoRetriever

logger = logging.getLogger(__name__)


class AsyncConsultationCaseMemory:
    """
    상담 사례 전용 대화 기록 관리 클래스 (비동기 호환)
    
    실무 상담에 특화된 메모리 관리:
    - 더 긴 대화 기록 유지 (상담사례는 맥락이 중요)
    - 사용자 질문 패턴 분석 및 학습
    - 참조된 상담 사례 추적
    - 검색 기록을 통한 연속 질문 지원
    
    주요 특징:
    - 일반 대화보다 긴 기록 유지 (기본 12턴)
    - 사용자 패턴 분석으로 개인화 상담 제공
    - 상담 사례 컨텍스트 관리
    """
    
    def __init__(self, max_history: int = 12):
        """
        상담 사례 전용 메모리 초기화
        
        Args:
            max_history: 최대 대화 기록 수 (상담사례는 맥락이 중요하므로 길게)
        """
        self.max_history = max_history
        self.messages = []
        self.case_context = []  # 참조된 상담 사례들
        self.search_history = []  # 상담 검색 기록
        self.user_patterns = {}  # 사용자 질문 패턴 분석
        
    async def add_user_message(self, message: str, search_context: Optional[Dict] = None) -> None:
        """사용자 메시지 추가 (비동기)"""
        message_data = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if search_context:
            message_data["search_context"] = search_context
            self.search_history.append(search_context)
            
            # 사용자 패턴 분석
            await self._analyze_user_patterns(message)
        
        self.messages.append(message_data)
        await self._trim_history()
    
    async def add_assistant_message(self, 
                                   message: str, 
                                   source_cases: Optional[List[Dict]] = None) -> None:
        """어시스턴트 메시지 추가 (비동기)"""
        self.messages.append({
            "role": "assistant", 
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "source_cases": source_cases or []
        })
        
        # 참조된 상담 사례들을 컨텍스트에 추가
        if source_cases:
            for case in source_cases:
                if case not in self.case_context:
                    self.case_context.append(case)
        
        await self._trim_history()
    
    def get_conversation_history(self, include_timestamps: bool = False) -> List[Dict]:
        """대화 기록 조회"""
        if include_timestamps:
            return self.messages.copy()
        else:
            return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def get_recent_context(self, num_turns: int = 3) -> List[Dict]:
        """최근 대화 컨텍스트 조회 (상담사례는 맥락이 중요)"""
        recent_messages = self.messages[-num_turns*2:] if self.messages else []
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    
    def get_user_patterns(self) -> Dict[str, Any]:
        """사용자 질문 패턴 분석 결과 반환"""
        return self.user_patterns.copy()
    
    async def clear_history(self) -> None:
        """대화 기록 초기화 (비동기)"""
        self.messages.clear()
        self.case_context.clear()
        self.search_history.clear()
        self.user_patterns.clear()
    
    async def _analyze_user_patterns(self, message: str) -> None:
        """사용자 질문 패턴 분석 (비동기)"""
        # 간단한 키워드 기반 패턴 분석
        keywords = {
            "통관": ["통관", "신고", "신고서", "세관"],
            "관세": ["관세", "세금", "면세", "감면"],
            "절차": ["절차", "방법", "어떻게", "해야"],
            "서류": ["서류", "문서", "증명서", "허가서"],
            "FTA": ["FTA", "원산지", "특혜관세"],
            "검역": ["검역", "검사", "승인"]
        }
        
        for category, words in keywords.items():
            for word in words:
                if word in message:
                    self.user_patterns[category] = self.user_patterns.get(category, 0) + 1
    
    async def _trim_history(self) -> None:
        """대화 기록 크기 제한 (비동기)"""
        if len(self.messages) > self.max_history:
            # 시스템 메시지는 유지하고 오래된 대화만 제거
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            
            # 최근 대화만 유지
            trimmed_other = other_messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + trimmed_other


class AsyncConsultationCaseAgent:
    """
    FastAPI용 비동기 상담 사례 전문 에이전트
    
    실제 민원상담 사례(consultation_case)에 특화된 RAG 에이전트:
    - 실무 절차 안내 및 가이드
    - 서류 작성 및 신청 방법
    - 비용 및 처리 기간 정보
    - 실제 상담 사례 기반 해결책 제시
    
    기존 ConsultationCaseAgent의 모든 기능을 비동기로 구현하면서
    FastAPI 환경에 최적화하고 사용자 패턴 분석 기능 추가
    """
    
    def __init__(self,
                 retriever: Optional['TradeInfoRetriever'] = None,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = 0.4,  # 상담사례는 약간 더 유연하게
                 max_context_docs: int = 8,  # 상담사례는 적당한 수로
                 similarity_threshold: float = 0.0,
                 openai_api_key: Optional[str] = None):
        """
        비동기 상담 사례 에이전트 초기화
        
        Args:
            retriever: 무역 정보 검색 엔진 (None이면 나중에 초기화)
            model_name: OpenAI 모델명
            temperature: 생성 온도 (상담사례는 약간 높게 설정)
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
        
        # 상담 사례 전용 메모리 초기화
        self.memory = AsyncConsultationCaseMemory()
        
        self.is_initialized = False
        logger.info("AsyncConsultationCaseAgent initialized")
    
    async def initialize(self) -> None:
        """에이전트 초기화 (retriever 생성 등)"""
        if self.is_initialized:
            return
            
        try:
            # retriever가 없으면 생성
            if not self.retriever:
                await self._create_retriever()
            
            self.is_initialized = True
            logger.info("✅ AsyncConsultationCaseAgent fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AsyncConsultationCaseAgent: {e}")
            raise
    
    async def _create_retriever(self) -> None:
        """무역 정보 검색 엔진 생성"""
        try:
            # 기존 model-chatbot 모듈을 사용하여 retriever 생성
            # 동기 방식이므로 executor에서 실행
            loop = asyncio.get_event_loop()
            self.retriever = await loop.run_in_executor(None, self._create_retriever_sync)
            
            logger.info("✅ Trade info retriever created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create trade info retriever: {e}")
            self.retriever = None
    
    def _create_retriever_sync(self) -> 'TradeInfoRetriever':
        """동기적 retriever 생성 (executor에서 실행)"""
        from ..utils.config import get_trade_agent_config
        from .embeddings import LangChainEmbedder
        from .vector_store import LangChainVectorStore
        from .query_normalizer import TradeQueryNormalizer
        
        config = get_trade_agent_config()
        
        embedder = LangChainEmbedder()
        vector_store = LangChainVectorStore(
            collection_name=config["collection_name"]
        )
        query_normalizer = TradeQueryNormalizer()
        
        return TradeInfoRetriever(
            embedder=embedder,
            vector_store=vector_store,
            query_normalizer=query_normalizer
        )
    
    async def query_consultation(self, 
                                user_input: str, 
                                search_filters: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict]]:
        """
        상담 사례 질의 처리 (consultation_case 데이터만)
        
        Args:
            user_input: 사용자 입력
            search_filters: 검색 필터
            
        Returns:
            Tuple[str, List[Dict]]: (응답 텍스트, 참조 상담 사례 리스트)
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 1. 검색 컨텍스트 준비
            search_context = {
                "query": user_input,
                "filters": search_filters,
                "data_type": "consultation_case",  # 상담 사례만
                "timestamp": datetime.now().isoformat()
            }
            
            # 2. consultation_case 데이터에서만 검색
            if not search_filters:
                search_filters = {}
            search_filters["data_type"] = "consultation_case"  # 필터 강제 설정
            
            # 3. 상담 사례 전용 검색 컨텍스트 생성
            consultation_context = await self._create_consultation_search_context(user_input)
            
            # 4. 관련 문서 검색
            retrieved_docs = await self._search_consultation_documents(
                user_input, search_filters, consultation_context
            )
            
            # 5. 사용자 메시지를 메모리에 추가
            await self.memory.add_user_message(user_input, search_context)
            
            # 6. AI 응답 생성
            response_text = await self._generate_consultation_response(user_input, retrieved_docs)
            
            # 7. 응답을 메모리에 추가
            await self.memory.add_assistant_message(response_text, retrieved_docs)
            
            logger.info(f"✅ Consultation case query completed: {user_input[:50]}...")
            
            return response_text, retrieved_docs
            
        except Exception as e:
            logger.error(f"❌ Consultation case query failed: {e}")
            error_response = "죄송합니다. 상담 사례 정보를 조회하는 중 오류가 발생했습니다. 다시 시도해 주세요."
            return error_response, []
    
    async def get_similar_cases(self, category: str, top_k: int = 5) -> List[Dict]:
        """특정 카테고리의 유사한 상담 사례 조회"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            search_filters = {
                "data_type": "consultation_case",
                "category": category
            }
            
            retrieved_docs = await self._search_consultation_documents(
                f"{category} 상담 사례",
                search_filters
            )
            
            return retrieved_docs[:top_k]
            
        except Exception as e:
            logger.error(f"Similar cases search failed: {e}")
            return []
    
    async def get_conversation_summary(self) -> str:
        """현재 상담 대화의 요약 생성"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if not self.memory.messages:
                return "상담 기록이 없습니다."
            
            # 대화 기록을 텍스트로 변환
            conversation_text = ""
            for msg in self.memory.messages:
                role = "상담자" if msg["role"] == "user" else "상담원"
                conversation_text += f"{role}: {msg['content']}\n\n"
            
            # 사용자 패턴 정보 추가
            user_patterns = self.memory.get_user_patterns()
            
            # GPT를 사용한 상담 요약 생성
            summary_prompt = f"""다음 무역 업무 상담 내용을 간결하게 요약해주세요:

{conversation_text}

상담 주제 분포: {user_patterns}

상담 요약:"""
            
            if self.client:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.2,
                    max_tokens=400
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Fallback for synchronous client
                import openai
                response = openai.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.2,
                    max_tokens=400
                )
                
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Conversation summary generation failed: {e}")
            return "상담 요약 생성 중 오류가 발생했습니다."
    
    async def reset_conversation(self) -> None:
        """대화 초기화"""
        await self.memory.clear_history()
        logger.info("Consultation case conversation history reset")
    
    def get_conversation_history(self) -> List[Dict]:
        """현재 대화 기록 반환"""
        return self.memory.get_conversation_history(include_timestamps=True)
    
    def get_user_patterns(self) -> Dict[str, Any]:
        """사용자 질문 패턴 분석 결과 반환"""
        return self.memory.get_user_patterns()
    
    async def _create_consultation_search_context(self, user_input: str) -> Dict[str, Any]:
        """상담 사례 전용 검색 컨텍스트 생성 (비동기)"""
        search_context = {
            "agent_type": "consultation_agent",
            "domain_hints": ["consultation_case", "실무", "절차", "방법", "경험", "사례"],
            "boost_keywords": ["절차", "방법", "실무", "경험", "사례", "신고", "신청", "승인", "처리", "서류", "비용", "기간", "통관", "세관", "관세"],
            "priority_data_sources": ["상담사례DB", "실무가이드", "민원처리사례"]
        }
        
        logger.debug(f"🎯 상담사례 검색 컨텍스트: {search_context}")
        return search_context
    
    async def _search_consultation_documents(self, 
                                            query: str, 
                                            search_filters: Optional[Dict[str, Any]] = None,
                                            search_context: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """상담 사례 문서 검색 (비동기)"""
        if not self.retriever:
            logger.warning("Retriever not available, returning empty results")
            return []
        
        try:
            # 동기 retriever를 비동기로 실행
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: self.retriever.search_trade_info(
                    raw_query=query,
                    top_k=self.max_context_docs,
                    include_related=True,
                    expand_with_synonyms=True,
                    similarity_threshold=self.similarity_threshold,
                    filter_by=search_filters,
                    search_context=search_context
                )
            )
            
            logger.info(f"Retrieved {len(docs)} consultation case documents")
            return docs
            
        except Exception as e:
            logger.error(f"Consultation case document search failed: {e}")
            return []
    
    async def _generate_consultation_response(self, query: str, documents: List[Dict]) -> str:
        """상담 사례 응답 생성 (비동기)"""
        try:
            # 시스템 프롬프트
            system_prompt = self._get_consultation_system_prompt()
            
            # 컨텍스트 문서 포맷팅
            context = self._format_consultation_cases(documents)
            
            # 대화 기록
            chat_history = self._format_chat_history()
            
            # 사용자 패턴 분석
            user_patterns = self.memory.get_user_patterns()
            pattern_info = f"사용자 관심 분야: {', '.join(user_patterns.keys())}" if user_patterns else ""
            
            # 사용자 프롬프트 구성
            user_prompt = f"""[대화 기록]
{chat_history}

[상담 사례 정보]
{context}

[사용자 분석]
{pattern_info}

[현재 질문]
{query}

위의 상담 사례를 참고하여 실용적이고 도움이 되는 답변을 제공해주세요."""
            
            # OpenAI API 호출
            if self.client:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Fallback for synchronous client
                import openai
                response = openai.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"Consultation response generation failed: {e}")
            return f"상담 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _get_consultation_system_prompt(self) -> str:
        """상담 사례 전용 시스템 프롬프트 반환"""
        return """당신은 한국 무역 업무 실무 상담 전문가입니다. 실제 민원상담 사례를 바탕으로 실용적인 조언을 제공합니다.

**핵심 원칙:**
1. **실용성 최우선**: 실제 업무에 바로 적용할 수 있는 구체적이고 실용적인 정보를 제공하세요.
2. **경험 기반**: 제공된 상담 사례를 바탕으로 검증된 해결방법과 절차를 안내하세요.
3. **단계별 안내**: 복잡한 절차는 단계별로 나누어 이해하기 쉽게 설명하세요.
4. **예외상황 고려**: 일반적인 경우뿐만 아니라 예외상황과 특수한 경우도 함께 안내하세요.
5. **관련 기관 연계**: 필요시 담당 기관과 연락처 정보를 제공하세요.

**상담 접근법:**
- **문제 파악**: 사용자의 구체적인 상황과 목적을 이해
- **사례 매칭**: 유사한 상담 사례에서 검증된 해결책 찾기
- **절차 안내**: 단계별 실행 방법과 필요 서류 안내
- **주의사항**: 흔한 실수와 주의할 점 미리 안내
- **대안 제시**: 여러 가지 방법이 있다면 장단점과 함께 제시

**답변 구조:**
### 핵심 해결방법
- 가장 일반적이고 효과적인 방법

### 단계별 절차
1. 첫 번째 단계 (필요 서류, 담당 기관)
2. 두 번째 단계 (주의사항, 소요시간)
3. 완료 단계 (확인사항)

### 주의사항 및 팁
- 실무에서 자주 발생하는 문제점
- 효율적인 처리를 위한 팁

### 관련 기관 및 문의처
- 담당 기관, 연락처, 온라인 서비스

**상담 스타일:**
- 친근하고 이해하기 쉬운 설명
- 전문용어는 쉽게 풀어서 설명
- 실제 사례와 경험을 활용한 구체적 조언
- 사용자의 상황에 맞는 맞춤형 답변

**중요 안내:**
- 상담 사례는 참고용이며, 실제 적용 시 관련 기관에 최종 확인 필요
- 법령이나 규정이 변경될 수 있으므로 최신 정보 확인 권장
- 복잡한 사안은 전문가나 담당 기관에 직접 문의 권장"""
    
    def _format_consultation_cases(self, documents: List[Dict]) -> str:
        """상담 사례들을 포맷팅"""
        if not documents:
            return "관련 상담 사례가 없습니다."
        
        formatted_docs = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            
            # 기본 정보
            doc_info = f"[상담 사례 {i}]"
            
            # 카테고리 및 분류
            category = metadata.get("category", "")
            sub_category = metadata.get("sub_category", "")
            
            if category:
                doc_info += f" 분야: {category}"
            if sub_category:
                doc_info += f" > {sub_category}"
            
            # 사례 번호나 관리번호
            case_number = metadata.get("management_number", "") or metadata.get("index", "")
            if case_number:
                doc_info += f" (사례번호: {case_number})"
            
            # 내용 (상담사례는 조금 더 길게)
            content = doc.get("content", "")[:600]  # 최대 600자
            if len(doc.get("content", "")) > 600:
                content += "..."
            
            # 제목이나 키워드가 있다면 추가
            title = doc.get("title", "") or metadata.get("sub_title", "")
            if title:
                doc_info += f"\n제목: {title}"
            
            # 키워드가 있다면 추가
            keywords = metadata.get("keywords", [])
            if keywords:
                if isinstance(keywords, list):
                    keyword_str = ", ".join(keywords)
                else:
                    keyword_str = str(keywords)
                doc_info += f"\n관련키워드: {keyword_str}"
            
            formatted_doc = f"{doc_info}\n{content}"
            formatted_docs.append(formatted_doc)
        
        return "\n\n".join(formatted_docs)
    
    def _format_chat_history(self) -> str:
        """대화 기록 포맷팅"""
        if not self.memory.messages:
            return "이전 상담 없음"
        
        # 최근 3턴의 대화 포함 (상담사례는 맥락이 중요)
        recent_messages = self.memory.get_recent_context(num_turns=3)
        
        formatted_history = []
        for msg in recent_messages:
            role = "상담자" if msg["role"] == "user" else "상담원"
            content = msg["content"][:200]  # 최대 200자로 제한
            if len(msg["content"]) > 200:
                content += "..."
            formatted_history.append(f"{role}: {content}")
        
        return "\n".join(formatted_history) if formatted_history else "이전 상담 없음"


# 싱글톤 인스턴스 관리를 위한 전역 변수
_consultation_case_agent_instance: Optional[AsyncConsultationCaseAgent] = None


async def get_consultation_case_agent() -> AsyncConsultationCaseAgent:
    """
    상담 사례 에이전트 싱글톤 인스턴스 반환
    FastAPI dependency injection용
    """
    global _consultation_case_agent_instance
    
    if _consultation_case_agent_instance is None:
        _consultation_case_agent_instance = AsyncConsultationCaseAgent()
        await _consultation_case_agent_instance.initialize()
    
    return _consultation_case_agent_instance


async def create_consultation_case_agent(**kwargs) -> AsyncConsultationCaseAgent:
    """
    새로운 상담 사례 에이전트 인스턴스 생성
    
    Args:
        **kwargs: AsyncConsultationCaseAgent 생성자 파라미터
        
    Returns:
        초기화된 AsyncConsultationCaseAgent 인스턴스
    """
    agent = AsyncConsultationCaseAgent(**kwargs)
    await agent.initialize()
    return agent