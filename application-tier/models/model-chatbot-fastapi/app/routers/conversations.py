"""
대화기록 관리 API 라우터
RESTful API를 통한 대화 세션 및 메시지 관리
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import logging

from ..services.conversation_service import ConversationService
from ..models.conversation import (
    ConversationCreate, ConversationDetail, ConversationSummary,
    MessageCreate, MessageResponse, ConversationListResponse,
    ConversationSearchRequest, ConversationSearchResponse,
    MessageListResponse, ConversationUpdate
)
from ..core.database import get_database_manager, DatabaseManager


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])
security = HTTPBearer(auto_error=False)


# Request/Response 모델들
class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str = Field(..., min_length=1, max_length=10000, description="사용자 메시지")
    conversation_id: Optional[str] = Field(None, description="기존 대화 ID (새 대화시 null)")
    include_history: bool = Field(True, description="이전 대화 컨텍스트 포함 여부")
    user_id: int = Field(..., description="사용자 ID")


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    is_new_conversation: bool


class ConversationCreateRequest(BaseModel):
    """대화 생성 요청"""
    user_id: int
    title: Optional[str] = None
    initial_message: Optional[str] = None


# 의존성 주입
async def get_conversation_service(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> ConversationService:
    """대화 서비스 의존성 주입"""
    service = ConversationService(db_manager)
    await service.initialize()
    return service


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> int:
    """
    현재 사용자 ID 추출 
    실제 구현에서는 presentation-tier/backend와 JWT 토큰 검증 연동 필요
    """
    # TODO: presentation-tier/backend의 JWT 토큰 검증 로직과 연동
    # 현재는 테스트용으로 하드코딩
    if not credentials:
        # 개발/테스트 모드: 기본 사용자
        return 1
    
    try:
        # JWT 토큰에서 사용자 ID 추출하는 로직 구현 필요
        # 예: jwt.decode(credentials.credentials, secret_key, algorithms=["HS256"])
        return 1  # 임시
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


# 메인 API 엔드포인트들
@router.post("/", response_model=ConversationDetail, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreateRequest,
    service: ConversationService = Depends(get_conversation_service),
    current_user: int = Depends(get_current_user_id)
):
    """
    새 대화 세션 생성
    
    - **user_id**: 사용자 ID
    - **title**: 대화 제목 (선택적)
    - **initial_message**: 첫 메시지 (선택적)
    """
    try:
        # 권한 확인 (자신의 대화만 생성 가능)
        if request.user_id != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create conversations for yourself"
            )
        
        conversation = await service.create_conversation(
            user_id=request.user_id,
            initial_message=request.initial_message
        )
        
        return conversation
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_langgraph(
    request: ChatRequest,
    service: ConversationService = Depends(get_conversation_service),
    current_user: int = Depends(get_current_user_id)
):
    """
    LangGraph 오케스트레이터와 통합된 채팅
    
    - **message**: 사용자 메시지
    - **conversation_id**: 기존 대화 ID (새 대화시 null)
    - **include_history**: 이전 대화 컨텍스트 포함 여부
    - **user_id**: 사용자 ID
    """
    try:
        # 권한 확인
        if request.user_id != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only chat as yourself"
            )
        
        is_new_conversation = False
        conversation_id = request.conversation_id
        
        # 새 대화 생성
        if not conversation_id:
            conversation = await service.create_conversation(
                user_id=request.user_id,
                initial_message=request.message
            )
            conversation_id = conversation.id
            is_new_conversation = True
        
        # LangGraph 오케스트레이터 가져오기 (임시 - 실제로는 의존성 주입 필요)
        from src.rag.langgraph_factory import create_orchestrated_system
        langgraph_orchestrator = create_orchestrated_system()
        
        # 메시지 처리
        user_msg, assistant_msg = await service.add_message_with_langgraph_integration(
            conversation_id=conversation_id,
            user_message=request.message,
            user_id=request.user_id,
            langgraph_orchestrator=langgraph_orchestrator,
            include_history=request.include_history
        )
        
        return ChatResponse(
            conversation_id=conversation_id,
            user_message=user_msg,
            assistant_message=assistant_msg,
            is_new_conversation=is_new_conversation
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat processing failed"
        )


@router.get("/", response_model=ConversationListResponse)
async def get_user_conversations(
    limit: int = Query(20, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="페이지 오프셋"),
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    사용자의 대화 목록 조회
    
    - **limit**: 페이지 크기 (1-100)
    - **offset**: 페이지 오프셋
    """
    try:
        return await service.get_user_conversations(
            user_id=current_user,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations"
        )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str = Path(..., description="대화 세션 ID"),
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    특정 대화 세션 상세 조회
    
    - **conversation_id**: 대화 세션 ID
    """
    try:
        # TODO: 실제 구현에서는 service.get_conversation_detail 메서드 필요
        conversations = await service.get_user_conversations(user_id=current_user, limit=1000)
        
        for conv in conversations.conversations:
            if conv.id == conversation_id:
                # 상세 정보 구성 (임시)
                return ConversationDetail(
                    id=conv.id,
                    user_id=current_user,
                    title=conv.title,
                    message_count=conv.message_count,
                    last_agent_used=conv.last_agent_used,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    is_active=conv.is_active,
                    metadata={},
                    recent_messages=[]
                )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str = Path(..., description="대화 세션 ID"),
    limit: int = Query(50, ge=1, le=200, description="메시지 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    대화 세션의 메시지 기록 조회
    
    - **conversation_id**: 대화 세션 ID
    - **limit**: 조회할 메시지 수 (1-200)
    - **offset**: 메시지 오프셋
    """
    try:
        messages = await service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=current_user,
            limit=limit,
            offset=offset
        )
        
        # TODO: 전체 메시지 수 조회 로직 추가
        total_count = len(messages)  # 임시
        
        return MessageListResponse(
            messages=messages,
            total_count=total_count,
            page=offset // limit + 1,
            page_size=limit,
            has_next=len(messages) == limit
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.post("/search", response_model=ConversationSearchResponse)
async def search_conversations(
    request: ConversationSearchRequest,
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    대화 전문검색 (PostgreSQL GIN 인덱스 활용)
    
    - **query**: 검색 쿼리
    - **agent_type**: 에이전트 타입 필터 (선택적)
    - **start_date**: 시작 날짜 (선택적)
    - **end_date**: 종료 날짜 (선택적)
    - **limit**: 결과 수 제한
    - **offset**: 페이지 오프셋
    """
    try:
        # 현재 사용자로 검색 제한
        request.user_id = current_user
        
        return await service.search_conversations(request)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.put("/{conversation_id}", response_model=ConversationDetail)
async def update_conversation(
    conversation_id: str = Path(..., description="대화 세션 ID"),
    update_data: ConversationUpdate = ...,
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    대화 세션 정보 업데이트
    
    - **conversation_id**: 대화 세션 ID
    - **title**: 새 제목 (선택적)
    - **is_active**: 활성 상태 (선택적)
    - **metadata**: 메타데이터 (선택적)
    """
    try:
        # TODO: service.update_conversation 메서드 구현 필요
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Update conversation not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str = Path(..., description="대화 세션 ID"),
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    대화 세션 삭제 (소프트 삭제)
    
    - **conversation_id**: 대화 세션 ID
    """
    try:
        # TODO: service.delete_conversation 메서드 구현 필요
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Delete conversation not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


# 추가 유틸리티 엔드포인트들
@router.get("/{conversation_id}/stats")
async def get_conversation_stats(
    conversation_id: str = Path(..., description="대화 세션 ID"),
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    대화 세션 통계 조회
    
    - **conversation_id**: 대화 세션 ID
    """
    try:
        # TODO: 대화 통계 조회 로직 구현
        return {
            "conversation_id": conversation_id,
            "total_messages": 0,
            "agents_used": [],
            "avg_response_time": 0.0,
            "message_per_day": 0.0
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation stats"
        )


@router.post("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str = Path(..., description="대화 세션 ID"),
    format: str = Query("json", regex="^(json|txt|pdf)$", description="내보내기 형식"),
    current_user: int = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    대화 세션 내보내기
    
    - **conversation_id**: 대화 세션 ID  
    - **format**: 내보내기 형식 (json, txt, pdf)
    """
    try:
        # TODO: 대화 내보내기 로직 구현
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Export conversation not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export conversation"
        )