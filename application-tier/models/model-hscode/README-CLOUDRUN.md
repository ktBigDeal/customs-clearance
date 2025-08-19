# Cloud Run 배포 가이드 - HS코드 서비스

## 📋 개요

이 가이드는 HS코드 추천 서비스와 US-KR 변환 서비스를 Google Cloud Run에 배포하는 방법을 설명합니다.

## 🏗️ 서비스 구성

### 1. HS코드 추천 서비스 (`hscode-recommend-service`)
- **포트**: 8003
- **이미지**: `hscode-recommender:latest`
- **기능**: 한국 관세청 HS코드 추천 및 검색
- **리소스**: CPU 1000m, Memory 2Gi
- **자동 스케일링**: 1-10 인스턴스

### 2. US-KR 변환 서비스 (`hscode-us-convert-service`)
- **포트**: 8006
- **이미지**: `hscode-us-converter:latest`
- **기능**: 한국↔미국 HS코드 및 관세율 변환
- **리소스**: CPU 500m, Memory 1Gi
- **자동 스케일링**: 1-5 인스턴스

## 🚀 배포 방법

### 자동 배포 (권장)

```bash
# 실행 권한 부여
chmod +x deploy-cloudrun.sh

# 자동 배포 실행
./deploy-cloudrun.sh
```

### 수동 배포

#### 1. Docker 이미지 빌드 및 푸시

```bash
# 프로젝트 설정
PROJECT_ID="customs-clearance-system"
REGION="asia-northeast3"
REGISTRY="asia-northeast3-docker.pkg.dev"

# Docker 인증
gcloud auth configure-docker ${REGISTRY}

# HS코드 추천 서비스 빌드
docker build -f Dockerfile -t ${REGISTRY}/${PROJECT_ID}/docker-repo/hscode-recommender:latest .
docker push ${REGISTRY}/${PROJECT_ID}/docker-repo/hscode-recommender:latest

# US-KR 변환 서비스 빌드
docker build -f Dockerfile.us-convert -t ${REGISTRY}/${PROJECT_ID}/docker-repo/hscode-us-converter:latest .
docker push ${REGISTRY}/${PROJECT_ID}/docker-repo/hscode-us-converter:latest
```

#### 2. Cloud Run 서비스 배포

```bash
# HS코드 추천 서비스 배포
gcloud run services replace cloudrun-hscode-recommend.yaml \
  --region=asia-northeast3 \
  --project=customs-clearance-system

# US-KR 변환 서비스 배포  
gcloud run services replace cloudrun-us-convert.yaml \
  --region=asia-northeast3 \
  --project=customs-clearance-system
```

## 🔐 환경 설정

### 필수 Secret 설정

```bash
# OpenAI API Key 설정
gcloud secrets create openai-api-key --data-file=- <<< "your-openai-api-key"

# Secret에 접근할 수 있는 권한 부여
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:your-cloud-run-service-account@your-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 환경 변수

각 서비스의 주요 환경 변수:

#### HS코드 추천 서비스
- `PORT`: 8003
- `SERVICE_NAME`: "HS Code Recommendation Service"
- `ENABLE_DOCS`: "true"
- `OPENAI_API_KEY`: Secret에서 로드

#### US-KR 변환 서비스
- `PORT`: 8006
- `SERVICE_NAME`: "US-Korea HS Code Converter Service"
- `US_TARIFF_FILE`: "/app/us_tariff_table_20250714.xlsx"
- `OPENAI_API_KEY`: Secret에서 로드

## 📊 모니터링 및 관리

### 서비스 상태 확인

```bash
# 서비스 목록 조회
gcloud run services list --region=asia-northeast3

# 서비스 상세 정보
gcloud run services describe hscode-recommend-service --region=asia-northeast3
gcloud run services describe hscode-us-convert-service --region=asia-northeast3

# 서비스 URL 확인
gcloud run services describe hscode-recommend-service --region=asia-northeast3 --format="value(status.url)"
gcloud run services describe hscode-us-convert-service --region=asia-northeast3 --format="value(status.url)"
```

### 로그 확인

```bash
# HS코드 추천 서비스 로그
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=hscode-recommend-service" --limit=50

# US-KR 변환 서비스 로그
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=hscode-us-convert-service" --limit=50
```

### 트래픽 관리

```bash
# 트래픽 100% 최신 리비전으로 이동
gcloud run services update-traffic hscode-recommend-service --to-latest --region=asia-northeast3
gcloud run services update-traffic hscode-us-convert-service --to-latest --region=asia-northeast3
```

## 🔧 문제해결

### 일반적인 이슈

1. **503 Service Unavailable**
   - 컨테이너 시작 시간 확인 (timeoutSeconds: 300)
   - 헬스체크 경로 확인 (/health)
   - 메모리 사용량 모니터링

2. **Authentication 오류**
   - Secret 권한 설정 확인
   - Service Account IAM 역할 확인

3. **Docker 빌드 실패**
   - 의존성 파일 경로 확인 (pyproject.toml, uv.lock)
   - 데이터 파일 존재 여부 확인

### 헬스체크 엔드포인트

각 서비스는 다음 경로에서 헬스체크를 제공합니다:
- HS코드 추천: `GET /health`
- US-KR 변환: `GET /health`

## 📝 API 문서

배포 완료 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- HS코드 추천 서비스: `https://your-service-url/docs`
- US-KR 변환 서비스: `https://your-service-url/docs`

## 🔄 업데이트 배포

서비스 업데이트 시:

1. 새 Docker 이미지 빌드 및 푸시
2. Cloud Run 서비스 재배포 (위 명령어 반복)
3. 트래픽이 새 리비전으로 자동 이동됨

## 💰 비용 최적화

- **자동 스케일링**: 트래픽에 따라 0-N 인스턴스로 자동 조정
- **CPU 제한**: 각 서비스별 적절한 CPU/메모리 제한 설정
- **콜드 스타트**: 첫 요청 시 지연시간 고려하여 최소 인스턴스 설정