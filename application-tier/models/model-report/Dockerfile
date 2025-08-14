# Report 생성 서비스 Dockerfile
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock* ./
COPY . .

# uv를 사용하여 의존성 설치
RUN uv sync --frozen --no-dev

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 비루트 사용자 생성
RUN useradd --create-home --shell /bin/bash reportuser
RUN chown -R reportuser:reportuser /app
USER reportuser

# 포트 노출
EXPOSE 8002

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# 애플리케이션 실행
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]