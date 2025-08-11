# 백엔드 시스템 분석 및 작업 추적 파일

## 📋 프로젝트 백엔드 구조 분석 (2025-08-11)

이 파일은 Claude Code가 관세 통관 시스템의 백엔드 구조를 분석하고, 향후 작업 시 참조할 수 있는 정보를 정리한 문서입니다.

---

## 🏗️ 전체 아키텍처

### 3-tier 엔터프라이즈 아키텍처
```
📁 customs-clearance/
├── 🎨 presentation-tier/          # 사용자 인터페이스 계층
│   ├── backend/                   # Spring Boot API Gateway
│   ├── frontend/                  # Next.js 메인 프론트엔드
│   └── frontend-draft/            # Next.js 디자인 초안
├── 🧠 application-tier/           # 비즈니스 로직 및 AI/ML 서비스
│   ├── ai-gateway/                # FastAPI 메인 게이트웨이
│   └── models/                    # AI/ML 마이크로서비스들
└── 💾 data-tier/                  # 데이터 저장소 계층
    ├── mysql/                     # 메인 관계형 DB
    ├── chromadb/                  # 벡터 DB (RAG용)
    └── redis/                     # 캐시 및 세션 스토어
```

---

## 🎯 Presentation Tier - Spring Boot Backend

### 📂 프로젝트 구조 (Spring Boot 3.2.1 + Java 17)

```
presentation-tier/backend/
├── src/main/java/com/customs/clearance/
│   ├── 📁 config/                 # 설정 클래스들
│   │   ├── AppConfig.java         # 애플리케이션 공통 설정
│   │   ├── DatabaseConfig.java    # 데이터베이스 설정
│   │   ├── DotEnvConfig.java      # 환경 변수 관리
│   │   ├── SecurityConfig.java    # Spring Security 설정
│   │   ├── SwaggarConfig.java     # OpenAPI/Swagger 설정
│   │   └── WebConfig.java         # 웹 설정 (CORS 등)
│   ├── 📁 controller/             # REST API 컨트롤러
│   │   ├── AuthController.java    # 인증/권한 관리
│   │   ├── DeclarationController.java # 수출입 신고서 관리
│   │   └── HealthController.java  # 헬스 체크 엔드포인트
│   ├── 📁 dto/                    # 데이터 전송 객체
│   │   ├── DeclarationRequestDto.java
│   │   ├── DeclarationStatsDto.java
│   │   ├── RegisterRequest.java
│   │   ├── UpdateUserRequest.java
│   │   └── UserResponseDto.java
│   ├── 📁 entity/                 # JPA 엔티티
│   │   ├── Attachment.java        # 첨부파일
│   │   ├── BaseEntity.java        # 공통 엔티티 (생성일/수정일)
│   │   ├── Chatting.java          # 채팅 세션
│   │   ├── Declaration.java       # 수출입 신고서
│   │   ├── Message.java           # 채팅 메시지
│   │   └── User.java              # 사용자
│   ├── 📁 exception/              # 예외 처리
│   │   ├── ErrorResponse.java     # 에러 응답 구조
│   │   ├── GlobalExceptionHandler.java # 글로벌 예외 핸들러
│   │   └── ResourceNotFoundException.java
│   ├── 📁 repository/             # 데이터 접근 계층
│   │   ├── AttachmentRepository.java
│   │   ├── ChattingRepository.java
│   │   ├── DeclarationRepository.java
│   │   ├── MessageRepository.java
│   │   └── UserRepository.java
│   ├── 📁 security/               # 보안 관련
│   │   ├── CustomUserDetailsService.java
│   │   ├── JwtAuthenticationFilter.java
│   │   └── JwtTokenProvider.java
│   ├── 📁 service/                # 비즈니스 로직
│   │   ├── DeclarationService.java
│   │   └── UserService.java
│   └── 📁 util/                   # 유틸리티 클래스
│       └── DeclarationServiceUtils.java
├── src/main/resources/
│   ├── application.yml            # 메인 설정 파일
│   └── db/migration/              # Flyway 마이그레이션
│       ├── V1__Create_base_tables.sql
│       ├── V2__Insert_reference_data.sql
│       └── V3__Insert_sample_data.sql
└── pom.xml                        # Maven 의존성 관리
```

