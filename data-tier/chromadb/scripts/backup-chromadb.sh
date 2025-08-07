#!/bin/bash

# ChromaDB 백업 스크립트 (Docker 볼륨용)
set -e

CONTAINER_NAME="customs-chromadb"
BACKUP_DIR="./chromadb/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="chromadb_backup_${TIMESTAMP}"

echo "🔄 ChromaDB Docker 볼륨 백업 시작..."

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# 컨테이너 실행 상태 확인
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ ChromaDB 컨테이너가 실행되지 않았습니다."
    echo "   docker-compose up -d chromadb 로 시작해주세요."
    exit 1
fi

# Docker 볼륨에서 백업 생성
echo "📦 백업 생성 중: $BACKUP_NAME"
docker run --rm \
    --volumes-from "$CONTAINER_NAME" \
    -v "$(pwd)/$BACKUP_DIR:/backup" \
    busybox \
    tar czf "/backup/${BACKUP_NAME}.tar.gz" -C /chroma/chroma .

# 백업 검증
if [ -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" ]; then
    echo "✅ 백업 생성 완료: ${BACKUP_NAME}.tar.gz"
    
    # 백업 파일 크기 출력
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    echo "📊 백업 크기: $BACKUP_SIZE"
else
    echo "❌ 백업 생성 실패!"
    exit 1
fi

# 오래된 백업 정리 (7일 이상)
echo "🧹 오래된 백업 정리 중..."
find "$BACKUP_DIR" -name "chromadb_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
echo "✅ 정리 완료"

# 현재 백업 목록
echo "📋 현재 백업 목록:"
ls -lh "$BACKUP_DIR"/chromadb_backup_*.tar.gz 2>/dev/null || echo "백업 파일이 없습니다."