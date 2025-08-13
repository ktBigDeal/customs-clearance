from src.hs_recommender import HSCodeRecommender
from config import SYSTEM_CONFIG
from pathlib import Path
import os

def print_system_info(recommender: HSCodeRecommender):
    """시스템 정보 출력 (final_combined_text 구조 정보 포함)"""
    stats = recommender.get_statistics()
    
    print("\n" + "="*80)
    print("시스템 정보")
    print("="*80)
    
    print(f"초기화 상태: {'완료' if stats['system_initialized'] else '미완료'}")
    print(f"OpenAI 사용 가능: {'예' if stats['openai_available'] else '아니오'}")
    print(f"의미 모델: {stats['semantic_model']}")
    print(f"캐시 디렉토리: {stats['cache_dir']}")
    
    if 'total_items' in stats:
        print(f"총 항목 수: {stats['total_items']:,}개")
        print(f"HS 챕터 수: {stats.get('chapters', 0)}개")
        
        # 🔍 데이터 구조 정보
        cache_info = stats.get('cache_info', {})
        if 'actual_structure' in cache_info:
            structure = cache_info['actual_structure']
            print(f"데이터 구조:")
            print(f"  - final_combined_text 컬럼: {'✅' if structure.get('has_final_combined_text') else '❌'}")
            if 'key_columns' in structure:
                key_cols = structure['key_columns']
                print(f"  - 핵심 컬럼:")
                for col, exists in key_cols.items():
                    print(f"    * {col}: {'✅' if exists else '❌'}")
        
        if 'data_sources' in stats:
            print("데이터 소스별 분포:")
            for source, count in stats['data_sources'].items():
                print(f"  - {source}: {count:,}개")
        
        if 'standard_coverage' in stats:
            print(f"표준품명 커버리지: {stats['standard_coverage']:.1f}%")
    
    # 캐시 정보
    cache_info = stats.get('cache_info', {})
    if cache_info:
        print(f"캐시 상태: {'유효' if cache_info['cache_valid'] else '무효'}")
        if cache_info.get('total_size_mb'):
            print(f"캐시 크기: {cache_info['total_size_mb']:.1f} MB")
        
        # 캐시 버전 정보
        metadata = cache_info.get('metadata', {})
        if metadata:
            cache_version = metadata.get('cache_version', '알 수 없음')
            print(f"캐시 버전: {cache_version}")
            
            # 데이터 구조 정보 (메타데이터에서)
            if 'data_structure' in metadata:
                data_struct = metadata['data_structure']
                print(f"캐시된 데이터 구조:")
                print(f"  - final_combined_text 지원: {'✅' if data_struct.get('has_final_combined_text') else '❌'}")
                if 'text_quality' in data_struct:
                    text_qual = data_struct['text_quality']
                    print(f"  - 평균 텍스트 길이: {text_qual.get('avg_length', 0):.1f}자")
                    print(f"  - 빈 텍스트: {text_qual.get('empty_count', 0)}개")
    
    print("="*80)

def print_help():
    """도움말 출력"""
    print("\n사용 가능한 명령어:")
    print("  - 'help' 또는 '?': 이 도움말 표시")
    print("  - 'info': 시스템 정보 확인")
    print("  - 'cache_info': 캐시 상세 정보")
    print("  - 'clear_cache': 캐시 삭제")
    print("  - 'rebuild_cache': 캐시 강제 재구축")
    print("  - 'stats': 상세 통계")
    print("  - 'quit' 또는 'exit': 프로그램 종료")
    print("  - 상품명 입력: HS 코드 추천")
    print("\n추천 옵션:")
    print("  - 재질과 용도를 함께 입력하면 더 정확한 결과를 얻을 수 있습니다")
    print("  - OpenAI가 활성화된 경우 더 정교한 분석을 제공합니다")
    print("\n데이터 구조:")
    print("  - 이 버전은 final_combined_text 기반으로 작동합니다")
    print("  - HSK 분류 데이터 중심으로 HS 코드 및 표준품명 데이터가 통합됩니다")