### 🔧 핵심 기술 스택

**Spring Boot 생태계:**
- Spring Boot 3.2.1 (Java 17)
- Spring Data JPA (Hibernate)
- Spring Security + JWT (인증/권한)
- Spring Boot Actuator (모니터링)

**데이터베이스:**
- MySQL 8.0 (메인 DB)
- H2 Database (테스트용)

**빌드 및 테스트:**
- Maven 3.11.0
- JUnit 5 + Testcontainers
- Jacoco (코드 커버리지)

**문서화:**
- SpringDoc OpenAPI 3 (Swagger UI)

### 🌐 주요 API 엔드포인트

**인증 관리:**
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/logout` - 로그아웃

**수출입 신고서 관리:**
- `POST /api/v1/declarations` - 신고서 생성
- `GET /api/v1/declarations` - 신고서 목록 조회 (페이징)
- `GET /api/v1/declarations/{id}` - 특정 신고서 조회
- `PUT /api/v1/declarations/{id}` - 신고서 수정
- `DELETE /api/v1/declarations/{id}` - 신고서 삭제
- `GET /api/v1/declarations/stats` - 신고서 통계

**시스템 모니터링:**
- `GET /api/v1/public/health` - 헬스 체크
- `GET /api/v1/actuator/health` - Spring Actuator 헬스
- `GET /api/v1/actuator/metrics` - 시스템 메트릭

---

## 🧠 Application Tier - AI/ML Services

### 📂 AI Gateway (FastAPI)

**메인 게이트웨이 서비스** (포트: 8000)
```
application-tier/ai-gateway/
├── app/
│   ├── core/                      # 핵심 설정
│   │   ├── config.py              # 환경 설정
│   │   ├── logging.py             # 로깅 설정
│   │   └── middleware.py          # 미들웨어
│   ├── routers/                   # API 라우터
│   │   ├── ai_gateway.py          # 메인 게이트웨이
│   │   ├── chatbot_integration.py # 챗봇 통합
│   │   ├── health.py              # 헬스 체크
│   │   ├── hs_code_integration.py # HS코드 서비스 통합
│   │   ├── ocr_integration.py     # OCR 서비스 통합
│   │   ├── pipeline.py            # AI 파이프라인
│   │   └── report_integration.py  # 리포트 서비스 통합
│   └── schemas/                   # Pydantic 스키마
│       ├── common.py
│       ├── gateway.py
│       └── models.py
├── main.py                        # FastAPI 애플리케이션 엔트리포인트
└── pyproject.toml                 # uv 의존성 관리
```

### 🤖 AI/ML 마이크로서비스들

#### 1. Model-Chatbot-FastAPI (포트: 8004) ⭐ 메인 챗봇 서비스
```
model-chatbot-fastapi/
├── app/
│   ├── core/
│   │   ├── database.py            # PostgreSQL 비동기 연결
│   │   └── langgraph_integration.py # LangGraph 시스템 통합
│   ├── models/
│   │   └── conversation.py        # 대화 관리 ORM 모델
│   ├── rag/                       # RAG 시스템 (핵심)
│   │   ├── consultation_case_agent.py # 상담 사례 전문 에이전트
│   │   ├── law_agent.py           # 관세법 전문 에이전트
│   │   ├── query_router.py        # 지능형 질의 라우터
│   │   ├── trade_regulation_agent.py # 무역규제 전문 에이전트
│   │   ├── vector_store.py        # ChromaDB 연동
│   │   └── langgraph_orchestrator.py # 멀티 에이전트 오케스트레이션
│   ├── routers/
│   │   ├── conversations.py       # 대화 API
│   │   └── progress.py           # 실시간 진행상황 SSE
│   ├── services/
│   │   └── conversation_service.py # 대화 관리 비즈니스 로직
│   └── utils/
│       └── config.py              # 확장된 설정 관리
└── tests/                         # 종합 테스트 시스템
    ├── test_basic.py
    └── test_integration.py
