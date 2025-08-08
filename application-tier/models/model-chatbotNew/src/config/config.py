"""
Configuration Management Module

환경 변수 및 설정 관리를 담당하는 모듈입니다.
구글 콜랩의 수동 API 키 로딩을 python-dotenv를 사용한 자동 로딩으로 개선했습니다.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

logger = logging.getLogger(__name__)


def load_config(env_file: Optional[str] = None) -> Dict[str, str]:
    """환경 변수 로드 및 설정
    
    Args:
        env_file (Optional[str]): .env 파일 경로 (None이면 자동 탐색)
        
    Returns:
        Dict[str, str]: 로드된 환경 변수들
    """
    # 프로젝트 루트 디렉토리 찾기
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent  # src/utils/ -> src/ -> project_root/
    
    # .env 파일 경로 결정
    if env_file is None:
        env_file = project_root / ".env"
    else:
        env_file = Path(env_file)
    
    # .env 파일 로드
    if env_file.exists() and HAS_DOTENV:
        load_dotenv(env_file)
        logger.info(f"Environment variables loaded from {env_file}")
        print(f"✅ 환경 변수 로드 완료: {env_file}")
    elif env_file.exists() and not HAS_DOTENV:
        logger.warning("python-dotenv not installed. Please install it with: pip install python-dotenv")
        print("⚠️ python-dotenv가 설치되지 않았습니다.")
        print("  다음 명령으로 설치해주세요: pip install python-dotenv")
        print("  또는 직접 환경 변수를 설정해주세요.")
    else:
        logger.warning(f".env file not found at {env_file}")
        print(f"⚠️ .env 파일을 찾을 수 없습니다: {env_file}")
        print("  .env.example을 참고하여 .env 파일을 생성해주세요.")
    
    # 필수 환경 변수 확인
    required_vars = ["OPENAI_API_KEY"]
    optional_vars = ["HF_TOKEN"]
    
    config = {}
    missing_vars = []
    
    # 필수 변수 체크
    for var in required_vars:
        value = os.getenv(var)
        if value:
            config[var] = value
            # API 키는 일부만 출력
            masked_value = value[:10] + "..." if len(value) > 10 else "***"
            logger.info(f"{var} loaded: {masked_value}")
            print(f"✅ {var}: {masked_value}")
        else:
            missing_vars.append(var)
    
    # 선택적 변수 체크
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            config[var] = value
            masked_value = value[:10] + "..." if len(value) > 10 else "***"
            logger.info(f"{var} loaded: {masked_value}")
            print(f"✅ {var}: {masked_value}")
        else:
            logger.info(f"{var} not provided (optional)")
            print(f"ℹ️ {var}: 설정되지 않음 (선택사항)")
    
    # 필수 변수가 누락된 경우 경고
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        print("  .env 파일에 필수 환경 변수를 설정해주세요.")
        raise ValueError(error_msg)
    
    return config


def get_data_path(relative_path: str = "") -> Path:
    """데이터 디렉토리 경로 반환
    
    Args:
        relative_path (str): 데이터 디렉토리 내 상대 경로
        
    Returns:
        Path: 절대 경로
    """
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    data_dir = project_root / "data"
    
    if relative_path:
        return data_dir / relative_path
    return data_dir


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 경로 반환
    
    Returns:
        Path: 프로젝트 루트 경로
    """
    current_dir = Path(__file__).parent
    return current_dir.parent.parent


def get_law_data_paths() -> Dict[str, Path]:
    """관세법 데이터 파일 경로들 반환
    
    Returns:
        Dict[str, Path]: 법령별 파일 경로
    """
    data_dir = get_data_path("DCM/raw_json")
    
    return {
        "관세법": data_dir / "관세법.json",
        "관세법시행령": data_dir / "관세법시행령.json", 
        "관세법시행규칙": data_dir / "관세법시행규칙.json"
    }


