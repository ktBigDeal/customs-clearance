from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
import logging
import re
import os
import sys
from dotenv import load_dotenv
# 프로젝트 루트를 sys.path에 추가
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

from us_ks_hs_converter_service import HSCodeConverterService, convert_numpy_types

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 변수
converter_service = None

# 시스템 초기화 함수
async def initialize_converter_service(openai_api_key: str = None, us_tariff_file: str = None):
    """변환 서비스 초기화"""
    global converter_service
    
    try:
        # .env 파일 로드 (프로젝트 루트의 .env 파일)
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"환경 변수 파일 로드: {env_file}")
        else:
            logger.warning(f"환경 변수 파일이 없음: {env_file}")
        # 기존 서비스가 있다면 정리
        if converter_service is not None:
            logger.info("기존 서비스 정리 중...")
            # 캐시 정리
            if hasattr(converter_service, 'clear_cache'):
                converter_service.clear_cache()
            converter_service = None
        
        # OpenAI API 키를 환경 변수에서 로드
        if not openai_api_key:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                logger.info("환경 변수에서 OpenAI API 키 로드")
            else:
                logger.warning("환경 변수에서 OpenAI API 키를 찾을 수 없음")
        
        # 미국 관세율표 파일 경로 설정
        if not us_tariff_file:
            # 환경변수에서 파일 경로 읽기
            us_tariff_file_env = os.getenv("US_TARIFF_FILE")
            if us_tariff_file_env:
                us_tariff_file = us_tariff_file_env
                logger.info(f"환경변수에서 파일 경로 로드: {us_tariff_file}")
            else:
                project_root = Path(__file__).parent.parent
                us_tariff_file = project_root / "us_tariff_table_20250714.xlsx"
                logger.info(f"프로젝트 루트: {project_root}")
            
            # 디버깅 정보 출력
            logger.info(f"찾는 파일 경로: {us_tariff_file}")
            logger.info(f"파일 존재 여부: {os.path.exists(us_tariff_file)}")
            
            if not os.path.exists(us_tariff_file):
                logger.error(f"파일을 찾을 수 없습니다: {us_tariff_file}")
                return False, f"미국 관세율표 파일을 찾을 수 없습니다: {us_tariff_file}"

        # 한국 추천 시스템 로드 시도
        korea_recommender = None
        try:
            from hs_recommender import HSCodeRecommender
            cache_dir = project_root / "cache" / "hs_code_cache"
            korea_recommender = HSCodeRecommender(cache_dir=str(cache_dir))
            if korea_recommender.load_data():
                print("✅ 한국 추천 시스템 로드 완료")
            else:
                print("⚠️ 한국 추천 시스템 로드 실패")
                korea_recommender = None
        except ImportError:
            print("⚠️ 한국 추천 시스템 모듈을 찾을 수 없음")
            korea_recommender = None
        except Exception as e:
            print(f"⚠️ 한국 추천 시스템 로드 중 오류: {e}")
            korea_recommender = None

        # 새로운 변환 서비스 생성
        print("🚀 새로운 변환 서비스 생성 중...")
        converter_service = HSCodeConverterService(
            str(us_tariff_file),  # Path 객체를 문자열로 변환
            korea_recommender,
            openai_api_key
        )

        # 시스템 초기화
        logger.info("시스템 초기화 시작...")
        success, message = converter_service.initialize_system()
        
        if success:
            logger.info(f"성공: {message}")
            return True, message
        else:
            logger.error(f"실패: {message}")
            # 초기화 실패시 converter_service를 None으로 리셋
            converter_service = None
            return False, message

    except Exception as e:
        error_msg = f"시스템 초기화 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        # 오류 발생시 converter_service를 None으로 리셋
        converter_service = None
        return False, error_msg


