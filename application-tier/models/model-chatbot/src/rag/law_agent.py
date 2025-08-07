"""
Conversation Agent Module

GPT-4.1mini를 사용한 대화형 RAG 에이전트
"""

import logging
import openai
from typing import List, Dict, Any, Optional, Tuple
import json
import os
from datetime import datetime
from .law_retriever import SimilarLawRetriever

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    AI와 사용자 간의 대화 기록을 관리하는 클래스
    
    왜 대화 기록이 필요한가?
    - 사용자가 "그것"이라고 말했을 때 이전 대화를 참고해야 함
    - 연속된 질문에서 맥락을 유지하여 자연스러운 대화 제공
    - 같은 질문을 반복했을 때 일관된 답변이 가능
    
    신입 개발자를 위한 핵심 개념:
    - 메모리 관리: 무한정 기록을 저장하면 메모리 부족 발생
    - 대화 턴: 사용자 질문 1번 + AI 답변 1번 = 1턴
    - 시간순 저장: 최신 대화가 더 중요하므로 오래된 것부터 삭제
    
    주요 기능:
    1. 사용자 메시지 저장 (타임스탬프 포함)
    2. AI 응답 저장 (참조 문서 정보 포함)
    3. 대화 기록 조회 (시간 정보 포함/제외 선택 가능)
    4. 최근 N턴의 대화만 가져오기
    5. 전체 대화 기록 초기화
    """
    
    def __init__(self, max_history: int = 10):
        """
        대화 메모리를 초기화합니다.
        
        Args:
            max_history (int): 저장할 최대 대화 기록 수
                              10이면 사용자 메시지 10개 + AI 답변 10개 = 총 20개 메시지
                              메모리 사용량과 성능의 균형을 맞춘 기본값
        
        신입 개발자 팁:
        - 너무 크면: 메모리 사용량 증가, API 호출 비용 증가
        - 너무 작으면: 대화 맥락 손실, 사용자 경험 저하
        - 일반적으로 5-15 정도가 적당함
        """
        self.max_history = max_history
        self.messages = []
        self.context_documents = []  # 대화에서 참조된 문서들
        
    def add_user_message(self, message: str) -> None:
        """사용자 메시지 추가"""
        self.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()
    
    def add_assistant_message(self, message: str, source_documents: List[Dict] = None) -> None:
        """어시스턴트 메시지 추가"""
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
        
        self._trim_history()
    
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
    
    def clear_history(self) -> None:
        """대화 기록 초기화"""
        self.messages.clear()
        self.context_documents.clear()
    
    def _trim_history(self) -> None:
        """대화 기록 크기 제한"""
        if len(self.messages) > self.max_history:
            # 시스템 메시지는 유지하고 오래된 대화만 제거
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            
            # 최근 대화만 유지
            trimmed_other = other_messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + trimmed_other


class ConversationAgent:
    """
    관세법 전문 대화형 RAG (Retrieval-Augmented Generation) 에이전트
    
    이 클래스가 하는 일을 간단히 설명하면:
    "관세법 전문 변호사처럼 정확한 법령 조문을 찾아서 쉽게 설명해주는 AI"
    
    RAG가 무엇인가요?
    1. Retrieval (검색): 질문과 관련된 관세법 조문을 데이터베이스에서 찾기
    2. Augmented (보강): 찾은 조문을 GPT에게 참고 자료로 제공
    3. Generation (생성): GPT가 조문을 바탕으로 정확하고 이해하기 쉬운 답변 생성
    
    왜 RAG를 사용하나요?
    - GPT만 사용: 관세법을 잘못 기억하거나 최신 정보 부족
    - 검색만 사용: 조문을 찾아도 어려운 법률 용어로 이해하기 힘듦
    - RAG 사용: 정확한 조문 + 쉬운 설명 = 최상의 사용자 경험
    
    주요 구성 요소:
    - retriever: 관련 법령 조문을 찾는 검색 엔진
    - memory: 대화 기록을 관리하는 메모리 시스템
    - llm: GPT 모델로 자연스러운 답변 생성
    
    신입 개발자를 위한 핵심 개념:
    - 유사도 임계값: 너무 낮으면 관련 없는 조문 포함, 너무 높으면 필요한 정보 누락
    - 컨텍스트 문서: 한 번에 GPT에게 보여줄 수 있는 조문 수 (토큰 제한)
    - 대화 기록: 이전 질문과 답변을 기억해서 자연스러운 대화 가능
    """
    
    def __init__(self,
                 retriever: SimilarLawRetriever,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = 0.2,
                 max_context_docs: int = 5,
                 similarity_threshold: float = 0.0):
        """
        초기화
        
        Args:
            retriever (SimilarLawRetriever): 문서 검색기
            model_name (str): 사용할 GPT 모델명
            temperature (float): 생성 온도
            max_context_docs (int): 최대 컨텍스트 문서 수
            similarity_threshold (float): 유사도 임계값
        """
        self.retriever = retriever
        self.model_name = model_name
        self.temperature = temperature
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please check your .env file or set the environment variable directly."
            )
        
        self.client = openai.OpenAI(api_key=api_key)
        self.memory = ConversationMemory()
        
        logger.info(f"ConversationAgent initialized with model: {model_name}")
    
    def chat(self, user_input: str, include_references: bool = True) -> Tuple[str, List[Dict]]:
        """
        사용자 입력에 대한 대화형 응답 생성
        
        Args:
            user_input (str): 사용자 입력
            include_references (bool): 참조 문서 포함 여부
            
        Returns:
            Tuple[str, List[Dict]]: (응답 텍스트, 참조 문서 리스트)
        """
        try:
            # 1. 관련 문서 검색 (컨텍스트 고려)
            if self.memory.context_documents:
                retrieved_docs = self.retriever.search_with_context_expansion(
                    query=user_input,
                    context_documents=self.memory.context_documents,
                    top_k=self.max_context_docs
                )
            else:
                retrieved_docs = self.retriever.search_similar_laws(
                    raw_query=user_input,
                    top_k=self.max_context_docs,
                    include_references=include_references,
                    similarity_threshold=self.similarity_threshold
                )
            
            # 2. 대화 기록에 사용자 메시지 추가
            self.memory.add_user_message(user_input)
            
            # 3. 응답 생성
            response_text = self._generate_response(user_input, retrieved_docs)
            
            # 4. 대화 기록에 응답 추가
            self.memory.add_assistant_message(response_text, retrieved_docs)
            
            logger.info(f"대화 응답 생성 완료 (참조 문서: {len(retrieved_docs)}개)")
            return response_text, retrieved_docs
            
        except Exception as e:
            logger.error(f"대화 처리 실패: {e}")
            error_response = "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."
            return error_response, []
    
    def get_conversation_summary(self) -> str:
        """현재 대화의 요약 생성"""
        try:
            if not self.memory.messages:
                return "대화 기록이 없습니다."
            
            # 대화 기록을 텍스트로 변환
            conversation_text = ""
            for msg in self.memory.messages:
                role = "사용자" if msg["role"] == "user" else "AI"
                conversation_text += f"{role}: {msg['content']}\n\n"
            
            # GPT를 사용한 요약 생성
            summary_prompt = f"""다음 관세법 상담 대화를 간결하게 요약해주세요:

