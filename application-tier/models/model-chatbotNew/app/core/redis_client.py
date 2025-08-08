"""
Redis 캐싱 시스템 관리 모듈

FastAPI 애플리케이션의 Redis 연결과 캐싱 기능을 관리합니다.
세션 저장, 응답 캐싱, 임시 데이터 저장 등에 사용됩니다.

주요 기능:
- 비동기 Redis 연결 관리
- 세션 캐싱 (JWT 토큰 검증 결과)
- API 응답 캐싱 (RAG 결과 등)
- 대화 컨텍스트 임시 저장
- 속도 제한 (Rate Limiting)
"""

import json
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import hashlib

import aioredis
from aioredis import Redis
from aioredis.exceptions import RedisError, ConnectionError

from app.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 Redis 클라이언트
_redis_client: Optional[Redis] = None


class RedisManager:
    """Redis 연결 및 캐시 관리 클래스
    
    Redis 서버와의 연결을 관리하고 다양한 캐싱 기능을 제공합니다.
    세션 관리, 응답 캐싱, 임시 데이터 저장 등을 지원합니다.
    """
    
    def __init__(self):
        self.client: Optional[Redis] = None
        self.connection_pool = None
    
    async def connect(self) -> None:
        """Redis 서버 연결 설정
        
        Redis 서버에 연결하고 연결 풀을 생성합니다.
        실패 시 재시도 로직을 포함합니다.
        
        Raises:
            ConnectionError: Redis 연결 실패
        """
        try:
            # Redis 연결 설정
            self.client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError],
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 연결 테스트
            await self.client.ping()
            
            logger.info(f"✅ Redis 연결 성공: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            raise ConnectionError(f"Redis 연결 실패: {e}")
    
    async def disconnect(self) -> None:
        """Redis 연결 해제
        
        Redis 클라이언트와 연결 풀을 정리합니다.
        """
        try:
            if self.client:
                await self.client.close()
                self.client = None
                logger.info("✅ Redis 연결 해제 완료")
        except Exception as e:
            logger.error(f"❌ Redis 연결 해제 실패: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Redis 헬스체크
        
        Redis 서버 상태와 연결 정보를 확인합니다.
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        if not self.client:
            return {
                "status": "unhealthy",
                "message": "Redis 클라이언트가 초기화되지 않음"
            }
        
        try:
            # 핑 테스트
            ping_result = await self.client.ping()
            
            # 서버 정보 조회
            info = await self.client.info()
            
            return {
                "status": "healthy",
                "ping": ping_result,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
            
        except Exception as e:
            logger.error(f"Redis 헬스체크 실패: {e}")
            return {
                "status": "unhealthy",
                "message": str(e)
            }
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """캐시 키 생성
        
        Args:
            prefix (str): 키 접두사 (예: "session", "chat", "rag")
            identifier (str): 고유 식별자
            
        Returns:
            str: 생성된 캐시 키
        """
        return f"{settings.APP_NAME}:{prefix}:{identifier}"
    
    def _serialize_value(self, value: Any) -> str:
        """값 직렬화
        
        Args:
            value (Any): 저장할 값
            
        Returns:
            str: 직렬화된 값
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    
    def _deserialize_value(self, value: str, value_type: type = str) -> Any:
        """값 역직렬화
        
        Args:
            value (str): 저장된 값
            value_type (type): 예상 타입
            
        Returns:
            Any: 역직렬화된 값
        """
        if value is None:
            return None
            
        if value_type in (dict, list):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        elif value_type == int:
            try:
                return int(value)
            except ValueError:
                return None
        elif value_type == float:
            try:
                return float(value)
            except ValueError:
                return None
        elif value_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        
        return value
    
    # 기본 캐시 작업
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        prefix: str = "cache"
    ) -> bool:
        """값 저장
        
        Args:
            key (str): 키
            value (Any): 저장할 값
            ttl (Optional[int]): TTL (초), None이면 기본값 사용
            prefix (str): 키 접두사
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.client:
            return False
        
        try:
            cache_key = self._generate_key(prefix, key)
            serialized_value = self._serialize_value(value)
            
            if ttl is None:
                ttl = settings.CACHE_TTL
            
            result = await self.client.setex(cache_key, ttl, serialized_value)
            return result is True
            
        except Exception as e:
            logger.error(f"Redis set 실패 - key: {key}, error: {e}")
            return False
    
    async def get(
        self, 
        key: str, 
        value_type: type = str,
        prefix: str = "cache"
    ) -> Any:
        """값 조회
        
        Args:
            key (str): 키
            value_type (type): 예상 값 타입
            prefix (str): 키 접두사
            
        Returns:
            Any: 저장된 값 또는 None
        """
        if not self.client:
            return None
        
        try:
            cache_key = self._generate_key(prefix, key)
            value = await self.client.get(cache_key)
            
            return self._deserialize_value(value, value_type)
            
        except Exception as e:
            logger.error(f"Redis get 실패 - key: {key}, error: {e}")
            return None
    
    async def delete(self, key: str, prefix: str = "cache") -> bool:
        """값 삭제
        
        Args:
            key (str): 키
            prefix (str): 키 접두사
            
        Returns:
            bool: 삭제 성공 여부
        """
        if not self.client:
            return False
        
        try:
            cache_key = self._generate_key(prefix, key)
            result = await self.client.delete(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete 실패 - key: {key}, error: {e}")
            return False
    
    async def exists(self, key: str, prefix: str = "cache") -> bool:
        """키 존재 여부 확인
        
        Args:
            key (str): 키
            prefix (str): 키 접두사
            
        Returns:
            bool: 키 존재 여부
        """
        if not self.client:
            return False
        
        try:
            cache_key = self._generate_key(prefix, key)
            result = await self.client.exists(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis exists 실패 - key: {key}, error: {e}")
            return False
    
    async def expire(self, key: str, ttl: int, prefix: str = "cache") -> bool:
        """TTL 설정
        
        Args:
            key (str): 키
            ttl (int): TTL (초)
            prefix (str): 키 접두사
            
        Returns:
            bool: 설정 성공 여부
        """
        if not self.client:
            return False
        
        try:
            cache_key = self._generate_key(prefix, key)
            result = await self.client.expire(cache_key, ttl)
            return result is True
            
        except Exception as e:
            logger.error(f"Redis expire 실패 - key: {key}, error: {e}")
            return False
    
    # 세션 관리
    async def set_session(self, session_id: str, user_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """세션 데이터 저장
        
        Args:
            session_id (str): 세션 ID
            user_data (Dict[str, Any]): 사용자 데이터
            ttl (Optional[int]): TTL (초)
            
        Returns:
            bool: 저장 성공 여부
        """
        if ttl is None:
            ttl = settings.SESSION_TTL
        
        return await self.set(session_id, user_data, ttl, prefix="session")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 조회
        
        Args:
            session_id (str): 세션 ID
            
        Returns:
            Optional[Dict[str, Any]]: 세션 데이터
        """
        return await self.get(session_id, dict, prefix="session")
    
    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제
        
        Args:
            session_id (str): 세션 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        return await self.delete(session_id, prefix="session")
    
    # RAG 응답 캐싱
    async def cache_rag_response(
        self, 
        query_hash: str, 
        response_data: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """RAG 응답 캐싱
        
        Args:
            query_hash (str): 쿼리 해시
            response_data (Dict[str, Any]): 응답 데이터
            ttl (int): TTL (초)
            
        Returns:
            bool: 캐싱 성공 여부
        """
        return await self.set(query_hash, response_data, ttl, prefix="rag")
    
    async def get_cached_rag_response(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """캐싱된 RAG 응답 조회
        
        Args:
            query_hash (str): 쿼리 해시
            
        Returns:
            Optional[Dict[str, Any]]: 캐싱된 응답 데이터
        """
        return await self.get(query_hash, dict, prefix="rag")
    
    # 대화 컨텍스트 관리
    async def set_conversation_context(
        self, 
        conversation_id: str, 
        context: List[Dict[str, Any]], 
        ttl: int = 1800
    ) -> bool:
        """대화 컨텍스트 저장
        
        Args:
            conversation_id (str): 대화 ID
            context (List[Dict[str, Any]]): 대화 컨텍스트
            ttl (int): TTL (초)
            
        Returns:
            bool: 저장 성공 여부
        """
        return await self.set(conversation_id, context, ttl, prefix="context")
    
    async def get_conversation_context(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        """대화 컨텍스트 조회
        
        Args:
            conversation_id (str): 대화 ID
            
        Returns:
            Optional[List[Dict[str, Any]]]: 대화 컨텍스트
        """
        return await self.get(conversation_id, list, prefix="context")
    
    # 속도 제한 (Rate Limiting)
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window: int = 60
    ) -> Dict[str, Any]:
        """속도 제한 확인
        
        Args:
            identifier (str): 식별자 (IP, user_id 등)
            limit (int): 제한 횟수
            window (int): 시간 윈도우 (초)
            
        Returns:
            Dict[str, Any]: 제한 상태 정보
        """
        if not self.client:
            return {"allowed": True, "remaining": limit, "reset_time": window}
        
        try:
            key = self._generate_key("rate_limit", identifier)
            
            # 현재 요청 수 조회
            current = await self.client.get(key)
            current_count = int(current) if current else 0
            
            if current_count >= limit:
                ttl = await self.client.ttl(key)
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": ttl,
                    "limit": limit
                }
            
            # 카운터 증가
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            await pipe.execute()
            
            return {
                "allowed": True,
                "remaining": limit - current_count - 1,
                "reset_time": window,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Rate limit 확인 실패: {e}")
            return {"allowed": True, "remaining": limit, "reset_time": window}
    
    @staticmethod
    def generate_query_hash(query: str, user_id: Optional[int] = None) -> str:
        """쿼리 해시 생성 (캐싱용)
        
        Args:
            query (str): 사용자 쿼리
            user_id (Optional[int]): 사용자 ID
            
        Returns:
            str: 쿼리 해시값
        """
        hash_input = f"{query.strip().lower()}"
        if user_id:
            hash_input += f":{user_id}"
        
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()


# 전역 Redis 매니저 인스턴스
redis_manager = RedisManager()


async def init_redis() -> None:
    """Redis 초기화
    
    Redis 연결을 설정하고 전역 클라이언트를 초기화합니다.
    """
    global _redis_client
    
    await redis_manager.connect()
    _redis_client = redis_manager.client


async def close_redis() -> None:
    """Redis 연결 종료
    
    Redis 연결을 정리합니다.
    """
    global _redis_client
    
    await redis_manager.disconnect()
    _redis_client = None


def get_redis_client() -> Optional[Redis]:
    """Redis 클라이언트 반환
    
    Returns:
        Optional[Redis]: Redis 클라이언트 인스턴스
    """
    return _redis_client


# 편의 함수들
async def cache_get(key: str, value_type: type = str, prefix: str = "cache") -> Any:
    """캐시에서 값 조회 (편의 함수)
    
    Args:
        key (str): 키
        value_type (type): 값 타입
        prefix (str): 접두사
        
    Returns:
        Any: 캐시된 값
    """
    return await redis_manager.get(key, value_type, prefix)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None, prefix: str = "cache") -> bool:
    """캐시에 값 저장 (편의 함수)
    
    Args:
        key (str): 키
        value (Any): 값
        ttl (Optional[int]): TTL
        prefix (str): 접두사
        
    Returns:
        bool: 저장 성공 여부
    """
    return await redis_manager.set(key, value, ttl, prefix)


async def cache_delete(key: str, prefix: str = "cache") -> bool:
    """캐시에서 값 삭제 (편의 함수)
    
    Args:
        key (str): 키
        prefix (str): 접두사
        
    Returns:
        bool: 삭제 성공 여부
    """
    return await redis_manager.delete(key, prefix)