def handle_cache_commands(recommender: HSCodeRecommender, command: str) -> bool:
    """캐시 관련 명령어 처리 (final_combined_text 정보 포함)"""
    if command == 'cache_info':
        cache_info = recommender.get_cache_info()
        print("\n캐시 상세 정보:")
        print(f"  디렉토리: {cache_info['cache_dir']}")
        print(f"  유효성: {'유효' if cache_info['cache_valid'] else '무효'}")
        
        if cache_info.get('file_sizes'):
            print("  파일별 크기:")
            for file_key, size in cache_info['file_sizes'].items():
                print(f"    - {file_key}: {size}")
        
        if cache_info.get('metadata'):
            metadata = cache_info['metadata']
            print("  메타데이터:")
            print(f"    - 생성일: {metadata.get('created_at', '알 수 없음')}")
            print(f"    - 모델: {metadata.get('model_name', '알 수 없음')}")
            print(f"    - 버전: {metadata.get('cache_version', '알 수 없음')}")
            print(f"    - 총 항목: {metadata.get('total_items', 0):,}개")
            
            # 🔍 데이터 구조 정보
            if 'data_structure' in metadata:
                data_struct = metadata['data_structure']
                print(f"  데이터 구조:")
                print(f"    - 컬럼 수: {data_struct.get('columns', 0)}개")
                print(f"    - final_combined_text 지원: {'✅' if data_struct.get('has_final_combined_text') else '❌'}")
                
                if 'text_quality' in data_struct:
                    text_qual = data_struct['text_quality']
                    print(f"    - 평균 텍스트 길이: {text_qual.get('avg_length', 0):.1f}자")
                    print(f"    - 빈 텍스트: {text_qual.get('empty_count', 0)}개")
        
        # 실제 캐시된 데이터 구조 확인
        if cache_info.get('actual_structure'):
            actual = cache_info['actual_structure']
            print("  실제 캐시 구조:")
            print(f"    - 레코드 수: {actual.get('total_records', 0):,}개")
            print(f"    - 컬럼 수: {actual.get('total_columns', 0)}개")
            print(f"    - final_combined_text: {'✅' if actual.get('has_final_combined_text') else '❌'}")
            
            if 'key_columns' in actual:
                print(f"    - 핵심 컬럼:")
                for col, exists in actual['key_columns'].items():
                    print(f"      * {col}: {'✅' if exists else '❌'}")
        
        return True
    
    elif command == 'clear_cache':
        confirm = input("정말로 캐시를 삭제하시겠습니까? (y/N): ").lower()
        if confirm.startswith('y'):
            deleted_count = recommender.clear_cache()
            print(f"캐시 삭제 완료: {deleted_count}개 파일")
        else:
            print("캐시 삭제 취소")
        return True
    
    elif command == 'rebuild_cache':
        confirm = input("캐시를 강제로 재구축하시겠습니까? (데이터 로딩 시간이 소요됩니다) (y/N): ").lower()
        if confirm.startswith('y'):
            print("캐시 재구축 중...")
            try:
                success = recommender.load_data(force_rebuild=True)
                if success:
                    print("✅ 캐시 재구축 완료!")
                    print_system_info(recommender)
                else:
                    print("❌ 캐시 재구축 실패")
            except Exception as e:
                print(f"❌ 캐시 재구축 중 오류: {e}")
        else:
            print("캐시 재구축 취소")
        return True
    
    return False

def setup_colab_cache(recommender: HSCodeRecommender) -> bool:
    """코랩 캐시 설정 (final_combined_text 지원 확인)"""
    cache_info = recommender.get_cache_info()
    
    if not cache_info['cache_valid']:
        print("현재 캐시가 무효합니다.")
        
        # 캐시 무효 이유 확인
        if cache_info.get('actual_structure'):
            actual = cache_info['actual_structure']
            if not actual.get('has_final_combined_text'):
                print("⚠️ 기존 캐시는 final_combined_text를 지원하지 않습니다.")
                print("   새로운 데이터 구조로 업그레이드가 필요합니다.")
        
        use_colab = input("코랩에서 생성한 캐시를 사용하시겠습니까? (y/N): ").lower()
        
        if use_colab.startswith('y'):
            colab_cache_dir = input("코랩 캐시 디렉토리 경로를 입력하세요: ").strip()
            if colab_cache_dir:
                success = recommender.copy_cache_from_colab(colab_cache_dir)
                if success:
                    print("코랩 캐시 복사 완료!")
                    
                    # 복사된 캐시 검증
                    new_cache_info = recommender.get_cache_info()
                    if new_cache_info.get('actual_structure', {}).get('has_final_combined_text'):
                        print("✅ final_combined_text 지원 캐시입니다.")
                        return True
                    else:
                        print("⚠️ 복사된 캐시도 이전 버전입니다. 데이터를 새로 로드합니다.")
                        return False
                else:
                    print("코랩 캐시 복사 실패")
    
    return False