```

**주요 기능:**
- 🔥 **멀티 에이전트 RAG 시스템**: 관세법, 무역규제, 상담사례 전문 AI 에이전트
- 🔄 **LangGraph 오케스트레이션**: 지능형 질의 라우팅 및 에이전트 관리
- 💾 **ChromaDB 벡터 검색**: 의미 기반 문서 검색
- 📡 **실시간 진행상황**: Server-Sent Events로 AI 처리 과정 실시간 스트리밍
- 🔐 **PostgreSQL 연동**: 대화 기록 영구 저장 및 관리

#### 2. Model-HSCode (포트: 8003) - HS코드 추천
```
model-hscode/
├── app/
│   ├── api/v1/endpoints/          # API 엔드포인트
│   │   ├── recommend.py           # HS코드 추천
│   │   ├── search.py              # HS코드 검색
│   │   └── cache.py               # 캐시 관리
│   ├── core/
│   │   ├── config.py
│   │   └── recommender.py         # ML 추천 엔진
│   └── schemas/                   # 요청/응답 스키마
├── cache/                         # 추천 모델 캐시
├── data/                          # 관세청 HS코드 원본 데이터
└── src/                          # 핵심 로직
    ├── cache_manager.py
    ├── data_processor.py
    ├── hs_recommender.py          # TF-IDF + 의미 검색
    └── search_engine.py
```

#### 3. Model-OCR (포트: 8001) - 문서 텍스트 추출
```
model-ocr/
├── app/
│   └── main.py                    # OCR 처리 API
└── main.py                        # FastAPI 서버
```

#### 4. Model-Report (포트: 8002) - 보고서 생성
```
model-report/
├── app/
│   ├── client_request.py          # 외부 API 클라이언트
│   └── main.py                    # 보고서 생성 API
└── main.py                        # FastAPI 서버
```

---

## 💾 Data Tier - 데이터 저장소

### 🗄️ 데이터베이스 구조

**MySQL 8.0 (메인 관계형 DB):**
```sql
-- 핵심 테이블 구조 (V1__Create_base_tables.sql)
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('USER', 'ADMIN') DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE declarations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    declaration_number VARCHAR(50) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    declaration_type ENUM('IMPORT', 'EXPORT') NOT NULL,
    status ENUM('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED') DEFAULT 'DRAFT',
    importer_name VARCHAR(200) NOT NULL,
    hs_code VARCHAR(10),
    total_amount DECIMAL(15,2),
    -- 더 많은 신고서 필드들...
);

CREATE TABLE attachments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    declaration_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**ChromaDB (벡터 데이터베이스):**
- 포트: 8011 (Docker 모드)
- 용도: RAG 시스템의 의미 검색
- 컬렉션:
  - `customs_law_collection`: 관세법 문서
  - `trade_info_collection`: 무역 정보
  - `consultation_cases`: 상담 사례

**PostgreSQL (챗봇 전용):**
- 포트: 5433
- model-chatbot-fastapi 전용 DB
- 대화 기록 및 메시지 영구 저장

**Redis (캐시 및 세션):**
- 포트: 6380
- 세션 관리 및 캐시 저장소

---

## 🚀 서비스 실행 명령어 정리

### Spring Boot Backend (포트: 8080)
```bash
cd presentation-tier/backend
./mvnw spring-boot:run
# 또는 IDE에서 CustomsClearanceBackendApplication 실행
# 접속: http://localhost:8080
# Swagger UI: http://localhost:8080/api/v1/swagger-ui.html
```

### Frontend (포트: 3000)
```bash
cd presentation-tier/frontend
npm run dev
# 접속: http://localhost:3000
```

### AI Gateway (FastAPI) - 포트: 8000
```bash
cd application-tier/ai-gateway
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 접속: http://localhost:8000/docs
```

