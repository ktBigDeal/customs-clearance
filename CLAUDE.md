# 이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 필요한 가이드를 제공합니다

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
- **Package Manager**: uv (Python 패키지 매니저)
- **Async**: uvicorn + httpx + aiohttp
- **Database**: SQLAlchemy + asyncpg/aiomysql
- **Validation**: Pydantic 2.5
- **Monitoring**: Prometheus metrics
- **Services**: AI Gateway, RAG Chatbot, OCR 모델, Report 생성 모델

### Database (MySQL 8.0)

- **Primary DB**: MySQL 8.0 with utf8mb4 charset
- **Schema**: 완성된 테이블 구조 (users, declarations, attachments, history)
- **Test Data**: 초기 시드 데이터 포함
- **Management**: phpMyAdmin 웹 인터페이스

[... 이하 기존 파일 내용 그대로 유지 ...]

## 🔨 Recent Work History

### 2025-01 작업 이력

#### 📊 Model-Chatbot 분석 및 개선 (완료)

**작업 일시**: 2025-01-04
**작업 내용**:

- **분석 완료**: `/sc:analyze` 명령으로 application-tier/model-chatbot 컴포넌트 전체 분석
  - Korean customs law RAG (Retrieval-Augmented Generation) 시스템 구조 파악
  - Multi-agent AI 아키텍처 이해 (LangGraph 오케스트레이션)
  - Vector 데이터베이스 (ChromaDB) 및 LangChain 프레임워크 활용
  - OpenAI API 통합 및 대화형 AI 에이전트 구현

- **Docstring 추가 완료**: 신입 개발자를 위한 교육용 docstring 작성
  - `unified_cli.py`: RAG 시스템과 멀티 에이전트 아키텍처 설명
  - `langgraph_orchestrator.py`: LangGraph 기반 지능형 오케스트레이터 설명
  - `config.py`: 환경 변수 및 보안 설정 관리 설명
  - `law_agent.py`: 대화형 RAG 에이전트와 메모리 관리 설명
  - `vector_store.py`: 벡터 데이터베이스 개념과 ChromaDB 사용법 설명

#### 🚀 Backend 시스템 커밋 (완료)

**작업 일시**: 2025-01-04
**커밋 ID**: `3e60fea`
**작업 내용**:

- **선택적 커밋**: presentation-tier/backend 관련 파일만 선별하여 커밋
- **신규 문서**: `DEPENDENCIES.md` 파일 추가 (의존성 관리 가이드)
- **파일 수**: 14개 파일, 578 추가, 30 삭제
- **커밋 메시지**: "feat(backend): Spring Boot 백엔드 시스템 구조 및 핵심 기능 구현"

#### 🎨 Frontend 시스템 업데이트 (완료)

**작업 일시**: 2025-01-04
**커밋 ID**: `ece9c8d`
**작업 내용**:

- **메인 Frontend 개선**:
  - 다국어(i18n) 시스템 제거 및 구조 단순화
  - 인증 시스템 추가 (로그인 페이지)
  - 채팅 기능 페이지 구현
  - 레이아웃 컴포넌트 개선 (Header, Sidebar, MainNav)
  - UI 컴포넌트 최적화 (DropdownMenu)

- **디자인 초안 추가**: `presentation-tier/frontend-draft/`
  - 수입신고서 양식 컴포넌트 (`ImportDeclarationForm.tsx`)
  - 채팅 인터페이스 디자인
  - Tailwind CSS 기반 모던 UI 디자인
  - 완전한 Next.js 프로젝트 구조

- **파일 변경**: 34개 파일 (6,664 추가, 906 삭제)
- **주요 변경**: i18n 미들웨어 제거, 인증/채팅 페이지 추가, 디자인 초안 구현

### 🔄 현재 상태 (2025-01-04)

#### ✅ 완료된 작업

1. **AI Chatbot 시스템 분석 및 문서화**: RAG 기반 다중 에이전트 시스템 완전 이해
2. **Backend 코드 커밋**: Spring Boot 시스템 구조 안정화
3. **Frontend 시스템 개선**: 메인 프론트엔드 + 디자인 초안 구현

