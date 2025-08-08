"""
LangChain Chroma Vector Store Module

LangChain 표준 Chroma 벡터 스토어와 도메인 특화 기능을 결합
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class LangChainVectorStore:
    """LangChain 표준 Chroma를 사용한 벡터 저장소 (Docker ChromaDB 지원)"""
    
    def __init__(self, 
                 db_path: str = "data/chroma_db",
                 collection_name: str = "universal_collection",
                 embedding_function: Optional[OpenAIEmbeddings] = None,
                 use_docker_chromadb: bool = True,
                 chromadb_host: str = "localhost",
                 chromadb_port: int = 8011):
        """
        초기화
        
        Args:
            db_path (str): ChromaDB 저장 경로 (use_docker_chromadb=False일 때만 사용)
            collection_name (str): 컬렉션 이름
            embedding_function (Optional[OpenAIEmbeddings]): 임베딩 함수
            use_docker_chromadb (bool): Docker ChromaDB 사용 여부
            chromadb_host (str): ChromaDB 호스트 주소
            chromadb_port (int): ChromaDB 포트 번호
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.use_docker_chromadb = use_docker_chromadb
        self.chromadb_host = chromadb_host
        self.chromadb_port = chromadb_port
        
        # 로컬 파일 기반 모드에서만 디렉토리 생성
        if not use_docker_chromadb:
            self.db_path.mkdir(parents=True, exist_ok=True)
        
        # 임베딩 함수 설정
        if embedding_function is None:
            # OpenAI API 키 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set. "
                    "Please check your .env file or set the environment variable directly."
                )
            self.embedding_function = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key
            )
        else:
            self.embedding_function = embedding_function
        
        # ChromaDB 클라이언트 설정
        if use_docker_chromadb:
            # Docker ChromaDB HTTP 클라이언트 사용
            import chromadb
            self._chroma_client = chromadb.HttpClient(
                host=chromadb_host, 
                port=chromadb_port
            )
            
            # LangChain Chroma 벡터스토어 초기화 (Docker 모드)
            self.vectorstore = Chroma(
                client=self._chroma_client,
                collection_name=collection_name,
                embedding_function=self.embedding_function
            )
            
            logger.info(f"LangChain Vector Store initialized with Docker ChromaDB at: {chromadb_host}:{chromadb_port}")
        else:
            # 기존 로컬 파일 기반 모드
            self.vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embedding_function,
                persist_directory=str(self.db_path)
            )
            
            logger.info(f"LangChain Vector Store initialized at: {self.db_path}")
    
    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 50) -> List[str]:
        """
        문서들을 배치 단위로 벡터 스토어에 추가 (토큰 제한 회피)
        
        Args:
            documents (List[Dict[str, Any]]): 추가할 문서 리스트
            batch_size (int): 배치 크기 (기본값: 50)
            
        Returns:
            List[str]: 추가된 문서들의 ID 리스트
        """
        try:
            all_ids = []
            total_docs = len(documents)
            
            logger.info(f"Adding {total_docs} documents in batches of {batch_size}")
            
            # 배치 단위로 문서 처리
            for batch_start in range(0, total_docs, batch_size):
                batch_end = min(batch_start + batch_size, total_docs)
                batch_docs = documents[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} ({len(batch_docs)} docs)")
                
                # 딕셔너리를 LangChain Document로 변환
                langchain_docs = []
                metadatas = []
                
                for i, doc in enumerate(batch_docs):
                    content = doc.get("content", "")
                    metadata = doc.get("metadata", {})
                    
                    # enhanced_content가 있으면 사용
                    if "enhanced_content" in doc:
                        content = doc["enhanced_content"]
                    
                    # 메타데이터 평면화 (LangChain Chroma 호환성)
                    flattened_metadata = self._flatten_metadata(metadata)
                    
                    # Document ID 생성 (전체 인덱스 사용)
                    doc_id = self._generate_document_id(doc, batch_start + i)
                    flattened_metadata["doc_id"] = doc_id
                    
                    langchain_docs.append(Document(
                        page_content=content,
                        metadata=flattened_metadata
                    ))
                    metadatas.append(flattened_metadata)
                
                # 벡터스토어에 배치 문서 추가
                try:
                    batch_ids = self.vectorstore.add_documents(
                        documents=langchain_docs,
                        ids=[meta["doc_id"] for meta in metadatas]
                    )
                    all_ids.extend(batch_ids)
                    logger.info(f"Successfully added batch {batch_start//batch_size + 1} ({len(batch_ids)} docs)")
                    
                except Exception as batch_error:
                    logger.warning(f"Failed to add batch {batch_start//batch_size + 1}, trying smaller batch size: {batch_error}")
                    
                    # 배치 크기를 절반으로 줄여서 재시도
                    smaller_batch_size = max(1, batch_size // 2)
                    for mini_batch_start in range(0, len(batch_docs), smaller_batch_size):
                        mini_batch_end = min(mini_batch_start + smaller_batch_size, len(batch_docs))
                        mini_batch = batch_docs[mini_batch_start:mini_batch_end]
                        
                        # 미니 배치 처리
                        mini_langchain_docs = []
                        mini_metadatas = []
                        
                        for i, doc in enumerate(mini_batch):
                            content = doc.get("content", "")
                            metadata = doc.get("metadata", {})
                            
                            if "enhanced_content" in doc:
                                content = doc["enhanced_content"]
                            
                            flattened_metadata = self._flatten_metadata(metadata)
                            doc_id = self._generate_document_id(doc, batch_start + mini_batch_start + i)
                            flattened_metadata["doc_id"] = doc_id
                            
                            mini_langchain_docs.append(Document(
                                page_content=content,
                                metadata=flattened_metadata
                            ))
                            mini_metadatas.append(flattened_metadata)
                        
                        mini_ids = self.vectorstore.add_documents(
                            documents=mini_langchain_docs,
                            ids=[meta["doc_id"] for meta in mini_metadatas]
                        )
                        all_ids.extend(mini_ids)
                        logger.info(f"Added mini-batch {mini_batch_start//smaller_batch_size + 1} ({len(mini_ids)} docs)")
            
            logger.info(f"Successfully added {len(all_ids)} total documents to vector store")
            return all_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def search_similar(self, 
                      query_embedding: Optional[List[float]] = None,
                      query_text: Optional[str] = None,
                      top_k: int = 5,
                      where: Optional[Dict[str, Any]] = None,
                      search_type: str = "similarity") -> List[Dict[str, Any]]:
        """
        유사도 검색 수행
        
        Args:
            query_embedding (Optional[List[float]]): 쿼리 임베딩 벡터
            query_text (Optional[str]): 쿼리 텍스트 (임베딩이 없을 경우)
            top_k (int): 반환할 결과 수
            where (Optional[Dict[str, Any]]): 메타데이터 필터 조건
            search_type (str): 검색 타입 ("similarity", "mmr", "similarity_score_threshold")
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 리스트
        """
        try:
            # 검색 파라미터 설정
            search_kwargs = {"k": top_k}
            if where:
                search_kwargs["filter"] = where
            
            # MMR 검색을 위한 추가 파라미터
            if search_type == "mmr":
                search_kwargs["fetch_k"] = min(top_k * 2, 20)
                search_kwargs["lambda_mult"] = 0.7
            elif search_type == "similarity_score_threshold":
                search_kwargs["score_threshold"] = 0.7
            
            # Retriever 생성
            retriever = self.vectorstore.as_retriever(
                search_type=search_type,
                search_kwargs=search_kwargs
            )
            
            # 검색 실행
            if query_text:
                docs = retriever.invoke(query_text)
            elif query_embedding:
                # 임베딩으로 직접 검색 (similarity_search_by_vector 사용)
                docs = self.vectorstore.similarity_search_by_vector(
                    embedding=query_embedding,
                    k=top_k,
                    filter=where
                )
            else:
                raise ValueError("Either query_text or query_embedding must be provided")
            
            # Document를 딕셔너리 형태로 변환 (유사도 점수 포함)
            results = []
            
            # 점수와 함께 검색하여 실제 유사도 획득
            if query_text:
                docs_with_scores = self.vectorstore.similarity_search_with_score(
                    query=query_text,
                    k=top_k,
                    filter=where
                )
                for doc, score in docs_with_scores:
                    result = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": float(score),  # 실제 유사도 점수
                        "score": float(score)  # legacy 호환성
                    }
                    results.append(result)
            else:
                # 임베딩 검색의 경우 점수 없이 처리
                for doc in docs:
                    result = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": 0.0,  # 임베딩 검색은 점수 없음
                        "score": 0.0
                    }
                    results.append(result)
            
            logger.debug(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            raise
    
    def search_with_score(self,
                         query_text: str,
                         top_k: int = 5,
                         where: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """
        점수와 함께 유사도 검색 수행
        
        Args:
            query_text (str): 쿼리 텍스트
            top_k (int): 반환할 결과 수
            where (Optional[Dict[str, Any]]): 메타데이터 필터 조건
            
        Returns:
            List[tuple]: (Document, score) 튜플 리스트
        """
        try:
            return self.vectorstore.similarity_search_with_score(
                query=query_text,
                k=top_k,
                filter=where
            )
        except Exception as e:
            logger.error(f"Failed to search with score: {e}")
            raise
    
    def get_retriever(self, 
                     search_type: str = "similarity",
                     search_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """
        LangChain Retriever 객체 반환
        
        Args:
            search_type (str): 검색 타입
            search_kwargs (Optional[Dict[str, Any]]): 검색 매개변수
            
        Returns:
            Retriever: LangChain Retriever 객체
        """
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def delete_documents(self, ids: List[str]) -> bool:
        """
        문서 삭제
        
        Args:
            ids (List[str]): 삭제할 문서 ID 리스트
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            self.vectorstore.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        컬렉션 통계 정보 반환 (legacy 호환)
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            # ChromaDB 클라이언트를 통해 통계 정보 가져오기
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "total_documents": count,  # legacy 호환성
                "embedding_dimension": 1536  # text-embedding-3-small 기본값
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def create_collection(self, reset: bool = False) -> bool:
        """
        컬렉션 생성 (LangChain 호환성을 위한 메서드)
        
        Args:
            reset (bool): 기존 컬렉션 재설정 여부
            
        Returns:
            bool: 성공 여부
        """
        try:
            if reset:
                # 기존 컬렉션 삭제 후 재생성
                logger.info(f"Resetting collection: {self.collection_name}")
                try:
                    # 기존 벡터스토어 삭제
                    self.vectorstore.delete_collection()
                except:
                    pass  # 컬렉션이 없어도 무시
                
                # 새 벡터스토어 인스턴스 생성
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embedding_function,
                    persist_directory=str(self.db_path)
                )
            
            logger.info(f"Collection ready: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def _generate_document_id(self, document: Dict[str, Any], index: int) -> str:
        """
        문서 ID 생성
        
        Args:
            document (Dict[str, Any]): 문서 객체
            index (int): 인덱스
            
        Returns:
            str: 생성된 문서 ID
        """
        metadata = document.get("metadata", {})
        
        # 기존 ID가 있으면 사용
        if "doc_id" in metadata:
            return metadata["doc_id"]
        
        # 법령 문서의 경우 특별한 ID 생성
        if metadata.get("law_name") and metadata.get("index"):
            law_name = metadata["law_name"].replace(" ", "_")
            return f"{law_name}_{metadata['index']}_{index}"
        
        # 무역 정보의 경우
        if metadata.get("data_type") and metadata.get("data_source"):
            data_type = metadata["data_type"]
            data_source = metadata["data_source"].replace(" ", "_")
            return f"{data_type}_{data_source}_{index}"
        
        # 기본 ID
        return f"doc_{index}"
    
    def _flatten_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool]]:
        """
        메타데이터를 평면화 (LangChain Chroma 호환성)
        
        Args:
            metadata (Dict[str, Any]): 원본 메타데이터
            
        Returns:
            Dict[str, Union[str, int, float, bool]]: 평면화된 메타데이터
        """
        flattened = {}
        
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                flattened[key] = value
            elif isinstance(value, list):
                # 리스트는 JSON 문자열로 변환 (파싱 가능하도록)
                import json
                flattened[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, dict):
                # 딕셔너리는 JSON 문자열로 변환
                import json
                flattened[key] = json.dumps(value, ensure_ascii=False)
            else:
                # 기타 타입은 문자열로 변환
                flattened[key] = str(value)
        
        return flattened


# 기존 코드와의 호환성을 위한 별칭
ChromaVectorStore = LangChainVectorStore