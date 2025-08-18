# 챗봇 서비스 ChromaDB 연결 가이드

Railway ChromaDB 배포 후 챗봇 서비스에서 연결하는 방법입니다.

## 🔗 챗봇 서비스 환경변수 설정

### Railway 환경변수 (프로덕션)
```env
# ChromaDB 연결 설정
CHROMADB_MODE=docker
CHROMADB_HOST=your-chromadb-service-production.railway.app
CHROMADB_PORT=443
CHROMADB_USE_SSL=true

# OpenAI API (필수)
OPENAI_API_KEY=your_openai_api_key

# 기타 환경변수
PORT=8004
ENVIRONMENT=production
```

### 로컬 개발 환경변수 (.env)
```env
# ChromaDB 연결 설정 (개발시에는 로컬 사용)
CHROMADB_MODE=local
CHROMADB_HOST=localhost
CHROMADB_PORT=8011

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# 기타 환경변수
PORT=8004
ENVIRONMENT=development
```

## 📁 챗봇 서비스 코드 수정 사항

### 1. vector_store.py 확인
현재 코드는 이미 Railway 연결을 지원합니다:

```python
# app/rag/vector_store.py
def _init_docker_connection(self):
    """Docker/Railway ChromaDB 연결"""
    host = self.config.get("host", "localhost")
    port = self.config.get("port", 443)
    use_ssl = self.config.get("use_ssl", True)
    
    if use_ssl:
        # HTTPS 연결 (Railway 환경)
        client = chromadb.HttpClient(
            host=host, 
            port=port,
            ssl=True
        )
    else:
        # HTTP 연결 (로컬 Docker)
        client = chromadb.HttpClient(host=host, port=port)
```

### 2. config.py 확인
환경변수 처리가 이미 구현되어 있습니다:

```python
# app/utils/config.py
def get_chromadb_config():
    mode = os.getenv("CHROMADB_MODE", "local").lower()
    
    if mode == "docker":
        config.update({
            "mode": "docker",
            "host": os.getenv("CHROMADB_HOST", "localhost"),
            "port": int(os.getenv("CHROMADB_PORT", "443")),
            "use_ssl": os.getenv("CHROMADB_USE_SSL", "true").lower() == "true"
        })
    else:
        config.update({
            "mode": "local",
            "persist_directory": str("chroma_db")
        })
```

## 🚀 Railway 배포 시 설정

### 1. 챗봇 서비스 환경변수
Railway 대시보드에서 다음 환경변수 설정:

```
CHROMADB_MODE=docker
CHROMADB_HOST=your-chromadb-service-production.railway.app
CHROMADB_PORT=443
CHROMADB_USE_SSL=true
OPENAI_API_KEY=sk-...your-key...
PORT=$PORT  # Railway가 자동 할당
```

### 2. 서비스 의존성 확인
ChatBot 서비스가 ChromaDB 서비스 배포 후에 배포되도록 순서 조정

### 3. 네트워크 연결 테스트
```python
# 연결 테스트 스크립트
import os
import chromadb

def test_railway_connection():
    try:
        client = chromadb.HttpClient(
            host=os.getenv("CHROMADB_HOST"),
            port=int(os.getenv("CHROMADB_PORT", "443")),
            ssl=True
        )
        
        # 헬스체크
        result = client.heartbeat()
        print(f"✅ ChromaDB 연결 성공: {result}")
        
        # 컬렉션 목록 조회
        collections = client.list_collections()
        print(f"📁 컬렉션 목록: {[c.name for c in collections]}")
        
        return True
    except Exception as e:
        print(f"❌ ChromaDB 연결 실패: {e}")
        return False

if __name__ == "__main__":
    test_railway_connection()
```

## 🔧 트러블슈팅

### 연결 실패시
1. **ChromaDB 서비스 상태 확인**
   ```bash
   curl https://your-chromadb-service-production.railway.app/api/v1/heartbeat
   ```

2. **환경변수 확인**
   - Railway 대시보드에서 환경변수 값 검증
   - CHROMADB_HOST가 정확한 Railway URL인지 확인

3. **SSL/포트 설정 확인**
   - HTTPS: 포트 443
   - HTTP: 포트 80 (비추천)

### 데이터 없음 오류시
1. **데이터 마이그레이션 확인**
   ```bash
   python migrate_data.py --verify-only \
     --source-path ../application-tier/models/model-chatbot-fastapi/data/chroma_db \
     --railway-url https://your-chromadb-service-production.railway.app
   ```

2. **컬렉션 생성 확인**
   - ChromaDB 로그에서 컬렉션 생성 확인
   - 필요시 수동으로 컬렉션 재생성

### 성능 이슈시
1. **Railway 리소스 확인**
   - 메모리 사용량 모니터링
   - CPU 사용량 확인

2. **배치 크기 조정**
   ```python
   # 대용량 검색시 배치 크기 조정
   result = collection.query(
       query_texts=["query"],
       n_results=5  # 너무 크지 않게 설정
   )
   ```

## 📊 모니터링

### 로그 확인
```bash
# ChromaDB 서비스 로그
railway logs --service chromadb

# 챗봇 서비스 로그
railway logs --service chatbot
```

### 메트릭 모니터링
- Railway 대시보드에서 CPU/메모리 사용량 확인
- ChromaDB API 응답 시간 모니터링
- 오류율 추적

## 🔄 로컬 ↔ Railway 전환

### 로컬 개발시
```env
CHROMADB_MODE=local
```

### Railway 배포시
```env
CHROMADB_MODE=docker
CHROMADB_HOST=your-chromadb-service-production.railway.app
CHROMADB_PORT=443
CHROMADB_USE_SSL=true
```

환경변수만 변경하면 자동으로 연결 모드가 전환됩니다!