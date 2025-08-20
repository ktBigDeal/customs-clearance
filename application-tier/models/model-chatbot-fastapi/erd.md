# Model-Chatbot-FastAPI ERD 문서

## 개요
이 문서는 Model-Chatbot-FastAPI 서비스에서 사용하는 PostgreSQL 데이터베이스 테이블들의 ERD(Entity Relationship Diagram)를 제공합니다.

## 데이터베이스 정보
- **데이터베이스**: PostgreSQL
- **포트**: 5433 (Docker 환경)
- **스키마**: conversations
- **ORM**: SQLAlchemy (비동기 지원)

## 테이블 구조

### 1. conversations (대화 세션)
대화 세션의 기본 정보를 저장하는 메인 테이블입니다.

| 컬럼명 | 데이터 타입 | 제약조건 | 설명 |
|--------|-------------|----------|------|
| id | VARCHAR(50) | PRIMARY KEY | 대화 세션 고유 ID (예: conv_abc123def456) |
| user_id | INTEGER | NOT NULL, INDEX | 사용자 식별자 |
| title | VARCHAR(200) | NOT NULL | 대화 제목 (첫 메시지 기반 자동 생성) |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 대화 생성 시간 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW(), AUTO UPDATE | 대화 마지막 업데이트 시간 |
| message_count | INTEGER | DEFAULT 0 | 대화 내 메시지 총 개수 |
| last_agent_used | VARCHAR(50) | NULL | 마지막으로 사용된 AI 에이전트 |
| is_active | BOOLEAN | DEFAULT true | 대화 활성 상태 |
| extra_metadata | JSONB | DEFAULT '{}' | 추가 메타데이터 (JSON 형태) |

### 2. messages (메시지)
대화 내 개별 메시지를 저장하는 테이블입니다.

| 컬럼명 | 데이터 타입 | 제약조건 | 설명 |
|--------|-------------|----------|------|
| id | VARCHAR(50) | PRIMARY KEY | 메시지 고유 ID (예: msg_abc123def456) |
| conversation_id | VARCHAR(50) | NOT NULL, FK, INDEX | 소속 대화 세션 ID |
| role | VARCHAR(20) | NOT NULL, CHECK | 메시지 역할 (user/assistant/system) |
| content | TEXT | NOT NULL | 메시지 내용 |
| agent_used | VARCHAR(50) | NULL, INDEX | 사용된 AI 에이전트 타입 |
| routing_info | JSONB | DEFAULT '{}' | AI 라우팅 정보 (복잡도, 선택 이유 등) |
| references | JSONB | DEFAULT '[]' | 참조 문서 정보 배열 |
| timestamp | TIMESTAMP WITH TIME ZONE | DEFAULT NOW(), INDEX | 메시지 생성 시간 |
| extra_metadata | JSONB | DEFAULT '{}' | 추가 메타데이터 |

## 관계도 (ERD)

```
┌─────────────────────────────────────┐
│           conversations             │
├─────────────────────────────────────┤
│ 🔑 id (VARCHAR(50)) PK              │
│    user_id (INTEGER) NOT NULL       │
│    title (VARCHAR(200)) NOT NULL    │
│    created_at (TIMESTAMPTZ)         │
│    updated_at (TIMESTAMPTZ)         │
│    message_count (INTEGER)          │
│    last_agent_used (VARCHAR(50))    │
│    is_active (BOOLEAN)              │
│    extra_metadata (JSONB)           │
└─────────────────────────────────────┘
                    │
                    │ 1:N (CASCADE DELETE)
                    │
                    ▼
┌─────────────────────────────────────┐
│             messages                │
├─────────────────────────────────────┤
│ 🔑 id (VARCHAR(50)) PK              │
│ 🔗 conversation_id (VARCHAR(50)) FK │
│    role (VARCHAR(20)) NOT NULL      │
│    content (TEXT) NOT NULL          │
│    agent_used (VARCHAR(50))         │
│    routing_info (JSONB)             │
│    references (JSONB)               │
│    timestamp (TIMESTAMPTZ)          │
│    extra_metadata (JSONB)           │
└─────────────────────────────────────┘
```

## 관계 설명

### 1:N 관계 (conversations → messages)
- **관계 유형**: 일대다 (One-to-Many)
- **외래키**: messages.conversation_id → conversations.id
- **CASCADE 삭제**: 대화가 삭제되면 관련된 모든 메시지도 함께 삭제
- **SQLAlchemy 관계**: `relationship("MessageORM", back_populates="conversation", cascade="all, delete-orphan")`

## 인덱스 구조

### conversations 테이블 인덱스
```sql
-- 기본 인덱스
PRIMARY KEY: id

-- 성능 최적화 인덱스
idx_conversations_user_id: user_id
idx_conversations_updated_at: updated_at DESC
idx_conversations_active: (user_id, is_active, updated_at DESC)  -- 복합 인덱스
```

### messages 테이블 인덱스
```sql
-- 기본 인덱스
PRIMARY KEY: id
FOREIGN KEY: conversation_id → conversations.id

-- 성능 최적화 인덱스
idx_messages_conversation_id: conversation_id
idx_messages_timestamp: timestamp DESC
idx_messages_conversation_time: (conversation_id, timestamp DESC)  -- 복합 인덱스
idx_messages_agent_used: agent_used (WHERE agent_used IS NOT NULL)

-- JSONB 필드 인덱스
idx_routing_info_complexity: BTREE(CAST(routing_info->>'complexity' AS FLOAT))
```

