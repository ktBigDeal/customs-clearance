#!/bin/bash

# ChromaDB 백업 스크립트
set -e

BACKUP_DIR=${BACKUP_DIR:-/app/backups}
DATA_DIR=${CHROMA_DB_PATH:-/app/data}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="chromadb_backup_${TIMESTAMP}"

echo "🔄 Starting ChromaDB backup..."

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# 백업 실행
echo "📦 Creating backup: $BACKUP_NAME"
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" -C "$DATA_DIR" .

# 백업 검증
if [ -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" ]; then
    echo "✅ Backup created successfully: ${BACKUP_NAME}.tar.gz"
    
    # 백업 파일 크기 출력
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    echo "📊 Backup size: $BACKUP_SIZE"
else
    echo "❌ Backup failed!"
    exit 1
fi

# 오래된 백업 정리 (7일 이상된 백업 삭제)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "chromadb_backup_*.tar.gz" -mtime +7 -delete
echo "✅ Cleanup completed"

# 백업 목록 출력
echo "📋 Current backups:"
ls -lh "$BACKUP_DIR"/chromadb_backup_*.tar.gz 2>/dev/null || echo "No backups found"