#### 🎯 남은 작업 (스테이징되지 않음)

- `application-tier/models/model-chatbot/`: AI 모델 관련 파일들 (docstring 추가된 상태)
- `application-tier/ai-gateway/`: AI Gateway 설정 파일들
- `application-tier/models/model-ocr/`: OCR 모델 서비스
- `application-tier/models/model-report/`: Report 생성 모델 서비스

#### 📋 기술 스택 업데이트

- **AI/ML**: RAG 시스템, LangGraph, ChromaDB, LangChain, OpenAI API
- **Frontend**: Next.js 14.2, React 18, TypeScript, Tailwind CSS
- **Backend**: Spring Boot 3.2.1, Java 17, MySQL 8.0
- **개발환경**: uv (Python 패키지 매니저), Docker Compose

### 🎓 학습 및 개선사항

1. **RAG 시스템 이해**: Retrieval-Augmented Generation 아키텍처 완전 파악
2. **멀티 에이전트 AI**: LangGraph 기반 지능형 오케스트레이션 시스템 분석
3. **벡터 데이터베이스**: ChromaDB와 임베딩 기반 의미 검색 시스템 이해
4. **교육용 문서화**: 신입 개발자를 위한 상세한 기술 설명 작성
5. **선택적 Git 관리**: 프로젝트 구성 요소별 단계적 커밋 전략 적용

#### 🚀 Model-Chatbot-FastAPI 구현 완료 (2025-01-07)

**작업 일시**: 2025-01-07
**커밋 ID**: `7169412`
**작업 내용**: model-chatbot의 모듈을 활용하여 model-chatbot-fastapi 완전 구현

**✅ 구현 완료 모듈들**:

1. **LangGraph 통합 시스템** (`app/core/langgraph_integration.py`)
   - 기존 model-chatbot의 LangGraph 시스템을 FastAPI용 비동기 버전으로 완전 포팅
   - 비동기 메시지 처리, 에이전트 라우팅 관리, 대화 컨텍스트 유지
   - 시스템 헬스 체크 및 에러 복구 매커니즘 구현

2. **설정 관리 모듈** (`app/utils/config.py`)
   - FastAPI 환경에 맞는 설정 관리 시스템 확장
   - ChromaDB, LangGraph, FastAPI 전용 설정 추가
   - 기존 model-chatbot 데이터 경로 호환성 유지

3. **비동기 RAG 에이전트 시스템**:
   - **법률 에이전트** (`app/rag/law_agent.py`): 관세법 전문 대화형 에이전트
   - **무역 규제 에이전트** (`app/rag/trade_regulation_agent.py`): 동식물 수입규제 전문 에이전트
   - **상담 사례 에이전트** (`app/rag/consultation_case_agent.py`): 실무 민원 상담 전문 에이전트
   - **쿼리 라우터** (`app/rag/query_router.py`): 지능형 질의 분류 및 라우팅 시스템

4. **데이터베이스 통합**:
   - SQLAlchemy ORM 모델 (`app/models/conversation.py`)
   - 대화 관리 서비스 (`app/services/conversation_service.py`)
   - PostgreSQL 비동기 연결 지원

5. **종합 테스트 시스템**:
   - 기본 기능 테스트 (`tests/test_basic.py`)
   - 통합 테스트 및 데이터베이스 테스트 스위트
   - 완전 자동화된 테스트 환경

**🔧 모델 표준화 작업 (중요)**:

- **변경 대상**: 모든 챗봇 AI 모델
- **변경 내용**: `gpt-4-turbo-preview` → `gpt-4.1-mini`로 통일
- **변경된 파일 수**: 6개 파일
  1. `app/core/langgraph_integration.py` - Line 57 (기본 모델)
  2. `app/utils/config.py` - Line 334 (LangGraph 설정)
  3. `app/rag/law_agent.py` - Line 136 (법률 에이전트)
  4. `app/rag/trade_regulation_agent.py` - Line 143 (무역 규제 에이전트)
  5. `app/rag/consultation_case_agent.py` - Line 170 (상담 사례 에이전트)
  6. `tests/test_basic.py` - Line 138 (테스트 검증)

