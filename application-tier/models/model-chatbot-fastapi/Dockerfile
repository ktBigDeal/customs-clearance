# Railway 배포용 ChatBot FastAPI Dockerfile
# RAG 기반 텍스트 챗봇 - 최소 의존성 버전

FROM python:3.11-slim

# Railway 포트 환경변수 지원
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 기본 도구
    curl \
    ca-certificates \
    # PostgreSQL 클라이언트 라이브러리
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# uv 패키지 매니저 설치
RUN pip install --no-cache-dir uv

# 사용자 생성 (보안)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Railway용 프로젝트 설정 복사 (최소 의존성)
COPY pyproject.railway.toml ./pyproject.toml
COPY uv.lock* ./

# Railway용 최소 의존성 설치
RUN uv sync --frozen --no-dev

# 소스 코드 복사
COPY app/ ./app/
COPY main.py ./

# 로그 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# 비루트 사용자로 전환
USER appuser

# 포트 노출
EXPOSE $PORT

# Railway 환경에서 실행
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]