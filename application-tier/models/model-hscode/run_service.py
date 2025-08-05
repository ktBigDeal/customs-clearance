
"""
HS Code 변환 API 서비스 실행 스크립트

이 스크립트는 HS Code 변환 FastAPI 서비스를 실행합니다.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """HS Code 변환 API 서비스 실행"""
    
    # 현재 디렉토리를 model-hscode로 설정
    current_dir = Path(__file__).parent
    os.chdir(current_dir)
    
    print("🚀 HS Code 변환 API 서비스 시작 중...")
    print(f"📁 작업 디렉토리: {current_dir}")
    print("🌐 서비스 URL: http://localhost:8003")
    print("📚 API 문서: http://localhost:8003/docs")
    print("-" * 50)
    
    try:
        # uvicorn으로 FastAPI 서비스 실행
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8003",
            "--reload",
            "--log-level", "info"
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 서비스가 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서비스 실행 중 오류 발생: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()