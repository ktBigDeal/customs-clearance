import os

def get_file_path(filename):
    """파일 경로를 찾아서 반환"""
    # data 폴더에서 먼저 찾기
    data_path = os.path.join("./data", filename)
    if os.path.exists(data_path):
        return data_path
    
    # 루트 디렉토리에서 찾기
    root_path = f"./{filename}"
    if os.path.exists(root_path):
        return root_path
    
    # 기본값 반환
    return data_path

FILE_PATHS = {
    'hs_codes': get_file_path("관세청_HS부호_2025.csv"),
    'standard_names': get_file_path("관세청_표준품명_20250101.xlsx"), 
    'hsk_classification': get_file_path("관세청_HSK별 신성질별_성질별 분류_20250101.xlsx")
}

# HS 코드 데이터 컬럼 설정 (보조 데이터, 5개 필드)
HS_CODE_COLUMNS = {
    'required': [
        'HS부호',           # HS 10자리 코드 (식별자)
        '한글품목명',       # 주요 검색 질의에 매칭되는 핵심 텍스트
        '영문품목명',       # 외국어 검색어 대응
        'HS부호내용',       # HS 코드 상세 설명
        '한국표준무역분류명', # 한국 기준 분류, 의미 기반 검색 확장
        '성질통합분류코드명'  # 의미 기반 분류명
    ],
    'optional': [
        '적용시작일자',     # 유효성 검사용
        '적용종료일자'      # 유효성 검사용
    ],
    'text_fields': ['한글품목명', '영문품목명', 'HS부호내용', '한국표준무역분류명', '성질통합분류코드명'],
    'id_field': 'HS부호',
    'weights': {
        '한글품목명': 3,        # 가장 높은 가중치
        '영문품목명': 2,        # 두 번째 가중치
        'HS부호내용': 2,        # 설명 정보
        '한국표준무역분류명': 1,
        '성질통합분류코드명': 1
    }
}

# 표준품명 데이터 컬럼 설정 (보조 데이터, 3개 필드)
STANDARD_NAME_COLUMNS = {
    'required': [
        'HS부호',           # HS 코드 매칭용 (또는 HS코드)
        '표준품명',         # 한글 표준품명 (핵심 필드)
        '표준품명영문',     # 영문 표준품명
        '세부분류'          # 세부 분류 정보
    ],
    'text_fields': ['표준품명', '표준품명영문', '세부분류'],
    'id_field': 'HS부호',  # 또는 'HS코드'
    'weights': {
        '표준품명': 3,         # 가장 높은 가중치
        '표준품명영문': 2,     # 두 번째 가중치
        '세부분류': 1          # 보조 정보
    }
}

# HSK 분류 데이터 컬럼 설정 (중심 데이터, 15개 필드)
HSK_CLASSIFICATION_COLUMNS = {
    # 사용하지 않을 컬럼들 (노이즈 제거)
    'exclude': [
        '년도',
        '관세청 신성질별 분류대분류코드',
        '관세청 신성질별 분류중분류코드',
        '관세청 신성질별 분류소분류코드',
        '관세청 신성질별 분류세분류코드',
        '관세청 신성질별 분류세세분류코드',
        '관세청 현행 수입 성질별 분류현행수입1단위분류코드',
        '관세청 현행 수입 성질별 분류현행수입3단위분류코드',
        '관세청 현행 수입 성질별 분류현행수입소분류코드',
        '관세청 현행 수입 성질별 분류현행수입세분류코드',
        '관세청 현행 수출 성질별 분류현행수출소분류코드',
        '관세청 현행 수출 성질별 분류현행수출세분류코드'
    ],
    
    # HS 코드 후보 컬럼들 (매핑 키 생성용)
    'hs_code_candidates': ['HS10단위부호', 'HSK부호', 'HS부호', 'HS10자리부호'],
    
    # 정의된 15개 검색 벡터 필드 (final_combined_text 생성용)
    'defined_fields': [
        # 세번 분류 (4개) - HS 계층 구조
        '세번2단위품명',   # 챕터 레벨 (2자리)
        '세번4단위품명',   # 헤딩 레벨 (4자리)  
        '세번6단위품명',   # 서브헤딩 레벨 (6자리)
        '세번10단위품명',  # 완전 분류 (10자리)
        
        # 신성질별 분류 (5개) - 관세청 신분류 체계
        '관세청 신성질별 분류대분류명',
        '관세청 신성질별 분류중분류명', 
        '관세청 신성질별 분류소분류명',
        '관세청 신성질별 분류세분류명', 
        '관세청 신성질별 분류세세분류명',
        
        # 현행 수입 성질별 분류 (4개) - 기존 수입 분류
        '관세청 현행 수입 성질별 분류현행수입1단위분류',
        '관세청 현행 수입 성질별 분류현행수입3단위분류',
        '관세청 현행 수입 성질별 분류현행수입소분류',
        '관세청 현행 수입 성질별 분류현행수입세분류',
        
        # 현행 수출 성질별 분류 (2개) - 기존 수출 분류
        '관세청 현행 수출 성질별 분류현행수출소분류',
        '관세청 현행 수출 성질별 분류현행수출세분류'
    ],
    
    # final_combined_text 생성을 위한 가중치 (중요도별)
    'weights': {
        # 세번 분류 - 구체적일수록 높은 가중치
        '세번10단위품명': 4,  # 가장 구체적
        '세번6단위품명': 3,   # 두 번째로 구체적
        '세번4단위품명': 2,   # 중간 레벨
        '세번2단위품명': 2,   # 챕터 레벨 (중요하므로 높은 가중치)
        
        # 신성질별 분류 - 세분화 정도에 따라
        '관세청 신성질별 분류세세분류명': 3,  # 가장 세분화
        '관세청 신성질별 분류세분류명': 2,   
        '관세청 신성질별 분류소분류명': 2,   
        '관세청 신성질별 분류중분류명': 1,   
        '관세청 신성질별 분류대분류명': 1,   # 가장 일반적
        
        # 현행 분류 - 보조적 정보
        '관세청 현행 수입 성질별 분류현행수입세분류': 2,
        '관세청 현행 수입 성질별 분류현행수입소분류': 2,
        '관세청 현행 수입 성질별 분류현행수입3단위분류': 1,
        '관세청 현행 수입 성질별 분류현행수입1단위분류': 1,
        '관세청 현행 수출 성질별 분류현행수출세분류': 2,
        '관세청 현행 수출 성질별 분류현행수출소분류': 2
    },
    
    # 챕터 설명 추출용 필드 (빈 텍스트 대체용)
    'chapter_desc_field': '세번2단위품명'
}

