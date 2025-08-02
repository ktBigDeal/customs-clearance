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
    ├── model-ocr/            # Azure Document Intelligence 기반 OCR 서비스
    ├── model-report/         # LangChain 기반 관세신고서 생성 서비스
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

#### 5. OCR 모델 서비스 실행 (선택적)
```bash
cd application-tier/models/model-ocr/app
pip install -r ../ocr_requirements.txt
uvicorn ocr_api:app --reload --port 8001
```

#### 6. 신고서 생성 모델 서비스 실행 (선택적)
```bash
cd application-tier/models/model-report
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### 🌐 서비스 URL
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/api/v1
- **Swagger UI**: http://localhost:8080/swagger-ui.html
- **AI Gateway**: http://localhost:8000
- **AI Docs**: http://localhost:8000/docs
- **OCR Service**: http://localhost:8001 (Azure Document Intelligence)
- **Report Service**: http://localhost:8002 (LangChain 신고서 생성)
- **phpMyAdmin**: http://localhost:8081

## 🎯 주요 기능

### 완성된 기능들
- ✅ **다국어 지원**: 한국어/영어 완전 번역
- ✅ **컴포넌트 시스템**: Header, Sidebar, Dashboard 레이아웃
- ✅ **API 클라이언트**: Axios 기반 타입 안전한 API 호출
- ✅ **데이터베이스**: MySQL 스키마 + 테스트 데이터
- ✅ **AI 서비스**: FastAPI 게이트웨이 + 모델 서비스들
- ✅ **OCR 처리**: Azure Document Intelligence 통합 OCR 서비스
- ✅ **신고서 생성**: LangChain 기반 자동 신고서 생성 모델
- ✅ **Spring-FastAPI 연동**: OCR 테스트 컨트롤러 구현
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

#### OCR 서비스 (model-ocr)
- `POST /ocr/` - Azure Document Intelligence 기반 다중 문서 OCR 처리
  - invoice_file, packing_list_file, bill_of_lading_file 동시 처리
  - 통합된 JSON 결과 반환

#### 신고서 생성 서비스 (model-report)
- LangChain + OpenAI 기반 관세신고서 자동 생성
- 수입/수출 신고서 전체 항목 정의 기반 구조화된 처리

#### Spring Boot 테스트 API
- `POST /test-ocr/call-ocr` - Spring Boot에서 FastAPI OCR 서비스 호출 테스트

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

## 📈 최근 업데이트 (2025-08-01)

### 🆕 새로 추가된 AI 모델 서비스들

#### 1. **model-ocr** - Azure Document Intelligence OCR 서비스
- **기능**: 무역 관련 문서 3종 동시 OCR 처리
- **지원 문서**: Invoice, Packing List, Bill of Lading
- **기술 스택**: FastAPI + Azure Document Intelligence
- **출력**: 통합된 JSON 형태 구조화 데이터
- **API**: `POST /ocr/` (포트 8001)

#### 2. **model-report** - LangChain 기반 신고서 생성 서비스
- **기능**: OCR 결과 기반 관세신고서 자동 생성
- **기술 스택**: FastAPI + LangChain + OpenAI GPT
- **데이터**: 수입/수출 신고서 전체 항목 정의 (v1) 포함
- **API**: 포트 8002 (구현 진행 중)
- **특징**: 한국 관세청 규정 기반 구조화된 처리

#### 3. **Spring Boot 연동 테스트**
- **컨트롤러**: `OcrTestController.java`
- **기능**: Spring Boot에서 FastAPI OCR 서비스 호출
- **API**: `POST /test-ocr/call-ocr`
- **상태**: 터미널 테스트 완료 (Spring 통합 진행 중)

### 🔧 개발 환경 세팅

#### OCR 서비스 환경 설정
```bash
# Azure Document Intelligence 설정 필요
# api_key.env 파일에 다음 정보 추가:
AZURE_ENDPOINT=your_azure_endpoint
AZURE_API_KEY=your_azure_api_key
```

#### LangChain 서비스 환경 설정  
```bash
# OpenAI API 키 설정 필요
# api_key.txt 파일에 다음 정보 추가:
OPENAI_API_KEY=your_openai_api_key
```

### ⚠️ 알려진 이슈
- **LangChain 의존성**: `pydantic==2.5.0` vs `langchain>=0.3.27` 버전 충돌
  - **해결책**: `pydantic>=2.7.4` 업그레이드 필요
- **Spring-FastAPI 연동**: 일부 통신 이슈 해결 중

## 📈 최근 업데이트 (2025-08-02)

### 🔄 AI Gateway 통합 및 코드 개선 작업

#### 1. **AI Gateway 모델 레지스트리 업데이트**
- **파일**: `application-tier/ai-gateway/app/routers/models.py`
- **주요 변경사항**:
  - 인메모리 모델 레지스트리를 실제 OCR/Report 서비스와 연동
  - 불필요한 predict/batch-predict 엔드포인트 완전 제거
  - OCR 전용 엔드포인트 추가: `POST /api/v1/models/model-ocr/analyze-documents`
  - Report 전용 엔드포인트 추가: `POST /api/v1/models/model-report/generate-declaration`
  - 모든 함수에 한국어 docstring 추가
  - httpx 기반 비동기 서비스 간 통신 구현

#### 2. **Pydantic 스키마 전면 개편**
- **파일**: `application-tier/ai-gateway/app/schemas/models.py`
- **주요 변경사항**:
  - 모든 클래스와 메서드에 상세한 한국어 docstring 추가
  - `ModelType`에 `TEXT_GENERATOR` 타입 추가 (신고서 생성용)
  - 기존 predict 관련 스키마 제거: `ModelRequest`, `ModelResponse`, `BatchModelRequest`, `BatchModelResponse`
  - 새로운 OCR 스키마 추가: `OcrAnalyzeRequest`, `OcrAnalyzeResponse`
  - 새로운 Report 스키마 추가: `ReportGenerateRequest`, `ReportGenerateResponse`
  - 각 스키마에 validation 로직과 한국어 에러 메시지 추가
  - 실제 서비스 메타데이터를 반영한 예시 업데이트

#### 3. **model-report 서비스 환경설정 개선**
- **파일**: `application-tier/models/model-report/app/main.py`
- **변경사항**:
  - 기존 `path = Path(__file__)` → `base_path = Path(__file__).parent.parent`로 수정
  - .env 파일 로딩 방식을 `python-dotenv` 패키지 활용으로 변경
  - 파일 경로 처리를 Path 객체의 `/` 연산자로 개선
  - 환경변수 기반 API 키 관리 체계 구축

#### 4. **AI Gateway 설정 파일 개선**
- **파일**: `application-tier/ai-gateway/app/core/config.py`
- **변경사항**:
  - `DEBUG = True`로 기본값 변경 (개발 편의성)
  - 모든 설정 클래스에 한국어 docstring 추가
  - 모델 서비스 URL 설정 체계화

#### 5. **통합 테스트 가이드 완성**
- **파일**: `application-tier/CURL_TEST_GUIDE.md`
- **내용**:
  - AI Gateway, OCR, Report 서비스 통합 테스트 가이드
  - 완전한 워크플로우 테스트 명령어
  - 성능 벤치마크 및 트러블슈팅 가이드
  - 자동화 테스트 스크립트 예시

### 🏗️ 아키텍처 개선 사항

#### **AI Gateway 통합 아키텍처**
```
┌─────────────────────────────────────────┐
│           AI Gateway (Port 8000)        │
│  ┌─────────────────────────────────────┐ │
│  │     Model Registry (In-Memory)     │ │
│  │  ┌─────────────┬─────────────────┐  │ │
│  │  │  model-ocr  │  model-report   │  │ │
│  │  │  (TEXT_     │  (TEXT_         │  │ │
│  │  │  EXTRACTOR) │  GENERATOR)     │  │ │
│  │  └─────────────┴─────────────────┘  │ │
│  └─────────────────────────────────────┘ │
│               │httpx calls│              │
└───────────────┼───────────┼──────────────┘
                │           │
     ┌──────────▼──────────┐ ┌──────▼──────────┐
     │  OCR Service        │ │ Report Service   │
     │  (Port 8001)        │ │ (Port 8002)      │
     │  Azure Document     │ │ LangChain +      │
     │  Intelligence       │ │ OpenAI GPT       │
     └─────────────────────┘ └──────────────────┘
