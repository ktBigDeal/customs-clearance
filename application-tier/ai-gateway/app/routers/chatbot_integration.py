"""
AI Gateway - 챗봇 통합 라우터

model-chatbot-fastapi 서비스와의 통합을 담당하는 라우터입니다.
RAG 기반 관세법 전문 상담 서비스를 AI Gateway를 통해 제공합니다.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
import httpx
import logging

from ..core.config import get_settings
from ..core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


class ChatRequest(BaseModel):
    """챗봇 대화 요청 모델"""
    message: str = Field(..., description="사용자 메시지", min_length=1, max_length=1000)
    user_id: Optional[int] = Field(None, description="사용자 ID")
    conversation_id: Optional[str] = Field(None, description="대화 세션 ID")
    include_history: bool = Field(True, description="대화 히스토리 포함 여부")


class ChatResponse(BaseModel):
    """챗봇 대화 응답 모델"""
    conversation_id: str = Field(..., description="대화 세션 ID")
    user_message: Dict[str, Any] = Field(..., description="사용자 메시지 정보")
    assistant_message: Dict[str, Any] = Field(..., description="AI 응답 정보")
    is_new_conversation: bool = Field(..., description="새로운 대화 여부")
    processing_time: Optional[float] = Field(None, description="처리 시간(초)")


class ConversationHistoryResponse(BaseModel):
    """대화 히스토리 응답 모델"""
    conversation_id: str = Field(..., description="대화 세션 ID")
    messages: List[Dict[str, Any]] = Field(..., description="메시지 목록")
    total_messages: int = Field(..., description="총 메시지 수")
    created_at: Optional[str] = Field(None, description="대화 시작 시간")


class ConversationListResponse(BaseModel):
    """사용자 대화 목록 응답 모델"""
    conversations: List[Dict[str, Any]] = Field(..., description="대화 목록")
    total_conversations: int = Field(..., description="총 대화 수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 항목 수")


async def get_chatbot_service_url() -> str:
    """챗봇 서비스 URL 반환"""
    return settings.MODEL_CHATBOT_URL


@router.post("/chat", response_model=ChatResponse)
async def chat_with_legal_expert(
    request: ChatRequest,
    service_url: str = Depends(get_chatbot_service_url)
):
    """
    RAG 기반 관세법 전문 상담
    
    LangGraph와 ChromaDB를 활용한 지능형 관세법 상담 서비스입니다.
    사용자의 질의를 분석하여 적절한 전문 에이전트(법률, 무역규제, 상담사례)로 
    자동 라우팅하고 정확한 답변을 제공합니다.
    
    Args:
        request: 챗봇 대화 요청 정보
        
    Returns:
        ChatResponse: AI 응답 및 대화 메타데이터
        
    Raises:
        HTTPException: 챗봇 서비스 오류 시
    """
    try:
        logger.info(f"Processing chat request: user_id={request.user_id}, conversation_id={request.conversation_id}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # RAG 처리 시간 고려
            payload = {
                "message": request.message,
                "user_id": request.user_id or 1,  # 기본값 1
                "conversation_id": request.conversation_id,
                "include_history": request.include_history
            }
            
            response = await client.post(
                f"{service_url}/api/v1/conversations/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Chat completed successfully: conversation_id={result.get('conversation_id')}")
                return ChatResponse(**result)
            
            # 오류 응답 처리
            error_detail = response.text if response.text else "Unknown error"
            logger.error(f"Chatbot service error: {response.status_code} - {error_detail}")
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Chatbot service error: {error_detail}"
            )
            
    except httpx.TimeoutException:
        logger.error("Chatbot service timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Chatbot service timeout. Please try again."
        )
    except httpx.ConnectError:
        logger.error(f"Failed to connect to chatbot service: {service_url}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot service is currently unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during chat processing"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    service_url: str = Depends(get_chatbot_service_url)
):
    """
    대화 세션 히스토리 조회
    
    특정 대화 세션의 메시지 히스토리를 조회합니다.
    페이지네이션을 지원하여 대용량 대화도 효율적으로 처리할 수 있습니다.
    
    Args:
        conversation_id: 대화 세션 ID
        limit: 조회할 메시지 수 (기본값: 50)
        offset: 시작 오프셋 (기본값: 0)
        
    Returns:
        ConversationHistoryResponse: 대화 히스토리 정보
    """
    try:
        logger.info(f"Fetching conversation history: {conversation_id}, limit={limit}, offset={offset}")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{service_url}/api/v1/conversations/{conversation_id}/messages",
                params={"limit": limit, "offset": offset}
            )
            
            if response.status_code == 200:
                result = response.json()
                return ConversationHistoryResponse(**result)
            
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {conversation_id} not found"
                )
            
            else:
                error_detail = response.text if response.text else "Unknown error"
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch conversation history: {error_detail}"
                )
                
    except httpx.TimeoutException:
        logger.error("Timeout fetching conversation history")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout fetching conversation history"
        )
    except httpx.ConnectError:
        logger.error(f"Failed to connect to chatbot service: {service_url}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot service is currently unavailable"
        )
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Unexpected error fetching conversation history: {str(e)}")
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=[],
            total_messages=0,
            created_at=None
        )


@router.get("/conversations/user/{user_id}", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: int,
    page: int = 1,
    limit: int = 10,
    service_url: str = Depends(get_chatbot_service_url)
):
    """
    사용자별 대화 목록 조회
    
    특정 사용자의 모든 대화 세션 목록을 조회합니다.
    최근 대화부터 정렬되어 반환됩니다.
    
    Args:
        user_id: 사용자 ID
        page: 페이지 번호 (기본값: 1)
        limit: 페이지당 항목 수 (기본값: 10)
        
    Returns:
        ConversationListResponse: 사용자 대화 목록
    """
    try:
        logger.info(f"Fetching conversations for user: {user_id}, page={page}, limit={limit}")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{service_url}/api/v1/conversations/",
                params={
                    "user_id": user_id,
                    "page": page,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return ConversationListResponse(**result)
            
            else:
                error_detail = response.text if response.text else "Unknown error"
                logger.error(f"Failed to fetch user conversations: {error_detail}")
                return ConversationListResponse(
                    conversations=[],
                    total_conversations=0,
                    page=page,
                    limit=limit
                )
                
    except httpx.TimeoutException:
        logger.error("Timeout fetching user conversations")
        return ConversationListResponse(
            conversations=[],
            total_conversations=0,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching user conversations: {str(e)}")
        return ConversationListResponse(
            conversations=[],
            total_conversations=0,
            page=page,
            limit=limit
        )


@router.post("/conversations/search")
async def search_conversations(
    query: str,
    user_id: Optional[int] = None,
    limit: int = 20,
    service_url: str = Depends(get_chatbot_service_url)
):
    """
    대화 내용 검색
    
    PostgreSQL 전문검색을 활용하여 대화 내용을 검색합니다.
    한국어 형태소 분석을 지원하여 정확한 검색 결과를 제공합니다.
    
    Args:
        query: 검색 쿼리
        user_id: 특정 사용자로 검색 제한 (선택적)
        limit: 검색 결과 수 제한
        
    Returns:
        Dict: 검색 결과 목록
    """
    try:
        logger.info(f"Searching conversations: query='{query}', user_id={user_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:  # 검색은 시간이 걸릴 수 있음
            response = await client.post(
                f"{service_url}/api/v1/conversations/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                return response.json()
            
            else:
                error_detail = response.text if response.text else "Unknown error"
                logger.error(f"Search failed: {error_detail}")
                return {
                    "results": [],
                    "total": 0,
                    "query": query,
                    "error": error_detail
                }
                
    except Exception as e:
        logger.error(f"Error during conversation search: {str(e)}")
        return {
            "results": [],
            "total": 0,
            "query": query,
            "error": str(e)
        }


@router.get("/health")
async def health_check(service_url: str = Depends(get_chatbot_service_url)):
    """
    챗봇 서비스 헬스 체크
    
    model-chatbot-fastapi 서비스의 상태를 확인합니다.
    
    Returns:
        Dict: 서비스 상태 정보
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "status": "healthy",
                    "service": "model-chatbot-fastapi",
                    "url": service_url,
                    "response_time": response.elapsed.total_seconds(),
                    "details": health_data
                }
            else:
                return {
                    "status": "unhealthy",
                    "service": "model-chatbot-fastapi", 
                    "url": service_url,
                    "error": f"HTTP {response.status_code}"
                }
                
    except httpx.ConnectError:
        return {
            "status": "unreachable",
            "service": "model-chatbot-fastapi",
            "url": service_url,
            "error": "Connection failed"
        }
    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "service": "model-chatbot-fastapi",
            "url": service_url,
            "error": "Request timeout"
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "model-chatbot-fastapi",
            "url": service_url,
            "error": str(e)
        }