{conversation_text}

요약:"""
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"대화 요약 생성 실패: {e}")
            return "요약 생성 중 오류가 발생했습니다."
    
    def reset_conversation(self) -> None:
        """대화 초기화"""
        self.memory.clear_history()
        logger.info("대화 기록이 초기화되었습니다.")
    
    def _generate_response(self, user_input: str, retrieved_docs: List[Dict]) -> str:
        """
        검색된 문서를 바탕으로 응답 생성
        
        Args:
            user_input (str): 사용자 입력
            retrieved_docs (List[Dict]): 검색된 관련 문서들
            
        Returns:
            str: 생성된 응답
        """
        try:
            # 시스템 프롬프트
            system_prompt = self._get_system_prompt()
            
            # 컨텍스트 문서 포맷팅
            context = self._format_context_documents(retrieved_docs)
            
            # 대화 기록
            chat_history = self._format_chat_history()
            
            # 사용자 프롬프트 구성
            user_prompt = f"""[대화 기록]
{chat_history}

[관련 법령 정보]
{context}

[현재 질문]
{user_input}

위의 법령 정보를 근거로 정확하고 도움이 되는 답변을 제공해주세요."""
            
            # GPT 응답 생성
            response = self.client.chat.completions.create(
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
            logger.error(f"응답 생성 실패: {e}")
            return "응답 생성 중 오류가 발생했습니다."
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 반환"""
        return """당신은 한국 관세법 전문 상담 AI입니다. 다음 원칙을 준수하여 답변하세요:

1. **정확성**: 제공된 법령 정보만을 근거로 답변하세요.
2. **명확성**: 복잡한 법률 용어를 이해하기 쉽게 설명하세요.
3. **구체성**: 조문 번호와 구체적인 근거를 제시하세요.
4. **실용성**: 실무에 도움이 되는 구체적인 안내를 제공하세요.
5. **연속성**: 이전 대화 맥락을 고려하여 일관된 답변을 하세요.

답변 구조:
- 핵심 답변을 먼저 제시
- 관련 법령 근거 명시
- 필요시 주의사항이나 추가 정보 제공

법령 정보가 불충분한 경우, "제공된 정보로는 정확한 답변이 어렵습니다"라고 명시하고 일반적인 안내만 제공하세요."""
    
    def _format_context_documents(self, documents: List[Dict]) -> str:
        """컨텍스트 문서들을 포맷팅"""
        if not documents:
            return "관련 법령 정보가 없습니다."
        
        formatted_docs = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            
            # 기본 정보
            doc_info = f"[법령 {i}] {metadata.get('index', 'N/A')}"
            if metadata.get('subtitle'):
                doc_info += f" - {metadata.get('subtitle')}"
            
            # 법령명 및 계층 정보
            if metadata.get('law_name'):
                doc_info += f" ({metadata.get('law_name')})"
            
            # 내용
            content = doc.get("content", "")[:500]  # 최대 500자
            if len(doc.get("content", "")) > 500:
                content += "..."
            
            # 참조 정보
            ref_info = ""
            if doc.get("reference_info", {}).get("is_referenced"):
                ref_info = f" [관련조문 참조]"
            
            formatted_doc = f"{doc_info}{ref_info}\n{content}"
            formatted_docs.append(formatted_doc)
        
        return "\n\n".join(formatted_docs)
    
    def _format_chat_history(self) -> str:
        """대화 기록 포맷팅"""
        if not self.memory.messages:
            return "이전 대화 없음"
        
        # 최근 3턴의 대화만 포함
        recent_messages = self.memory.get_recent_context(num_turns=3)
        
        formatted_history = []
        for msg in recent_messages:
            role = "사용자" if msg["role"] == "user" else "AI"
            content = msg["content"][:200]  # 최대 200자로 제한
            if len(msg["content"]) > 200:
                content += "..."
            formatted_history.append(f"{role}: {content}")
        
        return "\n".join(formatted_history) if formatted_history else "이전 대화 없음"


