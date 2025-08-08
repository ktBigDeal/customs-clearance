"""
간단한 테스트용 FastAPI 애플리케이션
의존성 없이 기본 기능만 확인
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 간단한 FastAPI 앱
app = FastAPI(
    title="Test Chatbot Service",
    description="Simple test version without dependencies",
    version="1.0.0"
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """기본 루트 엔드포인트"""
    return {
        "message": "Test Chatbot Service is running!",
        "status": "ok",
        "port": os.getenv("PORT", "8004")
    }

@app.get("/health")
async def health_check():
    """간단한 헬스 체크"""
    return {
        "status": "healthy",
        "service": "test-chatbot",
        "version": "1.0.0"
    }

@app.post("/api/v1/conversations/chat")
async def test_chat():
    """테스트용 챗 엔드포인트"""
    return {
        "conversation_id": "test-123",
        "user_message": {
            "id": "user-1",
            "content": "Test user message",
            "role": "user",
            "timestamp": "2025-01-01T00:00:00Z"
        },
        "assistant_message": {
            "id": "assistant-1", 
            "content": "이것은 테스트 응답입니다. 서비스가 정상적으로 작동하고 있습니다!",
            "role": "assistant",
            "timestamp": "2025-01-01T00:00:01Z"
        },
        "is_new_conversation": True,
        "processing_time": 0.1
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    print(f"🚀 Starting test server on port {port}")
    
    uvicorn.run(
        "test_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # auto-reload 비활성화
        log_level="info"
    )