def get_chunked_data_paths() -> Dict[str, Path]:
    """청킹된 관세법 데이터 파일 경로들 반환 (RAG용)
    
    Returns:
        Dict[str, Path]: 법령별 청킹된 파일 경로
    """
    chunk_dir = get_data_path("DCM/chunk_json")
    
    return {
        "관세법": chunk_dir / "customs_law.json",
        "관세법시행령": chunk_dir / "customs_law_enforcement.json",
        "관세법시행규칙": chunk_dir / "customs_law_rules.json"
    }


def get_output_paths() -> Dict[str, Path]:
    """출력 파일 경로들 반환 (document_loader.py 청킹 출력용)
    
    Returns:
        Dict[str, Path]: 출력 파일 경로들
    """
    return get_chunked_data_paths()  # 동일한 경로 사용


def get_pdf_data_paths() -> Dict[str, Path]:
    """PDF 문서 파일 경로들 반환
    
    Returns:
        Dict[str, Path]: PDF 문서별 파일 경로
    """
    pdf_dir = get_data_path("DCM/PDF")
    
    return {
        "수입제한품목": pdf_dir / "수입제한품목.pdf",
        "수출제한품목": pdf_dir / "수출제한품목.pdf", 
        "수출금지품목": pdf_dir / "수출금지품목.pdf",
        "무역통계부호": pdf_dir / "2025_무역통계부호 합본.pdf",
        "수입신고서작성요령": pdf_dir / "수입신고서 작성요령.pdf",
        "수출신고서작성요령": pdf_dir / "수출신고서 작성요령.pdf",
        "민원상담사례집": pdf_dir / "관세행정 민원상담 사례집.pdf"
    }


def get_pdf_output_paths() -> Dict[str, Path]:
    """PDF 문서 청킹 출력 파일 경로들 반환 (JSONL 형식)
    
    Returns:
        Dict[str, Path]: PDF 문서별 청킹된 파일 경로
    """
    chunk_dir = get_data_path("DCM/chunk_jsonl")
    
    return {
        "수입제한품목": chunk_dir / "import_restricted_items.jsonl",
        "수출제한품목": chunk_dir / "export_restricted_items.jsonl",
        "수출금지품목": chunk_dir / "export_prohibited_items.jsonl", 
        "무역통계부호": chunk_dir / "trade_statistics_code.jsonl",
        "수입신고서작성요령": chunk_dir / "import_declaration_guide.jsonl",
        "수출신고서작성요령": chunk_dir / "export_declaration_guide.jsonl"
    }


def get_consultation_case_paths() -> Dict[str, Path]:
    """민원상담 사례집 관련 경로들 반환
    
    Returns:
        Dict[str, Path]: 민원상담 사례집 관련 경로들
    """
    pdf_dir = get_data_path("DCM/PDF")
    json_dir = get_data_path("DCM/chunk_json")
    
    return {
        "input_pdf": pdf_dir / "관세행정 민원상담 사례집.pdf",
        "output_json": json_dir / "consultation_cases.json"
    }


def get_data_paths() -> Dict[str, Path]:
    """무역 정보 데이터 파일 경로들 반환 (CSV + JSON)
    
    Returns:
        Dict[str, Path]: 데이터 파일별 경로 (타입 구분: csv, json)
    """
    csv_dir = get_data_path("DCM/csv")
    json_dir = get_data_path("DCM/chunk_json")
    
    return {
        "수입규제DB_전체": csv_dir / "수입규제DB_전체.csv",
        "수출제한품목": csv_dir / "수출제한품목.csv",
        "수입제한품목": csv_dir / "수입제한품목.csv",
        "수출금지품목": csv_dir / "수출금지품목.csv",
        "동식물허용금지지역": csv_dir / "동식물 수입 허용 및 금지 지역.csv",
        "민원상담사례집": json_dir / "consultation_cases.json"
    }


def get_csv_data_paths() -> Dict[str, Path]:
    """CSV 데이터 파일 경로들 반환 (일반 정보용) - 하위 호환성
    
    Returns:
        Dict[str, Path]: CSV 파일별 경로
    """
    csv_dir = get_data_path("DCM/csv")
    
    return {
        "수입규제DB_전체": csv_dir / "수입규제DB_전체.csv",
        "수출제한품목": csv_dir / "수출제한품목.csv",
        "수입제한품목": csv_dir / "수입제한품목.csv",
        "수출금지품목": csv_dir / "수출금지품목.csv",
        "동식물허용금지지역": csv_dir / "동식물 수입 허용 및 금지 지역.csv"
    }


