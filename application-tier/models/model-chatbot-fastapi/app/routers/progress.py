"""
진행상황 스트리밍 라우터
실시간으로 AI 답변 생성 과정을 클라이언트에 전송
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from datetime import datetime

logger = logging.getLogger(__name__)

# 진행상황 스트리밍을 위한 글로벌 관리자
class ProgressManager:
    def __init__(self):
        # 활성 연결들을 추적
        self.active_connections: Set[str] = set()
        # 대화별 진행상황 큐
        self.progress_queues: Dict[str, asyncio.Queue] = {}
    
    async def add_connection(self, conversation_id: str) -> asyncio.Queue:
        """새 진행상황 연결 추가"""
        self.active_connections.add(conversation_id)
        self.progress_queues[conversation_id] = asyncio.Queue()
        logger.info(f"📡 Progress connection added: {conversation_id} (총 {len(self.active_connections)}개 연결)")
        return self.progress_queues[conversation_id]
    
    async def remove_connection(self, conversation_id: str):
        """진행상황 연결 제거"""
        self.active_connections.discard(conversation_id)
        if conversation_id in self.progress_queues:
            del self.progress_queues[conversation_id]
        logger.info(f"🔌 Progress connection removed: {conversation_id} (남은 연결: {len(self.active_connections)}개)")
    
    async def send_progress(self, conversation_id: str, step: str, message: str, details: str = ""):
        """특정 대화에 진행상황 전송"""
        if conversation_id in self.progress_queues:
            progress_data = {
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "step": step,
                "message": message,
                "details": details
            }
            try:
                await self.progress_queues[conversation_id].put(progress_data)
                logger.debug(f"📊 Progress sent: {conversation_id} - {step}")
            except Exception as e:
                logger.error(f"❌ Failed to send progress: {e}")

# 글로벌 진행상황 관리자 인스턴스
progress_manager = ProgressManager()

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])

@router.get("/stream/{conversation_id}")
async def stream_progress(conversation_id: str, request: Request):
    """
    대화별 진행상황 실시간 스트리밍
    
    Server-Sent Events를 사용하여 AI 답변 생성 과정을 실시간으로 전송합니다.
    
    Args:
        conversation_id: 추적할 대화 ID
        
    Returns:
        StreamingResponse: SSE 형식의 진행상황 스트림
    """
    
    async def generate():
        """진행상황 데이터 생성기"""
        logger.info(f"🚀 SSE 스트림 시작: {conversation_id}")
        # 연결 추가
        queue = await progress_manager.add_connection(conversation_id)
        
        try:
            # 연결 시작 알림
            start_data = {
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "step": "연결",
                "message": "진행상황 추적을 시작합니다",
                "details": ""
            }
            yield f"data: {json.dumps(start_data, ensure_ascii=False)}\n\n"
            
            # 진행상황 데이터 스트리밍
            while True:
                try:
                    # 클라이언트 연결 상태 확인
                    if await request.is_disconnected():
                        logger.info(f"🔌 클라이언트 연결 끊김: {conversation_id}")
                        break
                    
                    # 큐에서 진행상황 데이터 대기 (타임아웃 5초)
                    progress_data = await asyncio.wait_for(queue.get(), timeout=5.0)
                    yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"
                    
                except asyncio.TimeoutError:
                    # 연결 유지를 위한 heartbeat
                    heartbeat = {
                        "timestamp": datetime.now().isoformat(),
                        "conversation_id": conversation_id,
                        "step": "heartbeat",
                        "message": "연결 유지 중",
                        "details": ""
                    }
                    yield f"data: {json.dumps(heartbeat, ensure_ascii=False)}\n\n"
                    
                except Exception as e:
                    logger.error(f"❌ Stream error: {e}")
                    error_data = {
                        "timestamp": datetime.now().isoformat(),
                        "conversation_id": conversation_id,
                        "step": "오류",
                        "message": "진행상황 스트리밍 오류",
                        "details": str(e)
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    break
                    
        finally:
            # 연결 종료 시 정리
            await progress_manager.remove_connection(conversation_id)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@router.post("/send/{conversation_id}")
async def send_progress_update(
    conversation_id: str,
    step: str,
    message: str,
    details: str = ""
):
    """
    특정 대화에 진행상황 업데이트 전송
    
    내부 API로 사용되어 LangGraph 처리 과정에서 진행상황을 보고합니다.
    
    Args:
        conversation_id: 대화 ID
        step: 현재 단계
        message: 사용자 친화적 메시지
        details: 상세 정보 (선택적)
    """
    try:
        await progress_manager.send_progress(conversation_id, step, message, details)
        return {"status": "success", "conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"❌ Failed to send progress update: {e}")
        return {"status": "error", "message": str(e)}

# 다른 모듈에서 사용할 수 있도록 progress_manager 내보내기
__all__ = ["router", "progress_manager"]