"""
Utilities Module

공통 유틸리티 함수들과 AI 컴포넌트 관리를 담당하는 모듈입니다.
"""

# Core utilities and tools
from .tools import (
    deduplicate_by_id, 
    deduplicate_by_content, 
    smart_deduplicate,
    format_search_results,
    validate_agent_response,
    extract_key_concepts,
    safe_json_parse
)

# AI components
from .embeddings import LangChainEmbedder
from .db_connect import LangChainVectorStore
from .query_normalizer import UniversalQueryNormalizer, LawQueryNormalizer, TradeQueryNormalizer, get_query_normalizer, AdvancedQueryProcessor

__all__ = [
    # Deduplication functions
    "deduplicate_by_id", 
    "deduplicate_by_content", 
    "smart_deduplicate",
    # Utility functions
    "format_search_results",
    "validate_agent_response",
    "extract_key_concepts",
    "safe_json_parse",
    # AI components
    "LangChainEmbedder",
    "LangChainVectorStore",
    "UniversalQueryNormalizer",
    "LawQueryNormalizer",
    "TradeQueryNormalizer",
    "get_query_normalizer",
    "AdvancedQueryProcessor"
]