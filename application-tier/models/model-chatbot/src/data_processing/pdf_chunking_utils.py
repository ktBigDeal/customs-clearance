"""
PDF Chunking Utilities Module

PDF 문서 청킹 결과를 분석, 검증, 후처리하는 유틸리티 함수들을 제공합니다.
기존 chunking_utils.py의 법령 전용 함수들과 구별되는 PDF 문서 전용 기능들입니다.

Functions:
    - validate_pdf_chunks: PDF 청킹 결과 검증
    - analyze_pdf_processing_results: PDF 처리 결과 분석  
    - get_pdf_chunk_statistics: PDF 청크 통계 생성
    - merge_duplicate_chunks: 중복 청크 병합
    - enhance_pdf_metadata: PDF 메타데이터 보강
    - export_pdf_chunks_summary: PDF 청킹 결과 요약 내보내기
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter, defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


# JSONL 관련 새로운 유틸리티 함수들

def save_pdf_chunks_as_jsonl(chunks: List[Dict], output_path: Path) -> bool:
    """PDF 청크들을 JSONL 형식으로 저장 (유틸리티 래퍼)
    
    Args:
        chunks (List[Dict]): 저장할 청크 리스트
        output_path (Path): 출력 파일 경로
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from ..utils.file_utils import save_chunks_as_jsonl
        return save_chunks_as_jsonl(chunks, str(output_path))
    except ImportError as e:
        logger.error(f"Failed to import save_chunks_as_jsonl: {e}")
        return False


def load_pdf_chunks_from_jsonl(file_path: Path) -> Optional[List[Dict]]:
    """JSONL 파일에서 PDF 청크들 로드 (유틸리티 래퍼)
    
    Args:
        file_path (Path): JSONL 파일 경로
        
    Returns:
        Optional[List[Dict]]: 로드된 청크 리스트
    """
    try:
        from ..utils.file_utils import load_chunks_from_jsonl
        return load_chunks_from_jsonl(str(file_path))
    except ImportError as e:
        logger.error(f"Failed to import load_chunks_from_jsonl: {e}")
        return None


def stream_process_pdf_chunks(chunks: List[Dict], process_func, output_path: Path) -> bool:
    """PDF 청크들을 스트리밍 방식으로 처리하여 JSONL로 저장
    
    Args:
        chunks (List[Dict]): 처리할 청크 리스트
        process_func: 각 청크에 적용할 처리 함수
        output_path (Path): 출력 파일 경로
        
    Returns:
        bool: 처리 성공 여부
    """
    try:
        from ..utils.file_utils import append_chunk_to_jsonl
        
        # 기존 파일이 있으면 삭제
        if output_path.exists():
            output_path.unlink()
        
        processed_count = 0
        for chunk in chunks:
            try:
                # 청크 처리
                processed_chunk = process_func(chunk)
                if processed_chunk:
                    # JSONL에 추가
                    success = append_chunk_to_jsonl(processed_chunk, str(output_path))
                    if success:
                        processed_count += 1
                    else:
                        logger.warning(f"Failed to append chunk {chunk.get('index', 'unknown')}")
                        
            except Exception as e:
                logger.error(f"Error processing chunk {chunk.get('index', 'unknown')}: {e}")
                continue
        
        logger.info(f"Stream processing completed: {processed_count}/{len(chunks)} chunks processed")
        return processed_count > 0
        
    except Exception as e:
        logger.error(f"Stream processing failed: {e}")
        return False


