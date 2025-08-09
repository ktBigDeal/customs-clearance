"""
대화기록 데이터 모델 정의
PostgreSQL + SQLAlchemy + Pydantic 통합 모델
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON, func, select, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from ..core.database import Base


class MessageRole(str, Enum):
    """메시지 역할 정의"""
    USER = "user"
    ASSISTANT = "assistant"  
    SYSTEM = "system"


class AgentType(str, Enum):
    """에이전트 타입 정의"""
    CONVERSATION = "conversation_agent"  # 관세법 전문
    REGULATION = "regulation_agent"      # 무역규제 전문
    CONSULTATION = "consultation_agent"   # 상담사례 전문


# SQLAlchemy 모델
class ConversationORM(Base):
    """대화 세션 SQLAlchemy 모델"""
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    last_agent_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # 관계 정의 (대화가 삭제되면 메시지도 함께 삭제)
    messages: Mapped[List["MessageORM"]] = relationship("MessageORM", back_populates="conversation", cascade="all, delete-orphan")


class MessageORM(Base):
    """메시지 SQLAlchemy 모델"""
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(50), ForeignKey("conversations.id"), nullable=False, index=True)
    role: Mapped[MessageRole] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    routing_info: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    references: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # 관계 정의
    conversation: Mapped["ConversationORM"] = relationship("ConversationORM", back_populates="messages")


# Pydantic 모델 (API 입출력용)
class MessageReference(BaseModel):
    """참조 문서 정보"""
    source: str
    title: Optional[str] = None
    similarity: float
    extra_metadata: Dict[str, Any] = {}


class RoutingInfo(BaseModel):
    """라우팅 정보"""
    selected_agent: str
    complexity: float
    reasoning: str
    requires_multiple_agents: bool = False
    routing_history: List[Dict[str, Any]] = []


class MessageBase(BaseModel):
    """메시지 기본 정보"""
    role: MessageRole
    content: str
    agent_used: Optional[str] = None
    routing_info: Optional[RoutingInfo] = None
    references: List[MessageReference] = []
    extra_metadata: Dict[str, Any] = {}


class MessageCreate(MessageBase):
    """메시지 생성 요청"""
    conversation_id: str


class MessageResponse(MessageBase):
    """메시지 응답"""
    id: str
    conversation_id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ConversationBase(BaseModel):
    """대화 세션 기본 정보"""
    title: str
    extra_metadata: Dict[str, Any] = {}


class ConversationCreate(ConversationBase):
    """대화 세션 생성 요청"""
    user_id: int
    initial_message: Optional[str] = None


class ConversationUpdate(BaseModel):
    """대화 세션 업데이트 요청"""
    title: Optional[str] = None
    is_active: Optional[bool] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class ConversationSummary(BaseModel):
    """대화 세션 요약 정보"""
    id: str
    title: str
    message_count: int
    last_agent_used: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ConversationDetail(ConversationSummary):
    """대화 세션 상세 정보"""
    user_id: int
    extra_metadata: Dict[str, Any]
    recent_messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """대화 목록 응답"""
    conversations: List[ConversationSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class MessageListResponse(BaseModel):
    """메시지 목록 응답"""
    messages: List[MessageResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class ConversationSearchRequest(BaseModel):
    """대화 검색 요청"""
    query: str
    user_id: Optional[int] = None
    agent_type: Optional[AgentType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0, ge=0)


class ConversationSearchResponse(BaseModel):
    """대화 검색 응답"""
    conversations: List[ConversationSummary]
    messages: List[MessageResponse]
    total_count: int
    search_query: str


# 유틸리티 함수
class ConversationUtils:
    """대화 관련 유틸리티 함수"""
    
    @staticmethod
    def generate_conversation_id() -> str:
        """새로운 대화 ID 생성"""
        return f"conv_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_message_id() -> str:
        """새로운 메시지 ID 생성"""
        return f"msg_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_conversation_title(initial_message: str, max_length: int = 50) -> str:
        """초기 메시지로부터 대화 제목 생성"""
        if not initial_message:
            return "새 대화"
        
        # 의미 있는 제목 생성 - 핵심 키워드 추출 방식
        message = initial_message.strip()
        
        # 통관/관세 관련 키워드 매핑
        keywords_mapping = {
            'HS코드': 'HS코드 분류 문의',
            '수입신고': '수입신고서 문의',
            '수출신고': '수출신고서 문의',
            '원산지': '원산지증명 문의',
            'FTA': 'FTA 특혜관세 문의',
            '관세': '관세 계산 문의',
            '통관': '통관 절차 문의',
            '검역': '검역 절차 문의',
            '신고서': '신고서 작성 문의',
            '서류': '필요서류 문의'
        }
        
        # 키워드가 포함된 경우 매핑된 제목 사용
        for keyword, title in keywords_mapping.items():
            if keyword in message:
                return title
        
        # 키워드가 없으면 원본 메시지 기반 제목 생성
        if len(message) > max_length:
            title = message[:max_length-3] + "..."
        else:
            title = message
            
        return title
    
    @staticmethod
    def extract_keywords(content: str, max_keywords: int = 5) -> List[str]:
        """메시지 내용에서 키워드 추출 (간단한 버전)"""
        import re
        
        # 한글, 영문 단어 추출
        words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}', content)
        
        # 빈도 계산 및 상위 키워드 반환
        from collections import Counter
        word_counts = Counter(words)
        
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    @staticmethod
    def calculate_conversation_stats(messages: List[MessageORM]) -> Dict[str, Any]:
        """대화 통계 계산"""
        if not messages:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "agents_used": [],
                "avg_response_time": 0,
                "total_references": 0
            }
        
        stats = {
            "total_messages": len(messages),
            "user_messages": sum(1 for msg in messages if msg.role == MessageRole.USER),
            "assistant_messages": sum(1 for msg in messages if msg.role == MessageRole.ASSISTANT),
            "agents_used": list(set(msg.agent_used for msg in messages if msg.agent_used)),
            "total_references": sum(len(msg.references or []) for msg in messages)
        }
        
        # 평균 응답 시간 계산 (간단한 버전)
        response_times = []
        for i in range(1, len(messages)):
            if messages[i-1].role == MessageRole.USER and messages[i].role == MessageRole.ASSISTANT:
                time_diff = (messages[i].timestamp - messages[i-1].timestamp).total_seconds()
                response_times.append(time_diff)
        
        stats["avg_response_time"] = sum(response_times) / len(response_times) if response_times else 0
        
        return stats


# 검증 함수
class ConversationValidator:
    """대화 데이터 검증"""
    
    @staticmethod
    def validate_message_content(content: str) -> bool:
        """메시지 내용 검증"""
        if not content or not content.strip():
            return False
        
        if len(content) > 10000:  # 최대 10KB
            return False
        
        return True
    
    @staticmethod
    def validate_conversation_title(title: str) -> bool:
        """대화 제목 검증"""
        if not title or not title.strip():
            return False
        
        if len(title) > 200:
            return False
        
        return True
    
    @staticmethod
    def validate_user_permission(user_id: int, conversation: ConversationORM) -> bool:
        """사용자 권한 검증"""
        return conversation.user_id == user_id