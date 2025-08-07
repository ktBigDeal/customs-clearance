"""
API v1 라우터 통합
"""

from fastapi import APIRouter

from api.v1.endpoints import recommend, search, health, cache

api_router = APIRouter()

# 각 엔드포인트 라우터 등록
api_router.include_router(
    recommend.router,
    prefix="/recommend",
    tags=["추천"]
)

api_router.include_router(
    search.router,
    prefix="/search",
    tags=["검색"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["헬스체크"]
)

api_router.include_router(
    cache.router,
    prefix="/cache",
    tags=["캐시 관리"]
)

