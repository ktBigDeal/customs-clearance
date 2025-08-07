"""
Data Processing Module

한국 관세법 문서의 처리, 청킹, 메타데이터 추출을 담당하는 모듈입니다.
"""

from .law_document_loader import CustomsLawLoader
from .law_chunking_utils import (
    analyze_chunking_results, 
    get_chunk_statistics, 
    validate_chunk_integrity, 
    print_sample_chunks
)

__all__ = [
    "CustomsLawLoader", 
    "analyze_chunking_results",
    "get_chunk_statistics",
    "validate_chunk_integrity", 
    "print_sample_chunks"
]