#!/bin/bash

set -e

echo "🚀 Starting ChromaDB Server..."

# 환경변수 설정
export CHROMA_HOST=${CHROMA_HOST:-0.0.0.0}
export CHROMA_PORT=${CHROMA_PORT:-8000}
export CHROMA_DB_PATH=${CHROMA_DB_PATH:-/app/data}
export CHROMA_LOG_LEVEL=${CHROMA_LOG_LEVEL:-INFO}

# 데이터 디렉토리 권한 확인
if [ ! -w "$CHROMA_DB_PATH" ]; then
    echo "❌ Error: Cannot write to data directory: $CHROMA_DB_PATH"
    echo "   Please check volume mount permissions"
    exit 1
fi

# 로그 디렉토리 생성
mkdir -p /app/logs

# 기존 데이터 확인
if [ -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
    echo "✅ Found existing ChromaDB data"
    
    # 데이터 무결성 체크
    if sqlite3 "$CHROMA_DB_PATH/chroma.sqlite3" "SELECT COUNT(*) FROM collections;" > /dev/null 2>&1; then
        echo "✅ Database integrity check passed"
    else
        echo "⚠️ Warning: Database integrity check failed, but continuing..."
    fi
else
    echo "ℹ️ No existing data found, will create new database"
fi

# 헬스체크 엔드포인트 확인 스크립트
cat > /app/healthcheck.py << 'EOF'
#!/usr/bin/env python3
import requests
import sys
import os

try:
    port = os.environ.get('CHROMA_PORT', '8000')
    response = requests.get(f'http://localhost:{port}/api/v1/heartbeat', timeout=5)
    if response.status_code == 200:
        print("✅ ChromaDB health check passed")
        sys.exit(0)
    else:
        print(f"❌ ChromaDB health check failed: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ ChromaDB health check failed: {e}")
    sys.exit(1)
EOF

chmod +x /app/healthcheck.py

echo "🔧 Configuration:"
echo "   Host: $CHROMA_HOST"
echo "   Port: $CHROMA_PORT" 
echo "   Data Path: $CHROMA_DB_PATH"
echo "   Log Level: $CHROMA_LOG_LEVEL"

# ChromaDB 서버 시작
echo "▶️ Starting ChromaDB server..."
exec "$@"