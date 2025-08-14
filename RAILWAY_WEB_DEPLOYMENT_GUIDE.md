# Railway 웹사이트 배포 가이드

Railway.app 웹사이트를 통해 통관 시스템을 배포하는 완전 가이드입니다.

## 📋 목차

1. [Railway 계정 설정 및 프로젝트 생성](#railway-계정-설정-및-프로젝트-생성)
2. [GitHub 연동 설정](#github-연동-설정)
3. [데이터베이스 서비스 추가](#데이터베이스-서비스-추가)
4. [백엔드 및 AI 서비스 배포](#백엔드-및-ai-서비스-배포)
5. [환경변수 설정](#환경변수-설정)
6. [서비스 간 연결 설정](#서비스-간-연결-설정)
7. [도메인 및 네트워킹](#도메인-및-네트워킹)
8. [모니터링 및 디버깅](#모니터링-및-디버깅)

## 🚀 Railway 계정 설정 및 프로젝트 생성

### 1단계: Railway 계정 생성

1. **Railway 웹사이트 방문**
   - 🔗 https://railway.app 접속
   - **"Start a New Project"** 또는 **"Login"** 클릭

2. **GitHub로 회원가입/로그인**
   - "Continue with GitHub" 선택
   - GitHub 계정으로 인증 완료
   - Repository 접근 권한 허용

3. **새 프로젝트 생성**
   - Dashboard에서 **"New Project"** 클릭
   - 프로젝트 이름: `customs-clearance-system` 입력

## 📁 GitHub 연동 설정

### 2단계: Repository 연결

1. **프로젝트 생성 방식 선택**
   - **"Deploy from GitHub repo"** 선택

2. **Repository 선택**
   - `customs-clearance` repository 검색 및 선택
   - **"Deploy Now"** 클릭

3. **Root 디렉토리 설정**
   - Railway가 자동으로 프로젝트를 스캔합니다
   - 여러 서비스가 감지되면 각각 개별적으로 배포해야 합니다

## 🗄️ 데이터베이스 서비스 추가

### 3단계: 데이터베이스 설정

1. **MySQL 추가**
   - 프로젝트 대시보드에서 **"+ New"** 클릭
   - **"Database"** → **"Add MySQL"** 선택
   - 서비스 이름: `customs-mysql`

2. **PostgreSQL 추가 (챗봇용)**
   - **"+ New"** → **"Database"** → **"Add PostgreSQL"**
   - 서비스 이름: `customs-postgres`

3. **Redis 추가 (캐시용)**
   - **"+ New"** → **"Database"** → **"Add Redis"**
   - 서비스 이름: `customs-redis`

### 데이터베이스 초기화

**MySQL 설정:**
1. MySQL 서비스 클릭 → **"Connect"** 탭 → **"MySQL CLI"** 실행
2. 아래 스크립트들을 순서대로 실행:
```sql
-- 데이터베이스 및 사용자 생성
CREATE DATABASE IF NOT EXISTS customs_clearance;
CREATE USER IF NOT EXISTS 'customs_user'@'%' IDENTIFIED BY 'customs_pass';
GRANT ALL PRIVILEGES ON customs_clearance.* TO 'customs_user'@'%';
FLUSH PRIVILEGES;
USE customs_clearance;

-- 테이블 생성 (data-tier/mysql/init/01-schema.sql 내용 복사)
-- 샘플 데이터 삽입 (data-tier/mysql/init/02-seed-data.sql 내용 복사)
```

**PostgreSQL 설정:**
1. PostgreSQL 서비스 클릭 → **"Connect"** 탭 → **"psql"** 실행
2. 데이터베이스 생성:
```sql
CREATE DATABASE conversations;
```

## 🚀 백엔드 및 AI 서비스 배포

### 4단계: Spring Boot 백엔드 배포

1. **새 서비스 추가**
   - **"+ New"** → **"GitHub Repo"** → `customs-clearance` 선택
   - **"Deploy"** 클릭

2. **Root Directory 설정**
   - Service Settings → **"Source"** 탭
   - **"Root Directory"**: `presentation-tier/backend` 입력
   - **"Deploy"** 클릭

3. **서비스 이름 변경**
   - Service Settings → **"General"** 탭
   - Service Name: `customs-backend` 입력

### 5단계: AI Gateway 배포

1. **새 서비스 추가**
   - **"+ New"** → **"GitHub Repo"** → `customs-clearance` 선택

2. **Root Directory 설정**
   - Root Directory: `application-tier/ai-gateway`
   - Service Name: `customs-ai-gateway`

### 6단계: AI 모델 서비스들 배포

각 서비스마다 같은 방식으로 배포:

1. **Chatbot FastAPI 서비스**
   - Root Directory: `application-tier/models/model-chatbot-fastapi`
   - Service Name: `customs-chatbot-fastapi`

2. **OCR 서비스**
   - Root Directory: `application-tier/models/model-ocr`
   - Service Name: `customs-ocr`

3. **Report 서비스**
   - Root Directory: `application-tier/models/model-report`
   - Service Name: `customs-report`

4. **HS Code 서비스**
   - Root Directory: `application-tier/models/model-hscode`
   - Service Name: `customs-hscode`

## 🔧 환경변수 설정

### 7단계: 각 서비스별 환경변수 설정

각 서비스의 **"Variables"** 탭에서 환경변수를 설정합니다.

### 공통 환경변수

**모든 서비스에 설정:**
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
ENVIRONMENT=production
```

### Backend (Spring Boot) 환경변수

**customs-backend 서비스:**
```env
# Spring 설정
SPRING_PROFILES_ACTIVE=production
PORT=8080

# JWT 보안
JWT_SECRET=your-very-long-and-secure-jwt-secret-key-256-bits-minimum

# 데이터베이스 연결 (Railway 자동 생성)
SPRING_DATASOURCE_URL=${{customs-mysql.DATABASE_URL}}
SPRING_DATASOURCE_USERNAME=${{customs-mysql.MYSQL_USER}}
SPRING_DATASOURCE_PASSWORD=${{customs-mysql.MYSQL_PASSWORD}}

# JVM 최적화
JAVA_OPTS=-Xmx512m -XX:+UseContainerSupport -XX:+UseG1GC
```

### AI Gateway 환경변수

**customs-ai-gateway 서비스:**
```env
PORT=8000
ENVIRONMENT=production

# AI 서비스 연결 (내부 URL 사용)
MODEL_CHATBOT_URL=https://${{customs-chatbot-fastapi.RAILWAY_PUBLIC_DOMAIN}}
MODEL_OCR_URL=https://${{customs-ocr.RAILWAY_PUBLIC_DOMAIN}}
MODEL_REPORT_URL=https://${{customs-report.RAILWAY_PUBLIC_DOMAIN}}
MODEL_HSCODE_URL=https://${{customs-hscode.RAILWAY_PUBLIC_DOMAIN}}
```

### Chatbot FastAPI 환경변수

**customs-chatbot-fastapi 서비스:**
```env
PORT=8000
ENVIRONMENT=production

# ChromaDB 설정
CHROMADB_MODE=docker
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# 데이터베이스 연결
DATABASE_URL=${{customs-postgres.DATABASE_URL}}
REDIS_URL=${{customs-redis.REDIS_URL}}
```

### OCR 서비스 환경변수

**customs-ocr 서비스:**
```env
PORT=8001
ENVIRONMENT=production

# Azure OCR 설정 (선택사항)
AZURE_FORM_RECOGNIZER_ENDPOINT=your-azure-endpoint
AZURE_FORM_RECOGNIZER_KEY=your-azure-key
```

### Report 서비스 환경변수

**customs-report 서비스:**
```env
PORT=8002
ENVIRONMENT=production
```

### HS Code 서비스 환경변수

**customs-hscode 서비스:**
```env
PORT=8003
ENVIRONMENT=production
```

## 🔗 서비스 간 연결 설정

### 8단계: Railway 서비스 참조 설정

Railway에서 서비스 간 통신을 위해 내부 URL을 사용합니다:

1. **서비스 URL 확인**
   - 각 서비스의 **"Settings"** → **"Domains"** 탭에서 Public Domain 확인

2. **내부 통신 URL 설정**
   ```env
   # AI Gateway에서 다른 서비스 호출
   MODEL_CHATBOT_URL=https://customs-chatbot-fastapi-production-a1b2c3.up.railway.app
   MODEL_OCR_URL=https://customs-ocr-production-d4e5f6.up.railway.app
   MODEL_REPORT_URL=https://customs-report-production-g7h8i9.up.railway.app
   MODEL_HSCODE_URL=https://customs-hscode-production-j1k2l3.up.railway.app
   ```

## 🌐 도메인 및 네트워킹

### 9단계: 도메인 설정

1. **자동 생성된 도메인 확인**
   - 각 서비스는 자동으로 `https://service-name-production-xxxxx.up.railway.app` 형태의 도메인을 받습니다

2. **커스텀 도메인 설정 (선택사항)**
   - Service Settings → **"Domains"** 탭
   - **"Custom Domain"** 클릭하여 원하는 도메인 추가

3. **주요 서비스 URL**
   ```
   Backend API: https://customs-backend-production.up.railway.app
   AI Gateway: https://customs-ai-gateway-production.up.railway.app
   Chatbot API: https://customs-chatbot-fastapi-production.up.railway.app
   ```

## 📊 모니터링 및 디버깅

### 10단계: 로그 및 모니터링 설정

1. **로그 확인**
   - 각 서비스 클릭 → **"Deployments"** 탭 → 최신 배포의 **"View Logs"**

2. **실시간 로그 모니터링**
   - **"Observability"** 탭에서 실시간 로그 확인

3. **메트릭 확인**
   - **"Metrics"** 탭에서 CPU, 메모리, 네트워크 사용량 모니터링

### 일반적인 문제 해결

1. **빌드 실패시**
   - Logs에서 에러 메시지 확인
   - Dockerfile이나 빌드 설정 수정

2. **메모리 부족시**
   - Service Settings → **"Resources"** 탭에서 메모리 할당량 증가

3. **환경변수 누락시**
   - **"Variables"** 탭에서 필수 환경변수 추가

## ✅ 배포 검증

### 11단계: 서비스 동작 확인

1. **헬스체크 확인**
   ```
   Backend: https://your-backend-domain.up.railway.app/api/v1/health
   AI Gateway: https://your-gateway-domain.up.railway.app/health
   각 AI 서비스: https://your-service-domain.up.railway.app/health
   ```

2. **API 문서 확인**
   ```
   Backend Swagger: https://your-backend-domain.up.railway.app/swagger-ui/index.html
   AI Gateway Docs: https://your-gateway-domain.up.railway.app/docs
   ```

3. **데이터베이스 연결 확인**
   - 각 데이터베이스 서비스의 Connect 탭에서 연결 상태 확인

## 🎯 배포 완료 체크리스트

- [ ] Railway 계정 생성 및 GitHub 연동
- [ ] 프로젝트 생성 완료
- [ ] MySQL, PostgreSQL, Redis 데이터베이스 추가
- [ ] Backend (Spring Boot) 서비스 배포
- [ ] AI Gateway 서비스 배포
- [ ] AI 모델 서비스들 (Chatbot, OCR, Report, HSCode) 배포
- [ ] 모든 서비스의 환경변수 설정
- [ ] 서비스 간 URL 연결 설정
- [ ] 데이터베이스 초기화 완료
- [ ] 헬스체크 엔드포인트 정상 응답
- [ ] API 문서 접근 가능
- [ ] 로그 모니터링 설정

## 🔄 프론트엔드 연결

**Vercel 프론트엔드에서 연결할 API URLs:**
```env
# Vercel 환경변수에 추가
NEXT_PUBLIC_API_BASE_URL=https://customs-backend-production.up.railway.app
NEXT_PUBLIC_AI_GATEWAY_URL=https://customs-ai-gateway-production.up.railway.app
NEXT_PUBLIC_CHATBOT_URL=https://customs-chatbot-fastapi-production.up.railway.app
```

---

**🎉 배포 완료! 이제 완전한 통관 시스템이 Railway에서 운영됩니다.**

Railway 대시보드에서 모든 서비스의 상태를 실시간으로 모니터링하고 관리할 수 있습니다.