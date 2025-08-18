"""
초기 데이터 로딩 API 엔드포인트
Railway 배포 후 ChromaDB에 RAG 문서 데이터를 로딩하는 API
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings

from app.utils.config import get_law_chromadb_config, get_trade_chromadb_config, get_consultation_chromadb_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data", tags=["data-initialization"])


class InitializationRequest(BaseModel):
    """초기화 요청 모델"""
    collections: List[str] = ["law", "trade", "consultation"]
    force_reload: bool = False


class InitializationResponse(BaseModel):
    """초기화 응답 모델"""
    status: str
    message: str
    collections_loaded: List[str]
    total_documents: int


class DataInitializer:
    """데이터 초기화 클래스"""
    
    def __init__(self):
        self.data_sources = {
            "law": {
                "config": get_law_chromadb_config(),
                "documents": self._load_law_documents()
            },
            "trade": {
                "config": get_trade_chromadb_config(),
                "documents": self._load_trade_documents()
            },
            "consultation": {
                "config": get_consultation_chromadb_config(),
                "documents": self._load_consultation_documents()
            }
        }
    
    def _load_law_documents(self) -> List[Dict[str, Any]]:
        """관세법 문서 로딩"""
        documents = [
            {
                "id": "law_001",
                "content": "관세법 제1조 (목적) 이 법은 관세의 부과·징수와 수출입통관에 관한 사항을 규정함으로써 관세수입의 확보와 무역질서의 유지 및 국민경제의 건전한 발전에 이바지함을 목적으로 한다.",
                "metadata": {"type": "law", "section": "제1장", "article": "제1조"}
            },
            {
                "id": "law_002", 
                "content": "관세법 제2조 (정의) 이 법에서 사용하는 용어의 뜻은 다음과 같다. 1. \"관세\"란 관세율표에 따라 수입물품에 부과하는 세금을 말한다.",
                "metadata": {"type": "law", "section": "제1장", "article": "제2조"}
            },
            {
                "id": "law_003",
                "content": "관세법 제38조 (수입신고) 수입물품을 수입하려는 자는 그 물품의 품명·규격·수량·가격 등을 세관장에게 신고하여야 한다.",
                "metadata": {"type": "law", "section": "제3장", "article": "제38조"}
            }
        ]
        return documents
    
    def _load_trade_documents(self) -> List[Dict[str, Any]]:
        """무역규제 문서 로딩"""
        documents = [
            {
                "id": "trade_001",
                "content": "딸기 수입 시 주의사항: 딸기는 식물검역대상 품목으로 식물검역증명서가 필요합니다. 농림축산검역본부의 수입요건을 충족해야 합니다.",
                "metadata": {"type": "trade", "category": "식물검역", "product": "딸기"}
            },
            {
                "id": "trade_002",
                "content": "아보카도 수입규제: 아보카도는 미국, 멕시코, 칠레 등에서 수입 가능하며, 과실파리 방제를 위한 냉동처리 또는 증기열처리가 필요합니다.",
                "metadata": {"type": "trade", "category": "식물검역", "product": "아보카도"}
            },
            {
                "id": "trade_003",
                "content": "육류 수입제한: 구제역, 조류인플루엔자 등 가축질병 발생국가로부터의 육류 수입은 일시 중단됩니다.",
                "metadata": {"type": "trade", "category": "동물검역", "product": "육류"}
            }
        ]
        return documents
    
    def _load_consultation_documents(self) -> List[Dict[str, Any]]:
        """상담사례 문서 로딩"""
        documents = [
            {
                "id": "consult_001",
                "content": "Q: 개인이 해외에서 구매한 화장품을 수입할 때 필요한 절차는? A: 개인사용목적으로 소량 수입시 간이신고 가능하며, 식약처 수입요건 확인이 필요합니다.",
                "metadata": {"type": "consultation", "category": "개인수입", "product": "화장품"}
            },
            {
                "id": "consult_002",
                "content": "Q: FTA 협정세율 적용받으려면? A: 원산지증명서를 구비하고 수입신고 시 협정세율 적용을 신청해야 합니다.",
                "metadata": {"type": "consultation", "category": "관세율", "topic": "FTA"}
            },
            {
                "id": "consult_003",
                "content": "Q: 통관보류 시 대응방법은? A: 보완서류 제출, 물품검사 응하기, 필요시 관세사 선임하여 이의신청 가능합니다.",
                "metadata": {"type": "consultation", "category": "통관절차", "topic": "통관보류"}
            }
        ]
        return documents
    
    async def initialize_collection(self, collection_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """컬렉션 초기화"""
        try:
            if collection_name not in self.data_sources:
                raise ValueError(f"Unknown collection: {collection_name}")
            
            source = self.data_sources[collection_name]
            config = source["config"]
            documents = source["documents"]
            
            # ChromaDB 클라이언트 생성
            if config.get("host") and config.get("port"):
                # Docker/Railway 모드
                client = chromadb.HttpClient(
                    host=config["host"],
                    port=config["port"],
                    ssl=config.get("use_ssl", False)
                )
            else:
                # 로컬 모드
                client = chromadb.PersistentClient(path=config["data_path"])
            
            # 컬렉션 생성 또는 가져오기
            try:
                if force_reload:
                    try:
                        client.delete_collection(config["collection_name"])
                        logger.info(f"기존 컬렉션 삭제: {config['collection_name']}")
                    except:
                        pass
                
                collection = client.create_collection(
                    name=config["collection_name"],
                    metadata={"description": f"{collection_name} documents"}
                )
            except Exception:
                collection = client.get_collection(config["collection_name"])
                if not force_reload and collection.count() > 0:
                    logger.info(f"컬렉션이 이미 존재하고 데이터가 있습니다: {config['collection_name']}")
                    return {
                        "collection": collection_name,
                        "status": "already_exists",
                        "document_count": collection.count()
                    }
            
            # 문서 추가
            if documents:
                ids = [doc["id"] for doc in documents]
                contents = [doc["content"] for doc in documents]
                metadatas = [doc["metadata"] for doc in documents]
                
                collection.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas
                )
                
                logger.info(f"컬렉션 {collection_name}에 {len(documents)}개 문서 추가 완료")
            
            return {
                "collection": collection_name,
                "status": "success",
                "document_count": len(documents)
            }
            
        except Exception as e:
            logger.error(f"컬렉션 {collection_name} 초기화 실패: {e}")
            return {
                "collection": collection_name,
                "status": "error",
                "error": str(e)
            }


# 전역 초기화 객체
data_initializer = DataInitializer()


@router.post("/initialize", response_model=InitializationResponse)
async def initialize_data(
    request: InitializationRequest,
    background_tasks: BackgroundTasks
):
    """
    ChromaDB 초기 데이터 로딩
    
    Railway 배포 후 RAG 시스템에 필요한 문서들을 ChromaDB에 로딩합니다.
    """
    try:
        results = []
        total_docs = 0
        
        for collection_name in request.collections:
            result = await data_initializer.initialize_collection(
                collection_name, 
                request.force_reload
            )
            results.append(result)
            
            if result["status"] in ["success", "already_exists"]:
                total_docs += result["document_count"]
        
        successful_collections = [
            r["collection"] for r in results 
            if r["status"] in ["success", "already_exists"]
        ]
        
        if len(successful_collections) == len(request.collections):
            status = "success"
            message = f"모든 컬렉션 초기화 완료: {', '.join(successful_collections)}"
        else:
            status = "partial"
            failed_collections = [
                r["collection"] for r in results 
                if r["status"] == "error"
            ]
            message = f"일부 컬렉션 초기화 실패: {', '.join(failed_collections)}"
        
        return InitializationResponse(
            status=status,
            message=message,
            collections_loaded=successful_collections,
            total_documents=total_docs
        )
        
    except Exception as e:
        logger.error(f"데이터 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"초기화 실패: {str(e)}")


@router.get("/status")
async def get_data_status():
    """ChromaDB 데이터 상태 확인"""
    try:
        status = {}
        
        for collection_name, source in data_initializer.data_sources.items():
            config = source["config"]
            
            try:
                # ChromaDB 클라이언트 생성
                if config.get("host") and config.get("port"):
                    client = chromadb.HttpClient(
                        host=config["host"],
                        port=config["port"],
                        ssl=config.get("use_ssl", False)
                    )
                else:
                    client = chromadb.PersistentClient(path=config["data_path"])
                
                collection = client.get_collection(config["collection_name"])
                count = collection.count()
                
                status[collection_name] = {
                    "status": "available",
                    "document_count": count,
                    "collection_name": config["collection_name"]
                }
                
            except Exception as e:
                status[collection_name] = {
                    "status": "unavailable",
                    "error": str(e),
                    "collection_name": config["collection_name"]
                }
        
        return {"collections": status}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 확인 실패: {str(e)}")


@router.delete("/collections/{collection_name}")
async def clear_collection(collection_name: str):
    """특정 컬렉션의 모든 데이터 삭제"""
    try:
        if collection_name not in data_initializer.data_sources:
            raise HTTPException(status_code=404, detail=f"컬렉션을 찾을 수 없습니다: {collection_name}")
        
        config = data_initializer.data_sources[collection_name]["config"]
        
        # ChromaDB 클라이언트 생성
        if config.get("host") and config.get("port"):
            client = chromadb.HttpClient(
                host=config["host"],
                port=config["port"],
                ssl=config.get("use_ssl", False)
            )
        else:
            client = chromadb.PersistentClient(path=config["data_path"])
        
        # 컬렉션 삭제
        client.delete_collection(config["collection_name"])
        
        return {
            "status": "success",
            "message": f"컬렉션 {collection_name} 삭제 완료"
        }
        
    except Exception as e:
        logger.error(f"컬렉션 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")