def validate_pdf_jsonl_file(file_path: Path) -> Dict[str, Any]:
    """PDF JSONL 파일의 구조 유효성 검사
    
    Args:
        file_path (Path): 검사할 JSONL 파일 경로
        
    Returns:
        Dict[str, Any]: 검사 결과
    """
    try:
        from ..utils.file_utils import validate_jsonl_file
        
        # 기본 JSONL 유효성 검사
        base_result = validate_jsonl_file(str(file_path))
        
        if not base_result["is_valid"]:
            return base_result
        
        # PDF 청크 특화 검사
        pdf_specific_issues = []
        required_fields = ["index", "title", "content", "metadata"]
        required_metadata_fields = ["document_type", "source_pdf", "category", "chunk_type"]
        
        chunks = load_pdf_chunks_from_jsonl(file_path)
        if not chunks:
            return {
                "is_valid": False,
                "error": "Failed to load chunks for validation",
                "pdf_specific_issues": ["Could not load chunks"]
            }
        
        for i, chunk in enumerate(chunks, 1):
            chunk_id = f"청크 {i}"
            
            # 필수 필드 검사
            for field in required_fields:
                if field not in chunk:
                    pdf_specific_issues.append(f"{chunk_id}: 필수 필드 '{field}' 누락")
            
            # 메타데이터 필수 필드 검사
            if "metadata" in chunk and isinstance(chunk["metadata"], dict):
                for field in required_metadata_fields:
                    if field not in chunk["metadata"]:
                        pdf_specific_issues.append(f"{chunk_id}: 메타데이터 필수 필드 '{field}' 누락")
            
            # 내용 길이 검사
            content = chunk.get("content", "")
            if not content or len(content.strip()) < 10:
                pdf_specific_issues.append(f"{chunk_id}: 내용이 너무 짧거나 비어있음")
        
        base_result["pdf_specific_issues"] = pdf_specific_issues
        base_result["pdf_chunks_valid"] = len(pdf_specific_issues) == 0
        
        return base_result
        
    except Exception as e:
        logger.error(f"PDF JSONL validation failed: {e}")
        return {
            "is_valid": False,
            "error": str(e),
            "pdf_specific_issues": [f"Validation error: {e}"]
        }


def merge_pdf_jsonl_files(input_paths: List[Path], output_path: Path) -> bool:
    """여러 PDF JSONL 파일을 하나로 병합
    
    Args:
        input_paths (List[Path]): 병합할 JSONL 파일 경로들
        output_path (Path): 출력 파일 경로
        
    Returns:
        bool: 병합 성공 여부
    """
    try:
        from ..utils.file_utils import append_chunk_to_jsonl
        
        # 기존 출력 파일이 있으면 삭제
        if output_path.exists():
            output_path.unlink()
        
        total_chunks = 0
        for input_path in input_paths:
            if not input_path.exists():
                logger.warning(f"Input file not found: {input_path}")
                continue
            
            chunks = load_pdf_chunks_from_jsonl(input_path)
            if not chunks:
                logger.warning(f"No chunks loaded from: {input_path}")
                continue
            
            # 각 청크를 출력 파일에 추가
            for chunk in chunks:
                # 소스 파일 정보 추가
                if "metadata" not in chunk:
                    chunk["metadata"] = {}
                chunk["metadata"]["merged_from"] = input_path.name
                
                success = append_chunk_to_jsonl(chunk, str(output_path))
                if success:
                    total_chunks += 1
        
        logger.info(f"Successfully merged {len(input_paths)} files into {output_path}")
        logger.info(f"Total chunks merged: {total_chunks}")
        return total_chunks > 0
        
    except Exception as e:
        logger.error(f"Failed to merge PDF JSONL files: {e}")
        return False


def get_jsonl_statistics(file_path: Path) -> Dict[str, Any]:
    """JSONL 파일의 통계 정보 생성
    
    Args:
        file_path (Path): 분석할 JSONL 파일 경로
        
    Returns:
        Dict[str, Any]: 통계 정보
    """
    try:
        chunks = load_pdf_chunks_from_jsonl(file_path)
        if not chunks:
            return {"error": "Failed to load chunks"}
        
        # 기존 get_pdf_chunk_statistics 함수 재사용
        return get_pdf_chunk_statistics(chunks)
        
    except Exception as e:
        logger.error(f"Failed to get JSONL statistics: {e}")
        return {"error": str(e)}


