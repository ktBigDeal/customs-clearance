"""
ChromaDB Vector Store Module for FastAPI Integration
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
    """LangChain 표준 Chroma를 사용한 벡터 저장소 (Vector Store)"""
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 collection_name: str = "universal_collection",
                 embedding_function: Optional['OpenAIEmbeddings'] = None,
                 config: Optional[Dict[str, Any]] = None):
        """초기화"""
        self.collection_name = collection_name
        
        # 설정 로드 (config 우선, 없으면 기본값 사용)
        if config is None:
            try:
                from ..utils.config import get_chromadb_config
                config = get_chromadb_config()
            except:
                config = {"mode": "local"}
        
        self.config = config
        
        # 임베딩 함수 설정
        if embedding_function is None:
            # OpenAI API 키 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.embedding_function = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key
            )
        else:
            self.embedding_function = embedding_function
        
        # 연결 모드에 따른 초기화
        if self.config.get("mode") == "docker":
            self._init_docker_connection()
        else:
            self._init_local_connection(db_path)
        
        logger.info(f"LangChain Vector Store initialized: {collection_name} at {self.db_path}")
    
    def _init_docker_connection(self):
        """Docker 모드 ChromaDB 연결 초기화"""
        try:
            # Docker ChromaDB 서버 연결 설정
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 8011)
            
            if HAS_CHROMADB_CLIENT:
                # ChromaDB 클라이언트로 연결
                client = chromadb.HttpClient(host=host, port=port)
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embedding_function,
                    client=client
                )
                self.db_path = Path(f"http://{host}:{port}")
                logger.info(f"Connected to Docker ChromaDB: {host}:{port}")
            else:
                logger.warning("chromadb package not available, falling back to local mode")
                self._init_local_connection(None)
                
        except Exception as e:
            logger.error(f"Failed to connect to Docker ChromaDB: {e}")
            logger.info("Falling back to local mode")
            self._init_local_connection(None)
    
    def _init_local_connection(self, db_path: Optional[str]):
        """로컬 모드 ChromaDB 연결 초기화"""
        # 로컬 파일 기반 초기화
        if db_path:
            self.db_path = Path(db_path)
        elif "persist_directory" in self.config:
            self.db_path = Path(self.config["persist_directory"])
        else:
            # 로컬 data 디렉토리 사용
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # model-chatbot-fastapi 루트
            self.db_path = project_root / "data" / "chroma_db"
        
        # 디렉토리 생성
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # LangChain Chroma 벡터스토어 초기화
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=str(self.db_path)
        )
        logger.info(f"Initialized local ChromaDB at: {self.db_path}")
    
    def similarity_search(self, 
                         query: str, 
                         k: int = 5,
                         filter: Optional[Dict] = None) -> List[Document]:
        """유사도 검색"""
        try:
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
            logger.debug(f"Found {len(results)} similar documents")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def search_similar(self, 
                      query_embedding: List[float],
                      top_k: int = 5,
                      where: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """임베딩을 이용한 유사도 검색 (기존 호환성)"""
        try:
            # LangChain은 직접 임베딩 검색을 지원하지 않으므로
            # ChromaDB 클라이언트를 직접 사용하여 임베딩 기반 검색 수행
            collection = self.vectorstore._collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            
            # 결과를 딕셔너리 형태로 변환
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'][0] else {},
                    "similarity": 1.0 - results['distances'][0][i] if results['distances'][0] else 0.8,  # distance를 similarity로 변환
                    "id": results['ids'][0][i]
                })
            
            logger.debug(f"Found {len(formatted_results)} similar documents using direct ChromaDB client")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Direct ChromaDB embedding search failed: {e}")
            return []


class ChromaVectorStore:
    """ChromaDB 벡터 저장소 (FastAPI용 간소화 버전)"""
    
    def __init__(self, 
                 collection_name: str = "customs_law_collection",
                 db_path: Optional[str] = None):
        """
        초기화
        
        Args:
            collection_name: 컬렉션 이름
            db_path: 데이터베이스 경로
        """
        self.collection_name = collection_name
        
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # 임베딩 함수 설정
        self.embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        
        # 데이터베이스 경로 설정
        if db_path:
            self.db_path = Path(db_path)
        else:
            # 로컬 data 디렉토리 사용
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # model-chatbot-fastapi 루트
            self.db_path = project_root / "data" / "chroma_db"
        
        # LangChain Chroma 인스턴스 생성
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_function,
            persist_directory=str(self.db_path)
        )
        
        logger.info(f"ChromaVectorStore initialized: {collection_name} at {self.db_path}")
    
    def similarity_search(self, 
                         query: str, 
                         k: int = 5,
                         filter: Optional[Dict] = None) -> List[Document]:
        """
        유사도 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter: 메타데이터 필터
            
        Returns:
            유사한 문서 리스트
        """
        try:
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
            logger.debug(f"Found {len(results)} similar documents")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def similarity_search_with_score(self,
                                   query: str,
                                   k: int = 5,
                                   filter: Optional[Dict] = None) -> List[tuple]:
        """
        점수와 함께 유사도 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter: 메타데이터 필터
            
        Returns:
            (Document, score) 튜플 리스트
        """
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )
            logger.debug(f"Found {len(results)} documents with scores")
            return results
        except Exception as e:
            logger.error(f"Similarity search with score failed: {e}")
            return []
    
    def get_collection_count(self) -> int:
        """컬렉션 내 문서 수 반환"""
        try:
            # ChromaDB 클라이언트 직접 사용
            collection = self.vectorstore._collection
            return collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            return 0
    
    def search_similar(self, 
                      query_embedding: List[float],
                      top_k: int = 5,
                      where: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """임베딩을 이용한 유사도 검색 (기존 호환성)"""
        try:
            # LangChain은 직접 임베딩 검색을 지원하지 않으므로
            # 임베딩을 텍스트로 변환하는 더미 검색 사용
            # 실제 사용에서는 query string을 사용해야 함
            collection = self.vectorstore._collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            
            formatted_results = []
            for i in range(len(results['documents'][0])):
                doc = Document(
                    page_content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i]
                )
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": 1.0 - results['distances'][0][i],  # distance를 similarity로 변환
                    "id": results['ids'][0][i]
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Direct ChromaDB query failed: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """벡터 스토어 통계 정보 반환"""
        return {
            "collection_name": self.collection_name,
            "total_documents": self.get_collection_count(),
            "db_path": str(self.db_path),
            "embedding_model": "text-embedding-3-small"
        }