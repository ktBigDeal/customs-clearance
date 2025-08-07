# ChromaDB v2 API 테스트 가이드

## ✅ 작동하는 엔드포인트

### 헬스체크
```bash
curl http://localhost:8011/api/v2/heartbeat
# 응답: {"nanosecond heartbeat": 숫자}
```

### 버전 확인
```bash
curl http://localhost:8011/api/v2/version
# 응답: "1.0.0"
```

## ❌ 작동하지 않는 엔드포인트

### Collections (v2에서 제거됨)
```bash
curl http://localhost:8011/api/v2/collections
# 응답: 404 Not Found
```

## 🔧 Python 클라이언트로 데이터 확인

ChromaDB 1.0에서는 Python 클라이언트를 사용해야 합니다:

```python
import chromadb

# 클라이언트 연결
client = chromadb.HttpClient(host="localhost", port=8011)

# 컬렉션 목록 확인
collections = client.list_collections()
print(f"컬렉션 수: {len(collections)}")

for collection in collections:
    print(f"- {collection.name}: {collection.count()} 개 문서")
```

## 📊 현재 상태

- **컨테이너**: 정상 실행 중
- **데이터**: 58MB SQLite + 22개 벡터 인덱스 디렉토리
- **API**: v2 heartbeat/version만 지원
- **포트**: 8011 (외부) → 8000 (내부)

## 💡 결론

ChromaDB가 **정상 작동**하고 있으며, REST API 대신 **Python 클라이언트**를 사용하여 데이터에 접근해야 합니다.