# HS 코드 추천 API 문서

AI 기반 HS 코드 추천 시스템의 RESTful API 서비스입니다.

## 📋 서비스 개요

**37,049개의 한국 관세청 공식 HS 코드 데이터**를 기반으로 하여, 상품명을 입력하면 가장 적합한 HS 코드를 AI로 추천해주는 서비스입니다.

### ✨ 주요 기능
- **하이브리드 검색**: TF-IDF + 의미 검색 결합
- **LLM 분석**: OpenAI GPT 기반 정확도 향상  
- **배치 처리**: 최대 10개 상품 동시 처리
- **실시간 캐싱**: 고성능 검색 인덱스
- **운영 관리**: 헬스체크, 캐시 관리 기능

### 🗂️ 데이터 구조
- **HSK 분류 데이터** (중심): 15개 필드
- **HS 코드 데이터** (보조): 5개 필드  
- **표준품명 데이터** (보조): 3개 필드
- **final_combined_text** 기반 통합 검색

---

## 🚀 빠른 시작

### 서버 시작
```bash
# 가상환경 활성화
cd customs-clearance
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 서버 실행
cd application-tier/models/model-hscode/app
uvicorn main:app --reload
```

### API 문서 확인
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📖 API 엔드포인트

### 1. 추천 서비스 (`/api/v1/recommend`)

#### 1.1 단일 추천
**`POST /api/v1/recommend/`**

상품명으로 HS 코드를 추천받습니다.

**Request Body:**
```json
{
  "query": "스테인레스 볼트",
  "material": "스테인레스강",
  "usage": "산업용",
  "mode": "llm",
  "top_k": 5,
  "use_llm": true,
  "include_details": true
}
```

**Request Parameters:**
| 필드 | 필수 | 타입 | 기본값 | 설명 |
|-----|------|------|-------|------|
| `query` | ✅ | string | - | 상품명 (1~500자) |
| `material` | ❌ | string | `""` | 재질 정보 (0~100자) |
| `usage` | ❌ | string | `""` | 용도 정보 (0~100자) |
| `mode` | ❌ | enum | `"llm"` | 검색 모드 |
| `top_k` | ❌ | int | `5` | 결과 개수 (1~20) |
| `use_llm` | ❌ | bool | `true` | LLM 분석 사용 여부 |
| `include_details` | ❌ | bool | `true` | 상세 정보 포함 여부 |

**Search Mode:**
- `"basic"` - 기본 하이브리드 검색
- `"llm"` - LLM 통합 검색 (기본값)  
- `"keyword_only"` - 키워드 검색만
- `"semantic_only"` - 의미 검색만

**Response:**
```json
{
  "success": true,
  "message": "5개의 HS 코드를 추천했습니다",
  "recommendations": [
    {
      "hs_code": "7318110000",
      "name_kr": "코치 스크루(coach screw)",
      "name_en": "Coach screws",
      "description": "제73류 철강의 제품...",
      "confidence": 1.0,
      "keyword_score": 0.85,
      "semantic_score": 0.92,
      "hybrid_score": 0.89,
      "chapter": "73",
      "heading": "7318",
      "subheading": "731811",
      "data_source": "hsk_with_hs_with_std",
      "is_standard_match": false,
      "llm_analysis": {
        "reasoning": "스테인레스 볼트는 철강제 나사류로 분류됩니다...",
        "confidence": 0.95
      }
    }
  ],
  "search_info": {
    "query": "스테인레스 볼트",
    "expanded_query": "스테인레스 볼트 나사",
    "material": "스테인레스강",
    "usage": "산업용",
    "search_time_ms": 245.6,
    "total_candidates": 15,
    "method": "hybrid_llm",
    "llm_used": true,
    "llm_candidates": 3,
    "search_candidates": 12
  },
  "metadata": {
    "request_mode": "llm",
    "include_details": true,
    "processing_time_ms": 245.6
  }
}
```

#### 1.2 배치 추천
**`POST /api/v1/recommend/batch`**