**🎯 기술적 혁신**:

- **비동기 아키텍처**: 기존 동기 시스템을 완전한 비동기 FastAPI 환경으로 전환
- **메모리 관리**: 에이전트별 특화된 대화 메모리 시스템 구현
- **경로 호환성**: 기존 model-chatbot 데이터 및 설정과 완벽한 호환성 유지
- **에러 처리**: 포괄적인 예외 처리 및 복구 시스템
- **성능 최적화**: 비동기 실행기를 통한 동기/비동기 코드 통합

**📈 시스템 구성**:
```
application-tier/models/model-chatbot-fastapi/
├── app/
│   ├── core/
│   │   └── langgraph_integration.py  # LangGraph 비동기 통합
│   ├── utils/
│   │   └── config.py                 # 확장된 설정 관리
│   ├── rag/                         # 비동기 RAG 에이전트들
│   │   ├── law_agent.py
│   │   ├── trade_regulation_agent.py
│   │   ├── consultation_case_agent.py
│   │   └── query_router.py
│   ├── models/
│   │   └── conversation.py          # SQLAlchemy ORM
│   ├── services/
│   │   └── conversation_service.py  # 대화 관리 서비스
│   └── routers/
│       └── conversations.py         # FastAPI 라우터
└── tests/
    ├── test_basic.py                # 기본 기능 테스트
    ├── test_integration.py          # 통합 테스트
    └── test_database.py            # 데이터베이스 테스트
```

**🔗 통합성 보장**:
- 기존 `model-chatbot` 모듈과 완전 호환
- ChromaDB 벡터 데이터베이스 연동
- LangChain/LangGraph 오케스트레이션 유지
- OpenAI API 통합 및 모델 표준화

이로써 **model-chatbot-fastapi**는 기존 시스템의 모든 기능을 비동기 환경에서 완벽하게 구현하면서, 최신 AI 모델(`gpt-4.1-mini`)로 표준화된 완전한 RAG 기반 관세법 전문 챗봇 시스템이 되었습니다.

## 🐍 Application Tier - Python 환경 설정 및 실행 가이드

### 📦 uv 패키지 매니저 개요

Application Tier의 모든 Python 서비스는 **uv**를 사용하여 의존성 관리 및 가상환경을 구성합니다.

- **uv**: 빠른 Python 패키지 매니저 및 프로젝트 관리자
- **장점**: pip보다 10-100배 빠른 의존성 해결, 자동 가상환경 관리
- **설치**: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Linux/macOS) 또는 `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)

### 🏗️ Application Tier 구조

```Plain Text
application-tier/
├── ai-gateway/              # FastAPI 메인 게이트웨이
│   ├── pyproject.toml       # uv 의존성 설정
│   ├── uv.lock             # 의존성 잠금 파일
│   └── .venv/              # 가상환경 (자동 생성)
├── models/
│   ├── model-chatbot/      # RAG 기반 법률 챗봇 (uv 없음, requirements.txt 사용)
│   ├── model-chatbot-fastapi/ # 🆕 FastAPI용 비동기 RAG 챗봇 시스템
│   │   ├── app/
│   │   │   ├── core/       # LangGraph 통합 시스템
│   │   │   ├── rag/        # 비동기 RAG 에이전트들
│   │   │   ├── utils/      # 설정 및 유틸리티
│   │   │   └── routers/    # FastAPI 라우터들
│   │   ├── tests/          # 종합 테스트 시스템
│   │   ├── pyproject.toml  # uv 의존성 설정
│   │   ├── uv.lock        # 의존성 잠금 파일
│   │   └── .venv/         # 가상환경 (자동 생성)
│   ├── model-lawchatbot/   # GraphDB 기반 법률 챗봇
│   │   ├── pyproject.toml  # uv 의존성 설정  
│   │   ├── uv.lock        # 의존성 잠금 파일
│   │   └── .venv/         # 가상환경 (자동 생성)
│   ├── model-ocr/          # OCR 텍스트 추출 서비스
│   │   ├── pyproject.toml  # uv 의존성 설정
│   │   ├── uv.lock        # 의존성 잠금 파일
│   │   └── .venv/         # 가상환경 (자동 생성)
│   └── model-report/       # 보고서 생성 서비스
│       ├── pyproject.toml  # uv 의존성 설정
│       ├── uv.lock        # 의존성 잠금 파일
│       └── .venv/         # 가상환경 (자동 생성)
```

### 🚀 각 서비스별 실행 방법

#### 1. AI Gateway (메인 게이트웨이)

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

#### 2. Model-Chatbot (RAG 챗봇)

**주의**: 이 서비스는 uv가 아닌 기존 requirements.txt를 사용합니다.

```bash
cd application-tier/models/model-chatbot

