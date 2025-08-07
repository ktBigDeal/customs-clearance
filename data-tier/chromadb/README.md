# ChromaDB Docker 서비스

ChromaDB 공식 이미지를 사용한 벡터 데이터베이스 서비스입니다.

## 🏗️ 구조

```
chromadb/
├── .env                    # ChromaDB 환경 설정
├── scripts/               # 관리 스크립트
│   ├── backup-chromadb.sh  # 백업 스크립트
│   ├── restore-chromadb.sh # 복원 스크립트
│   └── test-connection.py  # 연결 테스트
├── backups/               # 백업 파일 저장
└── README.md              # 이 문서
```

## 🚀 사용법

### 서비스 시작
```bash
# data-tier 디렉토리에서 실행
docker-compose up -d chromadb
```

### 서비스 확인
```bash
# 컨테이너 상태 확인
docker-compose ps chromadb

# 로그 확인
docker-compose logs chromadb

# 헬스체크 확인
curl http://localhost:8011/api/v1/heartbeat
```

## 🔧 설정

### 환경 변수 (.env)
- `CHROMA_SERVER_HOST`: 서버 호스트 (기본: 0.0.0.0)
- `CHROMA_SERVER_HTTP_PORT`: 서버 포트 (기본: 8000, 외부 포트: 8011)
- `PERSIST_DIRECTORY`: 데이터 저장 경로 (기본: /chroma/chroma)
- `CHROMA_LOG_LEVEL`: 로그 레벨 (기본: INFO)

### 데이터 초기화
기존 `model-chatbot`의 ChromaDB 데이터가 자동으로 복사됩니다:
- 소스: `../application-tier/models/model-chatbot/data/chroma_db`
- 대상: Docker 볼륨 `chromadb_data`

## 💾 백업 & 복원

### 백업 생성
```bash
./chromadb/scripts/backup-chromadb.sh
```

### 백업 복원
```bash
# 사용 가능한 백업 목록 확인
./chromadb/scripts/restore-chromadb.sh

# 특정 백업 복원
./chromadb/scripts/restore-chromadb.sh chromadb_backup_20250805_120000.tar.gz
```

## 🧪 테스트

### 연결 테스트
```bash
# Python 스크립트로 테스트
python chromadb/scripts/test-connection.py

# 또는 curl로 간단 테스트
curl http://localhost:8011/api/v1/heartbeat
```

### API 테스트
```bash
# 컬렉션 목록 조회
curl http://localhost:8011/api/v1/collections

# 버전 정보 확인
curl http://localhost:8011/api/v1/version
```

## 📊 모니터링

### 컨테이너 리소스 확인
```bash
docker stats customs-chromadb
```

### 로그 실시간 모니터링
```bash
docker-compose logs -f chromadb
```

### 데이터 볼륨 확인
```bash
docker volume inspect customs-clearance_chromadb_data
```

## 🔗 연동

### application-tier에서 연결
ChromaDB가 `customs-network`에 연결되어 있어 다른 서비스에서 접근 가능:

```python
# Python에서 연결
import chromadb
client = chromadb.HttpClient(host="chromadb", port=8000)  # 내부 네트워크
# 또는 외부에서
client = chromadb.HttpClient(host="localhost", port=8011)
```

### 외부에서 접근
```bash
# 로컬호스트에서 접근
http://localhost:8011
```

## 🛠️ 문제해결

### 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
docker-compose logs chromadb

# 컨테이너 재시작
docker-compose restart chromadb
```

### 데이터가 보이지 않는 경우
```bash
# 볼륨 내용 확인
docker run --rm -v customs-clearance_chromadb_data:/data busybox ls -la /data

# 권한 문제 해결
docker-compose exec chromadb chown -R chromadb:chromadb /chroma/chroma
```

### 포트 충돌 해결
`.env` 파일에서 `CHROMA_SERVER_HTTP_PORT` 변경 후 재시작

## 📋 유용한 명령어

```bash
# 전체 스택 시작 (MySQL, Neo4j, ChromaDB)
docker-compose up -d

# ChromaDB만 재시작
docker-compose restart chromadb

# ChromaDB 컨테이너 접속
docker-compose exec chromadb sh

# 데이터 볼륨 삭제 (주의!)
docker-compose down -v
```