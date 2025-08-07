"""
Enhanced Data Processor Module

현재 JSON 구조(internal_law_references 포함)와 호환되는 데이터 처리
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from ..utils.file_utils import load_json_data, load_multiple_json_files
from ..utils.config import get_chunked_data_paths
from .embeddings import OpenAIEmbedder
from .vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class EnhancedDataProcessor:
    """내부 법령 참조를 활용한 향상된 데이터 처리기"""
    
    def __init__(self, 
                 embedder: OpenAIEmbedder,
                 vector_store: ChromaVectorStore):
        """
        초기화
        
        Args:
            embedder (OpenAIEmbedder): 임베딩 생성기
            vector_store (ChromaVectorStore): 벡터 저장소
        """
        self.embedder = embedder
        self.vector_store = vector_store
        
        # 데이터 통계
        self.processing_stats = {
            "total_documents": 0,
            "documents_by_law": {},
            "chunk_types": {},
            "internal_references": 0,
            "external_references": 0
        }
        
        logger.info("EnhancedDataProcessor initialized")
    
    def load_and_process_all_laws(self, reset_db: bool = True) -> Dict[str, Any]:
        """
        모든 법령 데이터를 로드하고 처리
        
        Args:
            reset_db (bool): 기존 데이터베이스 재설정 여부
            
        Returns:
            Dict[str, Any]: 처리 결과 및 통계
        """
        try:
            # 1. 청킹된 법령 데이터 경로 가져오기
            law_paths = get_chunked_data_paths()
            logger.info(f"청킹된 법령 데이터 로드 시작: {len(law_paths)}개 파일")
            
            # 2. JSON 데이터 로드
            all_documents = []
            for law_name, file_path in law_paths.items():
                documents = self._load_law_documents(file_path, law_name)
                if documents:
                    all_documents.extend(documents)
                    self.processing_stats["documents_by_law"][law_name] = len(documents)
                    logger.info(f"{law_name}: {len(documents)}개 문서 로드")
            
            if not all_documents:
                raise ValueError("로드된 문서가 없습니다.")
            
            # 3. 데이터 통계 업데이트
            self._update_statistics(all_documents)
            
            # 4. 임베딩 생성
            logger.info("임베딩 생성 시작...")
            embedded_documents = self.embedder.embed_documents(all_documents)
            
            # 5. 벡터 데이터베이스에 저장
            logger.info("벡터 데이터베이스 저장 시작...")
            self.vector_store.create_collection(reset=reset_db)
            self.vector_store.add_documents(embedded_documents)
            
            # 6. 내부 참조 분석 및 검증
            reference_analysis = self._analyze_internal_references(embedded_documents)
            
            processing_result = {
                "status": "success",
                "statistics": self.processing_stats,
                "reference_analysis": reference_analysis,
                "vector_store_stats": self.vector_store.get_collection_stats()
            }
            
            logger.info(f"데이터 처리 완료: 총 {len(embedded_documents)}개 문서")
            return processing_result
            
        except Exception as e:
            logger.error(f"데이터 처리 실패: {e}")
            return {
                "status": "error",
                "error": str(e),
                "statistics": self.processing_stats
            }
    
    def load_specific_law(self, law_name: str) -> List[Dict[str, Any]]:
        """
        특정 법령의 데이터만 로드
        
        Args:
            law_name (str): 법령명 (관세법, 관세법시행령, 관세법시행규칙)
            
        Returns:
            List[Dict[str, Any]]: 로드된 문서 리스트
        """
        try:
            law_paths = get_chunked_data_paths()
            
            if law_name not in law_paths:
                available_laws = list(law_paths.keys())
                raise ValueError(f"지원하지 않는 법령명입니다. 사용 가능: {available_laws}")
            
            file_path = law_paths[law_name]
            documents = self._load_law_documents(file_path, law_name)
            
            logger.info(f"{law_name}: {len(documents)}개 문서 로드 완료")
            return documents
            
        except Exception as e:
            logger.error(f"특정 법령 로드 실패 ({law_name}): {e}")
            return []
    
    def validate_document_structure(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서 구조 유효성 검사
        
        Args:
            documents (List[Dict[str, Any]]): 검사할 문서들
            
        Returns:
            Dict[str, Any]: 검사 결과
        """
        validation_result = {
            "total_documents": len(documents),
            "valid_documents": 0,
            "issues": [],
            "structure_analysis": {}
        }
        
        required_fields = ["index", "content", "metadata"]
        recommended_metadata_fields = [
            "law_name", "law_level", "chunk_type", 
            "internal_law_references", "hierarchy_path"
        ]
        
        for i, doc in enumerate(documents):
            issues = []
            
            # 필수 필드 검사
            for field in required_fields:
                if field not in doc:
                    issues.append(f"필수 필드 누락: {field}")
            
            # 메타데이터 검사
            if "metadata" in doc:
                metadata = doc["metadata"]
                for field in recommended_metadata_fields:
                    if field not in metadata:
                        issues.append(f"권장 메타데이터 필드 누락: {field}")
                
                # 내부 참조 구조 검사
                if "internal_law_references" in metadata:
                    internal_refs = metadata["internal_law_references"]
                    if not isinstance(internal_refs, dict):
                        issues.append("internal_law_references가 dict 타입이 아님")
            
            if not issues:
                validation_result["valid_documents"] += 1
            else:
                validation_result["issues"].append({
                    "document_index": i,
                    "document_id": doc.get("index", "Unknown"),
                    "issues": issues
                })
        
        # 구조 분석
        validation_result["structure_analysis"] = self._analyze_document_structure(documents)
        
        return validation_result
    
    def extract_reference_network(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서 간 참조 네트워크 추출
        
        Args:
            documents (List[Dict[str, Any]]): 분석할 문서들
            
        Returns:
            Dict[str, Any]: 참조 네트워크 정보
        """
        network = {
            "nodes": [],  # 문서들
            "edges": [],  # 참조 관계들
            "statistics": {}
        }
        
        # 문서 인덱스 매핑 생성
        doc_index_map = {}
        for doc in documents:
            doc_id = doc.get("index", "")
            if doc_id:
                doc_index_map[doc_id] = doc
                
                # 노드 정보 추가
                node = {
                    "id": doc_id,
                    "law_name": doc.get("metadata", {}).get("law_name", ""),
                    "subtitle": doc.get("subtitle", ""),
                    "chunk_type": doc.get("metadata", {}).get("chunk_type", "")
                }
                network["nodes"].append(node)
        
        # 참조 관계 추출
        reference_count = 0
        for doc in documents:
            source_id = doc.get("index", "")
            if not source_id:
                continue
            
            metadata = doc.get("metadata", {})
            internal_refs = metadata.get("internal_law_references", {})
            
            # 각 참조 유형별로 간선 생성
            for ref_type, ref_list in internal_refs.items():
                if not isinstance(ref_list, list):
                    continue
                    
                for target_ref in ref_list:
                    if target_ref in doc_index_map:
                        edge = {
                            "source": source_id,
                            "target": target_ref,
                            "reference_type": ref_type,
                            "weight": 1.0
                        }
                        network["edges"].append(edge)
                        reference_count += 1
        
        # 통계 정보
        network["statistics"] = {
            "total_nodes": len(network["nodes"]),
            "total_edges": len(network["edges"]),
            "total_references": reference_count,
            "average_references_per_document": reference_count / len(documents) if documents else 0
        }
        
        return network
    
    def _load_law_documents(self, file_path: str, law_name: str) -> List[Dict[str, Any]]:
        """
        개별 법령 파일에서 문서 로드
        
        Args:
            file_path (str): 파일 경로
            law_name (str): 법령명
            
        Returns:
            List[Dict[str, Any]]: 로드된 문서 리스트
        """
        try:
            data = load_json_data(file_path)
            if not data:
                logger.warning(f"데이터 로드 실패: {file_path}")
                return []
            
            documents = []
            
            # 데이터가 리스트인지 딕셔너리인지 확인
            if isinstance(data, list):
                documents = data
            elif isinstance(data, dict):
                # 딕셔너리라면 값들을 리스트로 변환
                documents = list(data.values())
            else:
                logger.error(f"지원하지 않는 데이터 형식: {type(data)}")
                return []
            
            # 각 문서에 법령명 정보 추가/확인
            for doc in documents:
                if "metadata" not in doc:
                    doc["metadata"] = {}
                
                # 법령명이 없거나 다르면 업데이트
                if not doc["metadata"].get("law_name"):
                    doc["metadata"]["law_name"] = law_name
            
            return documents
            
        except Exception as e:
            logger.error(f"법령 문서 로드 실패 ({file_path}): {e}")
            return []
    
    def _update_statistics(self, documents: List[Dict[str, Any]]) -> None:
        """데이터 통계 업데이트"""
        self.processing_stats["total_documents"] = len(documents)
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            
            # 청킹 타입 통계
            chunk_type = metadata.get("chunk_type", "unknown")
            self.processing_stats["chunk_types"][chunk_type] = \
                self.processing_stats["chunk_types"].get(chunk_type, 0) + 1
            
            # 내부/외부 참조 통계
            internal_refs = metadata.get("internal_law_references", {})
            if internal_refs:
                for ref_type, ref_list in internal_refs.items():
                    if isinstance(ref_list, list) and ref_list:
                        self.processing_stats["internal_references"] += len(ref_list)
            
            external_refs = metadata.get("external_law_references", [])
            if isinstance(external_refs, list):
                self.processing_stats["external_references"] += len(external_refs)
    
    def _analyze_internal_references(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """내부 참조 분석"""
        analysis = {
            "reference_types": {},
            "most_referenced_articles": {},
            "orphaned_references": [],
            "circular_references": []
        }
        
        # 문서 ID 세트 생성
        document_ids = {doc.get("index", "") for doc in documents if doc.get("index")}
        
        # 참조 분석
        reference_counts = {}
        
        for doc in documents:
            doc_id = doc.get("index", "")
            metadata = doc.get("metadata", {})
            internal_refs = metadata.get("internal_law_references", {})
            
            for ref_type, ref_list in internal_refs.items():
                if not isinstance(ref_list, list):
                    continue
                
                # 참조 타입별 통계
                analysis["reference_types"][ref_type] = \
                    analysis["reference_types"].get(ref_type, 0) + len(ref_list)
                
                for target_ref in ref_list:
                    # 참조 횟수 카운트
                    reference_counts[target_ref] = reference_counts.get(target_ref, 0) + 1
                    
                    # 고아 참조 확인 (참조는 하지만 실제 문서가 없는 경우)
                    if target_ref not in document_ids:
                        analysis["orphaned_references"].append({
                            "source": doc_id,
                            "target": target_ref,
                            "reference_type": ref_type
                        })
        
        # 가장 많이 참조되는 조문들
        sorted_refs = sorted(reference_counts.items(), key=lambda x: x[1], reverse=True)
        analysis["most_referenced_articles"] = dict(sorted_refs[:10])
        
        return analysis
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        문서들을 처리하여 임베딩을 추가
        
        Args:
            documents (List[Dict[str, Any]]): 처리할 문서들
            
        Returns:
            List[Dict[str, Any]]: 임베딩이 추가된 문서들
        """
        try:
            if not documents:
                logger.warning("처리할 문서가 없습니다.")
                return []
            
            # 임베딩 생성
            embedded_documents = self.embedder.embed_documents(documents)
            
            logger.info(f"문서 처리 완료: {len(embedded_documents)}개 문서")
            return embedded_documents
            
        except Exception as e:
            logger.error(f"문서 처리 실패: {e}")
            return []
    
    def _analyze_document_structure(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """문서 구조 분석"""
        structure_stats = {
            "field_presence": {},
            "content_length_stats": {},
            "metadata_field_stats": {}
        }
        
        if not documents:
            return structure_stats
        
        # 필드 존재 통계
        field_counts = {}
        content_lengths = []
        metadata_field_counts = {}
        
        for doc in documents:
            # 최상위 필드 통계
            for field in doc.keys():
                field_counts[field] = field_counts.get(field, 0) + 1
            
            # 콘텐츠 길이 통계
            content = doc.get("content", "")
            content_lengths.append(len(content))
            
            # 메타데이터 필드 통계
            metadata = doc.get("metadata", {})
            for meta_field in metadata.keys():
                metadata_field_counts[meta_field] = \
                    metadata_field_counts.get(meta_field, 0) + 1
        
        # 통계 계산
        total_docs = len(documents)
        
        structure_stats["field_presence"] = {
            field: {"count": count, "percentage": count/total_docs*100}
            for field, count in field_counts.items()
        }
        
        if content_lengths:
            structure_stats["content_length_stats"] = {
                "min": min(content_lengths),
                "max": max(content_lengths),
                "average": sum(content_lengths) / len(content_lengths),
                "median": sorted(content_lengths)[len(content_lengths)//2]
            }
        
        structure_stats["metadata_field_stats"] = {
            field: {"count": count, "percentage": count/total_docs*100}
            for field, count in metadata_field_counts.items()
        }
        
        return structure_stats


# 하위 호환성을 위한 alias
RAGDataProcessor = EnhancedDataProcessor