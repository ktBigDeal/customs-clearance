# OCR 서비스 Dockerfile
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
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock* ./
COPY . .

# uv를 사용하여 의존성 설치 (루트 권한으로)
RUN uv sync --frozen --no-dev

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 비루트 사용자 생성 및 파일 권한 설정
RUN useradd --create-home --shell /bin/bash ocruser
RUN chown -R ocruser:ocruser /app
RUN chmod +x /root/.local/bin/uv || true

# uv를 ocruser가 접근할 수 있도록 복사
RUN cp /root/.local/bin/uv /usr/local/bin/uv || true
RUN chmod +x /usr/local/bin/uv || true

USER ocruser

# 포트 노출 (Cloud Run uses PORT env var)
EXPOSE 8080

# 헬스체크 설정 (use PORT env var)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# 애플리케이션 실행 (use PORT env var)
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]