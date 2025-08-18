# Railway PostgreSQL & Redis 연결 설정 가이드

Railway 플랫폼에서 PostgreSQL과 Redis를 연결하는 방법을 설명합니다.

## 🚀 Railway 서비스 생성 순서

### 1단계: PostgreSQL 서비스 생성

1. **Railway Dashboard** → **New Project** → **Provision PostgreSQL**
2. PostgreSQL 서비스가 생성되면 다음 환경변수들이 자동으로 생성됩니다:
   ```bash
   DATABASE_URL=postgresql://postgres:password@host:port/railway
   PGHOST=containers-us-west-xxx.railway.app
   PGPORT=5432
   PGDATABASE=railway
   PGUSER=postgres
   PGPASSWORD=your-generated-password
   ```

### 2단계: Redis 서비스 생성

1. **Railway Dashboard** → **Add Service** → **Database** → **Redis**
2. Redis 서비스가 생성되면 다음 환경변수들이 자동으로 생성됩니다:
   ```bash
   REDIS_URL=redis://default:password@host:port
   REDIS_HOST=containers-us-west-xxx.railway.app
   REDIS_PORT=6379
   REDIS_PASSWORD=your-generated-password
   ```

### 3단계: ChatBot FastAPI 서비스 생성

1. **Railway Dashboard** → **Add Service** → **GitHub Repo**
2. 저장소 선택 후 **Root Directory**: `application-tier/models/model-chatbot-fastapi`
3. **Environment Variables** 설정:

```bash
# 필수 환경변수 (Railway Dashboard에서 설정)
OPENAI_API_KEY=sk-your-openai-api-key
RAILWAY_ENVIRONMENT=true
ENVIRONMENT=production

# PostgreSQL 연결 (자동으로 Railway에서 제공됨)
# DATABASE_URL이 있으면 자동으로 파싱됨

# Redis 연결 (자동으로 Railway에서 제공됨)  
# REDIS_URL이 있으면 자동으로 파싱됨

# ChromaDB 연결 (별도 ChromaDB 서비스와 연결)
CHROMADB_MODE=docker
CHROMADB_HOST=your-chromadb-service.railway.app
CHROMADB_PORT=443
CHROMADB_USE_SSL=true
```

## 🔧 데이터베이스 연결 설정 상세

### PostgreSQL 연결 방식

코드에서 자동으로 Railway 환경을 감지하고 적절한 설정을 적용합니다:

```python
# Railway 환경에서는 DATABASE_URL을 우선 사용
if self.is_railway:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # URL 파싱하여 개별 변수로 분해
        parsed = urlparse(database_url)
        self.postgres_host = parsed.hostname
        self.postgres_port = parsed.port or 5432
        # ...
```

### Redis 연결 방식

```python
# Railway 환경에서는 REDIS_URL을 우선 사용
if redis_url:
    parsed = urlparse(redis_url)
    self.redis_host = parsed.hostname
    self.redis_port = parsed.port or 6379
    self.redis_password = parsed.password
```

### 환경별 연결 풀 최적화

- **Railway 환경**: 보수적인 풀 크기 (메모리 제한 고려)
  - PostgreSQL Pool: 3개 기본, 최대 7개 오버플로우
  - Redis 연결: 최대 8개

- **로컬 환경**: 더 큰 풀 크기
  - PostgreSQL Pool: 10개 기본, 최대 20개 오버플로우
  - Redis 연결: 최대 20개

## 🧪 연결 테스트 방법

### 1. Railway 헬스체크 엔드포인트

```bash
# Railway 헬스체크 (단순한 응답)
curl https://your-chatbot-service.railway.app/health
# 응답: {"status": "healthy"}
```

### 2. 로컬에서 Railway DB 테스트

Railway PostgreSQL에 로컬에서 직접 연결하여 테스트:

```bash
# Railway에서 제공하는 연결 정보 사용
export DATABASE_URL="postgresql://postgres:password@host:port/railway"
export REDIS_URL="redis://default:password@host:port"
export RAILWAY_ENVIRONMENT="true"

# 로컬에서 Railway DB로 연결하여 테스트
python -c "
import asyncio
from app.core.database import db_manager
async def test():
    await db_manager.initialize()
    print('✅ Railway database connection successful!')
    await db_manager.close()
asyncio.run(test())
"
```

## 🔄 마이그레이션 방법

### 기존 로컬 데이터 → Railway DB

1. **로컬 PostgreSQL 덤프 생성**:
```bash
pg_dump -h localhost -p 5433 -U postgres conversations > local_data.sql
```

2. **Railway PostgreSQL로 복원**:
```bash
# Railway 연결 정보 사용
PGPASSWORD=railway-password psql -h railway-host -p 5432 -U postgres -d railway < local_data.sql
```

3. **테이블 생성 자동화**:
   - FastAPI 서비스 시작 시 자동으로 테이블 생성
   - `CREATE_TABLES_SQL`이 실행되어 스키마 구성

## ⚠️ 주의사항 및 모범 사례

### 1. 환경변수 보안
- **민감한 정보**: Railway Dashboard의 Variables 탭에서만 설정
- **공개 저장소**: `.env` 파일이나 설정 파일에 직접 기재 금지

### 2. 연결 풀 관리
- Railway의 메모리 제한을 고려하여 적절한 풀 크기 설정
- 연결 누수 방지를 위한 적절한 타임아웃 설정

### 3. 에러 처리
- Railway에서 일시적 연결 실패에 대한 재시도 로직
- 헬스체크 실패 시 적절한 로깅 및 복구

### 4. 모니터링
- Railway 대시보드에서 CPU/메모리 사용량 모니터링
- PostgreSQL과 Redis 연결 상태 지속적인 확인

## 🔗 관련 링크

- [Railway PostgreSQL 문서](https://docs.railway.app/databases/postgresql)
- [Railway Redis 문서](https://docs.railway.app/databases/redis)
- [FastAPI Database 모범 사례](https://fastapi.tiangolo.com/advanced/async-sql-databases/)