# 시스템 설정
SYSTEM_CONFIG = {
    # 의미 검색 모델 (한국어 특화)
    'semantic_model': 'jhgan/ko-sroberta-multitask',
    
    # 검색 결과 상위 개수
    'top_k': 30,
    
    # 캐시 디렉토리
    'cache_dir': './cache',
    
    # OpenAI API 키 파일
    'openai_api_file': './docs/Aivle-api.txt',
    
    # TF-IDF 벡터라이저 설정 (final_combined_text 최적화)
    'tfidf_config': {
        'analyzer': 'char_wb',      # 문자 단위 분석 (한국어 적합)
        'ngram_range': (1, 4),      # 1-4 글자 조합
        'max_features': 30000,      # 최대 특성 수
        'min_df': 1,                # 최소 문서 빈도
        'max_df': 0.85,             # 최대 문서 빈도 (너무 흔한 단어 제거)
        'use_idf': True,            # IDF 가중치 사용
        'smooth_idf': True,         # IDF 스무딩
        'sublinear_tf': True        # TF 로그 스케일링
    }
}

# 데이터 통합 설정 (final_combined_text 생성 관련)
DATA_INTEGRATION_CONFIG = {
    # 최종 텍스트 컬럼명
    'final_text_column': 'final_combined_text',
    
    # 데이터 소스 우선순위 (HSK 중심)
    'data_source_priority': [
        'hsk_main',                    # HSK만 있는 경우
        'hsk_with_hs',                # HSK + HS 코드 데이터
        'hsk_with_std',               # HSK + 표준품명 데이터
        'hsk_with_hs_with_std'        # HSK + HS 코드 + 표준품명 (최고)
    ],
    
    # 텍스트 정제 옵션
    'text_cleaning': {
        'remove_extra_spaces': True,   # 여러 공백을 하나로
        'strip_whitespace': True,      # 앞뒤 공백 제거
        'min_text_length': 1,          # 최소 텍스트 길이
        'replace_empty_with_hs': True  # 빈 텍스트를 HS 코드로 대체
    },
    
    # 빈 텍스트 대체 전략
    'empty_text_replacement': {
        'use_chapter_description': True,  # 챕터 설명 사용
        'use_hs_key': True,              # HS_KEY 사용
        'fallback_text': 'unknown_item'   # 최종 대체 텍스트
    }
}

