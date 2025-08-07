#!/bin/bash

# ChromaDB 초기 데이터 복사 스크립트 (별도 실행용)
set -e

echo "🔄 ChromaDB 초기 데이터 설정 시작..."

SOURCE_DIR="/chroma/source-data"
TARGET_DIR="/chroma/chroma" 

# 소스 데이터 확인
if [ -d "$SOURCE_DIR" ] && [ "$(ls -A $SOURCE_DIR 2>/dev/null)" ]; then
    echo "✅ 소스 데이터 발견: $SOURCE_DIR"
    
    # 대상 디렉토리에 chroma.sqlite3가 없는 경우에만 복사
    if [ ! -f "$TARGET_DIR/chroma.sqlite3" ]; then
        echo "📂 기존 ChromaDB 데이터 복사 중..."
        
        # 대상 디렉토리 생성
        mkdir -p "$TARGET_DIR"
        
        # 데이터 복사
        cp -r "$SOURCE_DIR"/* "$TARGET_DIR/" 2>/dev/null || {
            echo "⚠️ 일부 파일 복사 실패, 계속 진행..."
        }
        
        echo "✅ 데이터 복사 완료"
        
        # 복사된 파일 목록 출력
        echo "📋 복사된 파일:"
        ls -la "$TARGET_DIR" || echo "디렉토리 접근 실패"
        
    else
        echo "ℹ️ 기존 데이터가 이미 존재합니다. 복사 건너뜀."
    fi
else
    echo "ℹ️ 소스 데이터가 없습니다. 새로운 데이터베이스로 시작합니다."
fi

echo "✅ ChromaDB 초기 설정 완료"