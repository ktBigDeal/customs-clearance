#!/bin/bash

# 관세 통관 챗봇 시스템 복구 스크립트
# 백업된 데이터를 시스템으로 복구합니다.

set -euo pipefail

# 설정
BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
FORCE_RESTORE="${FORCE_RESTORE:-false}"

# 로깅 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
    exit 1
}

warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >&2
}

# 백업 목록 조회
list_backups() {
    log "사용 가능한 백업 목록:"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        error "백업 디렉토리를 찾을 수 없음: $BACKUP_DIR"
    fi
    
    local count=0
    for backup_path in "$BACKUP_DIR"/*/; do
        if [ -d "$backup_path" ] && [ -f "$backup_path/backup_metadata.json" ]; then
            local backup_name=$(basename "$backup_path")
            local backup_date=$(jq -r '.backup_date // "Unknown"' "$backup_path/backup_metadata.json" 2>/dev/null || echo "Unknown")
            local backup_size=$(du -sh "$backup_path" 2>/dev/null | cut -f1 || echo "Unknown")
            
            echo "  [$((++count))] $backup_name (날짜: $backup_date, 크기: $backup_size)"
        fi
    done
    
    if [ $count -eq 0 ]; then
        error "사용 가능한 백업이 없습니다"
    fi
}

# 백업 유효성 검사
validate_backup() {
    local backup_path="$1"
    
    log "백업 유효성 검사: $(basename "$backup_path")"
    
    # 백업 디렉토리 존재 확인
    if [ ! -d "$backup_path" ]; then
        error "백업 디렉토리를 찾을 수 없음: $backup_path"
    fi
    
    # 메타데이터 파일 확인
    if [ ! -f "$backup_path/backup_metadata.json" ]; then
        error "백업 메타데이터를 찾을 수 없음"
    fi
    
    # 필수 백업 파일들 확인
    local errors=0
    local backup_name=$(basename "$backup_path")
    local date_part="${backup_name}"
    
    # PostgreSQL 백업 파일 찾기
    local pg_backup
    pg_backup=$(find "$backup_path" -name "postgresql_*.sql.gz" | head -1)
    if [ -z "$pg_backup" ]; then
        warning "PostgreSQL 백업 파일을 찾을 수 없음"
        ((errors++))
    else
        # 압축 파일 무결성 검사
        if ! gzip -t "$pg_backup"; then
            error "PostgreSQL 백업 파일이 손상됨: $pg_backup"
        fi
        log "✓ PostgreSQL 백업 파일 확인: $(basename "$pg_backup")"
    fi
    
    # Redis 백업 파일 찾기
    local redis_backup
    redis_backup=$(find "$backup_path" -name "redis_*.rdb.gz" | head -1)
    if [ -z "$redis_backup" ]; then
        warning "Redis 백업 파일을 찾을 수 없음"
        ((errors++))
    else
        log "✓ Redis 백업 파일 확인: $(basename "$redis_backup")"
    fi
    
    # ChromaDB 백업 파일 찾기
    local chroma_backup
    chroma_backup=$(find "$backup_path" -name "chromadb_*.tar.gz" | head -1)
    if [ -z "$chroma_backup" ]; then
        warning "ChromaDB 백업 파일을 찾을 수 없음"
        ((errors++))
    else
        log "✓ ChromaDB 백업 파일 확인: $(basename "$chroma_backup")"
    fi
    
    # 에러가 있어도 강제 복구 옵션이 활성화되면 계속 진행
    if [ $errors -gt 0 ] && [ "$FORCE_RESTORE" != "true" ]; then
        error "백업 검증 실패. --force 옵션을 사용하여 강제 복구할 수 있습니다."
    elif [ $errors -gt 0 ]; then
        warning "백업에 문제가 있지만 강제 복구를 진행합니다."
    fi
    
    log "백업 유효성 검사 완료"
}

# 서비스 중지
stop_services() {
    log "서비스 중지 중..."
    
    docker-compose -f "$COMPOSE_FILE" stop chatbot-api || true
    docker-compose -f "$COMPOSE_FILE" stop postgres || true
    docker-compose -f "$COMPOSE_FILE" stop redis || true  
    docker-compose -f "$COMPOSE_FILE" stop chromadb || true
    
    log "서비스 중지 완료"
}

# 서비스 시작
start_services() {
    log "서비스 시작 중..."
    
    # 데이터베이스부터 시작
    docker-compose -f "$COMPOSE_FILE" up -d postgres
    sleep 5
    
    docker-compose -f "$COMPOSE_FILE" up -d redis
    sleep 3
    
    docker-compose -f "$COMPOSE_FILE" up -d chromadb
    sleep 5
    
    # 애플리케이션 마지막에 시작
    docker-compose -f "$COMPOSE_FILE" up -d chatbot-api
    
    log "서비스 시작 완료"
}

# PostgreSQL 복구
restore_postgresql() {
    local backup_path="$1"
    
    log "PostgreSQL 복구 시작..."
    
    # PostgreSQL 백업 파일 찾기
    local pg_backup
    pg_backup=$(find "$backup_path" -name "postgresql_*.sql.gz" | head -1)
    
    if [ -z "$pg_backup" ]; then
        warning "PostgreSQL 백업 파일을 찾을 수 없음. 건너뜀."
        return
    fi
    
    # PostgreSQL 컨테이너 시작
    docker-compose -f "$COMPOSE_FILE" up -d postgres
    
    # 데이터베이스 준비 대기
    log "PostgreSQL 준비 대기..."
    local retries=30
    while ! docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" >/dev/null 2>&1; do
        if [ $retries -eq 0 ]; then
            error "PostgreSQL이 준비되지 않음"
        fi
        sleep 2
        ((retries--))
    done
    
    # 기존 데이터베이스 삭제 후 재생성 (선택적)
    if [ "$FORCE_RESTORE" = "true" ]; then
        log "기존 데이터베이스 삭제 후 재생성..."
        docker-compose -f "$COMPOSE_FILE" exec -T postgres dropdb -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-conversations}" 2>/dev/null || true
        docker-compose -f "$COMPOSE_FILE" exec -T postgres createdb -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-conversations}"
    fi
    
    # 백업 파일 복구
    log "PostgreSQL 데이터 복구 중..."
    zcat "$pg_backup" | docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-conversations}"
    
    log "PostgreSQL 복구 완료"
}

# Redis 복구
restore_redis() {
    local backup_path="$1"
    
    log "Redis 복구 시작..."
    
    # Redis 백업 파일 찾기
    local redis_backup
    redis_backup=$(find "$backup_path" -name "redis_*.rdb.gz" | head -1)
    
    if [ -z "$redis_backup" ]; then
        warning "Redis 백업 파일을 찾을 수 없음. 건너뜀."
        return
    fi
    
    # Redis 컨테이너 중지
    docker-compose -f "$COMPOSE_FILE" stop redis
    
    # 백업 파일을 임시 디렉토리에 압축 해제
    local temp_rdb="/tmp/restore_dump.rdb"
    zcat "$redis_backup" > "$temp_rdb"
    
    # Redis 데이터 볼륨에 백업 파일 복사
    docker-compose -f "$COMPOSE_FILE" run --rm -v "$temp_rdb:/restore_dump.rdb" redis sh -c "cp /restore_dump.rdb /data/dump.rdb"
    
    # 임시 파일 삭제
    rm -f "$temp_rdb"
    
    # Redis 컨테이너 시작
    docker-compose -f "$COMPOSE_FILE" up -d redis
    
    log "Redis 복구 완료"
}

# ChromaDB 복구
restore_chromadb() {
    local backup_path="$1"
    
    log "ChromaDB 복구 시작..."
    
    # ChromaDB 백업 파일 찾기
    local chroma_backup
    chroma_backup=$(find "$backup_path" -name "chromadb_*.tar.gz" | head -1)
    
    if [ -z "$chroma_backup" ]; then
        warning "ChromaDB 백업 파일을 찾을 수 없음. 건너뜀."
        return
    fi
    
    # ChromaDB 컨테이너 중지
    docker-compose -f "$COMPOSE_FILE" stop chromadb
    
    # 백업 파일 복구
    log "ChromaDB 데이터 복구 중..."
    
    # ChromaDB 볼륨에 백업 데이터 복구
    docker run --rm -v "${PWD}/data/chroma:/chroma/chroma" -v "$chroma_backup:/backup.tar.gz" alpine:latest sh -c "
        cd /chroma && 
        rm -rf chroma/* 2>/dev/null || true &&
        tar -xzf /backup.tar.gz --strip-components=2
    "
    
    # ChromaDB 컨테이너 시작
    docker-compose -f "$COMPOSE_FILE" up -d chromadb
    
    log "ChromaDB 복구 완료"
}

# 설정 파일 복구
restore_configs() {
    local backup_path="$1"
    
    log "설정 파일 복구 시작..."
    
    # 설정 파일들이 있는지 확인
    if [ -d "$backup_path/config" ]; then
        if [ "$FORCE_RESTORE" = "true" ] || [ ! -d "config" ]; then
            cp -r "$backup_path/config" ./
            log "✓ config 디렉토리 복구됨"
        else
            warning "config 디렉토리가 이미 존재함. --force 옵션으로 덮어쓸 수 있습니다."
        fi
    fi
    
    # docker-compose.yml 백업이 있으면 참고용으로 복사
    if [ -f "$backup_path/docker-compose.yml" ]; then
        cp "$backup_path/docker-compose.yml" "./docker-compose.backup.yml"
        log "✓ docker-compose.yml이 docker-compose.backup.yml로 복구됨"
    fi
    
    log "설정 파일 복구 완료"
}

# 복구 후 검증
verify_restore() {
    log "복구 검증 시작..."
    
    # 서비스들이 정상 실행 중인지 확인
    local services=("postgres" "redis" "chromadb" "chatbot-api")
    local errors=0
    
    for service in "${services[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            log "✓ $service 서비스 정상 실행 중"
        else
            warning "✗ $service 서비스가 실행되지 않음"
            ((errors++))
        fi
    done
    
    # API 헬스 체크
    log "API 헬스 체크..."
    local retries=10
    while [ $retries -gt 0 ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log "✓ API 서비스 정상"
            break
        else
            log "API 준비 대기... (남은 시도: $retries)"
            sleep 10
            ((retries--))
        fi
    done
    
    if [ $retries -eq 0 ]; then
        warning "API 서비스 헬스 체크 실패"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log "복구 검증 성공"
        return 0
    else
        warning "복구 검증에서 ${errors}개 문제 발견"
        return 1
    fi
}

# 복구 알림
send_notification() {
    local status="$1"
    local backup_name="$2"
    
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local message
        if [ "$status" = "success" ]; then
            message="✅ 챗봇 시스템 복구 완료: $backup_name"
        else
            message="❌ 챗봇 시스템 복구 실패: $backup_name"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
             --data "{\"text\":\"$message\"}" \
             "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

# 메인 복구 프로세스
main() {
    local backup_path="$1"
    local backup_name=$(basename "$backup_path")
    
    log "복구 프로세스 시작: $backup_name"
    
    # 확인 메시지 (강제 모드가 아닌 경우)
    if [ "$FORCE_RESTORE" != "true" ]; then
        echo ""
        echo "⚠️  복구 작업은 기존 데이터를 덮어씁니다!"
        echo ""
        echo "복구할 백업: $backup_name"
        echo "복구 대상:"
        echo "  - PostgreSQL 데이터베이스"
        echo "  - Redis 캐시 데이터"  
        echo "  - ChromaDB 벡터 데이터"
        echo "  - 설정 파일들"
        echo ""
        read -p "정말 복구하시겠습니까? (yes/no): " confirm
        
        if [ "$confirm" != "yes" ]; then
            log "복구 취소됨"
            exit 0
        fi
    fi
    
    # 백업 검증
    validate_backup "$backup_path"
    
    # 서비스 중지
    stop_services
    
    # 복구 실행
    local restore_success=true
    
    restore_postgresql "$backup_path" || restore_success=false
    restore_redis "$backup_path" || restore_success=false
    restore_chromadb "$backup_path" || restore_success=false
    restore_configs "$backup_path" || restore_success=false
    
    # 서비스 시작
    start_services
    
    # 복구 검증
    sleep 30  # 서비스가 완전히 시작될 때까지 대기
    
    if $restore_success && verify_restore; then
        log "복구 완료: $backup_name"
        send_notification "success" "$backup_name"
        
        echo ""
        echo "🎉 복구가 성공적으로 완료되었습니다!"
        echo ""
        echo "서비스 URL:"
        echo "  - API: http://localhost:8000"
        echo "  - API 문서: http://localhost:8000/docs"
        echo "  - 헬스 체크: http://localhost:8000/health"
        echo ""
        
        exit 0
    else
        log "복구 실패: $backup_name"
        send_notification "failed" "$backup_name"
        
        echo ""
        echo "❌ 복구 중 문제가 발생했습니다."
        echo "로그를 확인하고 수동으로 서비스를 점검해주세요."
        echo ""
        
        exit 1
    fi
}

# 사용법 출력
usage() {
    cat << EOF
사용법: $0 [옵션] <백업경로>

옵션:
  -h, --help                이 도움말 출력
  -l, --list                사용 가능한 백업 목록 조회
  -f, --force               기존 데이터를 강제로 덮어쓰기
  -d, --backup-dir DIR      백업 디렉토리 지정 (기본값: ./backups)
  --compose-file FILE       docker-compose 파일 경로 (기본값: docker-compose.yml)
  --dry-run                 실제 복구 없이 테스트 실행

환경 변수:
  BACKUP_DIR                백업 디렉토리
  FORCE_RESTORE             강제 복구 모드 (true/false)
  SLACK_WEBHOOK_URL         Slack 알림 URL

예시:
  $0 --list                         백업 목록 조회
  $0 ./backups/20250106_143022      특정 백업으로 복구
  $0 -f ./backups/latest            강제 복구
  $0 --dry-run ./backups/test       테스트 실행

EOF
}

# 명령행 인수 처리
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -l|--list)
            list_backups
            exit 0
            ;;
        -f|--force)
            FORCE_RESTORE="true"
            shift
            ;;
        -d|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --dry-run)
            log "DRY RUN 모드 - 실제 복구는 실행되지 않습니다"
            exit 0
            ;;
        -*)
            error "알 수 없는 옵션: $1"
            ;;
        *)
            BACKUP_PATH="$1"
            shift
            ;;
    esac
done

# 백업 경로가 제공되지 않은 경우
if [ -z "${BACKUP_PATH:-}" ]; then
    echo "백업 경로가 제공되지 않았습니다."
    echo ""
    list_backups
    echo ""
    read -p "복구할 백업 디렉토리 이름을 입력하세요: " backup_name
    
    if [ -n "$backup_name" ]; then
        BACKUP_PATH="$BACKUP_DIR/$backup_name"
    else
        error "백업 경로가 제공되지 않았습니다."
    fi
fi

# Docker Compose 파일 존재 확인
if [ ! -f "$COMPOSE_FILE" ]; then
    error "Docker Compose 파일을 찾을 수 없음: $COMPOSE_FILE"
fi

# Docker가 실행 중인지 확인
if ! docker info >/dev/null 2>&1; then
    error "Docker가 실행되지 않음"
fi

# 메인 실행
main "$BACKUP_PATH"