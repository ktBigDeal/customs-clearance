"""
추천 서비스 래퍼 클래스
기존 HSCodeRecommender를 FastAPI 환경에 맞게 래핑
"""

import asyncio
from typing import Dict, List, Any, Optional
import time
import logging
from pathlib import Path
import sys
import numpy as np
import pandas as pd

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from hs_recommender import HSCodeRecommender
from app.core.config import Settings

logger = logging.getLogger(__name__)

class RecommenderService:
    """비동기 추천 서비스 래퍼"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.recommender: Optional[HSCodeRecommender] = None
        self.initialized = False
        self.start_time = time.time()
        self._initialization_lock = asyncio.Lock()
        
        logger.info(f"추천 서비스 생성 - 캐시 디렉토리: {settings.cache_dir}")
    
    async def initialize(self) -> bool:
        """추천 시스템 초기화 (비동기)"""
        async with self._initialization_lock:
            if self.initialized:
                return True
            
            try:
                logger.info("🔧 HSCodeRecommender 초기화 중...")
                
                # 동기 초기화를 비동기로 실행
                loop = asyncio.get_event_loop()
                
                # HSCodeRecommender 인스턴스 생성
                self.recommender = await loop.run_in_executor(
                    None,
                    self._create_recommender
                )
                
                # 데이터 로드
                logger.info("📊 데이터 로딩 중...")
                load_success = await loop.run_in_executor(
                    None,
                    self.recommender.load_data
                )
                
                if not load_success:
                    raise Exception("데이터 로드 실패")
                
                # OpenAI 초기화 (선택사항)
                logger.info("🤖 OpenAI 초기화 중...")
                await loop.run_in_executor(
                    None,
                    self.recommender.initialize_openai
                )
                
                self.initialized = True
                logger.info("✅ 추천 서비스 초기화 완료")
                
                # 초기화 상태 확인
                stats = await self.get_status()
                logger.info(f"📈 시스템 상태: {stats.get('total_items', 0):,}개 항목 로드됨")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ 추천 서비스 초기화 실패: {e}")
                self.initialized = False
                raise
    
    def _create_recommender(self) -> HSCodeRecommender:
        """HSCodeRecommender 인스턴스 생성 (동기)"""
        return HSCodeRecommender(
            semantic_model_name=self.settings.semantic_model,
            top_k=self.settings.top_k,
            cache_dir=self.settings.cache_dir
        )
    
    async def recommend(
        self,
        query: str,
        material: str = "",
        usage: str = "",
        use_llm: bool = True,
        final_count: int = 5
    ) -> Dict[str, Any]:
        """HS 코드 추천 (비동기)"""
        if not self.initialized or not self.recommender:
            raise RuntimeError("추천 서비스가 초기화되지 않았습니다")
        
        try:
            logger.info(f"🔍 추천 요청: '{query}' (재질: {material}, 용도: {usage})")
            
            # 동기 추천을 비동기로 실행
            loop = asyncio.get_event_loop()
            
            if use_llm and self.recommender.openai_client:
                # LLM 통합 추천
                result = await loop.run_in_executor(
                    None,
                    self.recommender.recommend_ultimate,
                    query,
                    material,
                    usage,
                    final_count
                )
            else:
                # 기본 추천
                result = await loop.run_in_executor(
                    None,
                    self.recommender.recommend,
                    query,
                    material,
                    usage,
                    use_llm,
                    final_count
                )
            
            # 결과 후처리
            if result and 'recommendations' in result:
                logger.info(f"✅ 추천 완료: {len(result['recommendations'])}개 결과")
            else:
                logger.warning("⚠️ 추천 결과 없음")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 추천 실행 실패: {e}")
            raise
    
    async def search(
        self,
        query: str,
        material: str = "",
        usage: str = "",
        limit: int = 10
    ) -> Dict[str, Any]:
        """검색 (추천과 유사하지만 더 많은 결과)"""
        return await self.recommend(
            query=query,
            material=material,
            usage=usage,
            use_llm=False,
            final_count=limit
        )
    
    async def get_health(self) -> Dict[str, Any]:
        """헬스체크 정보"""
        health_info = {
            "healthy": self.initialized,
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.start_time,
            "service": "HS 코드 추천 서비스"
        }
        
        if self.recommender:
            try:
                # 추천 시스템 상태 확인
                loop = asyncio.get_event_loop()
                stats = await loop.run_in_executor(
                    None,
                    self.recommender.get_statistics
                )
                
                health_info.update({
                    "data_loaded": stats.get('system_initialized', False),
                    "total_items": stats.get('total_items', 0),
                    "cache_valid": stats.get('cache_info', {}).get('cache_valid', False),
                    "openai_available": stats.get('openai_available', False)
                })
            except Exception as e:
                health_info.update({
                    "error": str(e),
                    "healthy": False
                })
        
        return health_info
    
    async def get_status(self) -> Dict[str, Any]:
        """상세 상태 정보"""
        status_info = {
            "initialized": self.initialized,
            "uptime_seconds": time.time() - self.start_time,
            "settings": {
                "semantic_model": self.settings.semantic_model,
                "top_k": self.settings.top_k,
                "cache_dir": self.settings.cache_dir
            }
        }
        
        if self.recommender:
            try:
                loop = asyncio.get_event_loop()
                stats = await loop.run_in_executor(
                    None,
                    self.recommender.get_statistics
                )
                
                status_info.update({
                    "total_items": stats.get('total_items', 0),
                    "unique_hs_keys": stats.get('unique_hs_keys', 0),
                    "chapters": stats.get('chapters', 0),
                    "data_sources": stats.get('data_sources', {}),
                    "cache_status": "valid" if stats.get('cache_info', {}).get('cache_valid') else "invalid",
                    "openai_available": stats.get('openai_available', False),
                    "standard_coverage": stats.get('standard_coverage', 0)
                })
                
                # 성능 정보
                cache_info = stats.get('cache_info', {})
                if 'total_size_mb' in cache_info:
                    status_info['performance'] = {
                        "cache_size_mb": cache_info['total_size_mb'],
                        "cache_version": cache_info.get('metadata', {}).get('cache_version', 'unknown')
                    }
                
            except Exception as e:
                status_info['error'] = str(e)
        
        return status_info
    
    async def rebuild_cache(self) -> bool:
        """캐시 재구축"""
        if not self.recommender:
            raise RuntimeError("추천 서비스가 초기화되지 않았습니다")
        
        try:
            logger.info("🔄 캐시 재구축 시작...")
            
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self.recommender.load_data,
                True  # force_rebuild=True
            )
            
            if success:
                logger.info("✅ 캐시 재구축 완료")
            else:
                logger.error("❌ 캐시 재구축 실패")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 캐시 재구축 중 오류: {e}")
            raise
    
    async def clear_cache(self) -> int:
        """캐시 삭제"""
        if not self.recommender:
            raise RuntimeError("추천 서비스가 초기화되지 않았습니다")
        
        try:
            loop = asyncio.get_event_loop()
            deleted_count = await loop.run_in_executor(
                None,
                self.recommender.clear_cache
            )
            
            logger.info(f"🗑️ 캐시 삭제 완료: {deleted_count}개 파일")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ 캐시 삭제 중 오류: {e}")
            raise
    
    async def cleanup(self):
        """서비스 정리"""
        logger.info("🧹 추천 서비스 정리 중...")
        
        # 현재는 특별한 정리 작업 없음
        # 필요시 리소스 해제 로직 추가
        
        self.initialized = False
        logger.info("✅ 추천 서비스 정리 완료")