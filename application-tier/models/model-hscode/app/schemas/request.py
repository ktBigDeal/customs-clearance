"""
API 요청 스키마 정의
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class SearchMode(str, Enum):
    """검색 모드"""
    BASIC = "basic"          # 기본 하이브리드 검색
    LLM = "llm"             # LLM 통합 검색
    KEYWORD_ONLY = "keyword_only"  # 키워드 검색만
    SEMANTIC_ONLY = "semantic_only"  # 의미 검색만

class RecommendRequest(BaseModel):
    """HS 코드 추천 요청"""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="검색할 상품명",
        example="스테인레스 볼트"
    )
    
    material: Optional[str] = Field(
        default="",
        max_length=100,
        description="재질 정보 (선택사항)",
        example="스테인레스강"
    )
    
    usage: Optional[str] = Field(
        default="",
        max_length=100,
        description="용도 정보 (선택사항)",
        example="산업용"
    )
    
    mode: SearchMode = Field(
        default=SearchMode.LLM,
        description="검색 모드"
    )
    
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="반환할 결과 개수"
    )
    
    use_llm: bool = Field(
        default=True,
        description="LLM 분석 사용 여부"
    )
    
    include_details: bool = Field(
        default=True,
        description="상세 정보 포함 여부"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """쿼리 검증"""
        if not v or not v.strip():
            raise ValueError('검색어는 비어있을 수 없습니다')
        return v.strip()
    
    @validator('material', 'usage')
    def validate_optional_fields(cls, v):
        """선택 필드 검증"""
        return v.strip() if v else ""

class SearchRequest(BaseModel):
    """일반 검색 요청 (추천보다 더 많은 결과)"""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="검색할 상품명"
    )
    
    material: Optional[str] = Field(default="", max_length=100)
    usage: Optional[str] = Field(default="", max_length=100)
    
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="반환할 결과 개수"
    )
    
    offset: int = Field(
        default=0,
        ge=0,
        description="결과 시작 위치"
    )
    
    include_scores: bool = Field(
        default=False,
        description="검색 점수 포함 여부"
    )

class BatchRecommendRequest(BaseModel):
    """배치 추천 요청"""
    
    requests: List[RecommendRequest] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="추천 요청 목록"
    )
    
    parallel_processing: bool = Field(
        default=True,
        description="병렬 처리 여부"
    )

class CacheRequest(BaseModel):
    """캐시 관리 요청"""
    
    action: str = Field(
        ...,
        regex="^(rebuild|clear|info)$",
        description="캐시 액션: rebuild, clear, info"
    )
    
    force: bool = Field(
        default=False,
        description="강제 실행 여부"
    )

class ValidateHSCodeRequest(BaseModel):
    """HS 코드 검증 요청"""
    
    hs_code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        regex="^[0-9]+$",
        description="검증할 HS 코드",
        example="7318159000"
    )

class CompareRequest(BaseModel):
    """HS 코드 비교 요청"""
    
    hs_codes: List[str] = Field(
        ...,
        min_items=2,
        max_items=5,
        description="비교할 HS 코드 목록"
    )
    
    include_hierarchy: bool = Field(
        default=True,
        description="계층 구조 포함 여부"
    )

class SimilarRequest(BaseModel):
    """유사 HS 코드 검색 요청"""
    
    hs_code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        regex="^[0-9]+$",
        description="기준 HS 코드"
    )
    
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="유사도 임계값"
    )
    
    max_results: int = Field(
        default=10,
        ge=1,
        le=30,
        description="최대 결과 개수"
    )