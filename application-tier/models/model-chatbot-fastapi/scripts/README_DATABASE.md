# 데이터베이스 설정 가이드

model-chatbot-fastapi 애플리케이션의 데이터베이스 설정 및 초기화 가이드입니다.

## 📋 데이터베이스 구성

### PostgreSQL (메인 데이터베이스)
- **용도**: 대화 기록, 메시지 저장
- **테이블**: `conversations`, `messages`
- **기능**: 전문검색, JSON 인덱싱, 관계형 데이터 저장

### Redis (캐시 및 세션)
- **용도**: 대화 세션 캐싱, 성능 최적화
- **기능**: 임시 데이터 저장, 빠른 조회

## 🚀 빠른 시작

### 1. 환경변수 설정

`.env` 파일을 생성하고 다음 설정을 추가하세요:

```bash
# PostgreSQL 설정
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=conversations
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis 설정
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 연결 풀 설정 (선택적)
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20
```

### 2. Docker Compose로 데이터베이스 실행

```bash
# PostgreSQL + Redis 실행
docker-compose up -d postgres redis

# 또는 전체 스택 실행
docker-compose up -d
```

### 3. 데이터베이스 테이블 생성

```bash
# 자동 설정 (권장)
python scripts/setup_database.py

# 연결 테스트만
python scripts/setup_database.py --test

# 설정 정보 확인
python scripts/setup_database.py --info
```

## 🛠️ 상세 설정 가이드

### 수동 PostgreSQL 설정

1. **PostgreSQL 설치**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql

# Windows: PostgreSQL 공식 설치 프로그램 사용
```

2. **데이터베이스 및 사용자 생성**
```sql
-- PostgreSQL 콘솔에서 실행
CREATE DATABASE conversations;
CREATE USER chatbot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE conversations TO chatbot_user;

-- 한국어 전문검색을 위한 확장 설치 (필요시)
\c conversations
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

3. **Redis 설치 및 실행**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS (Homebrew)
brew install redis
brew services start redis

# Windows: Redis 공식 바이너리 사용
```

### Docker 환경 설정

`docker-compose.yml` 예시:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: conversations
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 🔍 데이터베이스 구조

### conversations 테이블
```sql
CREATE TABLE conversations (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    last_agent_used VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### messages 테이블
```sql
CREATE TABLE messages (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    agent_used VARCHAR(50),
    routing_info JSONB DEFAULT '{}'::jsonb,
    references JSONB DEFAULT '[]'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### 주요 인덱스
- **검색 성능**: `idx_messages_content_search` (GIN 인덱스)
- **시간 정렬**: `idx_conversations_updated_at`
- **사용자별**: `idx_conversations_active`
- **에이전트별**: `idx_messages_agent_used`

## 🧪 테스트 및 검증

### 1. 연결 테스트
```bash
# 데이터베이스 연결만 확인
python scripts/setup_database.py --test
```

### 2. 헬스체크 API
```bash
# FastAPI 실행 후
curl http://localhost:8000/health/database
```

### 3. 수동 테스트
```python
# Python에서 직접 테스트
from app.utils.database_init import database_health_check
import asyncio

result = asyncio.run(database_health_check())
print(result)
```

## 🚨 트러블슈팅

### 일반적인 문제들

1. **PostgreSQL 연결 실패**
```bash
# 서비스 상태 확인
sudo systemctl status postgresql
sudo systemctl start postgresql

# 연결 권한 확인
sudo -u postgres psql -c "\du"
```

2. **Redis 연결 실패**
```bash
# Redis 서비스 확인
redis-cli ping
# 응답: PONG

# Redis 로그 확인
sudo journalctl -u redis
```

3. **권한 에러**
```sql
-- PostgreSQL에서 권한 부여
GRANT CONNECT ON DATABASE conversations TO chatbot_user;
GRANT USAGE ON SCHEMA public TO chatbot_user;
GRANT CREATE ON SCHEMA public TO chatbot_user;
```

4. **한국어 검색 문제**
```sql
-- 한국어 전문검색 설정 확인
SELECT to_tsvector('korean', '안녕하세요');

-- 확장 설치
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 환경별 설정

#### 개발 환경
- 로컬 PostgreSQL/Redis 사용
- 테이블 자동 생성 활성화
- 디버그 모드 활성화

#### 프로덕션 환경
- 관리형 데이터베이스 서비스 권장
- 백업 및 모니터링 설정
- 연결 풀 최적화
- SSL 연결 활성화

## 📚 추가 리소스

- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Redis 공식 문서](https://redis.io/documentation)
- [SQLAlchemy 비동기 가이드](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI 데이터베이스 가이드](https://fastapi.tiangolo.com/tutorial/databases/)

## 🔧 고급 설정

### 성능 튜닝
```sql
-- PostgreSQL 성능 최적화 (postgresql.conf)
shared_buffers = 256MB
effective_cache_size = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```

### 모니터링 설정
```python
# Prometheus 메트릭 수집을 위한 설정
from prometheus_client import Counter, Histogram

db_connection_counter = Counter('db_connections_total', 'Database connections')
query_duration = Histogram('db_query_duration_seconds', 'Database query duration')
```

### 백업 스크립트
```bash
#!/bin/bash
# PostgreSQL 자동 백업 스크립트
pg_dump -h localhost -U chatbot_user conversations > backup_$(date +%Y%m%d).sql
```