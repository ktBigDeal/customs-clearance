FROM chromadb/chroma:0.4.22

# Railway 포트 환경변수 지원
ENV PORT=8000

# ChromaDB 실행 (Railway PORT 환경변수 사용)
CMD ["sh", "-c", "uvicorn chromadb.app:app --host 0.0.0.0 --port ${PORT:-8000}"]