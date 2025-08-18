# HS코드 서비스 개별 Railway 배포 가이드

model-hscode 서비스를 Railway에 개별적으로 배포하는 단계별 가이드입니다.

## 📋 개요

**model-hscode**는 2개의 독립적인 서비스로 구성되어 있습니다:

1. **HS 코드 추천 서비스** (포트 8003)
   - 일반적인 한국 HS코드 검색 및 추천
   - TF-IDF + 의미 검색 하이브리드
   - OpenAI 선택적 지원

2. **미국→한국 HS 코드 변환 서비스** (포트 8006)
   - 미국 HS코드를 한국 HS코드로 변환
   - LLM 강화 변환 로직
   - OpenAI API 필수

## 🚀 서비스 1: HS 코드 추천 서비스 배포

### 1단계: Railway 프로젝트 생성

1. **Railway 웹사이트** 접속 (https://railway.app)
2. **"New Project"** 클릭
3. **"Deploy from GitHub repo"** 선택
4. `customs-clearance` 저장소 선택

### 2단계: 서비스 설정

1. **Root Directory 설정**:
   ```
   application-tier/models/model-hscode
   ```

2. **서비스 이름**: `hscode-recommend`

3. **Build 명령어**: 자동 감지 (railway.toml 사용)

### 3단계: 환경변수 설정

**Variables** 탭에서 다음 환경변수 추가:

```env
# 필수 환경변수
PORT=8003
ENVIRONMENT=production
SERVICE_NAME=HS Code Recommendation Service

# 선택적 환경변수 (OpenAI 기능 활성화시)
OPENAI_API_KEY=sk-your-openai-api-key-here

# 시스템 설정
UV_SYSTEM_PYTHON=1
LOG_LEVEL=INFO
ENABLE_DOCS=true
```

### 4단계: 배포 확인

배포 완료 후 다음 URL에서 확인:
- **API 서비스**: `https://hscode-recommend-production.up.railway.app`
- **API 문서**: `https://hscode-recommend-production.up.railway.app/docs`
- **헬스체크**: `https://hscode-recommend-production.up.railway.app/health`

### 5단계: API 테스트

```bash
# 헬스체크
curl https://hscode-recommend-production.up.railway.app/health

# HS코드 검색
curl -X POST "https://hscode-recommend-production.up.railway.app/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "딸기", "top_k": 5}'
```

## 🔄 서비스 2: 미국→한국 HS 코드 변환 서비스 배포

### 1단계: 새 서비스 추가

같은 Railway 프로젝트에서:
1. **"+ Add Service"** 클릭
2. **"GitHub Repo"** 선택
3. 같은 `customs-clearance` 저장소 선택

### 2단계: 서비스 설정

1. **Root Directory 설정**:
   ```
   application-tier/models/model-hscode
   ```

2. **서비스 이름**: `hscode-us-convert`

3. **Custom Start Command**:
   ```bash
   uv run uvicorn src.us_main:app --host 0.0.0.0 --port $PORT
   ```

### 3단계: 환경변수 설정

**Variables** 탭에서 다음 환경변수 추가:

```env
# 필수 환경변수
PORT=8006
ENVIRONMENT=production
SERVICE_NAME=US-Korea HS Code Converter Service

# 필수 OpenAI API (LLM 기능용)
OPENAI_API_KEY=sk-your-openai-api-key-here

# 데이터 파일 경로
US_TARIFF_FILE=/app/관세청_미국 관세율표_20250714.xlsx

# 시스템 설정
UV_SYSTEM_PYTHON=1
LOG_LEVEL=INFO
ENABLE_DOCS=true
```

### 4단계: 배포 확인

배포 완료 후 다음 URL에서 확인:
- **API 서비스**: `https://hscode-us-convert-production.up.railway.app`
- **API 문서**: `https://hscode-us-convert-production.up.railway.app/docs`
- **헬스체크**: `https://hscode-us-convert-production.up.railway.app/health`

### 5단계: API 테스트

```bash
# 헬스체크
curl https://hscode-us-convert-production.up.railway.app/health

# HS코드 변환
curl -X POST "https://hscode-us-convert-production.up.railway.app/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{"us_hs_code": "8471300000", "us_product_name": "portable computer"}'
```

## 🔧 고급 설정

### 메모리 및 CPU 설정

각 서비스의 **Settings** → **Resources**에서:
- **Memory**: 512MB - 1GB (권장)
- **CPU**: 0.5 - 1 vCPU (권장)

### 도메인 설정

**Settings** → **Domains**에서 커스텀 도메인 추가 가능:
- `hscode-api.yourdomain.com` (추천 서비스)
- `hscode-convert.yourdomain.com` (변환 서비스)

### 모니터링 설정

**Observability** 탭에서:
- 실시간 로그 모니터링
- 메트릭 및 성능 지표 확인
- 알림 설정

## 📊 배포 후 확인사항

### 1. 기능 테스트

**HS 코드 추천 서비스**:
```bash
# 기본 검색
curl -X POST "https://your-hscode-recommend.up.railway.app/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "스마트폰", "top_k": 3}'

# 캐시 상태 확인
curl "https://your-hscode-recommend.up.railway.app/api/v1/cache/status"
```

**미국→한국 변환 서비스**:
```bash
# 기본 변환
curl -X POST "https://your-hscode-convert.up.railway.app/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{"us_hs_code": "8471300000"}'

# LLM 강화 변환
curl -X POST "https://your-hscode-convert.up.railway.app/api/v1/convert" \
  -H "Content-Type: application/json" \
  -d '{"us_hs_code": "8471300000", "us_product_name": "laptop computer"}'
```

### 2. 성능 확인

- **응답 시간**: 일반적으로 1-3초 이내
- **메모리 사용량**: 초기 로딩 후 안정화
- **오류율**: 5% 미만 유지

### 3. 로그 확인

Railway 대시보드의 **Deployments** → **View Logs**에서:
- 서비스 시작 로그 확인
- 오류 메시지 모니터링
- API 호출 로그 추적

## 🚨 문제 해결

### 일반적인 문제

1. **빌드 실패**:
   - `uv.lock` 파일 확인
   - 환경변수 설정 재확인
   - 로그에서 구체적 오류 메시지 확인

2. **메모리 부족**:
   - Resources에서 메모리 할당량 증가
   - 불필요한 모델 로딩 최적화

3. **OpenAI API 오류**:
   - API 키 유효성 확인
   - 할당량 및 요금 한도 확인

### 지원 및 디버깅

- **로그 확인**: Railway 대시보드의 실시간 로그
- **헬스체크**: `/health` 엔드포인트로 서비스 상태 확인
- **API 문서**: `/docs` 엔드포인트에서 대화형 API 테스트

## ✅ 배포 완료 체크리스트

- [ ] HS 코드 추천 서비스 배포 완료
- [ ] 미국→한국 변환 서비스 배포 완료
- [ ] 환경변수 올바르게 설정
- [ ] 헬스체크 엔드포인트 정상 응답
- [ ] API 문서 접근 가능
- [ ] 기본 API 기능 테스트 완료
- [ ] OpenAI 기능 테스트 완료 (변환 서비스)
- [ ] 로그 모니터링 설정
- [ ] 성능 메트릭 확인

---

**🎉 배포 완료! 이제 Railway에서 안정적으로 HS코드 서비스들이 운영됩니다.**

각 서비스는 독립적으로 확장되고 관리될 수 있으며, Railway 대시보드에서 실시간으로 모니터링할 수 있습니다.