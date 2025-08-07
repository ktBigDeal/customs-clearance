#!/bin/bash

# 관세 통관 챗봇 시스템 백업 스크립트
# 데이터베이스, 캐시, 설정 파일을 자동으로 백업합니다.

set -euo pipefail

# 설정
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

# 로깅 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
    exit 1
}

# 백업 디렉토리 생성
create_backup_dir() {
    local backup_path="$BACKUP_DIR/$DATE"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# PostgreSQL 백업
backup_postgresql() {
    local backup_path="$1"
    
    log "PostgreSQL 백업 시작..."
    
    # 컨테이너가 실행 중인지 확인
    if ! docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        error "PostgreSQL 컨테이너가 실행되지 않음"
    fi
    
    # 데이터베이스 백업
    docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-conversations}" \
        --verbose \
        --no-owner \
        --no-privileges \
        --clean \
        --if-exists > "$backup_path/postgresql_${DATE}.sql"
    
    # 압축
    gzip "$backup_path/postgresql_${DATE}.sql"
    
    log "PostgreSQL 백업 완료: postgresql_${DATE}.sql.gz"
}

# Redis 백업
backup_redis() {
    local backup_path="$1"
    
    log "Redis 백업 시작..."
    
    # 컨테이너가 실행 중인지 확인
    if ! docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        error "Redis 컨테이너가 실행되지 않음"
    fi
    
    # Redis 스냅샷 생성
    docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli BGSAVE
    
    # 스냅샷 완료 대기
    while [ "$(docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli LASTSAVE)" = "$(docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli LASTSAVE)" ]; do
        sleep 1
    done
    
    # dump.rdb 파일 복사
    docker-compose -f "$COMPOSE_FILE" exec -T redis cat /data/dump.rdb > "$backup_path/redis_${DATE}.rdb"
    
    # 압축
    gzip "$backup_path/redis_${DATE}.rdb"
    
    log "Redis 백업 완료: redis_${DATE}.rdb.gz"
}

# ChromaDB 백업
backup_chromadb() {
    local backup_path="$1"
    
    log "ChromaDB 백업 시작..."
    
    # 컨테이너가 실행 중인지 확인
    if ! docker-compose -f "$COMPOSE_FILE" ps chromadb | grep -q "Up"; then
        error "ChromaDB 컨테이너가 실행되지 않음"
    fi
    
    # ChromaDB 데이터 압축 백업
    docker-compose -f "$COMPOSE_FILE" exec -T chromadb tar -czf - /chroma/chroma > "$backup_path/chromadb_${DATE}.tar.gz"
    
    log "ChromaDB 백업 완료: chromadb_${DATE}.tar.gz"
}

# 설정 파일 백업
backup_configs() {
    local backup_path="$1"
    
    log "설정 파일 백업 시작..."
    
    # 설정 파일들 복사
    cp -r config "$backup_path/" 2>/dev/null || true
    cp docker-compose.yml "$backup_path/" 2>/dev/null || true
    cp .env "$backup_path/env_backup" 2>/dev/null || true
    
    # pyproject.toml 백업
    cp pyproject.toml "$backup_path/" 2>/dev/null || true
    
    log "설정 파일 백업 완료"
}

# 애플리케이션 상태 백업
backup_app_state() {
    local backup_path="$1"
    
    log "애플리케이션 상태 백업 시작..."
    
    # 서비스 상태 정보
    docker-compose -f "$COMPOSE_FILE" ps > "$backup_path/service_status.txt"
    
    # 컨테이너 버전 정보
    docker-compose -f "$COMPOSE_FILE" config > "$backup_path/docker_config.yml"
    
    # 로그 파일들 (최근 1000줄만)
    if [ -d "logs" ]; then
        mkdir -p "$backup_path/logs"
        find logs -name "*.log" -exec sh -c 'tail -1000 "$1" > "'"$backup_path"'/logs/$(basename "$1")"' _ {} \;
    fi
    
    log "애플리케이션 상태 백업 완료"
}

# 백업 메타데이터 생성
create_metadata() {
    local backup_path="$1"
    
    cat > "$backup_path/backup_metadata.json" << EOF
{
    "backup_date": "${DATE}",
    "backup_type": "full",
    "version": "1.0.0",
    "components": {
        "postgresql": true,
        "redis": true,
        "chromadb": true,
        "configs": true,
        "app_state": true
    },
    "retention_days": ${RETENTION_DAYS},
    "environment": "${ENVIRONMENT:-production}",
    "created_by": "backup.sh",
    "hostname": "$(hostname)"
}
EOF
}

# 오래된 백업 정리
cleanup_old_backups() {
    log "오래된 백업 정리 시작 (${RETENTION_DAYS}일 이상)..."
    
    find "$BACKUP_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    
    log "오래된 백업 정리 완료"
}

