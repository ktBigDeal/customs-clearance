"""
LangChain OpenAI Embeddings Module

LangChain 표준 OpenAI 임베딩과 도메인 특화 강화 기능
"""

import logging
from typing import List, Union, Optional
import os
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from ..utils.config import get_setting

logger = logging.getLogger(__name__)


class LangChainEmbedder:
    """LangChain 표준 OpenAI 임베딩과 도메인 특화 기능을 결합한 임베딩 생성기"""
    
    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        초기화
        
        Args:
            model_name (str): 사용할 OpenAI 임베딩 모델명
        """
        self.model_name = model_name
        
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please check your .env file or set the environment variable directly."
            )
        
        # LangChain 표준 임베딩 초기화
        self.embeddings = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=api_key
        )
        
        # 임베딩 차원 설정 (text-embedding-3-small: 1536차원)
        self.embedding_dim = 1536
        
        logger.info(f"LangChain Embedder initialized with model: {model_name}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        단일 텍스트에 대한 임베딩 생성 (LangChain 표준 사용)
        
        Args:
            text (str): 임베딩할 텍스트
            
        Returns:
            List[float]: 임베딩 벡터
        """
        try:
            embedding = self.embeddings.embed_query(text)
            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def embed_texts(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        여러 텍스트에 대한 임베딩 배치 생성 (LangChain 표준 사용)
        
        Args:
            texts (List[str]): 임베딩할 텍스트 리스트
            batch_size (int): 배치 크기 (LangChain이 내부적으로 처리)
            
        Returns:
            List[List[float]]: 임베딩 벡터 리스트
        """
        try:
            # LangChain이 내부적으로 배치 처리를 최적화함
            embeddings = self.embeddings.embed_documents(texts)
            logger.info(f"Successfully generated {len(embeddings)} embeddings using LangChain")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def embed_document(self, document: dict) -> dict:
        """
        문서 객체에 대한 임베딩 생성 및 추가
        
        Args:
            document (dict): 문서 객체
            
        Returns:
            dict: 임베딩이 추가된 문서 객체
        """
        enhanced_content = self._create_enhanced_content(document)
        embedding = self.embed_text(enhanced_content)
        
        document_copy = document.copy()
        document_copy["embedding"] = embedding
        document_copy["enhanced_content"] = enhanced_content
        
        return document_copy
    
    def embed_documents(self, documents: List[dict]) -> List[dict]:
        """
        여러 문서에 대한 임베딩 배치 생성
        
        Args:
            documents (List[dict]): 문서 리스트
            
        Returns:
            List[dict]: 임베딩이 추가된 문서 리스트
        """
        # 모든 문서의 enhanced content 생성
        enhanced_contents = [self._create_enhanced_content(doc) for doc in documents]
        
        # 배치로 임베딩 생성
        embeddings = self.embed_texts(enhanced_contents)
        
        # 문서에 임베딩 및 enhanced content 추가
        enhanced_documents = []
        for doc, embedding, enhanced_content in zip(documents, embeddings, enhanced_contents):
            doc_copy = doc.copy()
            doc_copy["embedding"] = embedding
            doc_copy["enhanced_content"] = enhanced_content
            enhanced_documents.append(doc_copy)
        
        return enhanced_documents
    
    def _create_enhanced_content(self, document: dict) -> str:
        """
        문서의 검색 성능을 향상시키기 위한 강화된 콘텐츠 생성
        
        Args:
            document (dict): 문서 객체
            
        Returns:
            str: 강화된 콘텐츠
        """
        parts = []
        metadata = document.get("metadata", {})
        
        # 계층 구조 정보 추가
        if metadata.get("hierarchy_path"):
            parts.append(f"법령구조: {metadata['hierarchy_path'].replace('>', ' > ')}")
        
        # 조문 제목 추가
        if document.get("subtitle"):
            parts.append(f"주제: {document['subtitle']}")
        
        # 법령명 및 레벨 정보 추가
        if metadata.get("law_name"):
            parts.append(f"법령: {metadata['law_name']}")
        if metadata.get("law_level"):
            parts.append(f"법령종류: {metadata['law_level']}")
        
        # 내부 법령 참조 정보 추가 (새로운 기능)
        internal_refs = metadata.get("internal_law_references", {})
        if internal_refs:
            ref_parts = []
            if internal_refs.get("refers_to_main_law"):
                ref_parts.append(f"관세법 참조: {', '.join(internal_refs['refers_to_main_law'])}")
            if internal_refs.get("refers_to_enforcement_decree"):
                ref_parts.append(f"시행령 참조: {', '.join(internal_refs['refers_to_enforcement_decree'])}")
            if internal_refs.get("refers_to_enforcement_rules"):
                ref_parts.append(f"시행규칙 참조: {', '.join(internal_refs['refers_to_enforcement_rules'])}")
            
            if ref_parts:
                parts.append("법령참조: " + "; ".join(ref_parts))
        
        # 외부 법령 참조 정보 추가
        external_refs = metadata.get("external_law_references", [])
        if external_refs:
            parts.append(f"외부법령: {', '.join(external_refs[:3])}")  # 최대 3개까지만
        
        # 핵심 법률 용어 추출 및 추가
        content = document.get("content", "")
        keywords = self._extract_legal_keywords(content)
        if keywords:
            parts.append(f"핵심용어: {', '.join(keywords)}")
        
        # 실제 조문 내용 추가
        parts.append(content)
        
        return "\n".join(parts)
    
    def _extract_legal_keywords(self, content: str) -> List[str]:
        """
        법률 텍스트에서 핵심 용어 추출
        
        Args:
            content (str): 법률 텍스트
            
        Returns:
            List[str]: 추출된 핵심 용어 리스트 (최대 5개)
        """
        keywords = [
            '신고', '허가', '승인', '과세가격', '관세', '수입', '수출',
            '통관', '세관', '납세의무자', '보세구역', '검사', '확인',
            '신청', '제출', '첨부', '서류', '증명', '확인서', '납부',
            '징수', '부과', '면제', '감면', '환급', '벌금', '과태료',
            '원산지', '세율', '관세청', '세관장', '통관업', '운송',
            '반입', '반출', '저장', '가공', '제조', '수리', '조립'
        ]
        
        found_keywords = [kw for kw in keywords if kw in content]
        return found_keywords[:5]  # 최대 5개까지만 반환


# 기존 코드와의 호환성을 위한 별칭
OpenAIEmbedder = LangChainEmbedder