"""
AI 모델 관리 및 서빙을 위한 스키마 정의 모듈

이 모듈은 AI Gateway에서 사용되는 모든 모델 관련 데이터 구조를 정의합니다.
주요 기능:
- 모델 정보 스키마 (ModelInfo)
- OCR 서비스 요청/응답 스키마
- Report 서비스 요청/응답 스키마
- 모델 업데이트 및 목록 조회 스키마
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, validator

from .common import BaseResponse, ResponseStatus


class ModelType(str, Enum):
    """
    AI 모델 타입 열거형
    
    AI Gateway에서 지원하는 모델 타입들을 정의합니다.
    각 타입은 특정한 기능과 용도를 가지고 있습니다.
    """
    TEXT_EXTRACTOR = "text_extractor"  # OCR 텍스트 추출 모델
    TEXT_GENERATOR = "text_generator"  # 텍스트 생성 모델 (신고서 생성용)
    CODE_CONVERTER = "code_converter"  # 코드 변환 모델 (HS Code 변환 등)


class ModelStatus(str, Enum):
    """
    모델 상태 열거형
    
    모델 서비스의 현재 상태를 나타냅니다.
    각 상태는 모델의 가용성과 동작 상태를 표현합니다.
    """
    LOADING = "loading"  # 모델 로딩 중
    READY = "ready"  # 사용 준비 완료
    ERROR = "error"  # 오류 상태
    UPDATING = "updating"  # 업데이트 중
    DISABLED = "disabled"  # 비활성화됨


class ModelInfo(BaseModel):
    """
    모델 정보 스키마
    
    AI 모델의 기본 정보와 메타데이터를 정의합니다.
    모델 ID, 이름, 타입, 버전, 상태 등의 정보를 포함하며,
    각 모델 서비스의 특성에 맞는 메타데이터를 저장할 수 있습니다.
    
    Attributes:
        id: 모델 고유 식별자
        name: 사람이 읽기 쉬운 모델 이름
        type: 모델 타입 (TEXT_EXTRACTOR, TEXT_GENERATOR 등)
        version: 모델 버전
        status: 현재 모델 상태
        description: 모델 설명
        created_at: 생성 시간
        updated_at: 최종 업데이트 시간
        metadata: 모델별 추가 메타데이터 (서비스 URL, 엔드포인트, 성능 지표 등)
    """
    id: str = Field(..., description="모델 고유 식별자")
    name: str = Field(..., description="사람이 읽기 쉬운 모델 이름")
    type: ModelType = Field(..., description="모델 타입")
    version: str = Field(..., description="모델 버전")
    status: ModelStatus = Field(..., description="현재 모델 상태")
    description: Optional[str] = Field(None, description="모델 설명")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.now, description="최종 업데이트 시간")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="모델별 메타데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "model-ocr",
                "name": "Azure Document Intelligence OCR",
                "type": "text_extractor",
                "version": "1.0.0",
                "status": "ready",
                "description": "Azure Document Intelligence를 사용한 관세 문서 OCR 처리",
                "metadata": {
                    "service_url": "http://localhost:8001",
                    "endpoint": "/ocr/",
                    "supported_documents": ["invoice", "packing_list", "bill_of_lading"],
                    "accuracy": 0.95
                }
            }
        }


# OCR 서비스 관련 스키마
class OcrAnalyzeRequest(BaseModel):
    """
    OCR 문서 분석 요청 스키마
    
    관세 문서 3종(Invoice, Packing List, Bill of Lading)을 업로드하여
    OCR 분석을 요청할 때 사용되는 스키마입니다.
    파일 업로드는 FastAPI의 UploadFile을 통해 처리됩니다.
    
    Note:
        실제 파일 업로드는 FastAPI 엔드포인트에서 UploadFile로 처리됩니다.
        이 스키마는 문서화 및 검증 목적으로 사용됩니다.
    """
    pass  # 파일 업로드는 FastAPI UploadFile로 처리


class OcrAnalyzeResponse(BaseModel):
    """
    OCR 문서 분석 응답 스키마
    
    OCR 서비스에서 반환되는 분석 결과를 정의합니다.
    추출된 텍스트 데이터와 구조화된 정보, 처리 시간 등을 포함합니다.
    
    Attributes:
        status: 처리 상태
        message: 처리 결과 메시지
        ocr_data: OCR로 추출된 구조화된 데이터
        processing_time: 처리 소요 시간
        metadata: 추가 메타데이터 (파일 정보, 정확도 등)
    """
    status: str = Field(..., description="처리 상태")
    message: str = Field(..., description="처리 결과 메시지")
    ocr_data: Dict[str, Any] = Field(..., description="OCR 추출 데이터")
    processing_time: Optional[str] = Field(None, description="처리 소요 시간")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")

# HS Code 서비스 관련 스키마
class HsCodeConvertRequest(BaseModel):
    """
    HS Code 변환 요청 스키마
    
    미국 HS Code를 한국 HS Code로 변환하기 위한 요청 스키마입니다.
    제품 이름과 미국 HS Code를 입력받아 변환 결과를 반환합니다.
    Attributes:
        us_hs_code: 미국 HS Code
        product_name: 제품 이름
    """
    us_hs_code: str = Field(..., description="미국 HS Code")
    product_name: str = Field(..., description="제품 이름")

    @validator('us_hs_code')
    def validate_us_hs_code(cls, v):
        """
        미국 HS Code 검증
        미국 HS Code가 비어있지 않은지 확인합니다.
        """
        if not v:
            raise ValueError('미국 HS Code가 비어있습니다')
        return v
    @validator('product_name')
    def validate_product_name(cls, v):
        """
        제품 이름 검증
        
        제품 이름이 비어있지 않은지 확인합니다.
        """
        if not v:
            raise ValueError('제품 이름이 비어있습니다')
        return v
    
class HsCodeConvertResponse(BaseModel):
    """ HS Code 변환 응답 스키마
    
    HS Code 변환 서비스에서 반환되는 결과를 정의합니다.
    변환된 한국 HS Code와 관련 정보를 포함합니다.
    Attributes:
        status: 처리 상태
        message: 처리 결과 메시지
        converted_hs_code: 변환된 한국 HS Code
        processing_time: 처리 소요 시간
        metadata: 추가 메타데이터 (정확도, 사용된 모델 등)
    """
    status: str = Field(..., description="처리 상태")
    message: str = Field(..., description="처리 결과 메시지")
    converted_hs_code: str = Field(..., description="변환된 한국 HS Code")
    processing_time: Optional[str] = Field(None, description="처리 소요 시간")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")


# Report 서비스 관련 스키마
class ReportGenerateRequest(BaseModel):
    """
    신고서 생성 요청 스키마
    
    OCR 결과와 HSK 데이터를 기반으로 관세신고서 생성을 요청할 때 사용됩니다.
    LangChain 서비스에서 한국 관세청 규정에 맞는 신고서를 생성합니다.
    
    Attributes:
        ocr_data: OCR로 추출된 문서 정보
        hsk_data: HSK 코드 및 관련 데이터
        declaration_type: 신고서 타입 (import/export)
        options: 추가 처리 옵션
    """
    ocr_data: Dict[str, Any] = Field(..., description="OCR 추출 데이터")
    hsk_data: Dict[str, Any] = Field(..., description="HSK 코드 및 관련 데이터")
    declaration_type: Optional[str] = Field("import", description="신고서 타입 (import/export)")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 처리 옵션")
    
    @validator('ocr_data')
    def validate_ocr_data(cls, v):
        """
        OCR 데이터 검증
        
        OCR 데이터가 비어있지 않은지 확인합니다.
        """
        if not v:
            raise ValueError('OCR 데이터가 비어있습니다')
        return v
    
    @validator('hsk_data')
    def validate_hsk_data(cls, v):
        """
        HSK 데이터 검증
        
        HSK 데이터가 비어있지 않은지 확인합니다.
        """
        if not v:
            raise ValueError('HSK 데이터가 비어있습니다')
        return v


class ReportGenerateResponse(BaseModel):
    """
    신고서 생성 응답 스키마
    
    LangChain 서비스에서 생성된 관세신고서 데이터를 정의합니다.
    생성된 신고서 정보와 처리 시간, 메타데이터 등을 포함합니다.
    
    Attributes:
        status: 처리 상태
        message: 처리 결과 메시지
        declaration: 생성된 신고서 데이터
        processing_time: 처리 소요 시간
        metadata: 추가 메타데이터 (사용된 모델, 신뢰도 등)
    """
    status: str = Field(..., description="처리 상태")
    message: str = Field(..., description="처리 결과 메시지")
    declaration: Dict[str, Any] = Field(..., description="생성된 신고서 데이터")
    processing_time: Optional[str] = Field(None, description="처리 소요 시간")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")


class ModelUpdateRequest(BaseModel):
    """
    모델 정보 업데이트 요청 스키마
    
    등록된 모델의 정보를 업데이트할 때 사용됩니다.
    업데이트하고자 하는 필드만 포함하여 요청하면 됩니다.
    
    Attributes:
        name: 업데이트할 모델 이름
        description: 업데이트할 모델 설명
        status: 업데이트할 모델 상태
        metadata: 업데이트할 메타데이터
    """
    name: Optional[str] = Field(None, description="업데이트할 모델 이름")
    description: Optional[str] = Field(None, description="업데이트할 모델 설명")
    status: Optional[ModelStatus] = Field(None, description="업데이트할 모델 상태")
    metadata: Optional[Dict[str, Any]] = Field(None, description="업데이트할 메타데이터")


class ModelListResponse(BaseResponse):
    """
    모델 목록 응답 스키마
    
    등록된 모든 모델의 목록을 반환할 때 사용됩니다.
    페이지네이션과 필터링을 지원하며, 전체 모델 수와 함께 반환됩니다.
    
    Attributes:
        models: 모델 정보 목록
        total: 전체 모델 수
        status: 응답 상태
        message: 응답 메시지
    """
    models: List[ModelInfo] = Field(default_factory=list, description="모델 정보 목록")
    total: int = Field(0, description="전체 모델 수")