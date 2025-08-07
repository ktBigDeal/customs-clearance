#!/bin/bash

# ChromaDB Docker 서비스 테스트 스크립트 (공식 이미지용)
set -e

echo "🧪 ChromaDB Docker 서비스 테스트"
echo "================================"

# 현재 디렉토리 확인
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml 파일을 찾을 수 없습니다."
    echo "   data-tier 디렉토리에서 실행해주세요."
    exit 1
fi

# ChromaDB 서비스 상태 확인
echo "📊 ChromaDB 서비스 상태 확인..."
if docker-compose ps chromadb | grep -q "Up"; then
    echo "✅ ChromaDB 컨테이너가 실행 중입니다."
else
    echo "❌ ChromaDB 컨테이너가 실행되지 않았습니다."
    echo "   다음 명령으로 시작하세요: docker-compose up -d chromadb"
    exit 1
fi

# 헬스체크 대기
echo "⏳ ChromaDB 서비스 준비 대기 중..."
sleep 10

# 연결 테스트
echo "🔍 ChromaDB 연결 테스트..."
for i in {1..5}; do
    if curl -f http://localhost:8011/api/v1/heartbeat > /dev/null 2>&1; then
        echo "✅ ChromaDB 서버 연결 성공!"
        break
    else
        echo "⏳ 연결 시도 $i/5..."
        sleep 3
        if [ $i -eq 5 ]; then
            echo "❌ ChromaDB 서버 연결 실패"
            echo "   로그 확인: docker-compose logs chromadb"
            exit 1
        fi
    fi
done

# 버전 정보 확인
echo "🔍 ChromaDB 버전 확인..."
VERSION_RESPONSE=$(curl -s http://localhost:8011/api/v1/version 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$VERSION_RESPONSE" ]; then
    echo "✅ ChromaDB 버전: $VERSION_RESPONSE"
else
    echo "⚠️ 버전 정보 확인 실패"
fi

# API 기능 테스트
echo "🧪 ChromaDB API 테스트..."
COLLECTIONS_RESPONSE=$(curl -s http://localhost:8011/api/v1/collections 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ ChromaDB API 응답 성공"
    COLLECTION_COUNT=$(echo "$COLLECTIONS_RESPONSE" | grep -o "name" | wc -l)
    echo "   컬렉션 수: $COLLECTION_COUNT"
    if [ $COLLECTION_COUNT -gt 0 ]; then
        echo "   컬렉션 정보: $COLLECTIONS_RESPONSE"
    fi
else
    echo "❌ ChromaDB API 응답 실패"
    exit 1
fi

# 데이터 볼륨 확인
echo "💾 데이터 볼륨 확인..."
VOLUME_INFO=$(docker-compose exec chromadb ls -la /chroma/chroma 2>/dev/null || echo "접근 실패")
if echo "$VOLUME_INFO" | grep -q "chroma.sqlite3"; then
    echo "✅ ChromaDB 데이터 파일 확인됨"
    # SQLite 파일 크기 확인
    SIZE_INFO=$(docker-compose exec chromadb du -h /chroma/chroma/chroma.sqlite3 2>/dev/null || echo "크기 확인 실패")
    echo "   데이터베이스 크기: $SIZE_INFO"
else
    echo "⚠️ ChromaDB 데이터 파일이 없거나 접근 실패"
fi

# 로그 확인 (최근 10줄)
echo "📝 최근 로그 확인..."
docker-compose logs --tail=10 chromadb

echo ""
echo "🎉 ChromaDB Docker 서비스 테스트 완료!"
echo ""
echo "📌 유용한 명령어:"
echo "   - 전체 로그 보기: docker-compose logs chromadb"
echo "   - 컨테이너 접속: docker-compose exec chromadb sh"
echo "   - 서비스 재시작: docker-compose restart chromadb"
echo "   - 백업 실행: ./chromadb/scripts/backup-chromadb.sh"
echo "   - Python 연결 테스트: python chromadb/scripts/test-connection.py"