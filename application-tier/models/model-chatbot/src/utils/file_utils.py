"""
File Utilities Module

파일 입출력 관련 유틸리티 함수들을 제공합니다.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def save_processed_documents(documents: List[Dict[str, Any]], output_path: str) -> bool:
    """처리된 문서들을 JSON으로 저장
    
    Args:
        documents (List[Dict[str, Any]]): 저장할 문서 리스트
        output_path (str): 출력 파일 경로
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        output_path = Path(output_path)
        
        # 디렉토리가 없으면 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully saved {len(documents)} documents to {output_path}")
        print(f"✅ {len(documents)}개 문서가 {output_path}에 저장되었습니다.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save documents to {output_path}: {e}")
        print(f"❌ 파일 저장 실패: {e}")
        return False


def load_json_data(file_path: str) -> Optional[Dict[str, Any]]:
    """JSON 파일에서 데이터 로드
    
    Args:
        file_path (str): JSON 파일 경로
        
    Returns:
        Optional[Dict[str, Any]]: 로드된 데이터 (실패시 None)
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded data from {file_path}")
        print(f"✅ 데이터 로드 완료: {file_path}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in {file_path}: {e}")
        print(f"❌ JSON 형식 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load data from {file_path}: {e}")
        print(f"❌ 파일 로드 실패: {e}")
        return None


def load_multiple_json_files(file_paths: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
    """여러 JSON 파일을 한번에 로드
    
    Args:
        file_paths (List[str]): JSON 파일 경로들
        
    Returns:
        Dict[str, Optional[Dict[str, Any]]]: 파일명을 키로 하는 데이터 딕셔너리
    """
    results = {}
    
    for file_path in file_paths:
        file_name = Path(file_path).stem  # 확장자 제외한 파일명
        results[file_name] = load_json_data(file_path)
    
    return results


def validate_json_structure(data: Dict[str, Any], expected_structure: Dict[str, Any]) -> List[str]:
    """JSON 데이터 구조 유효성 검사
    
    Args:
        data (Dict[str, Any]): 검사할 데이터
        expected_structure (Dict[str, Any]): 예상 구조
        
    Returns:
        List[str]: 발견된 문제점들
    """
    issues = []
    
    def check_structure(current_data, expected, path=""):
        if isinstance(expected, dict):
            if not isinstance(current_data, dict):
                issues.append(f"{path}: Expected dict, got {type(current_data)}")
                return
                
            for key, expected_value in expected.items():
                if key not in current_data:
                    issues.append(f"{path}.{key}: Missing required key")
                else:
                    check_structure(current_data[key], expected_value, f"{path}.{key}")
                    
        elif isinstance(expected, list):
            if not isinstance(current_data, list):
                issues.append(f"{path}: Expected list, got {type(current_data)}")
                return
                
            if expected and len(current_data) > 0:
                # 첫 번째 요소의 구조 검사
                check_structure(current_data[0], expected[0], f"{path}[0]")
    
    check_structure(data, expected_structure)
    return issues


def get_file_info(file_path: str) -> Dict[str, Any]:
    """파일 정보 조회
    
    Args:
        file_path (str): 파일 경로
        
    Returns:
        Dict[str, Any]: 파일 정보
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {"exists": False, "path": str(path)}
        
        stat = path.stat()
        
        return {
            "exists": True,
            "path": str(path),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": stat.st_mtime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "extension": path.suffix
        }
        
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return {"exists": False, "error": str(e)}


