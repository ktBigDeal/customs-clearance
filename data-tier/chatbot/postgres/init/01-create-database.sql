-- 관세 통관 챗봇 시스템 - PostgreSQL 초기화 스크립트
-- 대화기록 및 세션 관리를 위한 데이터베이스 스키마

-- 데이터베이스 인코딩 및 로케일 설정 확인
SHOW server_encoding;
SHOW lc_collate;
SHOW lc_ctype;

-- 한국어 텍스트 검색 설정 (필요시)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 대화 세션 테이블
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    last_agent_used VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    extra_metadata JSONB DEFAULT '{}'::jsonb
);

-- 메시지 테이블
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    agent_used VARCHAR(50),
    routing_info JSONB DEFAULT '{}'::jsonb,
    "references" JSONB DEFAULT '[]'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extra_metadata JSONB DEFAULT '{}'::jsonb
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(user_id, is_active, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_time ON messages(conversation_id, timestamp DESC);

-- JSON 필드 특화 인덱스
CREATE INDEX IF NOT EXISTS idx_messages_agent_used ON messages(agent_used) WHERE agent_used IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_routing_info_complexity ON messages USING BTREE (CAST(routing_info->>'complexity' AS FLOAT));

-- 트리거 함수: 대화 테이블 자동 업데이트
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET updated_at = NOW(),
        message_count = message_count + 1
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
DROP TRIGGER IF EXISTS trigger_update_conversation_timestamp ON messages;
CREATE TRIGGER trigger_update_conversation_timestamp
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- 대화 제목 자동 생성 함수
CREATE OR REPLACE FUNCTION generate_conversation_title(content TEXT)
RETURNS VARCHAR(200) AS $$
BEGIN
    -- 첫 번째 메시지 기반으로 제목 생성 (50자 제한)
    IF LENGTH(content) > 50 THEN
        RETURN LEFT(content, 47) || '...';
    ELSE
        RETURN content;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 트리거: 첫 번째 사용자 메시지로 대화 제목 자동 설정
CREATE OR REPLACE FUNCTION set_conversation_title()
RETURNS TRIGGER AS $$
BEGIN
    -- 첫 번째 사용자 메시지인 경우 제목 설정
    IF NEW.role = 'user' AND (
        SELECT message_count FROM conversations WHERE id = NEW.conversation_id
    ) = 1 THEN
        UPDATE conversations 
        SET title = generate_conversation_title(NEW.content)
        WHERE id = NEW.conversation_id AND title = '새 대화';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_conversation_title
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION set_conversation_title();

-- 샘플 데이터 (테스트용)
INSERT INTO conversations (id, user_id, title, created_at) 
VALUES ('sample_conv_001', 1, '딸기 수입 관련 문의', NOW() - INTERVAL '1 day')
ON CONFLICT (id) DO NOTHING;

INSERT INTO messages (id, conversation_id, role, content, agent_used, routing_info, timestamp)
VALUES 
    ('sample_msg_001', 'sample_conv_001', 'user', '딸기를 수입하려고 하는데 필요한 서류가 무엇인가요?', NULL, '{}', NOW() - INTERVAL '1 day'),
    ('sample_msg_002', 'sample_conv_001', 'assistant', '딸기 수입시 필요한 주요 서류는 다음과 같습니다...', 'trade_regulation_agent', '{"complexity": 0.3, "selected_agent": "trade_regulation_agent"}', NOW() - INTERVAL '1 day' + INTERVAL '30 seconds')
ON CONFLICT (id) DO NOTHING;

-- 데이터베이스 통계 업데이트
ANALYZE conversations;
ANALYZE messages;

-- 초기화 완료 로그
INSERT INTO messages (id, conversation_id, role, content, agent_used, timestamp)
SELECT 'system_init_' || EXTRACT(epoch FROM NOW())::text, 'sample_conv_001', 'system', '챗봇 데이터베이스 초기화 완료', 'system', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM messages WHERE role = 'system' AND content LIKE '%초기화 완료%'
);

-- 성공 메시지
DO $$ 
BEGIN 
    RAISE NOTICE '✅ 관세 통관 챗봇 데이터베이스 초기화가 완료되었습니다.';
    RAISE NOTICE '📊 테이블 생성: conversations, messages';
    RAISE NOTICE '🔍 인덱스 생성: 성능 최적화 완료';
    RAISE NOTICE '⚡ 트리거 설정: 자동 업데이트 활성화';
END $$;