# 가상환경 생성 (Python 기본 방식)
python -m venv .venv

# 가상환경 활성화 (Windows)
source .venv/Scripts/activate

# 가상환경 활성화 (Linux/macOS)
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# CLI 실행 (통합 클라이언트)
python src/rag/unified_cli.py

# 또는 개별 테스트 실행
python test_cli_e2e.py
```

#### 3. Model-Chatbot-FastAPI (🆕 비동기 RAG 챗봇)

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
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8003

# 또는 가상환경 내에서 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8003

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

#### 4. Model-Lawchatbot (GraphDB 챗봇)

```bash
cd application-tier/models/model-lawchatbot

# 가상환경 자동 생성 및 의존성 설치
uv sync

# 가상환경 활성화 (Windows)
source .venv/Scripts/activate

# 가상환경 활성화 (Linux/macOS)
source .venv/bin/activate

# 메인 애플리케이션 실행
uv run python main.py

# 또는 Gradio 챗봇 실행
uv run python codes/gradio/chat_gradio.py
```

#### 5. Model-OCR (OCR 서비스)

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

#### 6. Model-Report (보고서 생성 서비스)

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

### 🌐 서비스 포트 및 URL

- **AI Gateway**: http://localhost:8000 (API 문서: /docs)
- **Model-OCR**: http://localhost:8001 (API 문서: /docs)
- **Model-Report**: http://localhost:8002 (API 문서: /docs)
- **Model-Chatbot-FastAPI**: http://localhost:8003 (API 문서: /docs) 🆕
- **Model-Chatbot**: CLI 기반 (터미널에서 대화형 실행)
- **Model-Lawchatbot**: Gradio UI (실행 시 포트 자동 할당)

### 🔧 개발 시 주의사항

### 📝 코딩 스타일 및 문서화 규칙

#### 🐍 Python 문서화 (Docstring)
모든 Python 파일, 클래스, 함수에는 **Google Style Docstring**을 작성하여 신입개발자가 이해할 수 있도록 합니다.

```python
def calculate_customs_duty(item_value: float, duty_rate: float) -> float:
    """수입품의 관세를 계산합니다.
    
    관세법에 따른 관세 계산 공식을 적용하여 수입품에 대한 관세액을 산출합니다.
    계산 결과는 원화 단위로 반환되며, 소수점 이하는 절상 처리됩니다.
    
    Args:
        item_value (float): 수입품의 과세가격 (원화 기준)
        duty_rate (float): 적용할 관세율 (0.0 ~ 1.0, 예: 0.08 = 8%)
    
    Returns:
        float: 계산된 관세액 (원화)
        
    Raises:
        ValueError: item_value가 0 이하이거나 duty_rate가 음수인 경우
        TypeError: 인자가 숫자 타입이 아닌 경우
        
    Example:
        >>> calculate_customs_duty(1000000, 0.08)
        80000.0
        
        >>> calculate_customs_duty(500000, 0.0)  # 무관세 품목
        0.0
        
    Note:
        - 관세법 제2조에 따른 과세가격 기준으로 계산
        - 특혜관세 적용시 duty_rate는 특혜세율 사용
        - FTA 협정세율 적용시 별도 함수 calculate_fta_duty() 사용 권장
    """
    if item_value <= 0:
        raise ValueError("수입품 가격은 0보다 커야 합니다")
    if duty_rate < 0:
        raise ValueError("관세율은 음수일 수 없습니다")
        
    return item_value * duty_rate
