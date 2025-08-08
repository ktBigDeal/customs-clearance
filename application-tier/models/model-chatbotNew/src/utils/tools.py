"""
Common Tools Module

공통 도구 및 유틸리티 함수들을 통합 관리하는 모듈
"""

import logging
import json
import re
import hashlib
from typing import List, Dict, Any, Set, Callable, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Deduplication Functions
# ============================================================================

def deduplicate_by_id(results: List[Dict[str, Any]], id_key: str = "id") -> List[Dict[str, Any]]:
    """
    ID 기반 중복 제거
    
    Args:
        results: 중복 제거할 결과 리스트
        id_key: ID 필드명
        
    Returns:
        중복 제거된 결과 리스트
    """
    seen_ids: Set[str] = set()
    unique_results = []
    
    for result in results:
        result_id = result.get(id_key, "")
        if result_id and result_id not in seen_ids:
            seen_ids.add(result_id)
            unique_results.append(result)
    
    return unique_results


def deduplicate_by_content(results: List[Dict[str, Any]], 
                          content_key: str = "content",
                          similarity_threshold: float = 0.9) -> List[Dict[str, Any]]:
    """
    내용 기반 중복 제거 (간단한 해시 기반)
    
    Args:
        results: 중복 제거할 결과 리스트
        content_key: 내용 필드명
        similarity_threshold: 유사도 임계값 (현재 미사용, 향후 구현용)
        
    Returns:
        중복 제거된 결과 리스트
    """
    seen_hashes: Set[str] = set()
    unique_results = []
    
    for result in results:
        content = result.get(content_key, "")
        if content:
            # 내용 해시 생성
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(result)
        else:
            unique_results.append(result)  # 내용이 없는 경우 유지
    
    return unique_results


def deduplicate_by_custom_key(results: List[Dict[str, Any]], 
                             key_extractor: Callable[[Dict[str, Any]], str]) -> List[Dict[str, Any]]:
    """
    사용자 정의 키 기반 중복 제거
    
    Args:
        results: 중복 제거할 결과 리스트
        key_extractor: 각 결과에서 고유 키를 추출하는 함수
        
    Returns:
        중복 제거된 결과 리스트
    """
    seen_keys: Set[str] = set()
    unique_results = []
    
    for result in results:
        try:
            key = key_extractor(result)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_results.append(result)
        except Exception:
            # 키 추출 실패 시 결과 유지
            unique_results.append(result)
    
    return unique_results


def smart_deduplicate(results: List[Dict[str, Any]], 
                     id_key: str = "id",
                     content_key: str = "content",
                     preserve_higher_score: bool = True,
                     score_key: str = "similarity") -> List[Dict[str, Any]]:
    """
    지능형 중복 제거 - ID 우선, 내용 보조, 점수 기반 선택
    
    Args:
        results: 중복 제거할 결과 리스트
        id_key: ID 필드명
        content_key: 내용 필드명
        preserve_higher_score: 높은 점수 결과 우선 여부
        score_key: 점수 필드명
        
    Returns:
        중복 제거된 결과 리스트
    """
    # 1단계: ID 기반 중복 제거 (점수 고려)
    id_map: Dict[str, Dict[str, Any]] = {}
    
    for result in results:
        result_id = result.get(id_key, "")
        if not result_id:
            continue
            
        current_score = result.get(score_key, 0.0)
        
        if result_id in id_map:
            existing_score = id_map[result_id].get(score_key, 0.0)
            if preserve_higher_score and current_score > existing_score:
                id_map[result_id] = result
            elif not preserve_higher_score and current_score < existing_score:
                id_map[result_id] = result
        else:
            id_map[result_id] = result
    
    # 2단계: 내용 기반 중복 제거 (ID가 없는 결과들)
    no_id_results = [r for r in results if not r.get(id_key)]
    content_deduped = deduplicate_by_content(no_id_results, content_key)
    
    # 결합
    final_results = list(id_map.values()) + content_deduped
    
    return final_results


# ============================================================================
# Other Utility Functions
# ============================================================================


def format_search_results(results: List[Dict[str, Any]], max_display: int = 5) -> str:
    """검색 결과를 사용자 친화적 형태로 포맷팅"""
    if not results:
        return "검색 결과가 없습니다."
    
    formatted = []
    for i, result in enumerate(results[:max_display], 1):
        metadata = result.get("metadata", {})
        content_preview = result.get("content", "")[:100] + "..." if len(result.get("content", "")) > 100 else result.get("content", "")
        
        formatted.append(f"{i}. {metadata.get('index', 'N/A')} - {metadata.get('subtitle', 'N/A')}")
        formatted.append(f"   {content_preview}")
        formatted.append(f"   유사도: {result.get('similarity', 0):.3f}")
        formatted.append("")
    
    return "\n".join(formatted)


def validate_agent_response(response: str) -> bool:
    """에이전트 응답의 유효성 검증"""
    if not response or not response.strip():
        return False
    
    # 최소 길이 체크
    if len(response.strip()) < 10:
        return False
        
    # 오류 메시지 체크
    error_indicators = ["오류", "실패", "에러", "error", "failed"]
    if any(indicator in response.lower() for indicator in error_indicators):
        return False
        
    return True


def extract_key_concepts(text: str, max_concepts: int = 5) -> List[str]:
    """텍스트에서 핵심 개념 추출"""
    # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용 가능)
    import re
    
    # 한국어 단어 추출
    korean_words = re.findall(r'[가-힣]{2,}', text)
    
    # 빈도 계산
    word_freq = {}
    for word in korean_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # 상위 개념들 반환
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_concepts]]


def safe_json_parse(json_str: str, default: Any = None) -> Any:
    """안전한 JSON 파싱"""
    try:
        import json
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        logger.warning(f"JSON 파싱 실패: {json_str[:100]}...")
        return default


__all__ = [
    'deduplicate_by_id', 'deduplicate_by_content', 'smart_deduplicate', 'deduplicate_by_custom_key',
    'format_search_results', 'validate_agent_response', 
    'extract_key_concepts', 'safe_json_parse'
]