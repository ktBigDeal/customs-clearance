"""
Chunking Utilities Module

문서 청킹 결과 분석 및 관련 유틸리티 함수들을 제공합니다.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def analyze_chunking_results(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """청킹 결과 분석
    
    Args:
        documents (List[Dict[str, Any]]): 처리된 문서 리스트
        
    Returns:
        Dict[str, Any]: 분석 결과 딕셔너리
    """
    if not documents:
        logger.warning("No documents provided for analysis")
        return {
            "total_chunks": 0,
            "article_level_count": 0,
            "paragraph_level_count": 0,
            "average_chunk_length": 0,
            "analysis_summary": "No documents to analyze"
        }
    
    article_level_count = sum(1 for doc in documents if doc['metadata']['chunk_type'] == 'article_level')
    paragraph_level_count = sum(1 for doc in documents if doc['metadata']['chunk_type'] == 'paragraph_level')
    
    # 평균 청크 크기 계산
    total_length = sum(len(doc['content']) for doc in documents)
    avg_length = total_length / len(documents) if documents else 0
    
    # 법령별 분석
    law_distribution = {}
    for doc in documents:
        law_name = doc['metadata'].get('law_name', 'Unknown')
        if law_name not in law_distribution:
            law_distribution[law_name] = 0
        law_distribution[law_name] += 1
    
    results = {
        "total_chunks": len(documents),
        "article_level_count": article_level_count,
        "paragraph_level_count": paragraph_level_count,
        "average_chunk_length": round(avg_length, 1),
        "law_distribution": law_distribution,
        "analysis_summary": f"총 {len(documents)}개 청크 생성 (조단위: {article_level_count}, 항단위: {paragraph_level_count})"
    }
    
    # 로그 출력
    logger.info(f"총 청크 수: {len(documents)}")
    logger.info(f"조 단위 청크: {article_level_count}")
    logger.info(f"항 단위 청크: {paragraph_level_count}")
    logger.info(f"평균 청크 길이: {avg_length:.0f} 문자")
    
    # 콘솔 출력 (기존 노트북 동작 유지)
    print(f"총 청크 수: {len(documents)}")
    print(f"조 단위 청크: {article_level_count}")
    print(f"항 단위 청크: {paragraph_level_count}")
    print(f"평균 청크 길이: {avg_length:.0f} 문자")
    
    return results


def get_chunk_statistics(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """더 자세한 청킹 통계 정보 제공
    
    Args:
        documents (List[Dict[str, Any]]): 처리된 문서 리스트
        
    Returns:
        Dict[str, Any]: 상세 통계 정보
    """
    if not documents:
        return {}
    
    # 길이 분포 분석
    lengths = [len(doc['content']) for doc in documents]
    lengths.sort()
    
    # 참조 패턴 분석
    internal_refs = 0
    external_refs = 0
    
    for doc in documents:
        metadata = doc.get('metadata', {})
        customs_refs = metadata.get('customs_law_references', {})
        external_law_refs = metadata.get('external_law_references', [])
        
        # 내부 참조 카운트
        for ref_type in customs_refs.values():
            internal_refs += len(ref_type) if isinstance(ref_type, list) else 0
        
        # 외부 참조 카운트
        external_refs += len(external_law_refs)
    
    stats = {
        "length_stats": {
            "min": min(lengths),
            "max": max(lengths),
            "median": lengths[len(lengths)//2],
            "q1": lengths[len(lengths)//4],
            "q3": lengths[3*len(lengths)//4]
        },
        "reference_stats": {
            "total_internal_references": internal_refs,
            "total_external_references": external_refs,
            "docs_with_internal_refs": sum(1 for doc in documents 
                                         if any(doc['metadata'].get('customs_law_references', {}).values())),
            "docs_with_external_refs": sum(1 for doc in documents 
                                         if doc['metadata'].get('external_law_references', []))
        }
    }
    
    return stats


def validate_chunk_integrity(documents: List[Dict[str, Any]]) -> List[str]:
    """청크 데이터 무결성 검증
    
    Args:
        documents (List[Dict[str, Any]]): 검증할 문서 리스트
        
    Returns:
        List[str]: 발견된 문제점들의 리스트
    """
    issues = []
    
    required_fields = ['index', 'subtitle', 'content', 'metadata']
    required_metadata_fields = ['law_name', 'law_level', 'chunk_type', 'effective_date']
    
    for i, doc in enumerate(documents):
        # 필수 필드 확인
        for field in required_fields:
            if field not in doc:
                issues.append(f"Document {i}: Missing required field '{field}'")
        
        # 메타데이터 필수 필드 확인
        metadata = doc.get('metadata', {})
        for field in required_metadata_fields:
            if field not in metadata:
                issues.append(f"Document {i}: Missing required metadata field '{field}'")
        
        # 내용 검증
        if not doc.get('content', '').strip():
            issues.append(f"Document {i}: Empty content")
        
        # 인덱스 형식 검증
        index = doc.get('index', '')
        if not index.startswith('제') or '조' not in index:
            issues.append(f"Document {i}: Invalid index format '{index}'")
    
    return issues


def print_sample_chunks(documents: List[Dict[str, Any]], num_samples: int = 2) -> None:
    """샘플 청크 출력 (노트북의 기존 동작 재현)
    
    Args:
        documents (List[Dict[str, Any]]): 문서 리스트
        num_samples (int): 출력할 샘플 수
    """
    if not documents:
        print("출력할 문서가 없습니다.")
        return
    
    # 조 단위 청크 예시 출력
    print("\n=== 조 단위 청크 예시 ===")
    article_chunks = [doc for doc in documents if doc['metadata']['chunk_type'] == 'article_level']
    
    if article_chunks:
        for i, chunk in enumerate(article_chunks[:num_samples]):
            print(f"내용: {chunk['content'][:200]}...")
            print(f"메타데이터: {chunk['metadata']}")
            if i < len(article_chunks[:num_samples]) - 1:
                print()
    else:
        print("조 단위 청크가 없습니다.")
    
    # 항 단위 청크 예시 출력
    print("\n=== 항 단위 청크 예시 ===")
    paragraph_chunks = [doc for doc in documents if doc['metadata']['chunk_type'] == 'paragraph_level']
    
    if paragraph_chunks:
        for i, chunk in enumerate(paragraph_chunks[:num_samples]):
            print(f"내용: {chunk['content'][:200]}...")
            print(f"메타데이터: {chunk['metadata']}")
            if i < len(paragraph_chunks[:num_samples]) - 1:
                print()
    else:
        print("항 단위 청크가 없습니다.")