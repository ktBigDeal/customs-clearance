# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 필요한 가이드를 제공합니다.

## 📋 프로젝트 개요

**기업형 관세 통관 시스템** - AI 기반 수출입 신고서 처리 및 관리 플랫폼

### 🏗️ 아키텍처
3-tier 엔터프라이즈 아키텍처로 구성된 완전한 시스템:

- **🎨 Presentation Tier**: 사용자 인터페이스 및 API 게이트웨이
- **🧠 Application Tier**: AI/ML 서비스 및 비즈니스 로직  
- **💾 Data Tier**: 데이터 저장소 및 캐시

## 🛠️ 기술 스택

### Frontend (Next.js 14.2)
- **Framework**: Next.js 14.2 + React 18 + TypeScript
- **Styling**: Tailwind CSS 3.4 + Radix UI 컴포넌트
- **State Management**: React Query (@tanstack/react-query)
- **Forms**: React Hook Form + Zod 검증
- **i18n**: next-intl (한국어/영어 완전 지원)
- **UI Components**: 완성된 컴포넌트 시스템 (Header, Sidebar, Dashboard)

### Backend (Spring Boot 3.2)
- **Framework**: Spring Boot 3.2.1 + Java 17
- **Database**: Spring Data JPA + MySQL 8.0 연동
- **Migration**: Flyway 마이그레이션 설정
- **Documentation**: SpringDoc OpenAPI (Swagger UI)
- **Security**: JWT 인증 준비
- **Monitoring**: Spring Actuator (health, metrics, prometheus)

### AI/ML Services (FastAPI 0.104)
- **Framework**: FastAPI + Python 3.11
- **Async**: uvicorn + httpx + aiohttp
- **Database**: SQLAlchemy + asyncpg/aiomysql
- **Validation**: Pydantic 2.5
- **Monitoring**: Prometheus metrics
- **Services**: 문서 분류 모델, OCR 텍스트 추출 모델

### Database (MySQL 8.0)
- **Primary DB**: MySQL 8.0 with utf8mb4 charset
- **Schema**: 완성된 테이블 구조 (users, declarations, attachments, history)
- **Test Data**: 초기 시드 데이터 포함
- **Management**: phpMyAdmin 웹 인터페이스

## 📁 현재 코드베이스 상태

### ✅ 완성된 컴포넌트들

#### 🎨 Presentation Tier
```
presentation-tier/
├── backend/                    # Spring Boot API 서버
│   ├── src/main/java/com/customs/clearance/
│   │   ├── controller/         # DeclarationController, HealthController
│   │   ├── dto/               # Request/Response DTOs
│   │   ├── entity/            # JPA 엔티티 (Declaration, BaseEntity)
│   │   ├── service/           # 비즈니스 로직 구현
│   │   ├── repository/        # 데이터 접근 계층
│   │   ├── config/            # Security, Database, Web 설정
│   │   └── exception/         # 글로벌 예외 처리
│   ├── src/main/resources/
│   │   ├── application.yml    # 환경별 설정 (dev, prod, test)
│   │   └── db/migration/      # Flyway 마이그레이션 스크립트
│   └── pom.xml               # Maven 의존성 관리
│
└── frontend/                  # Next.js 웹 애플리케이션
    ├── src/app/               # App Router 구조
    │   ├── (dashboard)/       # 대시보드 페이지들
    │   └── layout.tsx         # 글로벌 레이아웃
    ├── src/components/        # React 컴포넌트
    │   ├── layout/            # Header, Sidebar, MainNav 완성
    │   ├── ui/                # Button, Card, DropdownMenu
    │   └── providers/         # QueryProvider
    ├── src/lib/               # 유틸리티
    │   ├── api.ts             # Axios 기반 API 클라이언트
    │   └── declarations-api.ts # 신고서 API 래퍼
    ├── messages/              # 다국어 지원
    │   ├── ko.json            # 한국어 번역 (완성)
    │   └── en.json            # 영어 번역 (완성)
    └── package.json           # 의존성 관리
```

#### 🤖 Application Tier
```
application-tier/
├── ai-gateway/                # FastAPI 메인 게이트웨이
│   ├── app/
│   │   ├── main.py           # FastAPI 앱 진입점
│   │   ├── core/             # 설정, 미들웨어, 로깅
│   │   ├── routers/          # API 엔드포인트 (health, models, ai_gateway)
│   │   └── schemas/          # Pydantic 모델들
│   ├── requirements.txt      # Python 의존성
│   └── docker-compose.yml    # AI 스택 오케스트레이션
│
└── models/                   # AI 모델 마이크로서비스
    ├── model-a/              # 문서 분류 서비스
    ├── model-b/              # OCR 텍스트 추출 서비스
    └── shared/               # 공통 유틸리티
```

