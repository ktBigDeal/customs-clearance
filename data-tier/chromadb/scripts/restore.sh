#!/bin/bash

# ChromaDB 복원 스크립트
set -e

BACKUP_DIR=${BACKUP_DIR:-/app/backups}
DATA_DIR=${CHROMA_DB_PATH:-/app/data}

if [ -z "$1" ]; then
    echo "사용법: $0 <backup_filename>"
    echo ""
    echo "사용 가능한 백업 파일:"
    ls -1 "$BACKUP_DIR"/chromadb_backup_*.tar.gz 2>/dev/null || echo "백업 파일이 없습니다."
    exit 1
fi

BACKUP_FILE="$1"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

if [ ! -f "$BACKUP_PATH" ]; then
    echo "❌ 백업 파일을 찾을 수 없습니다: $BACKUP_PATH"
    exit 1
fi

echo "🔄 ChromaDB 복원 시작..."
echo "📁 백업 파일: $BACKUP_FILE"
echo "📂 복원 위치: $DATA_DIR"

# 기존 데이터 백업 (안전장치)
if [ -f "$DATA_DIR/chroma.sqlite3" ]; then
    SAFETY_BACKUP="$BACKUP_DIR/safety_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    echo "🛡️ 기존 데이터 안전 백업 생성: $(basename $SAFETY_BACKUP)"
    tar -czf "$SAFETY_BACKUP" -C "$DATA_DIR" .
fi

# 기존 데이터 삭제
echo "🗑️ 기존 데이터 삭제..."
rm -rf "$DATA_DIR"/*

# 백업 복원
echo "📦 백업 복원 중..."
tar -xzf "$BACKUP_PATH" -C "$DATA_DIR"

# 복원 검증
if [ -f "$DATA_DIR/chroma.sqlite3" ]; then
    echo "✅ 복원 완료!"
    
    # 데이터베이스 무결성 체크
    if sqlite3 "$DATA_DIR/chroma.sqlite3" "SELECT COUNT(*) FROM collections;" > /dev/null 2>&1; then
        echo "✅ 데이터베이스 무결성 검증 통과"
    else
        echo "⚠️ 경고: 데이터베이스 무결성 검증 실패"
    fi
else
    echo "❌ 복원 실패!"
    exit 1
fi

echo "🎉 ChromaDB 복원이 성공적으로 완료되었습니다."