def validate_pdf_chunks(chunks: List[Dict]) -> Dict[str, Any]:
    """PDF 청킹 결과 검증
    
    Args:
        chunks (List[Dict]): 검증할 PDF 청크 리스트
        
    Returns:
        Dict[str, Any]: 검증 결과 및 발견된 문제점들
    """
    validation_result = {
        "is_valid": True,
        "total_chunks": len(chunks),
        "issues": [],
        "warnings": [],
        "statistics": {}
    }
    
    if not chunks:
        validation_result["is_valid"] = False
        validation_result["issues"].append("청크가 하나도 생성되지 않았습니다")
        return validation_result
    
    # 필수 필드 검증
    required_fields = ["index", "title", "content", "metadata"]
    required_metadata_fields = ["document_type", "source_pdf", "category", "chunk_type"]
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"청크 {i+1}"
        
        # 필수 필드 확인
        for field in required_fields:
            if field not in chunk:
                validation_result["issues"].append(f"{chunk_id}: 필수 필드 '{field}' 누락")
                validation_result["is_valid"] = False
        
        # 메타데이터 필수 필드 확인
        if "metadata" in chunk and isinstance(chunk["metadata"], dict):
            for field in required_metadata_fields:
                if field not in chunk["metadata"]:
                    validation_result["issues"].append(f"{chunk_id}: 메타데이터 필수 필드 '{field}' 누락")
                    validation_result["is_valid"] = False
        
        # 내용 검증
        if "content" in chunk:
            content = chunk["content"]
            if not content or not content.strip():
                validation_result["issues"].append(f"{chunk_id}: 빈 내용")
                validation_result["is_valid"] = False
            elif len(content.strip()) < 20:
                validation_result["warnings"].append(f"{chunk_id}: 내용이 너무 짧음 ({len(content)} 문자)")
        
        # 인덱스 중복 확인
        indices = [chunk.get("index") for chunk in chunks if chunk.get("index")]
        duplicate_indices = [idx for idx, count in Counter(indices).items() if count > 1]
        if duplicate_indices:
            validation_result["issues"].append(f"중복된 인덱스: {duplicate_indices}")
            validation_result["is_valid"] = False
    
    # 통계 생성
    validation_result["statistics"] = _generate_chunk_statistics(chunks)
    
    return validation_result


def analyze_pdf_processing_results(chunks: List[Dict]) -> Dict[str, Any]:
    """PDF 처리 결과 종합 분석
    
    Args:
        chunks (List[Dict]): 분석할 PDF 청크 리스트
        
    Returns:
        Dict[str, Any]: 처리 결과 분석 정보
    """
    if not chunks:
        return {"error": "분석할 청크가 없습니다"}
    
    analysis = {
        "overview": {},
        "document_types": {},
        "extraction_methods": {},
        "chunk_types": {},
        "content_analysis": {},
        "metadata_analysis": {},
        "quality_metrics": {}
    }
    
    # 기본 개요
    analysis["overview"] = {
        "total_chunks": len(chunks),
        "total_content_length": sum(len(chunk.get("content", "")) for chunk in chunks),
        "average_chunk_size": 0,
        "source_documents": set()
    }
    
    if chunks:
        analysis["overview"]["average_chunk_size"] = analysis["overview"]["total_content_length"] // len(chunks)
    
    # 문서 유형별 분석
    doc_type_stats = defaultdict(lambda: {"count": 0, "total_length": 0, "avg_length": 0})
    extraction_method_stats = defaultdict(int)
    chunk_type_stats = defaultdict(int)
    
    hs_codes_total = 0
    law_refs_total = 0
    
    for chunk in chunks:
        content_length = len(chunk.get("content", ""))
        metadata = chunk.get("metadata", {})
        
        # 소스 문서 수집
        if "source_pdf" in metadata:
            analysis["overview"]["source_documents"].add(metadata["source_pdf"])
        
        # 문서 유형 통계
        doc_type = metadata.get("document_type", "unknown")
        doc_type_stats[doc_type]["count"] += 1
        doc_type_stats[doc_type]["total_length"] += content_length
        
        # 추출 방법 통계
        extraction_method = metadata.get("extraction_method", "unknown")
        extraction_method_stats[extraction_method] += 1
        
        # 청크 유형 통계
        chunk_type = metadata.get("chunk_type", "unknown")
        chunk_type_stats[chunk_type] += 1
        
        # HS코드 및 법령 참조 수집
        hs_codes = metadata.get("hs_codes", [])
        law_refs = metadata.get("related_law_references", [])
        hs_codes_total += len(hs_codes) if hs_codes else 0
        law_refs_total += len(law_refs) if law_refs else 0
    
    # 평균 길이 계산
    for doc_type, stats in doc_type_stats.items():
        if stats["count"] > 0:
            stats["avg_length"] = stats["total_length"] // stats["count"]
    
    analysis["document_types"] = dict(doc_type_stats)
    analysis["extraction_methods"] = dict(extraction_method_stats)
    analysis["chunk_types"] = dict(chunk_type_stats)
    analysis["overview"]["source_documents"] = list(analysis["overview"]["source_documents"])
    
    # 내용 분석
    analysis["content_analysis"] = {
        "hs_codes_found": hs_codes_total,
        "law_references_found": law_refs_total,
        "avg_hs_codes_per_chunk": hs_codes_total / len(chunks) if chunks else 0,
        "avg_law_refs_per_chunk": law_refs_total / len(chunks) if chunks else 0
    }
    
    # 품질 지표
    analysis["quality_metrics"] = _calculate_quality_metrics(chunks)
    
    return analysis


