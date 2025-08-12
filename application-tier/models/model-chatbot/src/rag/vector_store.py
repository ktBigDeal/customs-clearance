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

try:
    import chromadb
    HAS_CHROMADB_CLIENT = True
except ImportError:
    HAS_CHROMADB_CLIENT = False

logger = logging.getLogger(__name__)


class LangChainVectorStore:
    """
    LangChain 표준 Chroma를 사용한 벡터 저장소 (Vector Store)
    
    신입 개발자를 위한 핵심 개념:
    - Embedding (임베딩): 텍스트 → 숫자 벡터 변환 과정
    - Collection: 관련 문서들을 그룹으로 묶은 것 (DB의 테이블과 유사)
    - Similarity Search: 벡터 간 거리 계산으로 유사한 문서 찾기
    - ChromaDB: 오픈소스 벡터 데이터베이스 (로컬에서 실행 가능)
    
    이 클래스의 주요 기능:
    1. 문서를 벡터로 변환해서 저장
    2. 질문과 유사한 문서 검색 및 반환
    3. 메타데이터 기반 필터링
    4. 컬렉션 생성/삭제/통계 조회
    """
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 collection_name: str = "universal_collection",
                 embedding_function: Optional[OpenAIEmbeddings] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        초기화 - 로컬 파일 기반 또는 Docker HTTP 서버 연결 지원
        
        Args:
            db_path (Optional[str]): ChromaDB 저장 경로 (로컬 모드용, 호환성 유지)
            collection_name (str): 컬렉션 이름
            embedding_function (Optional[OpenAIEmbeddings]): 임베딩 함수
            config (Optional[Dict[str, Any]]): ChromaDB 연결 설정 (get_chromadb_config()에서 가져옴)
        """
        self.collection_name = collection_name
        
        # 설정 로드 (config 우선, 없으면 기본값 사용)
        if config is None:
            from ..utils.config import get_chromadb_config
            config = get_chromadb_config()
        
        self.config = config
        self.mode = config.get("mode", "local")
        
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
        
        # 연결 모드에 따른 초기화
        if self.mode == "docker":
            self._init_docker_connection()
        else:
            self._init_local_connection(db_path)
        
        # 호환성을 위한 속성 추가
        self.collection = None  # 기존 코드 호환성
        
        logger.info(f"LangChain Vector Store initialized in {self.mode} mode")
    
    def _init_local_connection(self, db_path: Optional[str] = None):
        """로컬 파일 기반 ChromaDB 연결 초기화"""
        # db_path 우선순위: 매개변수 > config > 기본값
        if db_path:
            self.db_path = Path(db_path)
        elif "persist_directory" in self.config:
            self.db_path = Path(self.config["persist_directory"])
        else:
            self.db_path = Path("data/chroma_db")
        
        # 디렉토리 생성
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # LangChain Chroma 벡터스토어 초기화 (로컬 파일 기반)
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=str(self.db_path)
        )
        
        logger.info(f"Local ChromaDB initialized at: {self.db_path}")
    
    def _init_docker_connection(self):
        """Docker HTTP 서버 기반 ChromaDB 연결 초기화"""
        if not HAS_CHROMADB_CLIENT:
            raise ImportError(
                "chromadb package is required for Docker mode. "
                "Install it with: pip install chromadb"
            )
        
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 8011)
        
        try:
            # ChromaDB HTTP 클라이언트 생성
            chroma_client = chromadb.HttpClient(host=host, port=port)
            
            # 연결 테스트
            version = chroma_client.get_version()
            logger.info(f"Connected to ChromaDB server {host}:{port} (version: {version})")
            
            # LangChain Chroma 벡터스토어 초기화 (HTTP 클라이언트 기반)
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                client=chroma_client
            )
            
            self.chroma_client = chroma_client
            logger.info(f"Docker ChromaDB connection established: {host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB server {host}:{port}: {e}")
            raise ConnectionError(
                f"Cannot connect to ChromaDB Docker service at {host}:{port}. "
                f"Please ensure the ChromaDB container is running. Error: {e}"
            )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        여러 문서를 벡터 저장소에 한 번에 추가하는 함수
        
        이 함수가 하는 일:
        1. 딕셔너리 형태의 문서들을 LangChain Document 객체로 변환
        2. 각 문서의 텍스트를 OpenAI 임베딩 모델로 벡터화
        3. 벡터와 메타데이터를 ChromaDB에 저장
        4. 나중에 검색할 때 사용할 고유 ID 생성
        
        Args:
            documents (List[Dict[str, Any]]): 추가할 문서들의 리스트
                각 문서는 다음과 같은 구조:
                {
                    "content": "문서의 실제 텍스트 내용",
                    "metadata": {
                        "law_name": "관세법",
                        "index": "제1조",
                        "title": "목적"
                    }
                }
                
        Returns:
            List[str]: 성공적으로 추가된 문서들의 고유 ID 리스트
                      예: ["doc_001", "doc_002", "doc_003"]
        
        신입 개발자 주의사항:
        - 대량의 문서를 한 번에 처리할 때는 배치 단위로 나누어 처리
        - 메타데이터는 평면화(flatten)해서 저장 (중첩 구조 제거)
        - 동일한 문서를 중복 추가하면 ID가 겹쳐서 덮어쓰기됨
        - OpenAI API 호출 비용이 발생하므로 불필요한 중복 호출 방지
        """
        try:
            # 딕셔너리를 LangChain Document로 변환
            langchain_docs = []
            metadatas = []
            
            for i, doc in enumerate(documents):
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                
                # enhanced_content가 있으면 사용
                if "enhanced_content" in doc:
                    content = doc["enhanced_content"]
                
                # 메타데이터 평면화 (LangChain Chroma 호환성)
                flattened_metadata = self._flatten_metadata(metadata)
                
                # Document ID 생성
                doc_id = self._generate_document_id(doc, i)
                flattened_metadata["doc_id"] = doc_id
                
                langchain_docs.append(Document(
                    page_content=content,
                    metadata=flattened_metadata
                ))
                metadatas.append(flattened_metadata)
            
            # 벡터스토어에 문서 추가
            ids = self.vectorstore.add_documents(
                documents=langchain_docs,
                ids=[meta["doc_id"] for meta in metadatas]
            )
            
            logger.info(f"Added {len(ids)} documents to vector store")
            return ids
            
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
            
            # Document를 딕셔너리 형태로 변환
            results = []
            for doc in docs:
                # 메타데이터에서 자주 사용되는 필드 추출 (law_retriever.py 호환성)
                doc_id = doc.metadata.get("doc_id", f"doc_{len(results)}")
                index = doc.metadata.get("index", "")
                subtitle = doc.metadata.get("subtitle", "")
                
                result = {
                    "id": doc_id,  # law_retriever.py에서 필요로 하는 id 필드
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "index": index,  # 최상위 레벨로 추가 (접근 편의성)
                    "subtitle": subtitle,  # 최상위 레벨로 추가 (접근 편의성)
                    "score": getattr(doc, "score", 0.0)  # 점수가 있으면 포함
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
    
    def create_collection(self, reset: bool = False) -> bool:
        """
        컬렉션 생성 (LangChain Chroma는 자동으로 컬렉션을 생성하므로 호환성을 위한 메서드)
        
        Args:
            reset (bool): 기존 컬렉션 재설정 여부
            
        Returns:
            bool: 성공 여부
        """
        try:
            if reset:
                # 기존 컬렉션 삭제 후 재생성
                try:
                    # ChromaDB 클라이언트를 통해 컬렉션 삭제
                    client = self.vectorstore._client
                    try:
                        client.delete_collection(name=self.collection_name)
                        logger.info(f"Deleted existing collection: {self.collection_name}")
                    except Exception:
                        # 컬렉션이 존재하지 않는 경우 무시
                        pass
                    
                    # 모드에 따라 다른 방식으로 새 벡터스토어 인스턴스 생성
                    if self.mode == "docker":
                        # Docker 모드: HTTP 클라이언트 사용
                        self.vectorstore = Chroma(
                            collection_name=self.collection_name,
                            embedding_function=self.embedding_function,
                            client=self.chroma_client
                        )
                    else:
                        # 로컬 모드: persist_directory 사용
                        self.vectorstore = Chroma(
                            collection_name=self.collection_name,
                            embedding_function=self.embedding_function,
                            persist_directory=str(self.db_path)
                        )
                    logger.info(f"Created new collection: {self.collection_name}")
                except Exception as e:
                    logger.warning(f"Could not reset collection: {e}")
                    # 재설정에 실패한 경우 새 인스턴스 생성 시도
                    if self.mode == "docker":
                        # Docker 모드: HTTP 클라이언트 사용
                        self.vectorstore = Chroma(
                            collection_name=self.collection_name,
                            embedding_function=self.embedding_function,
                            client=self.chroma_client
                        )
                    else:
                        # 로컬 모드: persist_directory 사용
                        self.vectorstore = Chroma(
                            collection_name=self.collection_name,
                            embedding_function=self.embedding_function,
                            persist_directory=str(self.db_path)
                        )
            
            # LangChain Chroma는 자동으로 컬렉션을 생성하므로 항상 성공
            logger.info(f"Collection '{self.collection_name}' is ready")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def _auto_connect_collection(self) -> bool:
        """
        기존 컬렉션에 자동 연결 (호환성을 위한 메서드)
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            # LangChain Chroma는 이미 초기화 시 컬렉션에 연결되므로
            # 간단히 collection 속성을 설정
            self.collection = self.vectorstore._collection
            logger.info(f"Auto-connected to collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to auto-connect to collection: {e}")
            return False
    
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
        컬렉션 통계 정보 반환
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            # ChromaDB 클라이언트를 통해 통계 정보 가져오기
            collection = self.vectorstore._collection
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "total_documents": count,  # 호환성을 위한 필드
                "document_count": count,
                "embedding_dimension": 1536  # text-embedding-3-small 기본값
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
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
                # 리스트는 문자열로 변환
                flattened[key] = str(value)
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