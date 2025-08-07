"""
AI 모델 관리 엔드포인트

이 모듈은 AI 모델의 등록, 조회 기능을 제공합니다.
각 모델의 상태 관리와 메타데이터 관리도 지원합니다.
"""

from typing import List, Optional, Dict, Any
import httpx

from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File

from ..core.logging import get_logger
from ..schemas.models import (
    ModelInfo, ModelUpdateRequest, ModelListResponse, ModelStatus, ModelType
)
from ..schemas.common import ResponseStatus, PaginationParams

logger = get_logger(__name__)
router = APIRouter()

# 실제 모델 서비스들과 연동된 모델 레지스트리 (프로덕션에선 DB 활용)
model_registry: Dict[str, ModelInfo] = {
    "model-ocr": ModelInfo(
        id="model-ocr",
        name="Azure Document Intelligence OCR",
        type=ModelType.TEXT_EXTRACTOR,
        version="1.0.0",
        status=ModelStatus.READY,
        description="Azure Document Intelligence를 사용한 관세 문서 OCR 처리 (Invoice, Packing List, Bill of Lading)",
        metadata={
            "service_url": "http://localhost:8001",
            "endpoint": "/ocr/",
            "supported_documents": ["invoice", "packing_list", "bill_of_lading"],
            "supported_formats": ["pdf", "jpg", "png", "tiff"],
            "max_file_size": "50MB",
            "processing_time": "2-5 seconds",
            "accuracy": 0.95
        }
    ),
    "model-report": ModelInfo(
        id="model-report",
        name="LangChain 관세신고서 생성",
        type=ModelType.TEXT_GENERATOR,
        version="1.0.0",
        status=ModelStatus.READY,
        description="LangChain과 OpenAI GPT를 사용한 한국 관세청 규정 기반 수입/수출 신고서 자동 생성",
        metadata={
            "service_url": "http://localhost:8002",
            "endpoints": {
                "import": "/generate-customs-declaration/import",
                "export": "/generate-customs-declaration/export"
            },
            "supported_types": ["import_declaration", "export_declaration"],
            "llm_model": "gpt-4o-mini",
            "temperature": 0.3,
            "processing_time": "3-8 seconds",
            "language": "Korean"
        }
    ),
    "model-hscode": ModelInfo(
        id="model-hscode",
        name="HS Code 변환 서비스",
        type=ModelType.CODE_CONVERTER,
        version="1.0.0",
        status=ModelStatus.READY,
        description="HS Code 변환 및 조회 서비스",
        metadata={
            "service_url": "http://localhost:8003",
            "endpoints": {
                "convert": "/convert",
                "lookup": "/lookup"
            },
            "supported_countries": ["US", "KR", "EU"],
            "max_conversion_time": "5 seconds",
            "accuracy": 0.98
        }
    )
}




@router.get("", response_model=ModelListResponse)
async def list_models(
    model_type: Optional[ModelType] = Query(None, description="Filter by model type"),
    status_filter: Optional[ModelStatus] = Query(None, description="Filter by status"),
    pagination: PaginationParams = Depends()
):
    """
    사용 가능한 모든 AI 모델 목록 조회
    
    등록된 모든 AI 모델들을 조회합니다.
    모델 타입과 상태로 필터링이 가능하며, 페이지네이션을 지원합니다.
    
    Args:
        model_type (Optional[ModelType]): 모델 타입별 필터
        status_filter (Optional[ModelStatus]): 상태별 필터
        pagination (PaginationParams): 페이지네이션 매개변수
        
    Returns:
        ModelListResponse: 모델 목록 및 메타데이터
        
    Raises:
        HTTPException: 모델 목록 조회 실패 시
    """
    
    try:
        models = list(model_registry.values())
        
        # 필터 적용
        if model_type:
            models = [m for m in models if m.type == model_type]
        
        if status_filter:
            models = [m for m in models if m.status == status_filter]
        
        # 페이지네이션 적용
        start_idx = (pagination.page - 1) * pagination.size
        end_idx = start_idx + pagination.size
        paginated_models = models[start_idx:end_idx]
        
        return ModelListResponse(
            status=ResponseStatus.SUCCESS,
            message="Models retrieved successfully",
            models=paginated_models,
            total=len(models)
        )
        
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve models"
        )


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    """
    특정 모델의 정보 조회
    
    주어진 모델 ID에 해당하는 모델의 상세 정보를 반환합니다.
    모델의 상태, 버전, 메타데이터 등을 포함합니다.
    
    Args:
        model_id (str): 조회할 모델의 고유 식별자
        
    Returns:
        ModelInfo: 모델 상세 정보
        
    Raises:
        HTTPException: 모델을 찾을 수 없는 경우 (404)
    """
    
    if model_id not in model_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    
    return model_registry[model_id]




