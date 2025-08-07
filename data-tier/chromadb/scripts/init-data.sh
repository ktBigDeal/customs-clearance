#!/bin/bash

# ChromaDB 초기 데이터 설정 스크립트
set -e

DATA_DIR=${CHROMA_DB_PATH:-/app/data}
SOURCE_DATA_DIR=${SOURCE_DATA_DIR:-/app/source-data}

echo "🔧 ChromaDB 초기 데이터 설정..."

# 소스 데이터 디렉토리 확인
if [ -d "$SOURCE_DATA_DIR" ] && [ "$(ls -A $SOURCE_DATA_DIR)" ]; then
    echo "✅ 소스 데이터 발견: $SOURCE_DATA_DIR"
    
    # 기존 데이터가 없는 경우에만 복사
    if [ ! -f "$DATA_DIR/chroma.sqlite3" ]; then
        echo "📂 기존 ChromaDB 데이터를 복사 중..."
        
        # 데이터 복사
        cp -r "$SOURCE_DATA_DIR"/* "$DATA_DIR/"
        
        # 권한 설정
        chown -R chromadb:chromadb "$DATA_DIR"
        chmod -R 755 "$DATA_DIR"
        
        echo "✅ 데이터 복사 완료"
        
        # 데이터 검증
        if sqlite3 "$DATA_DIR/chroma.sqlite3" "SELECT COUNT(*) FROM collections;" > /dev/null 2>&1; then
            COLLECTION_COUNT=$(sqlite3 "$DATA_DIR/chroma.sqlite3" "SELECT COUNT(*) FROM collections;")
            echo "✅ 데이터 검증 완료 - 컬렉션 수: $COLLECTION_COUNT"
        else
            echo "⚠️ 경고: 데이터 검증 실패, 하지만 계속 진행..."
        fi
    else
        echo "ℹ️ 기존 데이터가 이미 존재합니다. 건너뜀."
    fi
else
    echo "ℹ️ 소스 데이터가 없습니다. 빈 데이터베이스로 시작합니다."
fi

# 데이터 디렉토리 구조 출력
echo "📊 데이터 디렉토리 현황:"
ls -la "$DATA_DIR" || echo "데이터 디렉토리가 비어있습니다."

echo "✅ 초기 데이터 설정 완료"