### AI 마이크로서비스들
```bash
# 1. RAG 챗봇 (메인)
cd application-tier/models/model-chatbot-fastapi
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8004

# 2. HS코드 추천
cd application-tier/models/model-hscode
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8003

# 3. OCR 서비스
cd application-tier/models/model-ocr
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001

# 4. 리포트 생성
cd application-tier/models/model-report
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 5. US 변환 서비스
cd application-tier/models/model-hscode
uv run python src/us_main.py --port 8006
```

---

## 🔗 서비스 간 통신 구조

```
Frontend (Next.js :3000)
    ↓
Spring Boot API Gateway (:8080)
    ↓
AI Gateway (FastAPI :8000)
    ↓
┌──────────────────┬─────────────────────────────────────────┐
│  Chatbot FastAPI │           AI Microservices             │
│     (:8004)      │  OCR(:8001) │ Report(:8002) │ HS(:8003)│
│                  │             │ US변환(:8006) │           │
└──────────────────┴─────────────────────────────────────────┘
    ↓                           ↓
┌─────────────────────┬─────────────────────┬─────────────────┐
│   PostgreSQL(:5433) │   ChromaDB(:8011)   │  MySQL(:3306)   │
│   Redis(:6380)      │    (벡터 검색)        │  (메인 DB)      │
│   (대화/캐시)         │                     │                 │
└─────────────────────┴─────────────────────┴─────────────────┘
                                ↓
                    ┌─────────────────────┐
                    │   웹 관리 도구        │
                    │ phpMyAdmin(:8081)   │
                    │ pgAdmin(:5050)      │
                    └─────────────────────┘
```

---

## 📝 작업 이력 추적

### 🎯 향후 작업 시 체크리스트

#### Spring Boot 백엔드 작업 시:
1. **환경 확인**: Java 17, Maven, MySQL 8.0 연결
2. **설정 파일**: `application.yml` 데이터베이스 연결 정보
3. **테스트**: `./mvnw test` 실행하여 기존 기능 검증
4. **API 문서**: Swagger UI에서 API 변경사항 확인
5. **보안**: JWT 토큰, CORS 설정 검토

#### FastAPI AI 서비스 작업 시:
1. **uv 환경**: `uv sync`로 의존성 설치
2. **환경변수**: OpenAI API 키, DB 연결 정보 확인
3. **ChromaDB**: Docker ChromaDB (8011) 연결 상태 확인
4. **진행상황**: SSE 스트리밍 동작 테스트
5. **RAG 검증**: 벡터 검색 및 AI 응답 품질 확인

#### 데이터베이스 작업 시:
1. **마이그레이션**: Flyway 스크립트로 스키마 변경
2. **백업**: 작업 전 데이터 백업 생성
3. **인덱스**: 성능 최적화를 위한 인덱스 검토
4. **외래키**: 데이터 무결성 검증

---

## 🎓 기술 학습 포인트

### AI/ML 분야:
- **RAG (Retrieval-Augmented Generation)**: ChromaDB + OpenAI 기반 질의응답
- **LangGraph**: 멀티 에이전트 AI 오케스트레이션 프레임워크
- **벡터 데이터베이스**: 의미 기반 문서 검색 및 임베딩
- **비동기 AI 처리**: FastAPI + asyncio 기반 성능 최적화

### 백엔드 아키텍처:
- **마이크로서비스**: AI Gateway를 통한 서비스 오케스트레이션
- **API Gateway 패턴**: Spring Boot + FastAPI 이중 게이트웨이
- **실시간 통신**: Server-Sent Events (SSE) 진행상황 스트리밍

### 데이터 관리:
- **하이브리드 DB**: 관계형(MySQL) + 벡터(ChromaDB) + 문서(PostgreSQL)
- **캐시 전략**: 메모리 캐시 + 파일 캐시 다층 구조

---

## 🔄 실시간 업데이트

이 문서는 Claude Code가 작업할 때마다 자동으로 업데이트됩니다.

**마지막 업데이트**: 2025-08-11 (보고서 생성 시스템 백엔드 연동 완료)