#### 💾 Data Tier
```
data-tier/
├── mysql/
│   ├── config/my.cnf         # MySQL 설정 (한글 지원)
│   └── init/                 # 초기화 스크립트
│       ├── 01-schema.sql     # 테이블 스키마
│       └── 02-seed-data.sql  # 테스트 데이터
├── scripts/
│   └── test-connection.py    # DB 연결 테스트
└── docker-compose.yml        # MySQL + phpMyAdmin
```

## 🚀 개발 가이드

### 로컬 개발 환경 실행

#### 1. 데이터베이스 실행
```bash
cd data-tier
docker-compose up -d
```

#### 2. 백엔드 실행 
```bash
cd presentation-tier/backend
./mvnw spring-boot:run
```

#### 3. 프론트엔드 실행
```bash
cd presentation-tier/frontend
npm install
npm run dev
```

#### 4. AI 게이트웨이 실행
```bash
cd application-tier/ai-gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 🌐 서비스 URL
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/api/v1
- **Swagger UI**: http://localhost:8080/swagger-ui.html
- **AI Gateway**: http://localhost:8000
- **AI Docs**: http://localhost:8000/docs
- **phpMyAdmin**: http://localhost:8081

## 🎯 주요 기능

### 완성된 기능들
- ✅ **다국어 지원**: 한국어/영어 완전 번역
- ✅ **컴포넌트 시스템**: Header, Sidebar, Dashboard 레이아웃
- ✅ **API 클라이언트**: Axios 기반 타입 안전한 API 호출
- ✅ **데이터베이스**: MySQL 스키마 + 테스트 데이터
- ✅ **AI 서비스**: FastAPI 게이트웨이 + 모델 서비스들
- ✅ **Container**: Docker Compose 전체 스택

### API 엔드포인트
#### Spring Boot REST API
- `GET /api/v1/declarations` - 신고서 목록
- `POST /api/v1/declarations` - 신고서 생성
- `GET /api/v1/declarations/{id}` - 신고서 조회
- `PUT /api/v1/declarations/{id}` - 신고서 수정
- `DELETE /api/v1/declarations/{id}` - 신고서 삭제

#### FastAPI AI Gateway
- `POST /ai/classify-document` - 문서 분류
- `POST /ai/extract-text` - OCR 텍스트 추출
- `POST /ai/assess-risk` - 리스크 평가

## 🧪 테스트

### 테스트 실행
```bash
# Frontend 테스트
cd presentation-tier/frontend
npm run test

# Backend 테스트
cd presentation-tier/backend
./mvnw test

# AI Gateway 테스트
cd application-tier/ai-gateway
pytest
```

## 🔧 개발 시 주의사항

### 코딩 스타일
- **Frontend**: ESLint + Prettier 설정 준수
- **Backend**: Google Java Style Guide
- **Python**: PEP 8 + Black formatter
- **Database**: 표준 SQL 컨벤션 + snake_case

### 파일 수정 가이드
1. **Frontend 컴포넌트**: `src/components/` 하위에 기능별 분류
2. **API 엔드포인트**: Spring Boot Controller에 추가 후 OpenAPI 문서 확인
3. **데이터베이스**: Flyway 마이그레이션 파일로 스키마 변경
4. **AI 모델**: FastAPI 라우터에 새 엔드포인트 추가

### 환경 변수
- **Backend**: `application.yml`에서 `${ENV_VAR:default}` 형식 사용
- **Frontend**: `.env.local` 파일 생성 (`.env.example` 참고)
- **AI Gateway**: `.env` 파일 사용 (python-dotenv)

## 📝 Git Commit Convention

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Scopes**: `frontend`, `backend`, `ai`, `db`, `infra`, `docs`

**Examples**:
```bash
feat(frontend): add declaration list component
fix(backend): resolve null pointer in declaration service
docs(readme): update installation guide
chore(deps): update spring boot to 3.2.2
```

## 🚨 중요 참고사항

### 데이터베이스
- MySQL charset은 `utf8mb4`로 설정 (한글 지원)
- 테이블명, 컬럼명은 snake_case 사용
- 모든 테이블에 `created_at`, `updated_at` 컬럼 포함
- Foreign Key 제약조건 활용

### 보안
- JWT 토큰 기반 인증 준비됨 (`application.yml`에 설정)
- 민감 정보는 환경변수로 관리
- CORS 설정 확인 필요 (프론트엔드 연동 시)

### 성능
- React Query로 데이터 캐싱 활용
- Spring Boot Actuator로 메트릭 모니터링
- FastAPI async/await 패턴 활용
- MySQL 인덱스 최적화 고려

이 가이드를 통해 Claude Code가 프로젝트의 현재 상태를 정확히 이해하고 효율적으로 작업할 수 있습니다.
