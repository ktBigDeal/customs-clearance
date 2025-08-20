"""
Model-OCR 서비스 메인 실행 모듈
Azure Document Intelligence 기반 OCR 서비스
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
        port=int(os.getenv("PORT", "8080")),
        reload=True,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
