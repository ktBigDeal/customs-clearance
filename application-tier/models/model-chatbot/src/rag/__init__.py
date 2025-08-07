"""
RAG (Retrieval-Augmented Generation) Module

한국 관세법 문서 기반 RAG 시스템 구현
OpenAI API를 사용한 임베딩 및 챗봇 기능 제공
"""

# 환경 변수 로딩을 모듈 임포트 시점에 수행
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # config 모듈을 통해 환경 변수 로딩
    from ..utils.config import load_config
    
    # 환경 변수 로딩 시도
    try:
        config = load_config()
        print("🔧 RAG 시스템 환경 변수 로딩 완료")
    except Exception as e:
        print(f"⚠️ 환경 변수 로딩 실패: {e}")
        print("  .env 파일을 확인해주세요.")
        
except ImportError as e:
    print(f"⚠️ Config 모듈 로딩 실패: {e}")

from .embeddings import OpenAIEmbedder
from .law_retriever import SimilarLawRetriever  
from .query_normalizer import LawQueryNormalizer, TradeQueryNormalizer, UniversalQueryNormalizer, QueryNormalizer
from .law_agent import ConversationAgent
from .vector_store import ChromaVectorStore
from .law_data_processor import EnhancedDataProcessor

__all__ = [
    "OpenAIEmbedder",
    "SimilarLawRetriever", 
    "LawQueryNormalizer",
    "TradeQueryNormalizer",
    "UniversalQueryNormalizer",
    "QueryNormalizer",  # alias for LawQueryNormalizer (backward compatibility)
    "ConversationAgent",
    "ChromaVectorStore",
    "EnhancedDataProcessor"
]