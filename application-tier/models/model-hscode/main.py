#!/usr/bin/env python3
"""
HS Code 서비스 통합 실행 스크립트

사용법:
    uv run main.py                    # 대화형 서비스 선택
    uv run main.py recommend          # HS 코드 추천 서비스 실행 (포트 8003)
    uv run main.py convert            # US→KR HS 코드 변환 서비스 실행 (포트 8006)
    uv run main.py --help             # 도움말 표시
"""

import sys
import argparse
import subprocess
from pathlib import Path


def show_menu():
    """서비스 선택 메뉴 표시"""
    print("\n" + "="*70)
    print("🚀 HS Code 서비스 선택기")
    print("="*70)
    print("1. HS 코드 추천 API 서비스 (포트 8003)")
    print("   - FastAPI 기반 RESTful API")
    print("   - TF-IDF + 의미 검색 하이브리드")
    print("   - OpenAI 기반 정확도 향상")
    print("   - 웹 API 문서: http://localhost:8003/docs")
    print()
    print("2. 미국→한국 HS 코드 변환 API 서비스 (포트 8006)")
    print("   - 미국 HS 코드를 한국 HS 코드로 변환")
    print("   - LLM 강화 변환 로직")
    print("   - 관세율표 기반 정확한 매핑")
    print("   - 웹 API 문서: http://localhost:8006/docs")
    print()
    print("3. 종료")
    print("="*70)


def run_service(service_type):
    """선택된 서비스 실행"""
    project_root = Path(__file__).parent
    
    if service_type == "recommend":
        print("🚀 HS 코드 추천 API 서비스 시작 중...")
        print("📍 URL: http://localhost:8003")
        print("📚 API 문서: http://localhost:8003/docs")
        print("🔗 Redoc: http://localhost:8003/redoc")
        print("\n서버를 중지하려면 Ctrl+C를 누르세요.\n")
        
        # app/main.py 실행
        subprocess.run([
            sys.executable, str(project_root / "app" / "main.py")
        ], cwd=project_root)
        
    elif service_type == "convert":
        print("🚀 미국→한국 HS 코드 변환 API 서비스 시작 중...")
        print("📍 URL: http://localhost:8006")
        print("📚 API 문서: http://localhost:8006/docs")
        print("🔗 Redoc: http://localhost:8006/redoc")
        print("\n서버를 중지하려면 Ctrl+C를 누르세요.\n")
        
        # src/us_main.py 실행
        subprocess.run([
            sys.executable, str(project_root / "src" / "us_main.py")
        ], cwd=project_root)

    else:
        print("❌ 알 수 없는 서비스 타입:", service_type)
        sys.exit(1)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="HS Code 서비스 통합 실행 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  uv run main.py                    # 대화형 메뉴
  uv run main.py recommend          # HS 추천 API (포트 8003)
  uv run main.py convert            # HS 변환 API (포트 8006)
        """
    )
    
    parser.add_argument(
        "service", 
        nargs="?", 
        choices=["recommend", "convert", "cli"],
        help="실행할 서비스 (recommend: HS 추천 API, convert: HS 변환 API)"
    )
    
    args = parser.parse_args()
    
    # 명령행 인자가 주어진 경우 바로 실행
    if args.service:
        run_service(args.service)
        return
    
    # 대화형 메뉴
    while True:
        show_menu()
        
        try:
            choice = input("서비스를 선택하세요 (1-3): ").strip()
            
            if choice == "1":
                run_service("recommend")
                break
            elif choice == "2":
                run_service("convert")
                break
    
            elif choice == "3":
                print("👋 프로그램을 종료합니다.")
                sys.exit(0)
            else:
                print("❌ 잘못된 선택입니다. 1, 2, 또는 3를 입력하세요.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다.")
            sys.exit(0)
        except EOFError:
            print("\n\n👋 프로그램을 종료합니다.")
            sys.exit(0)


if __name__ == "__main__":
    main()