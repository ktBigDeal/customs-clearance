"""
Model-Report 서비스 메인 실행 모듈
LangChain 기반 관세신고서 생성 서비스
"""

import uvicorn
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def main():
    """메인 실행 함수"""
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8002")),
        reload=True,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
