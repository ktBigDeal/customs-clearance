# 멀티 스테이지 Docker 빌드
FROM python:3.11-slim as base

# 시스템 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libpq-dev \
    libmagic1 \
    # OCR을 위한 tesseract
    tesseract-ocr \
    tesseract-ocr-kor \
    # PDF 처리를 위한 poppler
    poppler-utils \
    # Java (tabula-py를 위해)
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 작업 디렉토리 설정
WORKDIR /app

# 사용자 생성 (보안을 위해)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Development Stage
FROM base as development

# 소스 코드 복사
COPY . .

# uv를 사용하여 의존성 설치 (개발 의존성 포함)
RUN uv sync --dev

# 포트 노출
EXPOSE 8000

# 개발 서버 실행
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production Stage
FROM base as production

# 성능을 위한 추가 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# 소스 코드만 복사 (불필요한 파일 제외)
COPY pyproject.toml uv.lock ./
COPY app/ ./app/
COPY main.py ./
COPY src/ ./src/

# uv를 사용하여 프로덕션 의존성만 설치
RUN uv sync --frozen --no-dev

# 로그 디렉토리 생성
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# 포트 노출
EXPOSE 8000

# appuser로 전환
USER appuser

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 프로덕션 서버 실행 (gunicorn + uvicorn workers)
CMD ["uv", "run", "gunicorn", "main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

# Testing Stage
FROM development as testing

# 테스트 실행
RUN uv run pytest tests/ -v --cov=app --cov-report=term-missing

# Builder Stage (CI/CD에서 사용)
FROM base as builder

# 소스 코드 복사
COPY . .

# 빌드 및 테스트
RUN uv sync --dev
RUN uv run pytest tests/ -v
RUN uv run black --check app/ tests/
RUN uv run isort --check-only app/ tests/
RUN uv run flake8 app/ tests/
RUN uv run mypy app/

# 빌드 아티팩트 생성
RUN uv build

# Final production stage
FROM python:3.11-slim as final

# 필수 런타임 패키지만 설치
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    libmagic1 \
    tesseract-ocr \
    tesseract-ocr-kor \
    poppler-utils \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# 사용자 생성
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 작업 디렉토리 설정
WORKDIR /app

# uv 설치 (최소 설치)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 빌드된 패키지 복사
COPY --from=builder /app/dist/*.whl ./

# 패키지 설치
RUN uv pip install --system *.whl

# 런타임 파일 복사
COPY --from=production --chown=appuser:appuser /app/src ./src
COPY --from=production --chown=appuser:appuser /app/main.py ./
COPY --from=production --chown=appuser:appuser /app/logs ./logs

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# appuser로 전환
USER appuser

# 프로덕션 실행
CMD ["gunicorn", "main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--worker-timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100"]