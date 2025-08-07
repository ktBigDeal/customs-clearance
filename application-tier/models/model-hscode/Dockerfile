# HS 코드 추천 API 서버 Dockerfile
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 기존 모델 및 설정 파일 복사
COPY config.py .
COPY src/ ./src/
COPY data/ ./data/
COPY cache/ ./cache/
COPY docs/ ./docs/

# 애플리케이션 코드 복사
COPY app/ ./app/

# 환경 변수 설정
ENV PYTHONPATH=/app:/app/src
ENV ENVIRONMENT=production

# 포트 설정
EXPOSE 8003

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]