class BatchConversationProcessor:
    """배치 대화 처리기 (테스트 및 평가용)"""
    
    def __init__(self, agent: ConversationAgent):
        """
        초기화
        
        Args:
            agent (ConversationAgent): 대화 에이전트
        """
        self.agent = agent
    
    def process_conversation_batch(self, conversations: List[List[str]]) -> List[Dict]:
        """
        여러 대화를 배치로 처리
        
        Args:
            conversations (List[List[str]]): 대화 세션들 (각 세션은 사용자 입력 리스트)
            
        Returns:
            List[Dict]: 처리 결과들
        """
        results = []
        
        for i, conversation in enumerate(conversations):
            # 각 대화 세션마다 에이전트 초기화
            self.agent.reset_conversation()
            
            session_results = {
                "session_id": i,
                "exchanges": [],
                "summary": ""
            }
            
            # 대화 진행
            for user_input in conversation:
                try:
                    response, docs = self.agent.chat(user_input)
                    
                    session_results["exchanges"].append({
                        "user_input": user_input,
                        "ai_response": response,
                        "retrieved_docs_count": len(docs)
                    })
                    
                except Exception as e:
                    logger.error(f"대화 처리 실패 (세션 {i}): {e}")
                    session_results["exchanges"].append({
                        "user_input": user_input,
                        "ai_response": "오류 발생",
                        "error": str(e)
                    })
            
            # 대화 요약 생성
            session_results["summary"] = self.agent.get_conversation_summary()
            results.append(session_results)
        
        return results