def get_pdf_chunk_statistics(chunks: List[Dict]) -> Dict[str, Any]:
    """PDF 청크 통계 정보 생성
    
    Args:
        chunks (List[Dict]): 통계를 생성할 PDF 청크 리스트
        
    Returns:
        Dict[str, Any]: 통계 정보
    """
    if not chunks:
        return {"total_chunks": 0}
    
    stats = _generate_chunk_statistics(chunks)
    
    # PDF 특화 통계 추가
    pdf_specific_stats = {
        "table_based_chunks": 0,
        "text_based_chunks": 0,
        "pages_processed": set(),
        "tables_processed": 0,
        "categories": defaultdict(int)
    }
    
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        
        # 추출 방법별 통계
        extraction_method = metadata.get("extraction_method", "")
        if extraction_method == "table":
            pdf_specific_stats["table_based_chunks"] += 1
            if "table_index" in metadata:
                pdf_specific_stats["tables_processed"] += 1
        elif extraction_method == "text":
            pdf_specific_stats["text_based_chunks"] += 1
        
        # 페이지 정보 수집
        if "page_number" in metadata and metadata["page_number"]:
            pdf_specific_stats["pages_processed"].add(metadata["page_number"])
        
        # 카테고리별 통계
        category = metadata.get("category", "기타")
        pdf_specific_stats["categories"][category] += 1
    
    pdf_specific_stats["pages_processed"] = len(pdf_specific_stats["pages_processed"])
    pdf_specific_stats["categories"] = dict(pdf_specific_stats["categories"])
    
    stats.update(pdf_specific_stats)
    return stats


def merge_duplicate_chunks(chunks: List[Dict], similarity_threshold: float = 0.9) -> List[Dict]:
    """중복 또는 유사한 청크들을 병합
    
    Args:
        chunks (List[Dict]): 원본 청크 리스트
        similarity_threshold (float): 유사도 임계값 (0.0-1.0)
        
    Returns:
        List[Dict]: 중복 제거된 청크 리스트
    """
    if not chunks or len(chunks) <= 1:
        return chunks
    
    merged_chunks = []
    used_indices = set()
    
    for i, chunk in enumerate(chunks):
        if i in used_indices:
            continue
        
        # 현재 청크와 유사한 청크들 찾기
        similar_chunks = [chunk]
        similar_indices = [i]
        
        for j, other_chunk in enumerate(chunks[i+1:], i+1):
            if j in used_indices:
                continue
            
            similarity = _calculate_content_similarity(
                chunk.get("content", ""),
                other_chunk.get("content", "")
            )
            
            if similarity >= similarity_threshold:
                similar_chunks.append(other_chunk)
                similar_indices.append(j)
        
        # 유사한 청크들을 하나로 병합
        if len(similar_chunks) > 1:
            merged_chunk = _merge_similar_chunks(similar_chunks)
            merged_chunks.append(merged_chunk)
            used_indices.update(similar_indices)
            logger.info(f"{len(similar_chunks)}개의 유사 청크를 병합했습니다")
        else:
            merged_chunks.append(chunk)
            used_indices.add(i)
    
    logger.info(f"중복 제거 결과: {len(chunks)} -> {len(merged_chunks)} 청크")
    return merged_chunks


