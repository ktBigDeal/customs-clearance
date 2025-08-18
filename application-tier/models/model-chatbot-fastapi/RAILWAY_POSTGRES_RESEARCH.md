# Railway PostgreSQL 연결 연구

Railway 환경에서 PostgreSQL 연결 방법을 연구합니다.

## 🔍 Railway PostgreSQL 환경변수

Railway에서 PostgreSQL 서비스를 생성하면 다음 환경변수들을 자동으로 제공합니다:

### 기본 환경변수들
```bash
# Railway가 자동으로 제공하는 변수들
DATABASE_URL=postgresql://postgres:password@host:port/railway
PGHOST=containers-us-west-xxx.railway.app
PGPORT=5432
PGDATABASE=railway
PGUSER=postgres
PGPASSWORD=auto-generated-password
```

### 현재 코드의 환경변수 기대값
```python
# app/core/database.py의 DatabaseConfig.__init__()
self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")      # ❌ 불일치
self.postgres_port = int(os.getenv("POSTGRES_PORT", "5433"))      # ❌ 불일치  
self.postgres_db = os.getenv("POSTGRES_DB", "conversations")     # ❌ 불일치
self.postgres_user = os.getenv("POSTGRES_USER", "postgres")      # ❌ 불일치
self.postgres_password = os.getenv("POSTGRES_PASSWORD", "password") # ❌ 불일치
```

## 🎯 문제점 분석

1. **환경변수 이름 불일치**:
   - Railway: `PGHOST`, `PGPORT`, `PGDATABASE` 등
   - 현재 코드: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` 등

2. **기본값 불일치**:
   - Railway: 데이터베이스명 `railway`, 포트 `5432`
   - 현재 코드: 데이터베이스명 `conversations`, 포트 `5433`

3. **DATABASE_URL 미활용**:
   - Railway는 `DATABASE_URL`로 모든 정보를 제공
   - 현재 코드는 개별 환경변수만 사용

## 💡 해결 방안들

### 방안 1: Railway 환경변수를 현재 형식으로 매핑 (추천)

`railway.toml`에서 환경변수 매핑:
```toml
[env]
# Railway 환경변수를 현재 코드 형식으로 매핑
POSTGRES_HOST = "$PGHOST"
POSTGRES_PORT = "$PGPORT"  
POSTGRES_DB = "$PGDATABASE"
POSTGRES_USER = "$PGUSER"
POSTGRES_PASSWORD = "$PGPASSWORD"

# 또는 Railway CLI로 설정
# railway variables set POSTGRES_HOST=$PGHOST
```

### 방안 2: DATABASE_URL 파싱 로직 추가

`database.py`에 DATABASE_URL 지원 추가:
```python
def __init__(self):
    # Railway DATABASE_URL 우선 사용
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        self.postgres_host = parsed.hostname
        self.postgres_port = parsed.port or 5432
        self.postgres_db = parsed.path[1:]  # 첫 번째 '/' 제거
        self.postgres_user = parsed.username
        self.postgres_password = parsed.password
    else:
        # 기존 개별 환경변수 사용 (로컬 환경)
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        # ...
```

### 방안 3: 환경별 설정 분리

Railway와 로컬 환경을 자동 감지하여 다른 설정 사용:
```python
def __init__(self):
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    if is_railway:
        self._setup_railway_postgres()
    else:
        self._setup_local_postgres()
```

## 🧪 테스트 방법

### 1단계: Railway PostgreSQL 정보 확인
```bash
# Railway CLI로 환경변수 확인
railway variables list

# 또는 Railway 대시보드에서 Variables 탭 확인
```

### 2단계: 연결 테스트
```bash
# Railway PostgreSQL에 직접 연결 테스트
psql $DATABASE_URL

# 또는 개별 변수로 연결
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE
```

### 3단계: Python에서 연결 테스트
```python
import asyncpg
import os

async def test_railway_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            conn = await asyncpg.connect(database_url)
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Railway PostgreSQL 연결 성공: {result}")
            await conn.close()
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
```

## 📋 권장 구현 순서

1. **즉시 해결**: 방안 1 - railway.toml에 환경변수 매핑
2. **장기 개선**: 방안 2 - DATABASE_URL 파싱 로직 추가
3. **최종 목표**: 방안 3 - 환경별 자동 설정

이렇게 하면 로컬 환경은 그대로 두고 Railway에서만 PostgreSQL 연결이 가능합니다.