여러 상품을 한 번에 처리합니다 (최대 10개).

**Request Body:**
```json
{
  "requests": [
    {
      "query": "볼트",
      "top_k": 3
    },
    {
      "query": "LED 전구",
      "material": "플라스틱",
      "usage": "조명용",
      "top_k": 5
    }
  ],
  "parallel_processing": true
}
```

**Response:**
```json
{
  "success": true,
  "total_requests": 2,
  "successful_requests": 2,
  "results": [
    {
      "success": true,
      "message": "3개 추천",
      "recommendations": [...],
      "search_info": {...}
    },
    {
      "success": true, 
      "message": "5개 추천",
      "recommendations": [...],
      "search_info": {...}
    }
  ],
  "processing_time_ms": 1203.45
}
```

---

### 2. 검색 서비스 (`/api/v1/search`)

#### 2.1 GET 방식 검색
**`GET /api/v1/search/?q={query}&limit={limit}`**

URL 파라미터로 간단한 검색을 수행합니다.

**Query Parameters:**
| 파라미터 | 필수 | 타입 | 기본값 | 설명 |
|---------|------|------|-------|------|
| `q` | ✅ | string | - | 검색어 |
| `material` | ❌ | string | - | 재질 |
| `usage` | ❌ | string | - | 용도 |
| `limit` | ❌ | int | `10` | 결과 개수 (1~50) |
| `offset` | ❌ | int | `0` | 시작 위치 |
| `include_scores` | ❌ | bool | `false` | 점수 포함 여부 |

**Example:**
```bash
GET /api/v1/search/?q=플라스틱%20용기&limit=5&include_scores=true
```

#### 2.2 POST 방식 검색
**`POST /api/v1/search/`**

더 복잡한 검색 조건을 POST로 처리합니다.

**Request Body:**
```json
{
  "query": "플라스틱 용기",
  "material": "폴리프로필렌", 
  "usage": "식품 포장용",
  "limit": 10,
  "offset": 0,
  "include_scores": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "10개의 검색 결과를 찾았습니다",
  "results": [
    {
      "hs_code": "3923300000",
      "name_kr": "병ㆍ플라스크와 이와 유사한 용기",
      "name_en": "Bottles, flasks and similar articles",
      "description": "...",
      "confidence": 0.95,
      "keyword_score": 0.88,
      "semantic_score": 0.91
    }
  ],
  "total_count": 25,
  "page_info": {
    "limit": 10,
    "offset": 0,
    "total": 25,
    "has_more": true
  },
  "search_info": {
    "query": "플라스틱 용기",
    "search_time_ms": 156.3,
    "total_candidates": 25,
    "method": "basic_search"
  }
}
```

---

### 3. 캐시 관리 (`/api/v1/cache`)

#### 3.1 캐시 정보 조회
**`GET /api/v1/cache/info`**

현재 캐시 상태를 확인합니다.

**Response:**
```json
{
  "success": true,
  "cache_info": {
    "cache_status": "valid",
    "total_items": 37049,
    "data_sources": {
      "hsk_main": 15234,
      "hsk_with_hs": 12456,
      "hsk_with_std": 8771,
      "hsk_with_hs_with_std": 588
    },
    "uptime_seconds": 3600,
    "performance": {
      "avg_search_time_ms": 145.6,
      "cache_hit_rate": 0.85
    }
  },
  "message": "캐시 정보를 성공적으로 조회했습니다"
}
```

#### 3.2 캐시 재구축
**`POST /api/v1/cache/rebuild`**

데이터를 다시 로드하여 캐시를 재구축합니다.

**Query Parameters:**
- `force` (optional, boolean): 강제 재구축 여부

**Response:**
```json
{
  "success": true,
  "action": "rebuild",
  "message": "캐시가 성공적으로 재구축되었습니다",
  "details": {
    "rebuild_time_seconds": 45.6,
    "total_items_loaded": 37049,
    "cache_size_mb": 156.7
  }
}
```