def backup_file(file_path: str, backup_suffix: str = ".backup") -> bool:
    """파일 백업 생성
    
    Args:
        file_path (str): 백업할 파일 경로
        backup_suffix (str): 백업 파일 접미사
        
    Returns:
        bool: 백업 성공 여부
    """
    try:
        source = Path(file_path)
        
        if not source.exists():
            logger.warning(f"Source file does not exist: {source}")
            return False
        
        backup_path = source.with_name(f"{source.name}{backup_suffix}")
        
        # 백업 파일이 이미 존재하면 타임스탬프 추가
        counter = 1
        while backup_path.exists():
            backup_path = source.with_name(f"{source.name}{backup_suffix}.{counter}")
            counter += 1
        
        import shutil
        shutil.copy2(source, backup_path)
        
        logger.info(f"Backup created: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False


def save_chunks_as_jsonl(chunks: List[Dict[str, Any]], output_path: str) -> bool:
    """청크들을 JSONL 형식으로 저장
    
    Args:
        chunks (List[Dict[str, Any]]): 저장할 청크 리스트
        output_path (str): 출력 파일 경로 (.jsonl)
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        output_path = Path(output_path)
        
        # 디렉토리가 없으면 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json_line = json.dumps(chunk, ensure_ascii=False)
                f.write(json_line + '\n')
        
        logger.info(f"Successfully saved {len(chunks)} chunks to JSONL: {output_path}")
        print(f"✅ {len(chunks)}개 청크가 JSONL 형식으로 {output_path}에 저장되었습니다.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save chunks as JSONL to {output_path}: {e}")
        print(f"❌ JSONL 저장 실패: {e}")
        return False


def load_chunks_from_jsonl(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """JSONL 파일에서 청크들 로드
    
    Args:
        file_path (str): JSONL 파일 경로
        
    Returns:
        Optional[List[Dict[str, Any]]]: 로드된 청크 리스트 (실패시 None)
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"JSONL file not found: {file_path}")
            print(f"❌ JSONL 파일을 찾을 수 없습니다: {file_path}")
            return None
        
        chunks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # 빈 줄 스킵
                    continue
                    
                try:
                    chunk = json.loads(line)
                    chunks.append(chunk)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON on line {line_num} in {file_path}: {e}")
                    print(f"⚠️ {line_num}번째 줄 JSON 오류 (건너뜀): {e}")
                    continue
        
        logger.info(f"Successfully loaded {len(chunks)} chunks from JSONL: {file_path}")
        print(f"✅ JSONL에서 {len(chunks)}개 청크 로드 완료: {file_path}")
        return chunks
        
    except Exception as e:
        logger.error(f"Failed to load chunks from JSONL {file_path}: {e}")
        print(f"❌ JSONL 로드 실패: {e}")
        return None


def append_chunk_to_jsonl(chunk: Dict[str, Any], file_path: str) -> bool:
    """JSONL 파일에 새로운 청크 추가
    
    Args:
        chunk (Dict[str, Any]): 추가할 청크
        file_path (str): JSONL 파일 경로
        
    Returns:
        bool: 추가 성공 여부
    """
    try:
        file_path = Path(file_path)
        
        # 디렉토리가 없으면 생성
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'a', encoding='utf-8') as f:
            json_line = json.dumps(chunk, ensure_ascii=False)
            f.write(json_line + '\n')
        
        logger.info(f"Successfully appended chunk to JSONL: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to append chunk to JSONL {file_path}: {e}")
        print(f"❌ JSONL 추가 실패: {e}")
        return False


def count_jsonl_lines(file_path: str) -> int:
    """JSONL 파일의 라인 수 (청크 수) 계산
    
    Args:
        file_path (str): JSONL 파일 경로
        
    Returns:
        int: 라인 수 (실패시 -1)
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return -1
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # 빈 줄은 제외
                    count += 1
        
        return count
        
    except Exception as e:
        logger.error(f"Failed to count JSONL lines in {file_path}: {e}")
        return -1


def validate_jsonl_file(file_path: str) -> Dict[str, Any]:
    """JSONL 파일 유효성 검사
    
    Args:
        file_path (str): JSONL 파일 경로
        
    Returns:
        Dict[str, Any]: 검사 결과
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "is_valid": False,
                "error": "File not found",
                "total_lines": 0,
                "valid_lines": 0,
                "invalid_lines": []
            }
        
        total_lines = 0
        valid_lines = 0
        invalid_lines = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # 빈 줄은 건너뜀
                    continue
                    
                total_lines += 1
                try:
                    json.loads(line)
                    valid_lines += 1
                except json.JSONDecodeError as e:
                    invalid_lines.append({
                        "line_number": line_num,
                        "error": str(e),
                        "content": line[:100] + "..." if len(line) > 100 else line
                    })
        
        is_valid = len(invalid_lines) == 0
        
        result = {
            "is_valid": is_valid,
            "total_lines": total_lines,
            "valid_lines": valid_lines,
            "invalid_lines": invalid_lines,
            "error_count": len(invalid_lines)
        }
        
        if is_valid:
            logger.info(f"JSONL file is valid: {file_path} ({total_lines} lines)")
        else:
            logger.warning(f"JSONL file has {len(invalid_lines)} invalid lines: {file_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to validate JSONL file {file_path}: {e}")
        return {
            "is_valid": False,
            "error": str(e),
            "total_lines": 0,
            "valid_lines": 0,
            "invalid_lines": []
        }


def ensure_directory_exists(directory_path: str) -> bool:
    """디렉토리 존재 확인 및 생성
    
    Args:
        directory_path (str): 디렉토리 경로
        
    Returns:
        bool: 성공 여부
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False