def enhance_pdf_metadata(chunks: List[Dict]) -> List[Dict]:
    """PDF 청크의 메타데이터를 보강
    
    Args:
        chunks (List[Dict]): 메타데이터를 보강할 청크 리스트
        
    Returns:
        List[Dict]: 메타데이터가 보강된 청크 리스트
    """
    enhanced_chunks = []
    
    # 전체 청크에서 공통 정보 추출
    all_hs_codes = set()
    all_law_refs = set()
    document_context = {}
    
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        
        # HS코드 수집
        hs_codes = metadata.get("hs_codes", [])
        if hs_codes:
            all_hs_codes.update(hs_codes)
        
        # 법령 참조 수집
        law_refs = metadata.get("related_law_references", [])
        if law_refs:
            all_law_refs.update(law_refs)
        
        # 문서 컨텍스트 구성
        doc_type = metadata.get("document_type")
        if doc_type:
            if doc_type not in document_context:
                document_context[doc_type] = {
                    "chunk_count": 0,
                    "categories": set(),
                    "extraction_methods": set()
                }
            
            document_context[doc_type]["chunk_count"] += 1
            document_context[doc_type]["categories"].add(metadata.get("category", ""))
            document_context[doc_type]["extraction_methods"].add(metadata.get("extraction_method", ""))
    
    # 각 청크의 메타데이터 보강
    for chunk in chunks:
        enhanced_chunk = chunk.copy()
        metadata = enhanced_chunk.get("metadata", {}).copy()
        
        # 전체 문서 컨텍스트 추가
        metadata["document_context"] = {
            "total_chunks_in_document": len(chunks),
            "total_hs_codes_in_document": len(all_hs_codes),
            "total_law_refs_in_document": len(all_law_refs),
            "document_types_in_collection": list(document_context.keys())
        }
        
        # 컨텐츠 품질 지표 추가
        content = chunk.get("content", "")
        metadata["content_quality"] = {
            "length": len(content),
            "word_count": len(content.split()) if content else 0,
            "sentence_count": len([s for s in content.split('.') if s.strip()]) if content else 0,
            "has_table_structure": bool(re.search(r'\|.*\|', content)),
            "has_numeric_data": bool(re.search(r'\d+', content))
        }
        
        # 관련성 점수 계산 (HS코드나 법령 참조가 많을수록 높은 점수)
        relevance_score = 0
        if metadata.get("hs_codes"):
            relevance_score += len(metadata["hs_codes"]) * 0.3
        if metadata.get("related_law_references"):
            relevance_score += len(metadata["related_law_references"]) * 0.2
        if content and len(content) > 100:
            relevance_score += 0.1
        
        metadata["relevance_score"] = min(relevance_score, 1.0)
        
        enhanced_chunk["metadata"] = metadata
        enhanced_chunks.append(enhanced_chunk)
    
    return enhanced_chunks


