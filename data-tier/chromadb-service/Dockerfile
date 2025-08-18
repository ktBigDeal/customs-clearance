FROM chromadb/chroma:0.4.22

# Railway 환경 설정
ENV CHROMA_HOST=0.0.0.0
ENV CHROMA_PORT=8000
ENV CHROMA_LOG_LEVEL=INFO
ENV ANONYMIZED_TELEMETRY=false
ENV IS_PERSISTENT=true
ENV PERSIST_DIRECTORY=/chroma/chroma

# Railway 포트 환경변수 지원
ENV PORT=8000

# 시스템 패키지 업데이트 및 curl 설치 (헬스체크용)
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# ChromaDB 데이터 디렉토리 생성
RUN mkdir -p /chroma/chroma && chown -R chroma:chroma /chroma

# 다시 chroma 사용자로 전환
USER chroma

# 작업 디렉토리 설정
WORKDIR /chroma

# 포트 노출 (Railway에서 동적 할당)
EXPOSE $PORT

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/v1/heartbeat || exit 1


# ChromaDB 실행 (Railway PORT 환경변수 사용)
CMD ["sh", "-c", "uvicorn chromadb.app:app --host 0.0.0.0 --port ${PORT:-8000}"]