def validate_system_requirements(recommender: HSCodeRecommender) -> bool:
    """시스템 요구사항 검증"""
    print("시스템 요구사항 검증 중...")
    
    # 데이터 파일 존재 확인
    from config import FILE_PATHS
    missing_files = []
    
    for file_key, file_path in FILE_PATHS.items():
        import os
        if not os.path.exists(file_path):
            missing_files.append(f"{file_key}: {file_path}")
    
    if missing_files:
        print("❌ 필수 데이터 파일이 없습니다:")
        for missing in missing_files:
            print(f"   - {missing}")
        print("\n해결 방법:")
        print("   1. config.py에서 파일 경로를 확인하세요")
        print("   2. 데이터 파일이 올바른 위치에 있는지 확인하세요")
        return False
    
    print("✅ 모든 데이터 파일 확인됨")
    
    # 캐시 디렉토리 쓰기 권한 확인
    try:
        cache_info = recommender.get_cache_info()
        cache_dir = cache_info['cache_dir']
        
        import os
        test_file = os.path.join(cache_dir, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"✅ 캐시 디렉토리 쓰기 권한 확인: {cache_dir}")
    except Exception as e:
        print(f"❌ 캐시 디렉토리 쓰기 권한 없음: {e}")
        return False
    
    return True

def get_search_input() -> tuple:
    """검색 입력 받기 (개선된 UI)"""
    query = input("\n상품명을 입력하세요: ").strip()
    
    if not query:
        return None, None, None
    
    # 추가 정보 입력 (선택사항)
    print("추가 정보 입력 (선택사항, Enter로 건너뛰기):")
    material = input("  재질 (예: 플라스틱, 금속, 유리 등): ").strip()
    usage = input("  용도 (예: 의료용, 산업용, 가정용 등): ").strip()
    
    return query, material, usage

def main():
    """메인 함수 (final_combined_text 지원)"""
    print("="*80)
    print("HS 코드 추천 시스템 v2.1")
    print("="*80)
    print("final_combined_text 기반 데이터 통합 버전")
    print("HSK 분류 데이터 중심, 23개 필드 정확 추출")
    print("="*80)
    
    # 추천 시스템 초기화
    project_root = Path(__file__).parent.parent
    cache_dir = project_root /"model-hscode"/"cache"/ "hs_code_cache"
    recommender = HSCodeRecommender(
        semantic_model_name=SYSTEM_CONFIG['semantic_model'],
        top_k=SYSTEM_CONFIG['top_k'],
        cache_dir=cache_dir
    )
    
    # 시스템 요구사항 검증
    if not validate_system_requirements(recommender):
        print("\n시스템 요구사항을 만족하지 않습니다. 프로그램을 종료합니다.")
        return
    
    # 코랩 캐시 설정 확인
    setup_colab_cache(recommender)
    
    # 데이터 로드
    print("\n데이터 로딩 중...")
    force_rebuild = False
    
    # 캐시 상태 미리 확인
    cache_info = recommender.get_cache_info()
    if not cache_info['cache_valid']:
        print("⚠️ 캐시가 무효하거나 없습니다.")
        
        # 이전 버전 캐시인지 확인
        if cache_info.get('actual_structure') and not cache_info['actual_structure'].get('has_final_combined_text'):
            print("⚠️ 이전 버전 캐시 감지 - 새로운 구조로 업그레이드 필요")
            force_rebuild = True
        
        rebuild_choice = input("데이터를 새로 로드하시겠습니까? (권장) (Y/n): ").lower()
        if rebuild_choice != 'n':
            force_rebuild = True
    
    if not recommender.load_data(force_rebuild=force_rebuild):
        print("데이터 로드 실패. 프로그램을 종료합니다.")
        return
    
    # 시스템 정보 출력
    print_system_info(recommender)
    
    # 데이터 로드 성공 확인
    stats = recommender.get_statistics()
    if not stats.get('system_initialized'):
        print("❌ 시스템 초기화에 실패했습니다.")
        return
    
    # OpenAI 초기화 (자동)
    print("\nOpenAI API 초기화 중...")
    openai_available = recommender.initialize_openai()
    
    if openai_available:
        print("✓ OpenAI LLM 분석이 활성화되었습니다.")
        print("  🧠  LLM 통합 추천 시스템을 사용합니다.")
    else:
        print("✗ OpenAI 초기화 실패. 기본 검색만 사용됩니다.")
        print("  📝 docs/Aivle-api.txt 파일을 확인하거나 API 키를 설정해주세요.")
    
    print("\n" + "="*80)
    print("HS 코드 추천 시스템이 준비되었습니다!")
    print("'help' 또는 '?'를 입력하면 사용법을 확인할 수 있습니다.")
    print("final_combined_text 기반으로 더욱 정확한 검색을 제공합니다.")
    print("="*80)
    
    # 메인 루프
    while True:
        try:
            user_input = input("\n>>> ").strip()
            
            if not user_input:
                continue
            
            # 종료 명령
            if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                print("HS 코드 추천 시스템을 종료합니다.")
                break
            
            # 도움말
            elif user_input.lower() in ['help', '?', '도움말']:
                print_help()
                continue
            
            # 시스템 정보
            elif user_input.lower() in ['info', '정보']:
                print_system_info(recommender)
                continue
            
            # 상세 통계
            elif user_input.lower() in ['stats', '통계']:
                stats = recommender.get_statistics()
                print("\n상세 통계:")
                for key, value in stats.items():
                    if key != 'cache_info':  # 캐시 정보는 따로 출력
                        if isinstance(value, dict):
                            print(f"  {key}:")
                            for sub_key, sub_value in value.items():
                                print(f"    - {sub_key}: {sub_value}")
                        else:
                            print(f"  {key}: {value}")
                continue
            
            # 캐시 관련 명령
            elif handle_cache_commands(recommender, user_input.lower()):
                continue
            
            # 검색 명령으로 처리
            else:
                # 단일 입력을 상품명으로 처리
                query = user_input
                material = ""
                usage = ""
                
                # 상세 입력 모드 확인
                detailed_input = input("상세 정보를 추가로 입력하시겠습니까? (y/N): ").lower().startswith('y')
                
                if detailed_input:
                    print("추가 정보 입력 (Enter로 건너뛰기):")
                    material = input("  재질: ").strip()
                    usage = input("  용도: ").strip()
                
                # 추천 실행
                print(f"\n'{query}' 검색 중...")
                if material:
                    print(f"  재질: {material}")
                if usage:
                    print(f"  용도: {usage}")
                
                try:
                    # 추천 시스템 사용 (LLM 통합)
                    if openai_available:
                        print("🧠 LLM 통합 추천 시스템 사용...")
                        results = recommender.recommend_ultimate(
                            query=query,
                            material=material,
                            usage=usage,
                            final_count=5
                        )
                    else:
                        # 기본 추천 시스템 사용
                        results = recommender.recommend(
                            query=query,
                            material=material,
                            usage=usage,
                            use_llm=False,
                            final_count=5
                        )
                    
                    # 결과 출력
                    recommender.print_results(results, query)
                    
                    # 추천 사용시 추가 정보 출력
                    if openai_available and results.get('search_info', {}).get('method') == 'ultimate_llm_hybrid':
                        search_info = results['search_info']
                        print(f"\n🎯 LLM 통합 추천 정보:")
                        print(f"  - LLM 직접 후보: {search_info.get('llm_candidates', 0)}개")
                        print(f"  - 검색엔진 후보: {search_info.get('search_candidates', 0)}개")
                        print(f"  - 최종 통합 후보: {search_info.get('total_candidates', 0)}개")
                    
                    # 추가 옵션
                    if results.get('recommendations'):
                        print("\n추가 옵션:")
                        print("  - 다른 검색어로 다시 검색")
                        print("  - 'help'로 도움말 확인")
                        print("  - 'info'로 시스템 정보 확인")
                    
                except Exception as e:
                    print(f"추천 중 오류 발생: {e}")
                    print("다시 시도해주세요.")
                    
                    # 디버그 정보 (개발 시에만)
                    import traceback
                    print(f"\n디버그 정보:")
                    print(traceback.format_exc())
        
        except KeyboardInterrupt:
            print("\n\n프로그램을 중단합니다.")
            break
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            print("계속 진행합니다...")