def export_pdf_chunks_summary(chunks: List[Dict], output_path: Path) -> bool:
    """PDF 청킹 결과 요약을 파일로 내보내기
    
    Args:
        chunks (List[Dict]): 요약할 청크 리스트
        output_path (Path): 출력 파일 경로
        
    Returns:
        bool: 내보내기 성공 여부
    """
    try:
        analysis = analyze_pdf_processing_results(chunks)
        statistics = get_pdf_chunk_statistics(chunks)
        
        summary = {
            "generation_info": {
                "timestamp": "placeholder",  # 실제 구현시 현재 시간 추가
                "total_chunks": len(chunks),
                "summary_version": "1.0"
            },
            "analysis": analysis,
            "statistics": statistics,
            "sample_chunks": chunks[:3] if chunks else []  # 샘플 청크 3개
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"PDF 청킹 요약이 저장되었습니다: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"PDF 청킹 요약 내보내기 실패: {e}")
        return False


def find_cross_document_references(chunks: List[Dict]) -> Dict[str, List[str]]:
    """문서 간 상호 참조 관계 찾기
    
    Args:
        chunks (List[Dict]): 분석할 청크 리스트
        
    Returns:
        Dict[str, List[str]]: 문서별 참조 관계 맵
    """
    references = defaultdict(list)
    
    # 문서별 그룹화
    documents = defaultdict(list)
    for chunk in chunks:
        source_pdf = chunk.get("metadata", {}).get("source_pdf", "unknown")
        documents[source_pdf].append(chunk)
    
    # 각 문서에서 다른 문서에 대한 참조 찾기
    for source_doc, source_chunks in documents.items():
        for chunk in source_chunks:
            content = chunk.get("content", "").lower()
            
            # 다른 문서들에 대한 언급 찾기
            for target_doc in documents.keys():
                if target_doc != source_doc and target_doc.lower() in content:
                    if target_doc not in references[source_doc]:
                        references[source_doc].append(target_doc)
    
    return dict(references)


# 내부 유틸리티 함수들

def _generate_chunk_statistics(chunks: List[Dict]) -> Dict[str, Any]:
    """청크 통계 정보 생성 (내부 함수)"""
    if not chunks:
        return {"total_chunks": 0}
    
    content_lengths = [len(chunk.get("content", "")) for chunk in chunks]
    
    return {
        "total_chunks": len(chunks),
        "total_content_length": sum(content_lengths),
        "average_content_length": sum(content_lengths) // len(chunks),
        "min_content_length": min(content_lengths),
        "max_content_length": max(content_lengths),
        "median_content_length": sorted(content_lengths)[len(content_lengths) // 2]
    }


def _calculate_quality_metrics(chunks: List[Dict]) -> Dict[str, float]:
    """품질 지표 계산 (내부 함수)"""
    if not chunks:
        return {}
    
    metrics = {
        "completeness_score": 0.0,  # 필수 필드 완성도
        "content_quality_score": 0.0,  # 내용 품질
        "metadata_richness_score": 0.0,  # 메타데이터 풍부도
        "extraction_success_rate": 0.0  # 추출 성공률
    }
    
    total_chunks = len(chunks)
    complete_chunks = 0
    quality_chunks = 0
    rich_metadata_chunks = 0
    successful_extractions = 0
    
    for chunk in chunks:
        # 완성도 체크
        if all(field in chunk for field in ["index", "title", "content", "metadata"]):
            complete_chunks += 1
        
        # 내용 품질 체크
        content = chunk.get("content", "")
        if content and len(content.strip()) > 50:
            quality_chunks += 1
        
        # 메타데이터 풍부도 체크
        metadata = chunk.get("metadata", {})
        rich_fields = ["hs_codes", "related_law_references", "page_number", "extraction_method"]
        if sum(1 for field in rich_fields if field in metadata and metadata[field]) >= 2:
            rich_metadata_chunks += 1
        
        # 추출 성공 체크
        if metadata.get("extraction_method") and content.strip():
            successful_extractions += 1
    
    metrics["completeness_score"] = complete_chunks / total_chunks
    metrics["content_quality_score"] = quality_chunks / total_chunks
    metrics["metadata_richness_score"] = rich_metadata_chunks / total_chunks
    metrics["extraction_success_rate"] = successful_extractions / total_chunks
    
    return metrics


def _calculate_content_similarity(content1: str, content2: str) -> float:
    """두 내용의 유사도 계산 (내부 함수)"""
    if not content1 or not content2:
        return 0.0
    
    # 간단한 단어 기반 유사도 계산
    words1 = set(content1.lower().split())
    words2 = set(content2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def _merge_similar_chunks(chunks: List[Dict]) -> Dict:
    """유사한 청크들을 하나로 병합 (내부 함수)"""
    if not chunks:
        return {}
    
    # 첫 번째 청크를 기준으로 병합
    base_chunk = chunks[0].copy()
    
    # 내용 병합
    merged_content = []
    for chunk in chunks:
        content = chunk.get("content", "").strip()
        if content and content not in merged_content:
            merged_content.append(content)
    
    base_chunk["content"] = "\n\n".join(merged_content)
    
    # 메타데이터 병합
    metadata = base_chunk.get("metadata", {}).copy()
    
    # 인덱스 병합
    indices = [chunk.get("index", "") for chunk in chunks if chunk.get("index")]
    if len(indices) > 1:
        metadata["merged_indices"] = indices
        base_chunk["index"] = f"merged_{indices[0]}"
    
    # HS코드 병합
    all_hs_codes = set()
    for chunk in chunks:
        hs_codes = chunk.get("metadata", {}).get("hs_codes", [])
        if hs_codes:
            all_hs_codes.update(hs_codes)
    if all_hs_codes:
        metadata["hs_codes"] = list(all_hs_codes)
    
    # 법령 참조 병합
    all_law_refs = set()
    for chunk in chunks:
        law_refs = chunk.get("metadata", {}).get("related_law_references", [])
        if law_refs:
            all_law_refs.update(law_refs)
    if all_law_refs:
        metadata["related_law_references"] = list(all_law_refs)
    
    metadata["merged_from"] = len(chunks)
    base_chunk["metadata"] = metadata
    
    return base_chunk