# Lifespan 이벤트 핸들러 (최신 FastAPI 방식)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global converter_service
    logger.info("HS Code Converter API 서버 시작")
    success, message = await initialize_converter_service()
    if success:
        logger.info(f"초기화 성공: {message}")
    else:
        logger.warning(f"기본 초기화 실패: {message}")
    
    yield
    
    # Shutdown
    logger.info("HS Code Converter API 서버 종료")

# FastAPI 앱 생성 (lifespan 이벤트 핸들러 포함)
app = FastAPI(
    title="HS Code Converter API",
    description="미국→한국 HS 코드 변환 서비스 (LLM 강화)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델들
class ConversionRequest(BaseModel):
    us_hs_code: str = Field(..., description="미국 HS 코드 (4-10자리)", example="8471300100")
    product_name: Optional[str] = Field("", description="상품명 (선택사항, LLM 분석에 도움)", example="노트북 컴퓨터")

class ConversionResponse(BaseModel):
    status: str
    method: Optional[str] = None
    us_hs_code: str
    us_product_name: str
    us_info: Optional[Dict] = None
    korea_recommendation: Optional[Dict] = None
    hs_analysis: Optional[Dict] = None
    search_query: Optional[str] = None
    all_candidates: Optional[List[Dict]] = None
    explanation: Optional[str] = None
    product_analysis: Optional[Dict] = None
    message: Optional[str] = None
    suggestions: Optional[List[str]] = None
    from_cache: Optional[bool] = False

class SystemStatusResponse(BaseModel):
    initialized: bool
    llm_available: bool
    us_data_loaded: bool
    korea_data_loaded: bool
    semantic_model_loaded: bool
    statistics: Optional[Dict] = None

class InitializeRequest(BaseModel):
    openai_api_key: Optional[str] = Field(None, description="OpenAI API 키 (LLM 기능 사용시)")
    us_tariff_file: Optional[str] = Field(None, description="미국 관세율표 파일 경로")

# API 엔드포인트들
@app.get("/")
async def root():
    """API 기본 정보"""
    result = {
        "service": "HS Code Converter API",
        "version": "1.0.0",
        "description": "미국→한국 HS 코드 변환 서비스 (LLM 강화)",
        "status": "running",
        "llm_available": converter_service.llm_available if converter_service else False
    }
    return convert_numpy_types(result)

@app.post("/initialize")
async def initialize_system():
    """시스템 수동 초기화 (기본 경로 자동 로드)"""
    try:
        logger.info("수동 초기화 요청 - 기본 경로에서 자동 로드")
        
        # 항상 None을 전달해서 자동 로드하도록 함
        success, message = await initialize_converter_service(
            openai_api_key=None,    # 자동으로 docs/Aivle-api.txt에서 로드
            us_tariff_file=None     # 자동으로 기본 경로 사용
        )

        result = {
            "success": success,
            "message": message,
            "llm_available": converter_service.llm_available if converter_service else False
        }
        return convert_numpy_types(result)

    except Exception as e:
        error_detail = f"초기화 실패: {str(e)}"
        logger.error(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)



@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """시스템 상태 조회"""
    if not converter_service:
        return SystemStatusResponse(
            initialized=False,
            llm_available=False,
            us_data_loaded=False,
            korea_data_loaded=False,
            semantic_model_loaded=False
        )
    
    stats = converter_service.get_system_statistics()
    
    return SystemStatusResponse(
        initialized=converter_service.initialized,
        llm_available=converter_service.llm_available,
        us_data_loaded=converter_service.us_data is not None,
        korea_data_loaded=converter_service.korea_data is not None,
        semantic_model_loaded=converter_service.semantic_model is not None,
        statistics=convert_numpy_types(stats)
    )

@app.post("/convert", response_model=ConversionResponse)
async def convert_hs_code(request: ConversionRequest):
    """HS 코드 변환"""
    if not converter_service:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다. /initialize 엔드포인트를 먼저 호출하세요.")
    
    if not converter_service.initialized:
        raise HTTPException(status_code=503, detail="시스템이 초기화되지 않았습니다.")
    
    # HS 코드 유효성 검사
    us_hs_code = request.us_hs_code.strip()
    if not re.match(r'^\d{4,10}$', us_hs_code):
        raise HTTPException(
            status_code=400, 
            detail="올바른 HS 코드를 입력하세요 (4-10자리 숫자)"
        )
    
    try:
        # 변환 실행
        result = converter_service.convert_hs_code(us_hs_code, request.product_name)
        
        # numpy 타입 변환
        result = convert_numpy_types(result)
        
        return ConversionResponse(**result)
        
    except Exception as e:
        logger.error(f"변환 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"변환 중 오류 발생: {str(e)}")

@app.get("/lookup/{us_hs_code}")
async def lookup_us_hs_code(us_hs_code: str):
    """미국 HS 코드 조회"""
    if not converter_service:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    
    if not converter_service.initialized:
        raise HTTPException(status_code=503, detail="시스템이 초기화되지 않았습니다.")
    
    # HS 코드 유효성 검사
    if not re.match(r'^\d{4,10}$', us_hs_code):
        raise HTTPException(
            status_code=400, 
            detail="올바른 HS 코드를 입력하세요 (4-10자리 숫자)"
        )
    
    try:
        us_info = converter_service.lookup_us_hs_code(us_hs_code)
        
        if not us_info:
            raise HTTPException(
                status_code=404, 
                detail=f"미국 HS코드 '{us_hs_code}'를 찾을 수 없습니다."
            )
        
        # numpy 타입 변환
        us_info = convert_numpy_types(us_info)
        
        return us_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 중 오류 발생: {str(e)}")

@app.delete("/cache")
async def clear_cache():
    """변환 캐시 초기화"""
    if not converter_service:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    
    try:
        cleared_count = converter_service.clear_cache()
        result = {
            "message": "캐시가 성공적으로 초기화되었습니다.",
            "cleared_items": cleared_count
        }
        # numpy 타입 변환
        return convert_numpy_types(result)
        
    except Exception as e:
        logger.error(f"캐시 초기화 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캐시 초기화 중 오류 발생: {str(e)}")

@app.get("/hs6/{hs6}/description")
async def get_hs6_description(hs6: str):
    """HS 6자리 분류 설명 조회"""
    if not converter_service:
        raise HTTPException(status_code=503, detail="서비스가 초기화되지 않았습니다.")
    
    if not converter_service.initialized:
        raise HTTPException(status_code=503, detail="시스템이 초기화되지 않았습니다.")
    
    # HS6 코드 유효성 검사
    if not re.match(r'^\d{4,10}$', hs6):
        raise HTTPException(
            status_code=400, 
            detail="올바른 HS 6자리 코드를 입력하세요"
        )
    
    try:
        description = converter_service.get_hs6_description(hs6)
        result = {
            "hs6": hs6,
            "description": description
        }
        # numpy 타입 변환
        return convert_numpy_types(result)
        
    except Exception as e:
        logger.error(f"HS6 설명 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 중 오류 발생: {str(e)}")

# 개발용 엔드포인트
@app.get("/health")
async def health_check():
    """헬스 체크"""
    result = {
        "status": "healthy",
        "service": "HS Code Converter API",
        "initialized": converter_service.initialized if converter_service else False
    }
    return convert_numpy_types(result)

if __name__ == "__main__":
    import uvicorn
    
    # .env 파일에서 포트 설정 로드 (기본값 8006)
    port = int(os.getenv("PORT", 8006))
    
    print("HS Code Converter API 서버 시작")
    print(f"API 문서: http://localhost:{port}/docs")
    print(f"Interactive API: http://localhost:{port}/redoc")
    
    uvicorn.run(
        "us_main:app",  # 문자열로 모듈명과 앱 객체 지정
        host="0.0.0.0",
        port=port,      # 환경 변수에서 읽어온 포트 사용
        reload=True,
        log_level="info"
    )