```

#### ☕ Java 문서화 (JavaDoc)
모든 Java 클래스, 메서드에는 **JavaDoc**을 작성하여 비즈니스 로직을 명확히 설명합니다.

```java
/**
 * 수출입 신고서 처리를 담당하는 서비스 클래스입니다.
 * 
 * <p>이 클래스는 관세청 UNI-PASS 시스템과 연동하여 수출입 신고서의 
 * 생성, 수정, 삭제 및 상태 관리를 담당합니다.</p>
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>신고서 작성 및 검증</li>
 *   <li>첨부서류 관리</li>
 *   <li>신고 진행 상태 추적</li>
 *   <li>세관 심사 결과 처리</li>
 * </ul>
 * 
 * @author 관세시스템팀
 * @version 1.0
 * @since 2025-01-06
 * @see DeclarationRepository
 * @see CustomsApiClient
 */
@Service
@Transactional
public class DeclarationService {
    
    /**
     * 새로운 수출입 신고서를 생성합니다.
     * 
     * <p>신고서 생성 과정:</p>
     * <ol>
     *   <li>필수 정보 검증 (업체정보, 품목정보 등)</li>
     *   <li>HS코드 유효성 확인</li>
     *   <li>관세 및 부가세 자동 계산</li>
     *   <li>데이터베이스 저장</li>
     *   <li>신고번호 발급</li>
     * </ol>
     * 
     * @param declarationDto 신고서 생성에 필요한 정보
     * @param userId 신고서를 작성하는 사용자 ID
     * @return 생성된 신고서 정보 (신고번호 포함)
     * @throws ValidationException 필수 정보가 누락되거나 잘못된 경우
     * @throws DuplicateDeclarationException 중복된 신고서가 이미 존재하는 경우
     * @throws CustomsApiException 관세청 API 호출 중 오류가 발생한 경우
     * 
     * @apiNote 이 메서드는 트랜잭션 내에서 실행되며, 오류 발생시 자동으로 롤백됩니다.
     * @implNote 대용량 첨부파일(>50MB)은 별도의 비동기 처리를 권장합니다.
     */
    public DeclarationResponseDto createDeclaration(
            DeclarationCreateDto declarationDto, 
            Long userId) throws ValidationException, DuplicateDeclarationException {
        
        // 비즈니스 로직 구현...
    }
}
```

#### 🌐 JavaScript/TypeScript 문서화 (JSDoc)
모든 JavaScript/TypeScript 함수, 컴포넌트에는 **JSDoc**을 작성합니다.

```typescript
/**
 * 수입신고서 작성 폼 컴포넌트
 * 
 * 사용자가 수입신고서를 작성할 수 있는 종합적인 폼을 제공합니다.
 * React Hook Form과 Zod를 사용하여 실시간 검증을 지원하며,
 * 단계별 입력 프로세스로 사용자 경험을 개선했습니다.
 * 
 * @component
 * @example
 * ```tsx
 * function ImportPage() {
 *   const handleSubmit = (data) => {
 *     console.log('신고서 데이터:', data);
 *   };
 *   
 *   return (
 *     <ImportDeclarationForm 
 *       onSubmit={handleSubmit}
 *       initialData={savedDraft}
 *       mode="create"
 *     />
 *   );
 * }
 * ```
 * 
 * @param {Object} props - 컴포넌트 props
 * @param {Function} props.onSubmit - 폼 제출시 호출되는 콜백 함수
 * @param {ImportFormData} [props.initialData] - 폼 초기값 (수정모드나 임시저장 데이터)
 * @param {'create' | 'edit' | 'view'} [props.mode='create'] - 폼 모드 (생성/수정/보기)
 * @param {boolean} [props.disabled=false] - 폼 비활성화 여부
 * 
 * @returns {JSX.Element} 수입신고서 작성 폼 컴포넌트
 * 
 * @author 프론트엔드팀
 * @since 2025-01-06
 * @version 1.2.0
 */