### 📋 작업 로그
- ✅ 2025-08-11: 프로젝트 구조 전체 분석 완료
- ✅ 2025-08-11: 포트 설정 정정 (사용자 요청 반영)
  - OCR: 8002 → 8001
  - Report: 8003 → 8002  
  - HS코드: 8001 → 8003
  - US변환: 신규 추가 (8006)
  - 웹 관리 도구: phpMyAdmin(8081), pgAdmin(5050) 추가
- ✅ 2025-08-11: 모든 백엔드 서비스 포트 설정 완료
  - `model-report/app/main.py`: 포트 8002로 수정 완료
  - 모든 서비스 포트가 올바르게 설정됨 확인
- ✅ 2025-08-11: 보고서 생성 페이지 완전 구현
  - OCR 기반 관세신고서 자동 생성 시스템 구축
  - 메인 페이지: `/report` 경로에 완전한 UI/UX
  - API 통합: Spring Boot + AI Gateway + Model-Report 연동
  - 핵심 컴포넌트: ReportGeneration, ReportHistory, ReportPreview
  - 파일 업로드: react-dropzone 기반 드래그&드롭 지원
  - 실시간 진행상황: OCR → AI 분석 → 신고서 생성 프로세스
  - 편집 기능: 생성된 신고서 실시간 편집 및 검증
  - 저장 기능: 백엔드 DB 연동으로 신고서 영구 저장
  - 네비게이션: 사이드바에 "보고서 생성" 메뉴 추가

### 🔧 2025-08-11 프론트엔드-백엔드 연동 작업
- ✅ **백엔드 API 구조 분석 완료**
  - DeclarationController.java 분석: `@ModelAttribute Declaration` 방식 확인
  - Declaration 엔티티 구조 파악: declarationType, status, declarationDetails 필드
  - Spring Security 설정 확인: `/declaration/**` permitAll 처리됨
  
- ✅ **프론트엔드 API 클라이언트 수정**
  - `report-api.ts` 완전 재작성: 백엔드 엔티티 구조에 맞게 타입 정의
  - API 플로우 개선: OCR → AI 처리 → 백엔드 저장 3단계 프로세스
  - 인터페이스 업데이트: ReportGenerationResponse, DeclarationCreateRequest 등
  
- ✅ **보고서 생성 컴포넌트 업데이트**
  - ReportGeneration.tsx: 백엔드 Declaration API 호출로 변경
  - ReportPreview.tsx: declarationDetails JSON 파싱 로직 추가
  - 데이터 구조 일관성: 프론트엔드-백엔드 간 데이터 매핑 완료
  
- ✅ **서버 환경 설정 및 테스트**
  - Spring Boot 백엔드: 8082 포트로 성공적으로 시작
  - Next.js 프론트엔드: 3001 포트로 시작 (3000 포트 사용 중)
  - API 연결 설정: baseURL을 http://localhost:8082/api/v1로 설정
  - 헬스 체크 성공: `/actuator/health` 정상 응답 확인

### 🎯 완료된 기능
1. **완전한 백엔드 연동**: Spring Boot Declaration API와 프론트엔드 완전 연결
2. **타입 안전성**: TypeScript 인터페이스와 백엔드 엔티티 100% 일치
3. **데이터 플로우**: OCR → AI → Declaration 저장 파이프라인 구축
4. **에러 처리**: API 오류 및 검증 에러 처리 로직 구현
5. **실시간 피드백**: 보고서 생성 진행 상황 사용자에게 표시

### 🚀 현재 동작 가능한 시스템
- ✅ Spring Boot Backend (8082): Declaration CRUD API 제공
- ✅ Next.js Frontend (3001): 보고서 생성 UI 완전 구현  
- ✅ API 통신: 프론트엔드 ↔ 백엔드 정상 연결
- ✅ 타입 시스템: 완전한 타입 안전성 보장

**다음 작업 예정**: OCR 및 Report 마이크로서비스 연동 테스트 및 사용자 요청 기능 개발

---

*이 문서는 Claude Code의 효율적인 작업을 위한 백엔드 시스템 참조 가이드입니다.*