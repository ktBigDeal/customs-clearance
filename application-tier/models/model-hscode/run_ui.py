#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HS 코드 추천 시스템 UI 실행 스크립트
빠른 실행을 위한 간단한 런처
"""

import os
import sys

def main():
    """UI 실행"""
    print("=" * 60)
    print("🏢 HS 코드 추천 시스템 UI")
    print("=" * 60)
    print("🚀 Gradio UI를 시작합니다...")
    print("📱 잠시 후 브라우저에서 자동으로 열립니다")
    print("🌐 수동 접속: http://localhost:7860")
    print("=" * 60)
    
    # ui_app 모듈 임포트 및 실행
    try:
        # 현재 디렉토리를 Python 경로에 추가
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from ui_app import main as ui_main
        ui_main()
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("💡 해결 방법:")
        print("  1. 'uv sync' 명령으로 종속성을 설치해주세요")
        print("  2. 현재 작업 디렉토리가 프로젝트 루트인지 확인해주세요")
        input("Press Enter to exit...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 사용자가 프로그램을 중단했습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        print("💡 문제가 지속되면 다음을 시도해보세요:")
        print("  1. 'uv run python ui_app.py' 직접 실행")
        print("  2. 시스템 재시작 후 다시 시도")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()