export function ImportDeclarationForm({
    onSubmit,
    initialData,
    mode = 'create',
    disabled = false
}: ImportDeclarationFormProps): JSX.Element {
    
    /**
     * HS코드 검색 및 자동완성 기능
     * 
     * 사용자가 입력한 키워드를 기반으로 관세청 HS코드 데이터베이스에서
     * 관련 품목을 검색하고 자동완성 목록을 제공합니다.
     * 
     * @async
     * @param {string} keyword - 검색할 키워드 (최소 2글자)
     * @param {AbortSignal} [signal] - 요청 취소용 AbortSignal
     * @returns {Promise<HSCodeItem[]>} 검색된 HS코드 목록
     * @throws {ValidationError} 키워드가 2글자 미만인 경우
     * @throws {ApiError} API 호출 실패시
     * 
     * @example
     * ```typescript
     * const results = await searchHSCode('딸기');
     * // 결과: [{ code: '0810.10', name: '딸기', duty_rate: 30 }, ...]
     * ```
     */
    const searchHSCode = useCallback(async (
        keyword: string, 
        signal?: AbortSignal
    ): Promise<HSCodeItem[]> => {
        if (keyword.length < 2) {
            throw new ValidationError('검색 키워드는 최소 2글자 이상 입력해주세요');
        }
        
        try {
            const response = await fetch(`/api/hscode/search?q=${keyword}`, {
                signal
            });
            
            if (!response.ok) {
                throw new ApiError(`HS코드 검색 실패: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('HS코드 검색이 취소되었습니다');
                return [];
            }
            throw error;
        }
    }, []);
    
    // 컴포넌트 로직...
}
```

#### 📐 문서화 작성 원칙

1. **신입개발자 친화적**: 전문용어 사용시 반드시 설명 추가
2. **비즈니스 로직 설명**: 단순한 기능 설명이 아닌 업무 맥락 제공
3. **예시 코드 포함**: 실제 사용 방법을 보여주는 예제 필수
4. **에러 케이스 명시**: 발생 가능한 예외상황과 대응방법 설명
5. **업무 규칙 참조**: 관련 법규나 업무 규칙 참조 링크 제공

#### 🔍 품질 검사 자동화

```bash
# Python: docstring 검사
uv add --dev pydocstyle
uv run pydocstyle app/

# Java: JavaDoc 검사 
./mvnw javadoc:javadoc

# JavaScript/TypeScript: JSDoc 검사
npm install --save-dev jsdoc @typescript-eslint/eslint-plugin
npm run lint:docs
```

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

## 🚨 현재 해결 필요한 이슈 (2025-08-08)

### RAG 문서 검색 실패 문제

**현상**: 
- TradeRegulationAgent가 ChromaDB에서 문서를 찾지 못함
- 로그: `✅ 0개 결과 반환 (요청된 top_k: 12)`
- 응답: "해당 품목(딸기)에 대한 동식물허용금지지역 및 수입규제DB에 관련 정보가 제공되지 않았습니다"

**확인된 상태**:
- ✅ ChromaDB Docker 컨테이너 정상 실행 중 (8011 포트)
- ✅ FastAPI 챗봇 시스템 정상 작동 (8004 포트)
- ✅ LangGraph 오케스트레이션 및 에이전트 라우팅 성공
- ✅ 벡터스토어 설정이 Docker 모드로 올바르게 구성됨

**추정 원인**:
1. **컬렉션명 불일치**: `trade_info_collection` vs 실제 데이터 컬렉션
2. **데이터 매칭 실패**: 검색 쿼리와 저장된 데이터 간 임베딩 불일치  
3. **필터링 조건**: 메타데이터 필터가 너무 제한적일 가능성
4. **ChromaDB 연결**: Docker 네트워크 설정 또는 포트 매핑 이슈

**다음 세션 작업**:
- [ ] ChromaDB 컬렉션 목록 및 데이터 확인
- [ ] 벡터 검색 쿼리 디버깅
- [ ] 임베딩 모델 호환성 검증  
- [ ] 테스트 데이터로 수동 검색 테스트