@router.put("/{model_id}", response_model=ModelInfo)
async def update_model(
    model_id: str,
    request: ModelUpdateRequest
):
    """
    모델 정보 업데이트
    
    지정된 모델의 메타데이터, 상태, 설명 등을 업데이트합니다.
    업데이트된 필드만 수정되며, 나머지는 기존 값을 유지합니다.
    
    Args:
        model_id (str): 업데이트할 모델의 고유 식별자
        request (ModelUpdateRequest): 업데이트할 모델 정보
        
    Returns:
        ModelInfo: 업데이트된 모델 정보
        
    Raises:
        HTTPException: 모델을 찾을 수 없는 경우 (404)
    """
    
    if model_id not in model_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    
    model_info = model_registry[model_id]
    
    # 필드 업데이트
    if request.name is not None:
        model_info.name = request.name
    if request.description is not None:
        model_info.description = request.description
    if request.status is not None:
        model_info.status = request.status
    if request.metadata is not None:
        model_info.metadata.update(request.metadata)
    
    model_info.updated_at = model_info.updated_at.__class__.now()
    
    return model_info


# OCR 전용 엔드포인트
@router.post("/model-ocr/analyze-documents")
async def ocr_analyze_documents(
    invoice_file: UploadFile = File(...),
    packing_list_file: UploadFile = File(...),
    bill_of_lading_file: UploadFile = File(...)
):
    """
    OCR 모델을 통한 문서 분석 전용 엔드포인트
    
    3개의 관세 문서(Invoice, Packing List, Bill of Lading)를 업로드하여
    Azure Document Intelligence OCR 서비스로 분석합니다.
    
    Args:
        invoice_file (UploadFile): 인보이스 문서
        packing_list_file (UploadFile): 포장 명세서 문서
        bill_of_lading_file (UploadFile): 선하증권 문서
        
    Returns:
        Dict: OCR 분석 결과
    """
    
    model_info = model_registry.get("model-ocr")
    if not model_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR model not found"
        )
    
    try:
        
        service_url = model_info.metadata.get("service_url")
        
        # 파일들을 OCR 서비스로 전송
        files = {
            "invoice_file": (invoice_file.filename, await invoice_file.read(), invoice_file.content_type),
            "packing_list_file": (packing_list_file.filename, await packing_list_file.read(), packing_list_file.content_type),
            "bill_of_lading_file": (bill_of_lading_file.filename, await bill_of_lading_file.read(), bill_of_lading_file.content_type)
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{service_url}/ocr/",
                files=files
            )
        
        if response.status_code == 200:
            return response.json()
        
        raise HTTPException(
            status_code=response.status_code,
            detail=f"OCR service error: {response.text}"
        )
            
    except httpx.RequestError as e:
        logger.error(f"Error calling OCR service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OCR service unavailable"
        )
    except Exception as e:
        logger.error(f"Error in OCR document analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OCR document analysis failed"
        )

# HS Code 전용 엔드포인트
@router.post("/model-hscode/hscode-convert")
async def convert_hs_code(
    us_hs_code: str = Query(..., description="미국 HS Code"),
    product_name: str = Query(..., description="제품 이름 (선택 사항)")
):
    """
    미국 HS Code를 한국 HS Code로 변환
    미국 HS Code와 선택적으로 제품 이름을 입력받아
    한국 HS Code로 변환합니다.
    Args:
        us_hs_code (str): 미국 HS Code
        product_name (Optional[str]): 제품 이름 (선택 사항)
    Returns:
        Dict: 변환된 HS Code 정보
    """
    model_info = model_registry.get("model-hscode")
    if not model_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HS Code model not found"
        )
    try:
        service_url = model_info.metadata.get("service_url")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{service_url}/convert",
                json={
                    "us_hs_code": us_hs_code,
                    "product_name": product_name
                }
            )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"HS Code conversion error: {response.text}"
            )
    except httpx.RequestError as e:
        logger.error(f"HS Code service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HS Code service is unavailable"
        )
    except Exception as e:
        logger.error(f"Error in HS Code conversion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="HS Code conversion failed"
        )

# Report 전용 엔드포인트
@router.post("/model-report/generate-declaration")
async def report_generate_declaration(
    request: Dict[str, Any]
):
    """
    Report 모델을 통한 신고서 생성 전용 엔드포인트
    
    OCR 결과와 HSK 데이터를 기반으로 LangChain 서비스를 통해
    한국 관세청 규정에 맞는 신고서를 생성합니다.
    
    Args:
        request (Dict): OCR 데이터와 HSK 데이터가 포함된 요청
        
    Returns:
        Dict: 생성된 신고서 데이터
    """
    
    model_info = model_registry.get("model-report")
    if not model_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report model not found"
        )
    
    try:
        
        service_url = model_info.metadata.get("service_url")
        endpoint = f"{service_url}/generate-customs-declaration/import"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            
            logger.error(f"Report service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Report service error: {response.text}"
            )
                
    except httpx.RequestError as e:
        logger.error(f"Error calling Report service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report service unavailable"
        )
    except Exception as e:
        logger.error(f"Error in report generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report generation failed"
        )