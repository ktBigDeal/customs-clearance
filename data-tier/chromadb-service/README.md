# ChromaDB Railway 배포 서비스

Railway에서 ChromaDB를 별도 서비스로 실행하기 위한 설정입니다.

## 📋 배포 방법

### 1. Railway CLI 설치 및 로그인
```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login
```

### 2. 새 프로젝트 생성
```bash
# 새 프로젝트 생성
railway init

# 또는 기존 프로젝트에 서비스 추가
railway link [your-project-id]
```

### 3. ChromaDB 서비스 배포
```bash
# 이 디렉토리에서 실행
cd data-tier/chromadb-service

# Railway에 배포
railway up

# 또는 특정 서비스명으로 배포
railway up --service chromadb
```

### 4. 환경변수 확인
Railway 대시보드에서 다음 환경변수들이 자동 설정되었는지 확인:
- `CHROMA_HOST=0.0.0.0`
- `CHROMA_LOG_LEVEL=INFO`
- `ANONYMIZED_TELEMETRY=false`
- `IS_PERSISTENT=true`
- `PERSIST_DIRECTORY=/chroma/chroma`

### 5. 서비스 URL 확인
배포 완료 후 Railway 대시보드에서 서비스 URL 확인:
- 형태: `https://your-service-name-production.railway.app`
- 헬스체크: `https://your-service-name-production.railway.app/api/v1/heartbeat`

## 🔗 챗봇 서비스 연결

챗봇 서비스에서 다음 환경변수 설정:

```env
CHROMADB_MODE=docker
CHROMADB_HOST=your-chromadb-service-production.railway.app
CHROMADB_PORT=443
CHROMADB_USE_SSL=true
```

## 📊 모니터링

### 헬스체크
```bash
curl https://your-chromadb-service-production.railway.app/api/v1/heartbeat
```

### API 문서
```bash
# ChromaDB API 테스트
curl https://your-chromadb-service-production.railway.app/api/v1
```

## 💾 데이터 지속성

Railway Volume을 통해 데이터가 지속됩니다:
- 볼륨 경로: `/chroma/chroma`
- 자동 백업: Railway에서 제공
- 수동 백업: 데이터 마이그레이션 스크립트 사용

## 🔧 트러블슈팅

### 연결 실패시
1. 서비스 로그 확인: `railway logs --service chromadb`
2. 헬스체크 상태 확인
3. 환경변수 확인
4. 방화벽/보안 그룹 설정 확인

### 데이터 손실시
1. Railway Volume 상태 확인
2. 백업에서 복원
3. 로컬 데이터 재마이그레이션

## 💰 비용

- Railway Hobby 플랜: $5/월
- 메모리: 512MB (기본)
- vCPU: 0.5 (기본)
- 스토리지: 1GB (기본)

확장 필요시 Railway 대시보드에서 리소스 조정 가능.