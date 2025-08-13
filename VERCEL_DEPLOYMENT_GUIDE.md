# 🚀 Vercel 배포 가이드

## 📋 배포 전략 개요

이 프로젝트는 **복잡한 마이크로서비스 아키텍처**로 구성되어 있습니다:
- Frontend (Next.js)
- Backend (Spring Boot) 
- Multiple AI Services (FastAPI)
- Databases (MySQL, PostgreSQL, ChromaDB, Redis)

Vercel은 **프론트엔드 전용 플랫폼**이므로, 단계적 배포가 필요합니다.

---

## 🎯 1단계: 프론트엔드만 배포 (권장)

### 전제 조건
- [x] Vercel 계정 생성
- [x] Git 저장소 (GitHub, GitLab, Bitbucket)
- [x] Node.js 18+ 설치

### 1.1 Vercel CLI 설치 및 로그인

```bash
npm install -g vercel
vercel login
```

### 1.2 프론트엔드 폴더만 배포

**옵션 A: 전체 저장소에서 배포**
```bash
cd customs-clearance/presentation-tier/frontend
vercel --prod
```

**옵션 B: 프론트엔드만 별도 저장소 생성 (권장)**
```bash
# 1. 새 저장소 생성
git clone <your-repo-url> customs-frontend
cd customs-frontend

# 2. 프론트엔드 파일들만 복사
cp -r customs-clearance/presentation-tier/frontend/* .

# 3. Git 초기화
git add .
git commit -m "feat: 프론트엔드 초기 설정"
git push origin main

# 4. Vercel 배포
vercel --prod
```

### 1.3 환경변수 설정

Vercel 대시보드에서 다음 환경변수들을 설정하세요:

```bash
# 필수 환경변수
NEXT_PUBLIC_API_URL=https://your-backend-url.com/api/v1
NEXT_PUBLIC_ENVIRONMENT=production

# AI 서비스 URL (백엔드 준비되면 추가)
NEXT_PUBLIC_AI_GATEWAY_URL=https://your-ai-gateway.com
```

---

## 🖥️ 2단계: 백엔드 배포 옵션

Vercel은 백엔드를 지원하지 않으므로 다른 플랫폼 사용이 필요합니다:

### 옵션 A: Heroku (가장 간단)
```bash
# Spring Boot 배포
cd presentation-tier/backend
heroku create customs-clearance-backend
heroku buildpacks:set heroku/java
git push heroku main
```

### 옵션 B: Railway
```bash
# Railway CLI 설치
npm install -g @railway/cli
railway login

# Spring Boot 배포
cd presentation-tier/backend  
railway link
railway up
```

### 옵션 C: DigitalOcean App Platform
- Spring Boot JAR 파일 업로드
- 환경변수 설정
- 자동 배포 설정

### 옵션 D: AWS EC2/ECS
- Docker 컨테이너화 필요
- 가장 복잡하지만 확장성 최고

---

## 🤖 3단계: AI 서비스 배포

### FastAPI 서비스들 배포 옵션:

**옵션 A: Render (무료 티어 있음)**
```bash
# 각 AI 서비스별로 배포
cd application-tier/ai-gateway
# render.yaml 설정 파일 생성 필요

cd application-tier/models/model-chatbot-fastapi
# render.yaml 설정 파일 생성 필요
```

**옵션 B: Heroku**
```bash
# AI Gateway 배포
cd application-tier/ai-gateway
heroku create customs-ai-gateway
heroku buildpacks:set heroku/python
git push heroku main
```

---

## 💾 4단계: 데이터베이스 배포

### MySQL
- **PlanetScale** (무료 티어)
- **AWS RDS**
- **Google Cloud SQL**

### PostgreSQL  
- **Supabase** (무료 티어)
- **Neon** (무료 티어)
- **Heroku Postgres**

### Redis
- **Upstash Redis** (무료 티어)
- **Redis Labs**

### ChromaDB
- **Chroma Cloud**
- 자체 호스팅 (Docker)

---

## ⚡ 빠른 시작 (프론트엔드만)

### 1. 즉시 배포하기

```bash
cd presentation-tier/frontend
npx vercel
```

### 2. 환경변수 설정
Vercel 대시보드에서:
```
NEXT_PUBLIC_API_URL = http://localhost:8080/api/v1  # 임시로 로컬
```

### 3. 도메인 확인
- `https://your-app.vercel.app`에서 프론트엔드 동작 확인
- API 호출은 CORS 에러가 날 수 있음 (백엔드 미배포 시)

---

## 🔧 고급 설정

### vercel.json 설정 (이미 생성됨)
```json
{
  "name": "customs-clearance-frontend",
  "version": 2,
  "builds": [{"src": "package.json", "use": "@vercel/next"}],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url"
  }
}
```

### next.config.js 최적화 (이미 적용됨)
- 프로덕션에서 console.log 제거
- 이미지 최적화 설정
- API rewrites 개발환경에서만 활성화

---

## 🚨 주의사항

### 1. 백엔드 없이 프론트엔드만 배포시
- 로그인/회원가입 불가
- 실제 데이터 조회 불가  
- UI/UX만 확인 가능

### 2. CORS 설정
백엔드에서 Vercel 도메인 허용 필요:
```java
@CrossOrigin(origins = {"https://your-app.vercel.app"})
```

### 3. 환경변수 보안
- API 키 등 민감정보는 서버 환경변수에만
- `NEXT_PUBLIC_*`는 브라우저에 노출됨

---

## 📈 단계별 배포 일정 제안

### Week 1: 프론트엔드
- [x] Vercel에 프론트엔드 배포
- [x] 기본 UI/UX 테스트
- [ ] 도메인 연결 (선택사항)

### Week 2: 백엔드  
- [ ] Heroku/Railway에 Spring Boot 배포
- [ ] MySQL 클라우드 연결
- [ ] 프론트엔드-백엔드 연동 테스트

### Week 3: AI 서비스
- [ ] FastAPI 서비스들 배포  
- [ ] ChromaDB 클라우드 연결
- [ ] 챗봇 기능 활성화

### Week 4: 최적화
- [ ] CDN 설정
- [ ] 모니터링 추가
- [ ] 성능 최적화

---

## 🎉 배포 완료 후 확인사항

- [ ] 프론트엔드 정상 로딩
- [ ] 반응형 디자인 확인
- [ ] 라우팅 작동 확인
- [ ] SEO 메타태그 확인
- [ ] 라이트하우스 점수 확인

---

**다음 단계**: 백엔드 배포가 준비되면 환경변수만 업데이트하면 됩니다!