# 검색 엔진 설정 (final_combined_text 최적화)
SEARCH_ENGINE_CONFIG = {
    # 하이브리드 검색 가중치 (동적 조정)
    'dynamic_weights': {
        'short_query': {'keyword': 0.7, 'semantic': 0.3},      # <= 2 단어
        'medium_query': {'keyword': 0.5, 'semantic': 0.5},     # 3-4 단어  
        'long_query': {'keyword': 0.4, 'semantic': 0.6},       # 5-7 단어
        'very_long_query': {'keyword': 0.6, 'semantic': 0.4}   # >= 8 단어
    },
    
    # 카테고리별 부스트 설정
    'category_boost': {
        'chapter_boost': 1.5,          # 챕터 매칭 시 50% 부스트
        'heading_boost': 2.0,          # 헤딩 매칭 시 100% 부스트
        'standard_match_boost': 2.0,   # 표준품명 직접 매칭 시 100% 부스트
        'standard_source_boost': 1.3   # 표준품명 데이터 소스 30% 부스트
    },
    
    # 네거티브 필터링
    'negative_filtering': {
        'penalty_ratio': 0.2,          # 네거티브 키워드 매칭 시 80% 점수 감소
        'apply_to_description': True    # final_combined_text에 적용
    },
    
    # 결과 필터링
    'result_filtering': {
        'dominant_chapter_threshold': 2,    # 상위 10개 중 2개 이상 같은 챕터면 지배적
        'chapter_dominance_ratio': 1.5,     # 지배적 챕터 평균이 1.5배 이상 높으면 필터링
        'min_score_threshold': 0.001        # 최소 점수 임계값
    }
}

# 캐시 관리 설정
CACHE_CONFIG = {
    # 캐시 버전 (final_combined_text 지원)
    'cache_version': '2.1',
    
    # 캐시 유효성 검사
    'validation': {
        'check_data_hash': True,           # 데이터 파일 해시 검사
        'check_model_name': True,          # 의미 모델명 검사
        'check_final_combined_text': True, # final_combined_text 컬럼 존재 검사
        'check_required_columns': [        # 필수 컬럼 존재 검사
            'HS_KEY', 'final_combined_text', 'data_source', 'chapter'
        ]
    },
    
    # 자동 업그레이드
    'auto_upgrade': {
        'from_old_cache': True,            # 이전 버전 캐시 자동 감지
        'rebuild_on_structure_change': True # 구조 변경 시 자동 재구축
    }
}

# LLM 분석 설정 (OpenAI)
LLM_CONFIG = {
    # 기본 모델
    'default_model': 'gpt-3.5-turbo',
    
    # 분석 설정
    'analysis': {
        'max_candidates': 5,      # 분석할 최대 후보 수
        'max_tokens': 1000,       # 최대 토큰 수
        'temperature': 0.3,       # 창의성 수준 (낮음 = 일관성)
        'timeout': 30             # 타임아웃 (초)
    },
    
    # 프롬프트 설정
    'prompt': {
        'system_message': "당신은 HS 코드 분류 전문가입니다.",
        'include_description': True,    # final_combined_text 포함
        'max_description_length': 200,  # 설명 최대 길이
        'request_json_format': True     # JSON 형식 요청
    }
}

# 성능 모니터링 설정
PERFORMANCE_CONFIG = {
    # 로깅 설정
    'logging': {
        'log_search_time': True,        # 검색 시간 로깅
        'log_cache_hits': True,         # 캐시 히트 로깅
        'log_data_quality': True        # 데이터 품질 로깅
    },
    
    # 벤치마크 설정
    'benchmark': {
        'test_queries': [               # 성능 테스트용 쿼리들
            '볼트', '프린터 토너', 'LED 전구', 
            '플라스틱 용기', '컴퓨터 마우스'
        ],
        'expected_min_results': 3,      # 기대 최소 결과 수
        'max_search_time': 5.0          # 최대 허용 검색 시간 (초)
    }
}

# 데이터 품질 검증 설정
DATA_QUALITY_CONFIG = {
    # final_combined_text 품질 기준
    'text_quality': {
        'min_length': 1,                # 최소 텍스트 길이
        'max_empty_ratio': 0.05,        # 최대 빈 텍스트 비율 (5%)
        'min_avg_length': 10,           # 최소 평균 텍스트 길이
        'check_encoding': True          # 인코딩 문제 검사
    },
    
    # 데이터 무결성 검사
    'integrity': {
        'check_duplicate_hs_keys': True,    # 중복 HS_KEY 검사
        'check_missing_chapters': True,     # 누락된 챕터 검사
        'validate_hs_key_format': True,     # HS_KEY 형식 검증 (10자리)
        'check_data_source_consistency': True # 데이터 소스 일관성 검사
    }
}

# 사용자 인터페이스 설정
UI_CONFIG = {
    # 결과 출력 설정
    'output': {
        'max_description_display': 150,  # 화면 출력 시 최대 설명 길이
        'show_scores': True,            # 점수 정보 표시
        'show_data_source': True,       # 데이터 소스 표시
        'show_llm_analysis': True,      # LLM 분석 결과 표시
        'color_coding': False           # 컬러 코딩 (터미널 지원 시)
    },
    
    # 상호작용 설정
    'interaction': {
        'confirm_cache_rebuild': True,   # 캐시 재구축 확인
        'show_progress_bars': True,      # 진행률 표시
        'auto_save_results': False,      # 결과 자동 저장
        'enable_shortcuts': True         # 단축키 활성화
    }
}