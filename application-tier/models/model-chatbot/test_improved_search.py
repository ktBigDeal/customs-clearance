#!/usr/bin/env python3
"""
개선된 동식물 검색 시스템 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.unified_cli import UnifiedTradeInfoCLI
from src.utils.config import load_config

def test_improved_search():
    """개선된 동식물 검색 시스템 테스트"""
    print("🧪 개선된 동식물 검색 시스템 테스트 시작...")
    
    try:
        # 환경 설정 로드
        config = load_config()
        
        # UnifiedTradeInfoCLI 초기화
        cli = UnifiedTradeInfoCLI()
        
        # 일반 무역 정보 에이전트 초기화
        if not cli.initialize_general_info_agent():
            print("❌ 일반 무역 정보 에이전트 초기화 실패")
            return
        
        print("✅ 일반 무역 정보 에이전트 초기화 완료")
        
        # 테스트 케이스들
        test_cases = [
            "멜론은 어디서 수입해야 해?",
            "아보카도는 어느 나라에서 수입할 수 있나요?",
            "바나나 수입 가능한 국가는?",
            "레몬 수입 허용 국가를 알려주세요",
            "오렌지는 어디서 수입할 수 있어요?"
        ]
        
        print(f"\n📋 {len(test_cases)}개 테스트 케이스 실행...")
        
        for i, test_query in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"🧪 테스트 {i}: {test_query}")
            print('='*60)
            
            try:
                # 응답 생성
                response, docs = cli.general_agent.chat(test_query)
                
                print(f"\n🤖 AI 응답:")
                print("-" * 50)
                print(response)
                
                # 참조 문서 분석
                print(f"\n📊 참조된 문서 ({len(docs)}개):")
                
                animal_plant_docs = 0
                consultation_docs = 0
                other_docs = 0
                
                for j, doc in enumerate(docs, 1):
                    metadata = doc.get("metadata", {})
                    data_source = metadata.get("data_source", "")
                    data_type = metadata.get("data_type", "")
                    similarity = doc.get("similarity", 0)
                    boosted = doc.get("boosted", False)
                    
                    if data_source == "동식물허용금지지역":
                        animal_plant_docs += 1
                        icon = "🐕🌱"
                    elif data_type == "consultation_case":
                        consultation_docs += 1
                        icon = "📞"
                    else:
                        other_docs += 1
                        icon = "📄"
                    
                    boost_info = " [BOOSTED]" if boosted else ""
                    print(f"  {j}. {icon} {data_source} - 유사도: {similarity:.3f}{boost_info}")
                    
                    if data_source == "동식물허용금지지역":
                        product_name = metadata.get("product_name", "N/A")
                        allowed_countries = metadata.get("allowed_countries", [])
                        print(f"      품목: {product_name}")
                        print(f"      허용국가: {', '.join(allowed_countries) if allowed_countries else '없음'}")
                
                # 문서 타입 분포 출력
                print(f"\n📈 문서 타입 분포:")
                print(f"  🐕🌱 동식물허용금지지역: {animal_plant_docs}개")
                print(f"  📞 민원상담 사례: {consultation_docs}개")
                print(f"  📄 기타: {other_docs}개")
                
                # 성공 기준 평가
                success = animal_plant_docs > 0
                print(f"\n{'✅ 테스트 성공' if success else '❌ 테스트 실패'}: {'동식물 규제 데이터 참조됨' if success else '동식물 규제 데이터 참조되지 않음'}")
                
            except Exception as e:
                print(f"❌ 테스트 {i} 실행 중 오류: {e}")
                continue
        
        print(f"\n{'='*60}")
        print("🎉 모든 테스트 완료!")
        print('='*60)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_search()