# 백업 검증
verify_backup() {
    local backup_path="$1"
    
    log "백업 검증 시작..."
    
    local errors=0
    
    # PostgreSQL 백업 검증
    if [ ! -f "$backup_path/postgresql_${DATE}.sql.gz" ]; then
        log "ERROR: PostgreSQL 백업 파일이 없음"
        ((errors++))
    else
        # 압축 파일 무결성 검사
        if ! gzip -t "$backup_path/postgresql_${DATE}.sql.gz"; then
            log "ERROR: PostgreSQL 백업 파일이 손상됨"
            ((errors++))
        fi
    fi
    
    # Redis 백업 검증
    if [ ! -f "$backup_path/redis_${DATE}.rdb.gz" ]; then
        log "ERROR: Redis 백업 파일이 없음"
        ((errors++))
    fi
    
    # ChromaDB 백업 검증
    if [ ! -f "$backup_path/chromadb_${DATE}.tar.gz" ]; then
        log "ERROR: ChromaDB 백업 파일이 없음"
        ((errors++))
    fi
    
    # 메타데이터 검증
    if [ ! -f "$backup_path/backup_metadata.json" ]; then
        log "ERROR: 백업 메타데이터가 없음"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log "백업 검증 성공"
        return 0
    else
        log "백업 검증 실패: ${errors}개 오류"
        return 1
    fi
}

# 백업 알림 (선택적)
send_notification() {
    local status="$1"
    local backup_path="$2"
    
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local message
        if [ "$status" = "success" ]; then
            message="✅ 챗봇 시스템 백업 완료: $(basename "$backup_path")"
        else
            message="❌ 챗봇 시스템 백업 실패: $backup_path"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
             --data "{\"text\":\"$message\"}" \
             "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    if [ -n "${EMAIL_TO:-}" ]; then
        local subject="챗봇 시스템 백업 $status"
        echo "$message" | mail -s "$subject" "$EMAIL_TO" 2>/dev/null || true
    fi
}

# 메인 백업 프로세스
main() {
    log "백업 프로세스 시작: $DATE"
    
    # 백업 디렉토리 생성
    local backup_path
    backup_path=$(create_backup_dir)
    
    # 백업 실행
    local backup_success=true
    
    backup_postgresql "$backup_path" || backup_success=false
    backup_redis "$backup_path" || backup_success=false  
    backup_chromadb "$backup_path" || backup_success=false
    backup_configs "$backup_path" || backup_success=false
    backup_app_state "$backup_path" || backup_success=false
    create_metadata "$backup_path" || backup_success=false
    
    # 백업 검증
    if $backup_success && verify_backup "$backup_path"; then
        log "전체 백업 완료: $backup_path"
        
        # 백업 크기 정보
        local backup_size
        backup_size=$(du -sh "$backup_path" | cut -f1)
        log "백업 크기: $backup_size"
        
        # 오래된 백업 정리
        cleanup_old_backups
        
        # 알림 전송
        send_notification "success" "$backup_path"
        
        exit 0
    else
        log "백업 실패: $backup_path"
        send_notification "failed" "$backup_path"
        exit 1
    fi
}

# 사용법 출력
usage() {
    cat << EOF
사용법: $0 [옵션]

옵션:
  -h, --help                이 도움말 출력
  -d, --backup-dir DIR      백업 디렉토리 지정 (기본값: ./backups)
  -r, --retention DAYS      백업 보관 기간 (기본값: 30일)
  -f, --compose-file FILE   docker-compose 파일 경로 (기본값: docker-compose.yml)
  --dry-run                 실제 백업 없이 테스트 실행

환경 변수:
  BACKUP_DIR                백업 디렉토리
  RETENTION_DAYS            백업 보관 기간
  SLACK_WEBHOOK_URL         Slack 알림 URL
  EMAIL_TO                  이메일 알림 주소

예시:
  $0                        기본 설정으로 백업 실행
  $0 -d /opt/backups -r 60  /opt/backups에 60일간 보관
  $0 --dry-run              테스트 실행

EOF
}

# 명령행 인수 처리
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -d|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -f|--compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --dry-run)
            log "DRY RUN 모드 - 실제 백업은 실행되지 않습니다"
            exit 0
            ;;
        *)
            error "알 수 없는 옵션: $1"
            ;;
    esac
done

# Docker Compose 파일 존재 확인
if [ ! -f "$COMPOSE_FILE" ]; then
    error "Docker Compose 파일을 찾을 수 없음: $COMPOSE_FILE"
fi

# Docker가 실행 중인지 확인
if ! docker info >/dev/null 2>&1; then
    error "Docker가 실행되지 않음"
fi

# 메인 실행
main