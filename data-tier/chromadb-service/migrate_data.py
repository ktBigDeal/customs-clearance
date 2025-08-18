#!/usr/bin/env python3
"""
ChromaDB 데이터 마이그레이션 스크립트
로컬 ChromaDB 데이터를 Railway ChromaDB로 이전

사용법:
python migrate_data.py --source local --target railway --railway-url https://your-chromadb.railway.app
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import requests
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChromaDBMigrator:
    """ChromaDB 마이그레이션 클래스"""
    
    def __init__(self):
        self.source_client = None
        self.target_client = None
    
    def connect_local(self, data_path: str) -> bool:
        """로컬 ChromaDB에 연결"""
        try:
            # 로컬 데이터 경로 확인
            local_path = Path(data_path)
            if not local_path.exists():
                logger.error(f"로컬 데이터 경로가 존재하지 않습니다: {data_path}")
                return False
            
            self.source_client = chromadb.PersistentClient(path=str(local_path))
            logger.info(f"로컬 ChromaDB 연결 성공: {data_path}")
            return True
            
        except Exception as e:
            logger.error(f"로컬 ChromaDB 연결 실패: {e}")
            return False
    
    def connect_railway(self, railway_url: str) -> bool:
        """Railway ChromaDB에 연결"""
        try:
            # URL에서 호스트와 포트 추출
            if railway_url.startswith('https://'):
                host = railway_url.replace('https://', '')
                port = 443
                ssl = True
            elif railway_url.startswith('http://'):
                host = railway_url.replace('http://', '')
                port = 80
                ssl = False
            else:
                host = railway_url
                port = 443
                ssl = True
            
            # Railway ChromaDB 연결 테스트
            test_url = f"{'https' if ssl else 'http'}://{host}/api/v1/heartbeat"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Railway ChromaDB 헬스체크 실패: {response.status_code}")
                return False
            
            # ChromaDB 클라이언트 생성
            self.target_client = chromadb.HttpClient(
                host=host,
                port=port,
                ssl=ssl
            )
            
            # 연결 테스트
            self.target_client.heartbeat()
            logger.info(f"Railway ChromaDB 연결 성공: {railway_url}")
            return True
            
        except Exception as e:
            logger.error(f"Railway ChromaDB 연결 실패: {e}")
            return False
    
    def list_collections(self, client_type: str = "source") -> List[str]:
        """컬렉션 목록 조회"""
        try:
            client = self.source_client if client_type == "source" else self.target_client
            collections = client.list_collections()
            collection_names = [col.name for col in collections]
            logger.info(f"{client_type} 컬렉션 목록: {collection_names}")
            return collection_names
            
        except Exception as e:
            logger.error(f"컬렉션 목록 조회 실패 ({client_type}): {e}")
            return []
    
    def migrate_collection(self, collection_name: str, batch_size: int = 100) -> bool:
        """개별 컬렉션 마이그레이션"""
        try:
            logger.info(f"컬렉션 '{collection_name}' 마이그레이션 시작...")
            
            # 소스 컬렉션 조회
            source_collection = self.source_client.get_collection(collection_name)
            
            # 타겟에 컬렉션 생성 (존재하면 가져오기)
            try:
                target_collection = self.target_client.get_collection(collection_name)
                logger.info(f"기존 컬렉션 '{collection_name}' 사용")
            except:
                target_collection = self.target_client.create_collection(collection_name)
                logger.info(f"새 컬렉션 '{collection_name}' 생성")
            
            # 소스 데이터 조회
            result = source_collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            if not result['ids']:
                logger.warning(f"컬렉션 '{collection_name}'에 데이터가 없습니다")
                return True
            
            total_items = len(result['ids'])
            logger.info(f"총 {total_items}개 아이템 마이그레이션 예정")
            
            # 배치 단위로 데이터 이전
            for i in range(0, total_items, batch_size):
                end_idx = min(i + batch_size, total_items)
                
                batch_ids = result['ids'][i:end_idx]
                batch_documents = result['documents'][i:end_idx] if result['documents'] else None
                batch_metadatas = result['metadatas'][i:end_idx] if result['metadatas'] else None
                batch_embeddings = result['embeddings'][i:end_idx] if result['embeddings'] else None
                
                # 데이터 추가
                target_collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    embeddings=batch_embeddings
                )
                
                logger.info(f"배치 {i//batch_size + 1}/{(total_items-1)//batch_size + 1} 완료 ({end_idx}/{total_items})")
                
                # API 부하 방지를 위한 대기
                time.sleep(0.1)
            
            logger.info(f"컬렉션 '{collection_name}' 마이그레이션 완료!")
            return True
            
        except Exception as e:
            logger.error(f"컬렉션 '{collection_name}' 마이그레이션 실패: {e}")
            return False
    
    def migrate_all(self, batch_size: int = 100) -> bool:
        """모든 컬렉션 마이그레이션"""
        try:
            collections = self.list_collections("source")
            
            if not collections:
                logger.warning("마이그레이션할 컬렉션이 없습니다")
                return True
            
            success_count = 0
            for collection_name in collections:
                if self.migrate_collection(collection_name, batch_size):
                    success_count += 1
                else:
                    logger.error(f"컬렉션 '{collection_name}' 마이그레이션 실패")
            
            logger.info(f"마이그레이션 완료: {success_count}/{len(collections)} 성공")
            return success_count == len(collections)
            
        except Exception as e:
            logger.error(f"전체 마이그레이션 실패: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """마이그레이션 검증"""
        try:
            source_collections = self.list_collections("source")
            target_collections = self.list_collections("target")
            
            logger.info("=== 마이그레이션 검증 ===")
            
            # 컬렉션 개수 비교
            if len(source_collections) != len(target_collections):
                logger.warning(f"컬렉션 개수 불일치: 소스({len(source_collections)}) vs 타겟({len(target_collections)})")
            
            # 각 컬렉션의 아이템 개수 비교
            for collection_name in source_collections:
                if collection_name not in target_collections:
                    logger.error(f"타겟에 컬렉션 '{collection_name}'이 없습니다")
                    continue
                
                source_collection = self.source_client.get_collection(collection_name)
                target_collection = self.target_client.get_collection(collection_name)
                
                source_count = source_collection.count()
                target_count = target_collection.count()
                
                if source_count == target_count:
                    logger.info(f"✅ {collection_name}: {source_count} == {target_count}")
                else:
                    logger.warning(f"❌ {collection_name}: {source_count} != {target_count}")
            
            logger.info("검증 완료!")
            return True
            
        except Exception as e:
            logger.error(f"검증 실패: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="ChromaDB 데이터 마이그레이션")
    parser.add_argument("--source-path", required=True, help="로컬 ChromaDB 데이터 경로")
    parser.add_argument("--railway-url", required=True, help="Railway ChromaDB URL")
    parser.add_argument("--batch-size", type=int, default=100, help="배치 크기 (기본: 100)")
    parser.add_argument("--verify-only", action="store_true", help="마이그레이션 없이 검증만 수행")
    
    args = parser.parse_args()
    
    # 마이그레이터 초기화
    migrator = ChromaDBMigrator()
    
    # 연결
    logger.info("데이터베이스 연결 중...")
    if not migrator.connect_local(args.source_path):
        sys.exit(1)
    
    if not migrator.connect_railway(args.railway_url):
        sys.exit(1)
    
    # 검증만 수행
    if args.verify_only:
        migrator.verify_migration()
        return
    
    # 마이그레이션 수행
    logger.info("데이터 마이그레이션 시작...")
    if migrator.migrate_all(args.batch_size):
        logger.info("마이그레이션 성공!")
        
        # 검증 수행
        migrator.verify_migration()
    else:
        logger.error("마이그레이션 실패!")
        sys.exit(1)


if __name__ == "__main__":
    main()