def get_csv_output_paths() -> Dict[str, Path]:
    """CSV 데이터 청킹 출력 파일 경로들 반환 (일반 정보용)
    
    Returns:
        Dict[str, Path]: CSV별 청킹된 파일 경로
    """
    chunk_dir = get_data_path("DCM/chunk_json")
    
    return {
        "수입규제DB_전체": chunk_dir / "export_destination_restrictions.json",
        "수출제한품목": chunk_dir / "export_restrictions.json", 
        "수입제한품목": chunk_dir / "import_restrictions.json",
        "수출금지품목": chunk_dir / "export_prohibitions.json",
        "동식물허용금지지역": chunk_dir / "import_regulations_animal_plant.json"
    }


def get_trade_agent_config() -> Dict[str, Any]:
    """무역 정보 에이전트 설정 반환
    
    Returns:
        Dict[str, Any]: 무역 정보 에이전트 설정
    """
    return {
        "collection_name": "trade_info_collection",
        "model_name": "gpt-4o-mini",
        "temperature": 0.3,
        "max_context_docs": 8,  # 더 많은 문서 참조
        "similarity_threshold": 0.0,  # 검색 단계에서는 낮게 유지 (리랭킹에서 처리)
        "animal_plant_threshold": 0.1,  # 동식물 규제 데이터 전용 임계값
        "rerank_threshold": 0.2,  # 최종 결과 재랭킹 임계값
        "max_history": 10,
        "search_filters": {
            "default_expand_synonyms": True,
            "default_include_related": True,
            "supported_countries": [
                "미국", "중국", "일본", "독일", "영국", "프랑스", 
                "이탈리아", "캐나다", "호주", "인도", "인도네시아",
                "말레이시아", "필리핀", "튀르키예", "이집트", "EU"
            ],
            "supported_categories": [
                "철강", "플라스틱", "고무", "화학품", "기계", "전기기기",
                "농산물", "섬유", "의류", "신발", "가구", "완구"
            ]
        }
    }


def validate_environment() -> bool:
    """환경 설정 유효성 검사
    
    Returns:
        bool: 환경이 올바르게 설정되었는지 여부
    """
    try:
        # 환경 변수 로드 시도
        config = load_config()
        
        # 데이터 디렉토리 존재 확인
        data_paths = get_law_data_paths()
        missing_files = []
        
        for law_name, path in data_paths.items():
            if not path.exists():
                missing_files.append(f"{law_name}: {path}")
        
        if missing_files:
            logger.warning("Missing data files:")
            for missing in missing_files:
                logger.warning(f"  - {missing}")
            print("⚠️ 일부 데이터 파일이 누락되었습니다:")
            for missing in missing_files:
                print(f"  - {missing}")
            return False
        
        logger.info("Environment validation successful")
        print("✅ 환경 설정 검증 완료")
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        print(f"❌ 환경 설정 검증 실패: {e}")
        return False