def quick_test():
    """빠른 테스트 함수 (final_combined_text 검증 포함)"""
    print("빠른 테스트 모드 (final_combined_text 기반)")
    
    recommender = HSCodeRecommender(cache_dir='./test_cache')
    
    if not recommender.load_data():
        print("테스트 실패: 데이터 로드 불가")
        return
    
    # 🔍 데이터 구조 검증
    stats = recommender.get_statistics()
    cache_info = stats.get('cache_info', {})
    
    if cache_info.get('actual_structure', {}).get('has_final_combined_text'):
        print("✅ final_combined_text 기반 데이터 확인됨")
    else:
        print("❌ final_combined_text 컬럼이 없습니다!")
        return
    
    # 테스트 쿼리들
    test_queries = [
        "볼트",
        "프린터 토너",
        "LED 전구",
        "플라스틱 용기",
        "컴퓨터 마우스"
    ]
    
    print(f"\n{len(test_queries)}개 테스트 쿼리 실행:")
    
    for query in test_queries:
        print(f"\n--- {query} ---")
        try:
            results = recommender.recommend(query, use_llm=False, final_count=3)
            
            if results.get('recommendations'):
                for i, rec in enumerate(results['recommendations'][:3], 1):
                    print(f"{i}. {rec['hs_code']} - {rec['name_kr']} (신뢰도: {rec['confidence']:.3f})")
                    # final_combined_text 기반 설명 출력
                    if rec.get('description'):
                        desc = rec['description'][:100] + "..." if len(rec['description']) > 100 else rec['description']
                        print(f"   설명: {desc}")
            else:
                print("결과 없음")
        except Exception as e:
            print(f"오류: {e}")
    
    print(f"\n테스트 완료!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        quick_test()
    else:
        main()