#### 3.3 캐시 삭제
**`POST /api/v1/cache/clear`**

모든 캐시 파일을 삭제합니다.

**Response:**
```json
{
  "success": true,
  "action": "clear", 
  "message": "캐시가 성공적으로 삭제되었습니다",
  "details": {
    "cleared_files": 4,
    "freed_space_mb": 156.7
  }
}
```

#### 3.4 통합 캐시 관리
**`POST /api/v1/cache/manage`**

다양한 캐시 작업을 통합적으로 처리합니다.

**Request Body:**
```json
{
  "action": "rebuild",
  "force": false
}
```

**Actions:**
- `"rebuild"` - 캐시 재구축
- `"clear"` - 캐시 삭제  
- `"info"` - 캐시 정보 조회

#### 3.5 캐시 통계
**`GET /api/v1/cache/stats`**

캐시 사용량 및 성능 통계를 확인합니다.

**Response:**
```json
{
  "cache_statistics": {
    "hit_rate": 0.85,
    "miss_rate": 0.15,
    "total_requests": 1250,
    "cache_hits": 1062,
    "cache_misses": 188,
    "avg_response_time_ms": 145.6,
    "memory_usage_mb": 156.7,
    "last_rebuild": "2025-01-15T10:30:45Z"
  }
}
```

---

### 4. 헬스체크 (`/health`, `/api/v1/health`)

#### 4.1 기본 헬스체크
**`GET /health`**

서비스의 전반적인 상태를 확인합니다.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1736934645.123,
  "version": "2.1.0",
  "details": {
    "healthy": true,
    "timestamp": 1736934645.123,
    "uptime_seconds": 3600.5,
    "service": "HS 코드 추천 서비스",
    "data_loaded": true,
    "total_items": 37049,
    "cache_valid": true,
    "openai_available": true
  }
}
```

#### 4.2 라이브니스 프로브  
**`GET /api/v1/health/live`**

Kubernetes 라이브니스 체크용 엔드포인트입니다.

**Response:**
```json
{
  "status": "alive",
  "timestamp": 1736934645.123
}
```

#### 4.3 레디니스 프로브
**`GET /api/v1/health/ready`**

서비스가 요청을 처리할 준비가 되었는지 확인합니다.

**Response:**
```json
{
  "status": "ready",
  "timestamp": 1736934645.123,
  "data_loaded": true
}
```

#### 4.4 스타트업 프로브
**`GET /api/v1/health/startup`**

서비스 시작 완료 여부를 확인합니다.

**Response:**
```json
{
  "status": "started",
  "timestamp": 1736934645.123,
  "initialization_complete": true
}
```

---

### 5. 시스템 정보

#### 5.1 루트 정보
**`GET /`**

API 서비스 기본 정보를 확인합니다.

**Response:**
```json
{
  "service": "HS 코드 추천 API",
  "version": "2.1.0", 
  "status": "running",
  "docs": "/docs",
  "api_prefix": "/api/v1"
}
```

#### 5.2 상태 정보
**`GET /status`**

서비스의 상세 상태 정보를 확인합니다.

**Response:**
```json
{
  "service_name": "HS 코드 추천 서비스",
  "version": "2.1.0",
  "status": "active",
  "uptime_seconds": 3600.5,
  "total_items": 37049,
  "cache_status": "valid",
  "openai_available": true,
  "data_sources": {
    "hsk_main": 15234,
    "hsk_with_hs": 12456,
    "hsk_with_std": 8771,
    "hsk_with_hs_with_std": 588
  },
  "performance": {
    "avg_search_time_ms": 145.6,
    "cache_hit_rate": 0.85,
    "total_searches_today": 1250
  }
}
```

---

## 🔧 에러 응답

### HTTP 상태 코드
- `200` - 성공
- `400` - 잘못된 요청 (유효성 검증 실패)
- `404` - 리소스를 찾을 수 없음
- `422` - 요청 데이터 검증 오류  
- `500` - 내부 서버 오류
- `503` - 서비스 사용 불가 (초기화 중)

### 에러 응답 형식
```json
{
  "detail": "에러 메시지",
  "error": "내부 서버 오류",
  "message": "요청 처리 중 오류가 발생했습니다"
}
```

### 유효성 검증 에러 (422)
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "검색어는 비어있을 수 없습니다",
      "type": "value_error"
    }
  ]
}
```

