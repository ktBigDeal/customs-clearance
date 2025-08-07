#!/bin/bash

# ChromaDB 복원 스크립트 (Docker 볼륨용)
set -e

CONTAINER_NAME="customs-chromadb"
BACKUP_DIR="./chromadb/backups"

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

echo "🔄 ChromaDB Docker 볼륨 복원 시작..."
echo "📁 백업 파일: $BACKUP_FILE"

# 컨테이너가 실행 중이면 중지
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "⏸️ ChromaDB 컨테이너 중지 중..."
    docker-compose stop chromadb
fi

# 기존 데이터 안전 백업
SAFETY_BACKUP="chromadb_safety_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "🛡️ 기존 데이터 안전 백업: $SAFETY_BACKUP"
docker run --rm \
    -v customs-clearance_chromadb_data:/data \
    -v "$(pwd)/$BACKUP_DIR:/backup" \
    busybox \
    tar czf "/backup/$SAFETY_BACKUP" -C /data . 2>/dev/null || echo "기존 데이터 없음"

# 기존 볼륨 데이터 삭제
echo "🗑️ 기존 볼륨 데이터 삭제..."
docker run --rm \
    -v customs-clearance_chromadb_data:/data \
    busybox \
    sh -c "rm -rf /data/*"

# 백업에서 복원
echo "📦 백업 복원 중..."
docker run --rm \
    -v customs-clearance_chromadb_data:/data \
    -v "$(pwd)/$BACKUP_DIR:/backup" \
    busybox \
    tar xzf "/backup/$BACKUP_FILE" -C /data

echo "✅ 복원 완료!"

# ChromaDB 컨테이너 재시작
echo "🚀 ChromaDB 컨테이너 재시작..."
docker-compose up -d chromadb

# 복원 검증 대기
echo "⏳ 서비스 준비 대기 중..."
sleep 10

# 복원 검증
if curl -f http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
    echo "✅ 복원 검증 성공!"
    echo "🎉 ChromaDB 복원이 성공적으로 완료되었습니다."
else
    echo "❌ 복원 검증 실패"
    echo "   로그 확인: docker-compose logs chromadb"
fi