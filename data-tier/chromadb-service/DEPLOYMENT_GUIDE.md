# 🚂 Railway ChromaDB 배포 가이드 (완전판)

Railway에서 ChromaDB를 별도 서비스로 배포하고 챗봇과 연결하는 완전한 가이드입니다.

## 📋 배포 순서 (중요!)

### 1️⃣ 사전 준비
```bash
# Railway CLI 설치
npm install -g @railway/cli

# Railway 로그인
railway login

# 새 프로젝트 생성
railway init
```

### 2️⃣ ChromaDB 서비스 배포 (첫 번째)
```bash
# ChromaDB 서비스 디렉토리로 이동
cd data-tier/chromadb-service

# Railway 볼륨 생성 (데이터 영속성 확보)
railway volume create --name chromadb-data --mount-path /chroma/chroma --service chromadb

# Railway에 배포
railway up --service chromadb

# 배포 상태 확인
railway status --service chromadb
```

**배포 후 확인사항:**
- ✅ 서비스 URL 획득: `https://chromadb-production-xxxx.railway.app`
- ✅ 헬스체크 성공: `/api/v1/heartbeat`
- ✅ Railway 볼륨 연결 확인: `railway volume list --service chromadb`
- ✅ 서비스 로그 정상

### 3️⃣ 데이터 마이그레이션 (두 번째)
```bash
# 마이그레이션 도구 의존성 설치
pip install -r requirements.txt

# 로컬 ChromaDB 데이터를 Railway로 마이그레이션
python migrate_data.py \
  --source-path ../../application-tier/models/model-chatbot-fastapi/data/chroma_db \
  --railway-url https://chromadb-production-xxxx.railway.app \
  --batch-size 50

# 마이그레이션 검증
python migrate_data.py \
  --source-path ../../application-tier/models/model-chatbot-fastapi/data/chroma_db \
  --railway-url https://chromadb-production-xxxx.railway.app \
  --verify-only
```

### 4️⃣ 챗봇 서비스 환경변수 설정 (세 번째)
```bash
# 챗봇 서비스로 이동
cd ../../application-tier/models/model-chatbot-fastapi

# Railway 환경변수 설정
railway variables set CHROMADB_MODE=docker --service chatbot
railway variables set CHROMADB_HOST=chromadb-production-xxxx.railway.app --service chatbot
railway variables set CHROMADB_PORT=443 --service chatbot
railway variables set CHROMADB_USE_SSL=true --service chatbot
railway variables set OPENAI_API_KEY=sk-your-openai-key --service chatbot
```

### 5️⃣ 챗봇 서비스 배포 (네 번째)
```bash
# 챗봇 서비스 배포
railway up --service chatbot

# 배포 상태 확인
railway status --service chatbot
```

### 6️⃣ 연결 테스트 (다섯 번째)
```bash
# ChromaDB 헬스체크
curl https://chromadb-production-xxxx.railway.app/api/v1/heartbeat

# 챗봇 헬스체크
curl https://chatbot-production-yyyy.railway.app/health

# 챗봇 API 테스트
curl -X POST https://chatbot-production-yyyy.railway.app/api/v1/conversations/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요", "user_id": 1}'
```

## 🎯 서비스별 환경변수 매트릭스

### ChromaDB 서비스
```env
CHROMA_HOST=0.0.0.0
CHROMA_LOG_LEVEL=INFO
ANONYMIZED_TELEMETRY=false
IS_PERSISTENT=true
PERSIST_DIRECTORY=/chroma/chroma
PORT=$PORT  # Railway 자동 할당
```

### 챗봇 서비스
```env
CHROMADB_MODE=docker
CHROMADB_HOST=chromadb-production-xxxx.railway.app
CHROMADB_PORT=443
CHROMADB_USE_SSL=true
OPENAI_API_KEY=sk-your-openai-key
PORT=$PORT  # Railway 자동 할당
ENVIRONMENT=production
```

## ⚡ 빠른 시작 스크립트

