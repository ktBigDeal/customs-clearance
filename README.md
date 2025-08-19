# 🏛️ 기업형 통관 시스템 (Customs Clearance System)

> **AI 기반 통합 통관 플랫폼** - 수출입 신고서 처리, RAG 챗봇, OCR, 보고서 생성, US 대한민국 관세율 변환을 통합한 차세대 전자통관시스템

[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2.1-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-purple.svg)](https://www.trychroma.com/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-orange.svg)](https://langchain.com/)

## 📋 목차 

- [🎯 프로젝트 개요](#🎯-프로젝트-개요)
- [🏗️ 시스템 아키텍처](#🏗️-시스템-아키텍처)
- [🚀 빠른 시작](#🚀-빠른-시작)
- [📁 프로젝트 구조](#📁-프로젝트-구조)
- [🔧 개발 환경 설정](#🔧-개발-환경-설정)
- [📚 API 문서](#📚-api-문서)
- [🧪 테스트](#🧪-테스트)
- [🚀 배포](#🚀-배포)
- [🤝 기여하기](#🤝-기여하기)

---

## 🎯 프로젝트 개요

**통관시스템**은 한국관세청의 수출입 신고서 처리를 위한 현대적이고 효율적인 전자통관 플랫폼입니다.

### ✨ 주요 기능

#### 🤖 **AI 통합 서비스**
- **RAG 기반 전문 챗봇**: 관세법, 무역규제, 상담사례 전문 AI 에이전트
- **LangGraph 오케스트레이션**: 멀티 에이전트 지능형 라우팅 시스템
- **실시간 진행상황**: Server-Sent Events 기반 실시간 처리 과정 표시
- **마크다운 렌더링**: 구조화된 AI 응답으로 향상된 사용자 경험
- **지능형 HS코드 추천**: TF-IDF + 시맨틱 임베딩 혼합 검색 알고리즘
- **US 관세율 변환**: 한국↔미국 관세율 실시간 자동 변환

#### 📄 **전자 신고서 시스템**
- **수입/수출 신고서**: 완전한 전자신고서 작성, 제출, 승인 프로세스
- **HS코드 자동검색**: 품목명 기반 HS코드 추천 및 관세율 계산
- **OCR 문서 처리**: 무역서류 자동 텍스트 추출 및 데이터 변환
- **보고서 생성**: AI 기반 통관 현황 보고서 자동 생성
- **US 관세율 변환**: 한국혀 미국등 방횥에 따른 관세율 자동 변환

#### 🏗️ **시스템 인프라**
- **3-Tier 아키텍처**: 확장 가능한 엔터프라이즈급 시스템 구조
- **Docker 컨테이너화**: 완전한 마이크로서비스 환경 구축
- **Vector Database**: ChromaDB 기반 의미 검색 및 RAG 시스템
- **실시간 모니터링**: 시스템 상태 및 성능 실시간 추적
- **AOP 로깅 시스템**: 자동 시스템 로그 수집 및 분석
- **Vercel 배포**: 프로덕션 준비 완료된 배포 환경

### 🎨 기술 스택

**Frontend** | **Backend** | **AI/ML 서비스** | **Database** | **Infrastructure**
---|---|---|---|---
Next.js 14.2 | Spring Boot 3.2.1 | FastAPI 0.104 | MySQL 8.0 | Docker Compose
React 18 | Java 17 | Python 3.11 | PostgreSQL 5433 | ChromaDB 8011
TypeScript | Spring Data JPA | LangChain | Redis 6380 | uv Package Manager
Tailwind CSS | AOP Logging | LangGraph | Vector Store | Vercel Deploy
SSE & Markdown | JWT Authentication | OpenAI GPT-4.1-mini | phpMyAdmin + pgAdmin | System Monitoring

#### 🧠 **AI/ML 모델 아키텍처**

**모델 서비스** | **포트** | **기능** | **기술 스택**
---|---|---|---
**AI Gateway** | 8000 | 통합 API 게이트웨이 | FastAPI, 서비스 오케스트레이션
**Model-OCR** | 8001 | 문서 OCR 처리 | Azure Form Recognizer
**Model-Report** | 8002 | 보고서 생성 | 템플릿 기반 자동화
**Model-HSCode** | 8003 | HS코드 검색 추천 | TF-IDF, 시맨틱 임베딩, 캐시
**Model-Chatbot-FastAPI** | 8004 | RAG 기반 법률 챗봇 | LangGraph, ChromaDB, GPT-4.1-mini
**Model-US-Converter** | 8006 | 미국 관세율 변환 | HS코드 변환 및 매핑

---

## 🏗️ 시스템 아키텍처

```mermaid
graph TB
    subgraph "🎨 Presentation Tier"
        A["🌐 Next.js Frontend<br/>:3000<br/>관리자 패널 포함"] --> B["☕ Spring Boot Backend<br/>:8080<br/>REST API + JWT Auth"]
    end
    
    subgraph "🧠 Application Tier - AI Services"
        B --> C["🚪 AI Gateway<br/>:8000<br/>통합 API 게이트웨이"]
        C --> D["🤖 RAG Chatbot<br/>:8004<br/>LangGraph + GPT-4.1-mini"]
        C --> E["📄 OCR Service<br/>:8001<br/>Azure Form Recognizer"]
        C --> F["📊 Report Generator<br/>:8002<br/>템플릿 기반 자동화"]
        C --> G["🔍 HS Code Search<br/>:8003<br/>시맨틱 검색 + TF-IDF"]
        C --> H["🔄 US Tariff Converter<br/>:8006<br/>한국↔미국 관세율 매핑"]
    end
    
    subgraph "💾 Data Tier"
        B --> I["🗄️ MySQL 8.0<br/>:3306<br/>메인 데이터베이스"]
        D --> J["🐘 PostgreSQL<br/>:5433<br/>챗봇 대화 기록"]
        D --> K["🧠 ChromaDB<br/>:8011<br/>벡터 데이터베이스"]
        C --> L["⚡ Redis<br/>:6380<br/>캐시 + 세션"]
        B --> M["📁 File Storage<br/>uploads/<br/>무역서류 파일"]
    end
    
    subgraph "🔧 Management Tools"
        I --> N["🔧 phpMyAdmin<br/>:8081<br/>MySQL 관리"]
        J --> O["🐘 pgAdmin<br/>:5050<br/>PostgreSQL 관리"]
    end
    
    subgraph "☁️ Infrastructure"
        P["🌐 Vercel Deploy<br/>Frontend"] --> A
        Q["📊 AOP Logging<br/>SystemLogAspect"] --> B
        R["🐳 Docker Compose<br/>Data Services"] --> I
        R --> J
        R --> K
        R --> L
    end
```

### 🔄 3-Tier 아키텍처

1. **🎨 Presentation Tier**: 사용자 인터페이스 및 API 게이트웨이
2. **🧠 Application Tier**: AI/ML 서비스 및 비즈니스 로직
3. **💾 Data Tier**: 데이터 저장소 및 캐시

---

## 🚀 빠른 시작

### 📋 **사전 요구사항**

```bash
# 필수 도구 설치
- Docker & Docker Compose 20.10+
- Java 17+ (Spring Boot용)
- Node.js 18.17+ (Next.js용)  
- Python 3.11+ (AI 서비스용)
- uv (Python 패키지 매니저)

# uv 설치 (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# uv 설치 (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 🚀 **단계별 실행 가이드**

#### **1단계: Data Tier 실행** (필수 먼저)

```bash
# ChromaDB, MySQL, PostgreSQL, Redis 동시 실행
cd data-tier
docker-compose up -d

# 연결 확인
python scripts/test-connection.py
# ChromaDB: http://localhost:8011
# MySQL: http://localhost:8081 (phpMyAdmin)
# PostgreSQL: localhost:5433
```

#### **2단계: AI 모델 서비스들 실행** 

```bash
# 🤖 RAG 챗봇 (핵심 서비스)
cd application-tier/models/model-chatbot-fastapi
uv sync  # 의존성 자동 설치
uv run uvicorn main:app --reload --port 8004 &

# 🔍 OCR 처리 서비스
cd ../model-ocr
uv sync
uv run uvicorn main:app --reload --port 8001 &

# 📊 보고서 생성 서비스  
cd ../model-report
uv sync
uv run uvicorn main:app --reload --port 8002 &

# 🔍 HS코드 검색 서비스
cd ../model-hscode  
uv sync
uv run uvicorn run_server:app --reload --port 8003 &

# 🔄 US 관세율 변환 서비스
cd ../model-hscode  # US 변환은 hscode 모듈 내에 포함
uv run python src/us_main.py --port 8006 &
```

#### **3단계: AI Gateway 실행**

```bash
# 🚪 통합 AI Gateway
cd application-tier/ai-gateway
uv sync
uv run uvicorn main:app --reload --port 8000 &
```

#### **4단계: Presentation Tier 실행**

```bash
# 🌐 Spring Boot Backend
cd presentation-tier/backend
./mvnw spring-boot:run &

# 💻 Next.js Frontend  
cd ../frontend
npm install
npm run dev
```

### ✅ **서비스 상태 확인**

```bash
# 모든 서비스 Health Check
curl http://localhost:3000             # Frontend
curl http://localhost:8080/actuator/health    # Backend
curl http://localhost:8000/health      # AI Gateway
curl http://localhost:8001/health      # OCR Service
curl http://localhost:8002/health      # Report Service  
curl http://localhost:8003/health      # HS Code Service
curl http://localhost:8004/health      # RAG Chatbot
curl http://localhost:8006/health      # US Converter Service
```

### 🌐 서비스 접속

#### **사용자 인터페이스**
| 서비스 | URL | 설명 |
|--------|-----|------|
| **메인 웹 포털** | <http://localhost:3000> | Next.js 프론트엔드 (관리자 패널 포함) |
| **Spring Boot API** | <http://localhost:8080/swagger-ui> | 백엔드 API 문서 |
| **phpMyAdmin** | <http://localhost:8081> | MySQL 웹 관리도구 |
| **pgAdmin** | <http://localhost:5050> | PostgreSQL 웹 관리도구 |

#### **AI 서비스 API**
| AI 모델 | URL | 포트 | 기능 |
|---------|-----|------|---------|
| **AI Gateway** | <http://localhost:8000/docs> | 8000 | 통합 AI API 게이트웨이 |
| **OCR 처리** | <http://localhost:8001/docs> | 8001 | 문서 텍스트 추출 |
| **보고서 생성** | <http://localhost:8002/docs> | 8002 | 자동 보고서 작성 |
| **HS코드 검색** | <http://localhost:8003/docs> | 8003 | 품목 분류 및 관세율 조회 |
| **RAG 챗봇** | <http://localhost:8004/docs> | 8004 | 법률 상담 챗봇 (LangGraph) |
| **US 관세율 변환** | <http://localhost:8006/docs> | 8006 | 미국 관세율 변환 서비스 |

#### **데이터베이스**
| 데이터베이스 | URL | 포트 | 용도 |
|-------------|-----|------|---------|
| **MySQL** | localhost:3306 | 3306 | 메인 데이터베이스 |
| **PostgreSQL** | localhost:5433 | 5433 | 챗봇 대화 기록 |
| **ChromaDB** | localhost:8011 | 8011 | 벡터 데이터베이스 |
| **Redis** | localhost:6380 | 6380 | 캐시 서버 |

---

## 📁 프로젝트 구조

```
customs-clearance/
├── 📄 README.md                     # 프로젝트 메인 문서 (📍 현재 업데이트)
├── 🔧 CLAUDE.md                     # Claude Code 개발 가이드
├── 🔍 CLAUDE_BACKEND_ANALYSIS.md    # 백엔드 시스템 분석 문서
│
├── 🎨 presentation-tier/            # 🎯 Presentation Layer
│   ├── 🌐 backend/                  # Spring Boot 3.2.1 API 서버
│   │   ├── 📦 src/main/java/com/customs/clearance/
│   │   │   ├── 🎮 controller/       # REST 컨트롤러 (Auth, Declaration, Health, Admin)
│   │   │   ├── 📊 dto/              # 요청/응답 DTO 객체들
│   │   │   └── ⚙️ config/           # Spring 설정 (Security, Database, Swagger)
│   │   ├── 📋 src/main/resources/
│   │   │   ├── application.yml      # Spring Boot 설정
│   │   │   └── db/migration/        # Flyway 마이그레이션 (V1~V5)
│   │   ├── 🗂️ uploads/              # 업로드된 무역서류 파일들
│   │   ├── 📝 DEPENDENCIES.md       # 의존성 관리 가이드
│   │   └── 📜 pom.xml               # Maven 설정 및 의존성
│   │
│   ├── 💻 frontend/                 # Next.js 14.2 메인 웹 애플리케이션
│   │   ├── 📱 src/app/              # App Router 구조
│   │   │   ├── (auth)/login/        # 로그인 페이지
│   │   │   ├── (dashboard)/         # 메인 대시보드
│   │   │   │   ├── chat/            # 🤖 AI 챗봇 페이지 (SSE, 마크다운 지원)
│   │   │   │   ├── hscode/          # HS코드 추천 페이지
│   │   │   │   ├── report/          # 보고서 생성 페이지
│   │   │   │   └── admin/           # 관리자 패널
│   │   │   └── layout.tsx           # 루트 레이아웃
│   │   ├── 🧩 src/components/       # React 컴포넌트들
│   │   │   ├── chat/                # 💬 채팅 관련 컴포넌트
│   │   │   │   ├── ProgressIndicator.tsx    # 실시간 진행상황 (SSE)
│   │   │   │   └── MarkdownRenderer.tsx     # 마크다운 렌더링
│   │   │   ├── layout/              # 헤더, 사이드바, 네비게이션
│   │   │   ├── admin/               # 관리자 전용 컴포넌트
│   │   │   └── ui/                  # 기본 UI 컴포넌트 라이브러리
│   │   ├── 🛠️ src/lib/              # API 클라이언트 및 유틸리티
│   │   ├── 📦 package.json          # 프론트엔드 의존성
│   │   └── ⚙️ next.config.js        # Next.js 설정
│   │
│   └── 📝 frontend-draft/           # UI/UX 디자인 초안 (참고용)
│       └── app/import-declaration/  # 수입신고서 폼 프로토타입
│
├── 🤖 application-tier/             # 🚀 Application Layer (AI/ML)
│   ├── 🚪 ai-gateway/               # FastAPI 통합 AI 게이트웨이
│   │   ├── 📱 app/routers/
│   │   │   ├── ai_gateway.py        # AI 서비스 통합 API
│   │   │   ├── chatbot_integration.py   # 챗봇 API 통합
│   │   │   ├── hs_code_integration.py   # HS코드 서비스 연동
│   │   │   ├── ocr_integration.py   # OCR 서비스 연동
│   │   │   └── report_integration.py    # 보고서 서비스 연동
│   │   ├── 📜 pyproject.toml         # uv 패키지 관리
│   │   └── 🔒 uv.lock               # 의존성 잠금 파일
│   │
│   ├── 📋 CURL_TEST_GUIDE.md        # API 테스트 가이드
│   │
│   └── 🧠 models/                   # 🎯 전문 AI 모델 서비스들
│       ├── 🤖 model-chatbot-fastapi/    # ⭐ RAG 기반 법률 챗봇 (주요 서비스)
│       │   ├── 📱 app/
│       │   │   ├── core/langgraph_integration.py    # LangGraph 오케스트레이션
│       │   │   ├── rag/             # 전문 에이전트들
│       │   │   │   ├── law_agent.py         # 관세법 전문 에이전트
│       │   │   │   ├── trade_regulation_agent.py    # 무역규제 에이전트
│       │   │   │   ├── consultation_case_agent.py   # 상담사례 에이전트
│       │   │   │   └── query_router.py      # 지능형 쿼리 라우터
│       │   │   ├── routers/
│       │   │   │   ├── conversations.py     # 대화 관리 API
│       │   │   │   └── progress.py          # 💡 실시간 진행상황 (SSE)
│       │   │   └── utils/config.py   # ChromaDB, LangGraph 설정
│       │   ├── 🧪 tests/            # 종합 테스트 시스템
│       │   ├── 📜 pyproject.toml     # uv 패키지 관리
│       │   └── 🔒 uv.lock           # 의존성 잠금 파일
│       │
│       ├── 🔤 model-chatbot/        # 기존 CLI 기반 챗봇 (개발/테스트용)
│       │   ├── 📚 src/rag/          # RAG 시스템 코어
│       │   ├── 📋 README.md         # 상세 사용법
│       │   └── 📜 requirements.txt  # pip 기반 의존성
│       │
│       ├── 🔍 model-hscode/         # HS코드 검색 및 추천 서비스
│       │   ├── 📱 app/api/v1/endpoints/
│       │   │   ├── search.py        # HS코드 검색 API
│       │   │   ├── recommend.py     # 품목 추천 API
│       │   │   └── cache.py         # 캐시 관리 API
│       │   ├── 📊 cache/hs_code_cache/  # 시맨틱 임베딩 캐시
│       │   ├── 📈 data/             # 관세청 공식 데이터
│       │   │   ├── 관세청_HS부호_2025.csv
│       │   │   └── 관세청_표준품명_20250101.xlsx
│       │   ├── 🛠️ src/              # 검색 엔진 및 추천 알고리즘
│       │   ├── 📋 API_DOCS.md       # API 문서
│       │   └── 📜 pyproject.toml     # uv 패키지 관리
│       │
│       ├── 📄 model-ocr/            # OCR 문서 처리 서비스
│       │   ├── 📱 app/main.py       # Azure Form Recognizer 연동
│       │   ├── 📜 pyproject.toml     # uv 패키지 관리
│       │   └── 🔒 uv.lock           # 의존성 잠금 파일
│       │
│       ├── 📊 model-report/         # 자동 보고서 생성 서비스
│       │   ├── 📱 app/main.py       # 보고서 템플릿 처리
│       │   ├── 📋 무역통계부호.json   # 통계 코드 매핑
│       │   ├── 📄 수입신고서_전체항목정의(v1).json  # 신고서 스키마
│       │   ├── 📜 pyproject.toml     # uv 패키지 관리
│       │   └── 🔒 uv.lock           # 의존성 잠금 파일
│       │
│       └── 🔄 model-us-converter/   # US 관세율 변환 서비스 (:8006)
│           ├── 📱 src/us_main.py    # 미국 관세율 변환 로직
│           ├── 📊 src/us_ks_hs_converter_service.py  # HS코드 변환 매핑
│           ├── 📜 pyproject.toml     # uv 패키지 관리
│           └── 🔒 uv.lock           # 의존성 잠금 파일
│
└── 💾 data-tier/                    # 🗃️ Data Layer
    ├── 🗃️ chromadb/                # ChromaDB Vector Database
    │   ├── 📊 data/chroma_db/       # 벡터 데이터 저장소
    │   │   ├── chroma.sqlite3       # 메타데이터 DB
    │   │   └── [collection-ids]/    # 임베딩 벡터 컬렉션들
    │   ├── 🛠️ scripts/
    │   │   ├── backup-chromadb.sh   # 백업 스크립트
    │   │   └── test-connection.py   # 연결 테스트
    │   └── 📋 README.md             # ChromaDB 설정 가이드
    │
    ├── 🗄️ chatbot/                 # 챗봇 전용 데이터베이스
    │   ├── postgres/init/           # PostgreSQL 초기화
    │   └── redis/config/            # Redis 캐시 설정
    │
    ├── 🏗️ mysql/                   # MySQL 메인 데이터베이스
    │   ├── config/my.cnf            # MySQL 설정 (UTF8MB4)
    │   └── init/                    # 초기 스키마 및 데이터
    │       ├── 01-init-databases.sql
    │       ├── 01-schema.sql
    │       └── 02-seed-data.sql
    │
    ├── 🔧 scripts/                  # 데이터 관리 스크립트
    │   ├── backup.sh                # 전체 백업
    │   ├── test-connection.py       # DB 연결 테스트
    │   └── setup-database.sh        # DB 초기 설정
    │
    └── 🐳 docker-compose.yml        # 통합 데이터 스택 오케스트레이션
```

---

## 🔧 개발 환경 설정

### 📦 **uv 패키지 매니저 개요**

Application Tier의 모든 Python 서비스는 **uv**를 사용하여 의존성 관리 및 가상환경을 구성합니다.

- **uv**: 빠른 Python 패키지 매니저 및 프로젝트 관리자
- **장점**: pip보다 10-100배 빠른 의존성 해결, 자동 가상환경 관리
- **설치**: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Linux/macOS) 또는 `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)

### 🏗️ **각 서비스별 개발 환경 설정**

#### **1. AI Gateway (메인 게이트웨이)**

```bash
cd application-tier/ai-gateway

# 가상환경 자동 생성 및 의존성 설치
uv sync

# 가상환경 활성화 (Windows)
source .venv/Scripts/activate

# 가상환경 활성화 (Linux/macOS)
source .venv/bin/activate

# 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 가상환경 내에서 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### **2. Model-Chatbot-FastAPI (⭐ RAG 챗봇)**

**신규 서비스**: FastAPI 기반 비동기 RAG 챗봇 시스템

```bash
cd application-tier/models/model-chatbot-fastapi

# 가상환경 자동 생성 및 의존성 설치
uv sync

# 가상환경 활성화 (Windows)
source .venv/Scripts/activate

# 가상환경 활성화 (Linux/macOS)
source .venv/bin/activate

# FastAPI 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8004

# 또는 가상환경 내에서 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8004

# 기본 기능 테스트 실행
uv run python tests/test_basic.py

# 통합 테스트 실행
uv run python tests/test_integration.py
```

**✨ 특징**:
- **비동기 처리**: FastAPI 기반 완전 비동기 아키텍처
- **LangGraph 통합**: 기존 model-chatbot의 LangGraph 시스템과 100% 호환
- **멀티 에이전트**: 법률, 무역규제, 상담사례 전문 에이전트
- **실시간 API**: RESTful API를 통한 실시간 대화 서비스
- **모델 최적화**: `gpt-4.1-mini`로 표준화된 최신 AI 모델 사용

#### **3. Model-HSCode (HS코드 검색)**

```bash
cd application-tier/models/model-hscode

# 가상환경 자동 생성 및 의존성 설치
uv sync

# 가상환경 활성화 (Windows)
source .venv/Scripts/activate

# 가상환경 활성화 (Linux/macOS)
source .venv/bin/activate

# 서버 실행
uv run uvicorn run_server:app --reload --host 0.0.0.0 --port 8003

# 또는 가상환경 내에서 직접 실행
uvicorn run_server:app --reload --host 0.0.0.0 --port 8003
```

#### **4. Model-OCR (OCR 처리 서비스)**

```bash
cd application-tier/models/model-ocr

# 가상환경 자동 생성 및 의존성 설치
uv sync

# 가상환경 활성화 (Windows)
source .venv/Scripts/activate

# 가상환경 활성화 (Linux/macOS)
source .venv/bin/activate

# FastAPI 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 또는 가상환경 내에서 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

#### **5. Model-Report (보고서 생성 서비스)**

```bash
cd application-tier/models/model-report

# 가상환경 자동 생성 및 의존성 설치
uv sync

# 가상환경 활성화 (Windows)
source .venv/Scripts/activate

# 가상환경 활성화 (Linux/macOS)
source .venv/bin/activate

# FastAPI 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 또는 가상환경 내에서 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

#### **6. Model-US-Converter (미국 관세율 변환)**

```bash
cd application-tier/models/model-hscode  # US 변환은 hscode 모듈 내에 포함

# 가상환경 자동 생성 및 의존성 설치
uv sync

# US 변환 서버 실행
uv run python src/us_main.py --port 8006
```

#### **7. Spring Boot Backend**

```bash
cd presentation-tier/backend

# Maven을 사용한 실행
./mvnw spring-boot:run

# 테스트 실행
./mvnw test

# 패키징
./mvnw clean package
```

#### **8. Next.js Frontend**

```bash
cd presentation-tier/frontend

# 의존성 설치
npm install

# 개발 서버 실행  
npm run dev

# 타입 체크
npm run type-check

# 린팅
npm run lint

# 빌드
npm run build
```

#### **9. Data Tier (데이터베이스)**

```bash
cd data-tier

# 전체 데이터베이스 스택 실행
docker-compose up -d

# 연결 테스트
python scripts/test-connection.py

# 개별 서비스 접속
# MySQL: http://localhost:8081 (phpMyAdmin)
# PostgreSQL: http://localhost:5050 (pgAdmin)
# ChromaDB: http://localhost:8011
```

### 🔧 **개발 시 주의사항**

#### uv 명령어 치트시트

```bash
# 프로젝트 초기화
uv init

# 의존성 설치 및 가상환경 동기화
uv sync

# 새 패키지 추가
uv add fastapi uvicorn

# 개발 의존성 추가
uv add --dev pytest black

# 패키지 제거
uv remove package-name

# 가상환경에서 Python 실행
uv run python script.py

# 가상환경에서 명령어 실행
uv run uvicorn main:app --reload
```

#### 환경변수 설정

각 서비스별로 `.env` 파일이 필요할 수 있습니다:

**AI Gateway** (`.env`):
```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=mysql://user:password@localhost:3306/customs_db
```

**Model-OCR** (`api_key.env`):
```env
AZURE_FORM_RECOGNIZER_ENDPOINT=your_azure_endpoint
AZURE_FORM_RECOGNIZER_KEY=your_azure_key
```

#### 테스트 실행

```bash
# 각 서비스 디렉토리에서
uv run pytest

# 또는 가상환경 내에서
pytest
```

---

## 📚 API 문서

### 🌐 **Spring Boot Backend API (포트 8080)**

#### 📄 신고서 (Declarations) API

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/api/declarations` | 신고서 목록 조회 |
| `POST` | `/api/declarations` | 새 신고서 생성 |
| `GET` | `/api/declarations/{id}` | 특정 신고서 조회 |
| `PUT` | `/api/declarations/{id}` | 신고서 수정 |
| `DELETE` | `/api/declarations/{id}` | 신고서 삭제 |
| `POST` | `/api/declarations/{id}/submit` | 신고서 제출 |

#### 🔐 인증 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/auth/login` | 사용자 로그인 |
| `POST` | `/api/auth/logout` | 사용자 로그아웃 |
| `GET` | `/api/auth/me` | 현재 사용자 정보 |

#### 👨‍💼 관리자 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| `GET` | `/api/admin/users` | 사용자 목록 조회 |
| `GET` | `/api/admin/logs` | 시스템 로그 조회 |
| `GET` | `/api/admin/stats` | 시스템 통계 |

### 🤖 **AI Gateway API (포트 8000)**

#### 🚪 통합 AI 서비스 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/chatbot/chat` | RAG 챗봇 대화 |
| `GET` | `/api/v1/chatbot/conversations/user/{user_id}` | 대화 목록 조회 |
| `GET` | `/api/v1/chatbot/conversations/{id}/messages` | 대화 메시지 조회 |
| `POST` | `/api/v1/hscode/search` | HS코드 검색 |
| `POST` | `/api/v1/hscode/recommend` | 품목 추천 |
| `POST` | `/api/v1/ocr/extract` | OCR 텍스트 추출 |
| `POST` | `/api/v1/report/generate` | 보고서 생성 |
| `POST` | `/api/v1/us-converter/convert` | US 관세율 변환 |

### 🔍 **개별 AI 서비스 API**

#### **RAG 챗봇 API (포트 8004)**

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/conversations/chat` | 새로운 대화 시작 |
| `GET` | `/api/v1/conversations/user/{user_id}` | 사용자별 대화 목록 |
| `GET` | `/api/v1/conversations/{id}/messages` | 대화 메시지 조회 |
| `GET` | `/api/v1/progress/stream/{conversation_id}` | 실시간 진행상황 (SSE) |
| `GET` | `/health` | 서비스 상태 확인 |

#### **OCR 처리 API (포트 8001)**

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/extract-text` | 문서 텍스트 추출 |
| `POST` | `/extract-form-data` | 폼 데이터 추출 |
| `GET` | `/health` | 서비스 상태 확인 |

#### **보고서 생성 API (포트 8002)**

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/generate-report` | 보고서 생성 |
| `GET` | `/templates` | 보고서 템플릿 목록 |
| `GET` | `/health` | 서비스 상태 확인 |

#### **HS코드 검색 API (포트 8003)**

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/v1/search` | HS코드 검색 |
| `POST` | `/api/v1/recommend` | 품목 추천 |
| `GET` | `/api/v1/cache/warm-up` | 캐시 워밍업 |
| `GET` | `/health` | 서비스 상태 확인 |

#### **US 관세율 변환 API (포트 8006)**

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/convert-hs-code` | HS코드 변환 |
| `GET` | `/get-us-tariff-rate` | 미국 관세율 조회 |
| `GET` | `/health` | 서비스 상태 확인 |

### 📖 **API 문서 접속**

#### **메인 API 문서**
- **Spring Boot API**: <http://localhost:8080/swagger-ui/index.html>
- **AI Gateway**: <http://localhost:8000/docs> | <http://localhost:8000/redoc>

#### **개별 AI 서비스 문서**
- **RAG 챗봇**: <http://localhost:8004/docs> | <http://localhost:8004/redoc>
- **OCR 처리**: <http://localhost:8001/docs>
- **보고서 생성**: <http://localhost:8002/docs>
- **HS코드 검색**: <http://localhost:8003/docs>
- **US 관세율 변환**: <http://localhost:8006/docs>

### 📋 **API 테스트 가이드**

상세한 API 테스트 방법은 [`application-tier/CURL_TEST_GUIDE.md`](./application-tier/CURL_TEST_GUIDE.md) 문서를 참고하세요.

---

## 🧪 테스트 시스템

### 🔬 **AI 서비스 테스트**

```bash
# 🤖 RAG 챗봇 테스트 (핵심 기능)
cd application-tier/models/model-chatbot-fastapi

# 기본 기능 테스트
uv run python tests/test_basic.py

# 통합 테스트 (ChromaDB, LangGraph 연동)
uv run python tests/test_integration.py

# 데이터베이스 테스트 
uv run python tests/test_database.py
```

### 🔍 **개별 모델 테스트**

```bash
# HS코드 검색 정확도 테스트
cd application-tier/models/model-hscode
uv run python -m pytest tests/

# OCR 처리 성능 테스트  
cd application-tier/models/model-ocr
uv run python tests/test_ocr_accuracy.py

# 보고서 생성 테스트
cd application-tier/models/model-report
uv run python tests/test_report_generation.py
```

### 🌐 **시스템 통합 테스트**

```bash
# Backend 테스트 (JUnit + MockMvc)
cd presentation-tier/backend  
./mvnw test

# Frontend 테스트 (Jest + React Testing Library)
cd presentation-tier/frontend
npm run test
npm run test:coverage

# AI Gateway 통합 테스트
cd application-tier/ai-gateway
uv run pytest tests/ -v
```

### 📊 **실시간 기능 테스트**

```bash
# SSE (Server-Sent Events) 연결 테스트
curl -N http://localhost:8004/api/v1/progress/stream/test_conv_001

# 채팅 API 전체 플로우 테스트
curl -X POST http://localhost:8000/api/v1/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "message": "딸기 수입할 때 주의사항은?"}'
```

### 🔧 **데이터베이스 연결 테스트**

```bash
# 전체 데이터베이스 연결 상태 확인
cd data-tier
python scripts/test-connection.py

# ChromaDB 벡터 검색 테스트
python scripts/test-chromadb.sh
```

---

## 🚀 배포 및 운영

### 🐳 **Docker 컨테이너 배포**

```bash
# 📊 Data Tier 우선 실행
cd data-tier
docker-compose up -d

# 🤖 AI 서비스들 개별 컨테이너 실행 (선택사항)
# 각 model-*/Dockerfile 사용

# 🌐 Presentation Tier 컨테이너 실행
cd presentation-tier/backend
docker build -t customs-backend .
docker run -p 8080:8080 customs-backend

cd ../frontend  
docker build -t customs-frontend .
docker run -p 3000:3000 customs-frontend
```

### 📊 **모니터링 및 로그**

```bash
# 각 서비스 로그 실시간 확인
docker-compose logs -f mysql chromadb  # Data Tier
tail -f presentation-tier/backend/logs/customs-clearance-backend.log  # Backend

# AI 서비스 상태 모니터링
watch "curl -s http://localhost:8000/health && echo && curl -s http://localhost:8004/health"

# ChromaDB 벡터 데이터 상태 확인
ls -la data-tier/chromadb/data/chroma_db/
```

### ⚡ **성능 최적화**

```bash
# AI 모델 캐시 워밍업
curl http://localhost:8003/api/v1/cache/warm-up  # HS코드 캐시

# ChromaDB 인덱스 최적화
cd data-tier/chromadb
python scripts/optimize-vectors.py

# Backend JVM 튜닝
export JAVA_OPTS="-Xms2g -Xmx4g -XX:+UseG1GC"
./mvnw spring-boot:run
```

---

## 🤝 기여하기

### 🔄 **개발 워크플로우**

1. **Fork** 저장소를 포크합니다
2. **Branch** 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. **Commit** 변경사항을 커밋합니다 (`git commit -m 'feat: add amazing feature'`)
4. **Push** 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. **Pull Request** 를 생성합니다

### 📝 **커밋 컨벤션**

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:

```bash
feat(auth): add JWT authentication
fix(api): resolve declaration status update bug
docs: update API documentation
style(frontend): improve button component styling
```

### 🧑‍💻 **코딩 스타일**

- **Frontend**: ESLint + Prettier
- **Backend**: Google Java Style Guide  
- **Python**: PEP 8 + Black formatter
- **Database**: 표준 SQL 컨벤션

---

## 📞 지원 및 문의

- **📱 이슈 트래킹**: [GitHub Issues](https://github.com/your-org/customs-clearance/issues)
  
---


## 🙏 감사의 글

- Aivle-18조 팀의 지원과 협력

---

<p align="center">
  <b>🏛️ Made with ❤️ for Customs Service</b>
</p>
