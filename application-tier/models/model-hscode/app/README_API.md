# HS 코드 추천 API 서버

기존 hs_recommender 시스템을 FastAPI 기반 RESTful API로 제공하는 서비스입니다.

## 📋 개요


- **기술 스택**: FastAPI + Python 3.11
- **기능**: AI 기반 HS 코드 추천 및 검색
- **데이터**: HSK 분류 + HS 코드 + 표준품명 통합

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
cd app
pip install -r requirements.txt
```


### 3. 서버 실행

```bash
# 개발 모드
python main.py --reload

# 또는 uvicorn 직접 실행
uvicorn app.main:app --reload --port 8003
```

### 4. API 문서 확인

- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

## 🐳 Docker 실행

### Docker Compose 사용 (권장)

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

### Docker 단독 실행

```bash
# 이미지 빌드
docker build -t hs-recommender-api .

# 컨테이너 실행
docker run -d -p 8003:8003 --name hs-recommender hs-recommender-api
```

## 📡 API 엔드포인트

### 기본 정보

```http
GET /                    # 서비스 정보
GET /health              # 헬스체크
GET /status              # 상세 상태 정보
```

### 추천 API

```http
POST /api/v1/recommend/                # HS 코드 추천
POST /api/v1/recommend/batch           # 배치 추천
GET  /api/v1/recommend/popular         # 인기 검색어
GET  /api/v1/recommend/categories      # 카테고리 정보
```

### 검색 API

```http
GET  /api/v1/search/                   # 간단 검색
POST /api/v1/search/                   # 고급 검색
GET  /api/v1/search/suggestions        # 검색어 제안
GET  /api/v1/search/filters            # 검색 필터
```

### 검증 API

```http
GET  /api/v1/validate/hs-code/{code}   # HS 코드 검증
POST /api/v1/validate/compare          # HS 코드 비교
POST /api/v1/validate/similar          # 유사 코드 찾기
GET  /api/v1/validate/hierarchy/{code} # 계층 구조
```

### 캐시 관리

```http
GET  /api/v1/cache/info                # 캐시 정보
POST /api/v1/cache/rebuild             # 캐시 재구축
POST /api/v1/cache/clear               # 캐시 삭제
GET  /api/v1/cache/stats               # 캐시 통계
```

## 📝 사용 예시

### 1. HS 코드 추천

```bash
curl -X POST "http://localhost:8003/api/v1/recommend/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "스테인레스 볼트",
    "material": "스테인레스강",
    "usage": "산업용",
    "top_k": 5,
    "use_llm": true
  }'
```

### 2. 간단 검색

```bash
curl "http://localhost:8003/api/v1/search/?q=프린터%20토너&limit=10"
```

### 3. HS 코드 검증

```bash
curl "http://localhost:8003/api/v1/validate/hs-code/7318159000"
```

### 4. 캐시 정보 확인

```bash
curl "http://localhost:8003/api/v1/cache/info"
```

## ⚙️ 설정

### 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `ENVIRONMENT` | `development` | 실행 환경 |
| `HOST` | `0.0.0.0` | 서버 호스트 |
| `PORT` | `8003` | 서버 포트 |
| `OPENAI_API_KEY` | - | OpenAI API 키 |
| `SEMANTIC_MODEL` | `jhgan/ko-sroberta-multitask` | 의미 검색 모델 |
| `TOP_K` | `30` | 기본 검색 결과 수 |

### 데이터 파일

다음 데이터 파일들이 필요합니다:

- `data/관세청_HS부호_2025.csv`
- `data/관세청_표준품명_20250101.xlsx`
- `data/관세청_HSK별 신성질별_성질별 분류_20250101.xlsx`

## 🔧 개발

### 코드 스타일

```bash
# 코드 포맷팅
black app/
isort app/

# 린팅
flake8 app/
```

### 테스트

```bash
# 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app
```

### 성능 테스트

```bash
# 부하 테스트 (Apache Bench)
ab -n 100 -c 10 http://localhost:8003/api/v1/recommend/popular

# 또는 wrk 사용
wrk -t4 -c100 -d30s http://localhost:8003/health
```

## 📊 모니터링

### 헬스체크

```bash
# 기본 헬스체크
curl http://localhost:8003/health

# Kubernetes 스타일 프로브
curl http://localhost:8003/api/v1/health/live     # 라이브니스
curl http://localhost:8003/api/v1/health/ready    # 레디니스
curl http://localhost:8003/api/v1/health/startup  # 스타트업
```

### 로그 모니터링

```bash
# Docker Compose 로그
docker-compose logs -f hs-recommender-api

# 컨테이너 로그
docker logs -f hs-recommender
```

## 🔗 기존 시스템과의 통합

### AI Gateway 연동

기존 `ai-gateway`의 모델 레지스트리에 등록:

```python
# ai-gateway의 models.py에 추가
"model-hscode": {
    "name": "HS 코드 추천 모델",
    "type": ModelType.TEXT_CLASSIFIER,
    "url": "http://localhost:8003",
    "endpoints": {
        "recommend": "/api/v1/recommend/",
        "search": "/api/v1/search/"
    }
}
```

### Spring Boot 연동

```java
// Spring Boot에서 호출 예시
@Service
public class HSCodeService {
    
    @Value("${hscode.api.url:http://localhost:8003}")
    private String hsCodeApiUrl;
    
    public HSCodeRecommendation recommend(String query) {
        // RestTemplate 또는 WebClient 사용
        // POST {hsCodeApiUrl}/api/v1/recommend/
    }
}
```

## 🚨 문제 해결

### 자주 발생하는 문제

1. **데이터 파일 없음**
   ```
   FileNotFoundError: 관세청_HS부호_2025.csv
   ```
   → `data/` 폴더에 필요한 파일들을 확인하고 배치

2. **캐시 초기화 실패**
   ```
   캐시가 무효하거나 없습니다
   ```
   → `/api/v1/cache/rebuild` 엔드포인트로 캐시 재구축

3. **OpenAI API 오류**
   ```
   OpenAI 초기화 실패
   ```
   → `.docs` 파일의 `Aivle-api` 확인

4. **메모리 부족**
   ```
   OOM: Out of Memory
   ```
   → Docker 메모리 제한 늘리기 또는 모델 설정 조정

### 로그 레벨 조정

```bash
# 환경 변수로 설정
export LOG_LEVEL=DEBUG

# 또는 .env 파일에서
LOG_LEVEL=DEBUG
```

## 📈 성능 최적화

### 권장 설정

```yaml
# docker-compose.yml
services:
  hs-recommender-api:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
    environment:
      - WORKERS=4  # CPU 코어 수에 맞게 조정
```

### 캐시 워밍업

```bash
# 서버 시작 후 캐시 사전 로드
curl -X POST http://localhost:8003/api/v1/cache/rebuild
```