---

## 📊 사용 예시

### cURL 예시

```bash
# 1. 단일 추천
curl -X POST "http://localhost:8000/api/v1/recommend/" \
-H "Content-Type: application/json" \
-d '{
  "query": "스테인레스 볼트",
  "material": "SUS304",
  "usage": "기계 조립용",
  "top_k": 3
}'

# 2. 배치 추천
curl -X POST "http://localhost:8000/api/v1/recommend/batch" \
-H "Content-Type: application/json" \
-d '{
  "requests": [
    {"query": "볼트", "top_k": 3},
    {"query": "LED 전구", "top_k": 5}
  ],
  "parallel_processing": true
}'

# 3. GET 검색
curl "http://localhost:8000/api/v1/search/?q=플라스틱%20용기&limit=5"

# 4. 헬스체크
curl "http://localhost:8000/health"

# 5. 캐시 정보
curl "http://localhost:8000/api/v1/cache/info"
```

### Python 예시

```python
import requests

# API 기본 설정
BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

# 1. 단일 추천
response = requests.post(
    f"{BASE_URL}/api/v1/recommend/",
    json={
        "query": "스테인레스 볼트",
        "material": "스테인레스강",
        "usage": "산업용",
        "top_k": 5,
        "use_llm": True
    },
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"추천 결과: {len(result['recommendations'])}개")
    for rec in result['recommendations']:
        print(f"- {rec['hs_code']}: {rec['name_kr']}")

# 2. 배치 처리
batch_response = requests.post(
    f"{BASE_URL}/api/v1/recommend/batch",
    json={
        "requests": [
            {"query": "볼트", "top_k": 3},
            {"query": "너트", "top_k": 3},
            {"query": "와셔", "top_k": 3}
        ],
        "parallel_processing": True
    },
    headers=headers
)

print(f"배치 처리 결과: {batch_response.json()}")
```

---

## ⚙️ 설정 및 환경변수

### 환경변수
- `ENVIRONMENT` - 실행 환경 (development, production, test)
- `OPENAI_API_KEY` - OpenAI API 키
- `CACHE_DIR` - 캐시 디렉토리 경로
- `LOG_LEVEL` - 로그 레벨 (INFO, DEBUG, ERROR)

### 설정 파일
- `docs/Aivle-api.txt` - OpenAI API 키 파일
- `cache/hs_code_cache/` - 캐시 저장 디렉토리
- `data/` - 원본 데이터 파일들

---

## 🚀 성능 정보

### 데이터 규모
- **총 HS 코드**: 37,049개
- **검색 인덱스**: TF-IDF (30,000 특성) + 임베딩 (768차원)
- **캐시 크기**: 약 150MB

### 응답 시간
- **일반 검색**: 평균 150ms
- **LLM 통합 검색**: 평균 2-3초  
- **배치 처리**: 병렬 처리로 단축

### 처리 용량
- **동시 요청**: 10-50개 (서버 사양에 따라)
- **배치 크기**: 최대 10개 상품
- **캐시 적중률**: 85% 이상

---

## 📝 주의사항

1. **초기화 시간**: 서버 시작 시 데이터 로딩에 2-3분 소요
2. **OpenAI API**: LLM 기능 사용 시 API 키 필요
3. **메모리 사용량**: 약 2GB 이상 권장
4. **캐시 관리**: 정기적인 캐시 재구축 권장

---

## 🔗 참고 링크

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **헬스체크**: http://localhost:8000/health

---

*이 문서는 HS 코드 추천 API v2.1.0 기준으로 작성되었습니다.*