```

#### **API 엔드포인트 매트릭스**
| 기능 | AI Gateway 엔드포인트 | 백엔드 서비스 | 상태 |
|------|---------------------|--------------|------|
| 모델 목록 조회 | `GET /api/v1/models` | In-Memory Registry | ✅ 완료 |
| OCR 문서 분석 | `POST /api/v1/models/model-ocr/analyze-documents` | Port 8001 | ✅ 완료 |
| 신고서 생성 | `POST /api/v1/models/model-report/generate-declaration` | Port 8002 | ✅ 완료 |
| 통합 파이프라인 | `POST /api/v1/pipeline/process-complete-workflow` | Multiple | 🔄 진행중 |

### 🎯 개발자 경험 개선

#### **한국어 문서화**
- 모든 Python 파일에 한국어 docstring 완성
- 각 함수의 매개변수, 반환값, 예외 상황 상세 설명
- 실제 사용 예시와 함께 제공되는 스키마 문서

#### **타입 안전성 강화**
- Pydantic 스키마의 validation 로직 추가
- OCR/Report 요청 데이터 검증 강화
- 한국어 에러 메시지로 디버깅 편의성 향상

#### **프로덕션 준비**
- 데이터베이스 기반 모델 레지스트리 구현 예시 제공
- 환경변수 기반 설정 관리 체계 구축
- Docker 컨테이너 환경에서의 서비스 간 통신 최적화

### 🔧 개발 환경 개선사항

#### **통합 테스트 환경**
```bash
# 모든 서비스 동시 실행 스크립트
./application-tier/run_services.py

# 통합 테스트 실행
cd application-tier && python -m pytest tests/

# CURL 기반 수동 테스트
cd application-tier && bash test_all_services.sh
```

#### **개발 편의성 개선**
- AI Gateway Swagger UI 기본 활성화 (`DEBUG=True`)
- 모든 서비스의 헬스체크 엔드포인트 표준화
- 에러 로깅 및 디버깅 정보 한국어화

### 📋 다음 단계 계획

1. **통합 파이프라인 완성**: OCR → Report 자동 연계 워크플로우
2. **Spring Boot 연동**: AI Gateway와 Spring Boot 백엔드 완전 통합
3. **모니터링 구축**: Prometheus + Grafana 메트릭 수집
4. **프로덕션 배포**: Docker Compose 기반 배포 환경 구성

이 가이드를 통해 Claude Code가 프로젝트의 현재 상태를 정확히 이해하고 효율적으로 작업할 수 있습니다.