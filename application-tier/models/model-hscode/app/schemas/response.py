"""
API 응답 스키마 정의
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class HSCodeRecommendation(BaseModel):
    """HS 코드 추천 결과"""
    
    hs_code: str = Field(..., description="HS 코드")
    name_kr: str = Field(..., description="한글 품목명")
    name_en: Optional[str] = Field(default="", description="영문 품목명")
    description: Optional[str] = Field(default="", description="상세 설명")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    
    # 점수 정보
    keyword_score: Optional[float] = Field(default=None, description="키워드 매칭 점수")
    semantic_score: Optional[float] = Field(default=None, description="의미 매칭 점수")
    hybrid_score: Optional[float] = Field(default=None, description="통합 점수")
    
    # 분류 정보
    chapter: Optional[str] = Field(default="", description="HS 챕터 (2자리)")
    heading: Optional[str] = Field(default="", description="HS 헤딩 (4자리)")
    subheading: Optional[str] = Field(default="", description="HS 서브헤딩 (6자리)")
    
    # 데이터 소스
    data_source: Optional[str] = Field(default="", description="데이터 출처")
    is_standard_match: Optional[bool] = Field(default=False, description="표준품명 직접 매칭 여부")
    
    # LLM 분석 (있는 경우)
    llm_analysis: Optional[Dict[str, Any]] = Field(default=None, description="LLM 분석 결과")

class SearchInfo(BaseModel):
    """검색 정보"""
    
    query: str = Field(..., description="검색어")
    expanded_query: Optional[str] = Field(default="", description="확장된 검색어")
    material: Optional[str] = Field(default="", description="재질")
    usage: Optional[str] = Field(default="", description="용도")
    
    search_time_ms: Optional[float] = Field(default=None, description="검색 시간 (밀리초)")
    total_candidates: Optional[int] = Field(default=None, description="총 후보 개수")
    method: Optional[str] = Field(default="", description="사용된 검색 방법")
    
    # LLM 관련 정보
    llm_used: Optional[bool] = Field(default=False, description="LLM 사용 여부")
    llm_candidates: Optional[int] = Field(default=None, description="LLM 직접 후보 수")
    search_candidates: Optional[int] = Field(default=None, description="검색엔진 후보 수")

class RecommendResponse(BaseModel):
    """추천 응답"""
    
    success: bool = Field(..., description="성공 여부")
    message: str = Field(default="", description="응답 메시지")
    
    recommendations: List[HSCodeRecommendation] = Field(
        default=[],
        description="추천 결과 목록"
    )
    
    search_info: Optional[SearchInfo] = Field(
        default=None,
        description="검색 정보"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="추가 메타데이터"
    )

class SearchResponse(BaseModel):
    """검색 응답"""
    
    success: bool = Field(..., description="성공 여부")
    message: str = Field(default="", description="응답 메시지")
    
    results: List[HSCodeRecommendation] = Field(
        default=[],
        description="검색 결과 목록"
    )
    
    total_count: int = Field(default=0, description="전체 결과 개수")
    page_info: Optional[Dict[str, int]] = Field(
        default=None,
        description="페이징 정보"
    )
    
    search_info: Optional[SearchInfo] = Field(
        default=None,
        description="검색 정보"
    )

class BatchRecommendResponse(BaseModel):
    """배치 추천 응답"""
    
    success: bool = Field(..., description="전체 성공 여부")
    total_requests: int = Field(..., description="총 요청 수")
    successful_requests: int = Field(..., description="성공한 요청 수")
    
    results: List[RecommendResponse] = Field(
        default=[],
        description="각 요청별 추천 결과"
    )
    
    processing_time_ms: Optional[float] = Field(
        default=None,
        description="전체 처리 시간 (밀리초)"
    )

class HealthResponse(BaseModel):
    """헬스체크 응답"""
    
    status: str = Field(..., description="서비스 상태")
    timestamp: float = Field(..., description="응답 시간")
    version: str = Field(..., description="API 버전")
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="상세 상태 정보"
    )

class StatusResponse(BaseModel):
    """상태 정보 응답"""
    
    service_name: str = Field(..., description="서비스명")
    version: str = Field(..., description="버전")
    status: str = Field(..., description="현재 상태")
    uptime_seconds: float = Field(..., description="가동 시간 (초)")
    
    # 데이터 상태
    total_items: int = Field(default=0, description="총 데이터 항목 수")
    cache_status: str = Field(default="unknown", description="캐시 상태")
    openai_available: bool = Field(default=False, description="OpenAI 사용 가능 여부")
    
    # 데이터 소스별 분포
    data_sources: Optional[Dict[str, int]] = Field(
        default=None,
        description="데이터 소스별 항목 수"
    )
    
    # 성능 정보
    performance: Optional[Dict[str, Any]] = Field(
        default=None,
        description="성능 관련 정보"
    )

class CacheResponse(BaseModel):
    """캐시 관리 응답"""
    
    success: bool = Field(..., description="성공 여부")
    action: str = Field(..., description="수행된 액션")
    message: str = Field(..., description="결과 메시지")
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="상세 정보"
    )

class ValidateHSCodeResponse(BaseModel):
    """HS 코드 검증 응답"""
    
    hs_code: str = Field(..., description="검증한 HS 코드")
    valid: bool = Field(..., description="유효성")
    
    info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="HS 코드 정보"
    )
    
    message: str = Field(default="", description="검증 결과 메시지")

class CompareResponse(BaseModel):
    """HS 코드 비교 응답"""
    
    success: bool = Field(..., description="성공 여부")
    
    comparison: Dict[str, Dict[str, Any]] = Field(
        default={},
        description="HS 코드별 정보"
    )
    
    similarities: Optional[Dict[str, float]] = Field(
        default=None,
        description="코드간 유사도"
    )
    
    hierarchy_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="계층 구조 분석"
    )

class SimilarResponse(BaseModel):
    """유사 HS 코드 응답"""
    
    base_hs_code: str = Field(..., description="기준 HS 코드")
    threshold: float = Field(..., description="사용된 유사도 임계값")
    
    similar_codes: List[Dict[str, Any]] = Field(
        default=[],
        description="유사한 HS 코드 목록"
    )
    
    total_found: int = Field(default=0, description="찾은 유사 코드 수")

class ErrorResponse(BaseModel):
    """에러 응답"""
    
    error: str = Field(..., description="에러 타입")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(default=None, description="상세 에러 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간")
    request_id: Optional[str] = Field(default=None, description="요청 ID")