### 전체 배포 자동화 스크립트
```bash
#!/bin/bash
# deploy_chromadb.sh

set -e

echo "🚂 Railway ChromaDB 배포 시작..."

# 1. ChromaDB 서비스 배포
echo "1️⃣ ChromaDB 서비스 배포 중..."
cd data-tier/chromadb-service
railway up --service chromadb --detach

# 배포 완료 대기
echo "⏳ ChromaDB 서비스 배포 완료 대기..."
sleep 60

# 2. 서비스 URL 획득
CHROMADB_URL=$(railway domain --service chromadb)
echo "📍 ChromaDB URL: $CHROMADB_URL"

# 3. 헬스체크
echo "🔍 헬스체크 중..."
curl -f "$CHROMADB_URL/api/v1/heartbeat" || exit 1

# 4. 데이터 마이그레이션
echo "📦 데이터 마이그레이션 중..."
pip install -r requirements.txt
python migrate_data.py \
  --source-path ../../application-tier/models/model-chatbot-fastapi/data/chroma_db \
  --railway-url "$CHROMADB_URL" \
  --batch-size 50

# 5. 챗봇 서비스 환경변수 설정
echo "⚙️ 챗봇 환경변수 설정 중..."
cd ../../application-tier/models/model-chatbot-fastapi
railway variables set CHROMADB_MODE=docker --service chatbot
railway variables set CHROMADB_HOST="$(echo $CHROMADB_URL | sed 's|https://||')" --service chatbot
railway variables set CHROMADB_PORT=443 --service chatbot
railway variables set CHROMADB_USE_SSL=true --service chatbot

# 6. 챗봇 서비스 배포
echo "🤖 챗봇 서비스 배포 중..."
railway up --service chatbot --detach

echo "✅ 배포 완료!"
echo "🌐 ChromaDB: $CHROMADB_URL"
echo "🤖 챗봇: $(railway domain --service chatbot)"
```

### 연결 테스트 스크립트
```bash
#!/bin/bash
# test_connection.sh

CHROMADB_URL="https://chromadb-production-xxxx.railway.app"
CHATBOT_URL="https://chatbot-production-yyyy.railway.app"

echo "🧪 연결 테스트 시작..."

# ChromaDB 헬스체크
echo "1. ChromaDB 헬스체크..."
if curl -f "$CHROMADB_URL/api/v1/heartbeat"; then
    echo "✅ ChromaDB 연결 성공"
else
    echo "❌ ChromaDB 연결 실패"
    exit 1
fi

# 챗봇 헬스체크
echo "2. 챗봇 헬스체크..."
if curl -f "$CHATBOT_URL/health"; then
    echo "✅ 챗봇 연결 성공"
else
    echo "❌ 챗봇 연결 실패"
    exit 1
fi

# 챗봇 API 테스트
echo "3. 챗봇 API 테스트..."
response=$(curl -s -X POST "$CHATBOT_URL/api/v1/conversations/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "테스트 메시지", "user_id": 1}')

if echo "$response" | grep -q "response"; then
    echo "✅ 챗봇 API 테스트 성공"
    echo "📝 응답: $(echo $response | head -c 100)..."
else
    echo "❌ 챗봇 API 테스트 실패"
    echo "📝 응답: $response"
fi

echo "🎉 모든 테스트 완료!"
```

## 🔧 트러블슈팅 가이드

### 자주 발생하는 오류들

#### 1. ChromaDB 배포 실패
```
Error: Container failed to start
```
**해결방법:**
- Railway 로그 확인: `railway logs --service chromadb`
- Dockerfile 문법 확인
- 포트 설정 확인 (PORT 환경변수)

#### 2. 데이터 마이그레이션 실패
```
ConnectionError: Could not connect to ChromaDB
```
**해결방법:**
- ChromaDB 서비스 상태 확인
- 네트워크 연결 확인
- SSL 인증서 확인

#### 3. 챗봇 연결 실패
```
CHROMADB_HOST not found
```
**해결방법:**
- 환경변수 재설정: `railway variables list --service chatbot`
- ChromaDB URL 확인
- SSL 설정 확인

### 모니터링 명령어
```bash
# 서비스 상태 확인
railway status

# 로그 실시간 모니터링
railway logs --follow --service chromadb
railway logs --follow --service chatbot

# 환경변수 확인
railway variables list --service chromadb
railway variables list --service chatbot

# 도메인 확인
railway domain --service chromadb
railway domain --service chatbot
```

## 💰 비용 관리

### Railway 요금제
- **Hobby**: $5/월 - 개인 프로젝트
- **Pro**: $20/월 - 팀 프로젝트
- **Team**: $99/월 - 기업용

### 리소스 최적화
```bash
# 서비스별 리소스 모니터링
railway metrics --service chromadb
railway metrics --service chatbot

# 스케일링 조정 (필요시)
railway service configure --memory 1GB --service chromadb
railway service configure --cpu 1.0 --service chatbot
```

## 📊 성공 지표

✅ **배포 성공 확인:**
- ChromaDB 헬스체크 응답: 200 OK
- 챗봇 헬스체크 응답: 200 OK
- 데이터 마이그레이션 완료: 100% 성공
- API 테스트 통과: 모든 엔드포인트 정상

✅ **성능 확인:**
- ChromaDB 응답시간: < 500ms
- 챗봇 응답시간: < 2초
- 메모리 사용량: < 80%
- CPU 사용량: < 70%

Railway ChromaDB 배포가 완료되면 챗봇 서비스가 클라우드 환경에서 안정적으로 운영됩니다! 🎉