def create_env_example() -> bool:
    """예제 .env 파일 생성
    
    Returns:
        bool: 생성 성공 여부
    """
    try:
        project_root = get_project_root()
        env_example_path = project_root / ".env.example"
        
        # .env.example이 이미 존재하면 덮어쓰지 않음
        if env_example_path.exists():
            logger.info(f".env.example already exists: {env_example_path}")
            return True
        
        example_content = """# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# Hugging Face 토큰 (선택적)
HF_TOKEN=hf_your-huggingface-token-here
"""
        
        with open(env_example_path, 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        logger.info(f".env.example created: {env_example_path}")
        print(f"✅ .env.example 파일 생성 완료: {env_example_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create .env.example: {e}")
        print(f"❌ .env.example 생성 실패: {e}")
        return False


# 기본 설정값들
DEFAULT_SETTINGS = {
    "chunk_strategy": {
        "paragraph_threshold": 3,  # 항이 3개 이상이면 항 단위로 분할
        "max_content_length": 2000,  # 최대 청크 길이
        "min_content_length": 10     # 최소 청크 길이
    },
    "csv_processing": {
        "encoding_detection": True,  # 자동 인코딩 감지
        "fallback_encodings": ["utf-8", "cp949", "euc-kr", "utf-8-sig"],
        "max_content_length": 1000,  # CSV 청크 최대 길이
        "min_content_length": 20,    # CSV 청크 최소 길이
        "clean_text": True,          # 텍스트 정리 활성화
        "extract_hs_codes": True,    # HS코드 자동 추출
        "normalize_countries": True, # 국가명 정규화
        "product_categorization": True  # 제품 카테고리 자동 분류
    },
    "pdf_processing": {
        "extraction_method": "hybrid",  # "text", "table", "ocr", "hybrid"
        "chunk_strategy": {
            "restriction_items": "item_based",  # 품목별 청킹
            "guideline": "section_based",       # 섹션별 청킹
            "statistics": "category_based"      # 카테고리별 청킹
        },
        "max_chunk_size": 1500,  # PDF 청크 최대 크기
        "min_chunk_size": 50,    # PDF 청크 최소 크기
        "overlap_size": 100,     # 청크 간 오버랩 크기
        "table_extraction": {
            "min_rows": 2,       # 최소 테이블 행 수
            "confidence_threshold": 0.8  # OCR 신뢰도 임계값
        }
    },
    "trade_agent": {
        "collection_name": "trade_info_collection",
        "vector_store_settings": {
            "similarity_threshold": 0.0,
            "max_results": 20,
            "rerank_results": True
        },
        "retrieval_settings": {
            "expand_synonyms": True,
            "include_related": True,
            "hs_code_matching": True,
            "country_normalization": True
        }
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    },
    "output": {
        "indent": 2,
        "ensure_ascii": False
    }
}


def get_quality_thresholds() -> Dict[str, float]:
    """품질 관련 임계값들 중앙 관리"""
    return {
        "similarity_threshold": 0.0,      # 검색 단계 임계값
        "animal_plant_threshold": 0.1,    # 동식물 규제 전용
        "rerank_threshold": 0.2,          # 최종 재랭킹 임계값  
        "model_temperature": 0.1,         # 기본 모델 온도
        "regulation_temperature": 0.1,    # 규제 에이전트 온도
        "consultation_temperature": 0.4,  # 상담 에이전트 온도
        "query_temperature": 0.3,         # 쿼리 정규화 온도
        "intent_temperature": 0.2,        # 의도 분석 온도
        "regulation_confidence": 0.8,     # 규제 질의 신뢰도
        "consultation_confidence": 0.7,   # 상담 질의 신뢰도
        "complexity_threshold": 0.7,      # 복합 질의 임계값
        "animal_plant_score_threshold": 0.8,  # 동식물 감지 임계값
        "decision_threshold_high": 0.3,   # 높은 확신 임계값
        "decision_threshold_low": 0.1,    # 낮은 확신 임계값
        "boost_score_limit": 0.5,         # 부스팅 점수 최대값
        "importance_score_limit": 1.0,    # 중요도 점수 최대값
        "merge_similarity": 0.9,          # 중복 병합 유사도
        "reference_boost": 0.1,           # 참조 부스트 점수
        "intent_weight": 0.1,             # 의도 매칭 가중치
        "concept_score": 0.2,             # 개념 매칭 점수
        "area_score": 0.3,                # 영역 매칭 점수
        "importance_weight": 0.3,         # 중요도 가중치
        "similarity_weight": 0.7          # 유사도 가중치
    }


def get_setting(key_path: str, default: Any = None) -> Any:
    """설정값 조회
    
    Args:
        key_path (str): 점으로 구분된 설정 키 경로 (예: "chunk_strategy.paragraph_threshold")
        default (Any): 기본값
        
    Returns:
        Any: 설정값
    """
    keys = key_path.split('.')
    value = DEFAULT_SETTINGS
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value