## 트리거 및 자동화

### 1. 대화 업데이트 시간 자동 갱신
```sql
-- 트리거 함수
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET updated_at = NOW() 
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 등록
CREATE TRIGGER trigger_update_conversation_timestamp
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();
```

### 효과
- 새 메시지가 추가될 때마다 대화의 `updated_at` 필드가 자동으로 현재 시간으로 업데이트
- 대화 목록 정렬 시 최근 활동 기준 정렬 가능

## 데이터 타입 및 제약조건

### CHECK 제약조건
```sql
-- messages.role 필드
CHECK (role IN ('user', 'assistant', 'system'))
```

### JSONB 필드 구조

#### routing_info (메시지 라우팅 정보)
```json
{
  "selected_agent": "law_agent",
  "complexity": 0.75,
  "reasoning": "관세법 관련 질문으로 law_agent가 적합",
  "requires_multiple_agents": false,
  "routing_history": []
}
```

#### references (참조 문서 정보)
```json
[
  {
    "source": "customs_law_doc_001",
    "title": "관세법 제2조 정의",
    "similarity": 0.89,
    "extra_metadata": {
      "chapter": "제1장",
      "article": "제2조"
    }
  }
]
```

#### extra_metadata (확장 메타데이터)
```json
{
  "session_info": {
    "browser": "Chrome",
    "ip_address": "192.168.1.100"
  },
  "processing_time": 1.2,
  "model_version": "gpt-4.1-mini"
}
```

## AI 에이전트 타입

### 지원 에이전트
- **law_agent**: 관세법 전문 상담
- **regulation_agent**: 무역규제 전문 상담  
- **consultation_agent**: 실무 민원 상담

### 에이전트별 통계
messages 테이블의 `agent_used` 필드를 통해 다음 통계 추출 가능:
- 에이전트별 사용 빈도
- 에이전트별 평균 응답 시간
- 에이전트별 사용자 만족도 (참조 문서 수 기준)

## 성능 고려사항

### 쿼리 최적화
1. **대화 목록 조회**: `idx_conversations_active` 복합 인덱스 활용
2. **메시지 조회**: `idx_messages_conversation_time` 복합 인덱스 활용
3. **에이전트별 분석**: `idx_messages_agent_used` 부분 인덱스 활용

### JSONB 성능
- PostgreSQL의 JSONB는 바이너리 형태로 저장되어 JSON보다 빠른 검색 성능
- GIN 인덱스를 통한 JSONB 필드 전문검색 가능 (필요시 추가)

### 확장성
- **Partitioning**: 메시지 테이블이 대용량화될 경우 날짜 기준 파티셔닝 고려
- **Sharding**: 사용자별 샤딩으로 수평 확장 가능
- **Read Replica**: 조회 전용 복제본을 통한 읽기 성능 향상

## 마이그레이션 및 백업

### 데이터 마이그레이션
```sql
-- 대화 데이터 내보내기
COPY conversations TO '/tmp/conversations_backup.csv' DELIMITER ',' CSV HEADER;
COPY messages TO '/tmp/messages_backup.csv' DELIMITER ',' CSV HEADER;

-- 대화 데이터 가져오기
COPY conversations FROM '/tmp/conversations_backup.csv' DELIMITER ',' CSV HEADER;
COPY messages FROM '/tmp/messages_backup.csv' DELIMITER ',' CSV HEADER;
```

### 백업 전략
- **일간 백업**: pg_dump를 통한 전체 데이터베이스 백업
- **실시간 백업**: WAL(Write-Ahead Logging) 기반 연속 백업
- **포인트인타임 복구**: 특정 시점으로의 데이터 복구 지원

## 모니터링 및 관리

### 성능 모니터링 쿼리
```sql
-- 가장 활발한 사용자 TOP 10
SELECT user_id, COUNT(*) as conversation_count, 
       MAX(updated_at) as last_activity
FROM conversations 
WHERE is_active = true
GROUP BY user_id 
ORDER BY conversation_count DESC 
LIMIT 10;

-- 에이전트별 사용 통계
SELECT agent_used, COUNT(*) as usage_count,
       AVG(CAST(routing_info->>'complexity' AS FLOAT)) as avg_complexity
FROM messages 
WHERE agent_used IS NOT NULL
GROUP BY agent_used
ORDER BY usage_count DESC;

-- 대화당 평균 메시지 수
SELECT AVG(message_count) as avg_messages_per_conversation
FROM conversations;
```

### 정리 작업
```sql
-- 비활성 대화 정리 (90일 이상 비활성)
DELETE FROM conversations 
WHERE is_active = false 
  AND updated_at < NOW() - INTERVAL '90 days';

-- 빈 대화 정리 (메시지가 없는 대화)
DELETE FROM conversations 
WHERE message_count = 0 
  AND created_at < NOW() - INTERVAL '7 days';
```

이 ERD는 Model-Chatbot-FastAPI의 대화 관리 시스템을 위한 완전한 데이터베이스 설계를 제공하며, AI 에이전트 기반 챗봇 서비스의 모든 요구사항을 충족하도록 구성되었습니다.