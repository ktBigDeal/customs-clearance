#!/usr/bin/env python3
"""
HS 코드 추천 API 서버 실행 스크립트
"""
import sys
import os
from pathlib import Path

# 현재 디렉토리와 src 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "src"))

# 환경변수도 설정
os.environ.setdefault("PYTHONPATH", f"{current_dir}/src:{current_dir}")

print("🚀 HS 코드 추천 API 서버 시작 중...")
print("📂 현재 디렉토리:", current_dir)
print("🐍 Python Path:", sys.path[:3])

try:
    # 직접 app을 import
    from app.main import app
    print("✅ 앱 모듈 로드 성공")
    
    import uvicorn
    print("📖 API 문서: http://localhost:8003/docs")
    
    uvicorn.run(
        app,  # 문자열 대신 직접 앱 객체 전달
        host="0.0.0.0",
        port=8003,
        reload=False,  # reload 비활성화
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("🔍 사용 가능한 모듈 확인:")
    import os
    for item in os.listdir(current_dir):
        if os.path.isdir(os.path.join(current_dir, item)):
            print(f"  📁 {item}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 서버 실행 실패: {e}")
    sys.exit(1)