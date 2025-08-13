-- 시스템 로그 테이블 생성
-- 작성자: Backend Team
-- 작성일: 2025-08-13
-- 목적: 관리자가 시스템 활동 및 오류를 모니터링할 수 있도록 로그 데이터를 저장

CREATE TABLE system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '로그 고유 ID',
    
    -- 기본 로그 정보
    timestamp DATETIME NOT NULL COMMENT '로그 발생 시간',
    level ENUM('DEBUG', 'INFO', 'WARN', 'ERROR') NOT NULL DEFAULT 'INFO' COMMENT '로그 레벨',
    source VARCHAR(50) COMMENT '로그 소스 (AUTH, SYSTEM, API, DOCUMENT, CHAT 등)',
    message TEXT COMMENT '로그 메시지',
    
    -- 사용자 관련 정보
    user_id BIGINT COMMENT '관련 사용자 ID',
    user_name VARCHAR(100) COMMENT '사용자명',
    
    -- 요청 관련 정보  
    ip_address VARCHAR(45) COMMENT '클라이언트 IP 주소 (IPv6 지원을 위해 45자)',
    user_agent VARCHAR(500) COMMENT '사용자 에이전트 정보',
    request_uri VARCHAR(500) COMMENT '요청 URI',
    http_method VARCHAR(10) COMMENT 'HTTP 메서드 (GET, POST, PUT, DELETE 등)',
    
    -- 성능 관련 정보
    status_code INT COMMENT 'HTTP 응답 상태 코드',
    processing_time BIGINT COMMENT '처리 시간 (밀리초)',
    
    -- 인덱스를 위한 컬럼 정의
    INDEX idx_timestamp (timestamp DESC) COMMENT '시간순 조회를 위한 인덱스',
    INDEX idx_level (level) COMMENT '로그 레벨별 조회를 위한 인덱스', 
    INDEX idx_source (source) COMMENT '소스별 조회를 위한 인덱스',
    INDEX idx_user_id (user_id) COMMENT '사용자별 로그 조회를 위한 인덱스',
    INDEX idx_level_timestamp (level, timestamp DESC) COMMENT '레벨별 시간순 조회 최적화',
    INDEX idx_source_timestamp (source, timestamp DESC) COMMENT '소스별 시간순 조회 최적화',
    
    -- 외래키 제약조건 (users 테이블과 연결)
    CONSTRAINT fk_system_logs_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='시스템 활동 및 오류 로그를 저장하는 테이블';

-- 샘플 데이터 삽입 (개발/테스트 환경용)
INSERT INTO system_logs (timestamp, level, source, message, user_id, user_name, ip_address, user_agent, request_uri, http_method, status_code, processing_time) VALUES
-- 인증 관련 로그
(NOW() - INTERVAL 1 HOUR, 'INFO', 'AUTH', '사용자 로그인 성공', 1, '관리자', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/auth/login', 'POST', 200, 350),
(NOW() - INTERVAL 2 HOUR, 'WARN', 'AUTH', '잘못된 비밀번호로 로그인 시도', NULL, NULL, '192.168.1.105', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/auth/login', 'POST', 401, 180),
(NOW() - INTERVAL 3 HOUR, 'ERROR', 'AUTH', '계정 잠금: 5회 연속 로그인 실패', NULL, NULL, '192.168.1.105', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/auth/login', 'POST', 423, 120),

-- 시스템 관련 로그
(NOW() - INTERVAL 30 MINUTE, 'WARN', 'SYSTEM', '데이터베이스 연결 풀 사용률 80% 초과', NULL, NULL, '127.0.0.1', 'CustomsSystemMonitor/1.0', '/actuator/health', 'GET', 200, 45),
(NOW() - INTERVAL 45 MINUTE, 'INFO', 'SYSTEM', '시스템 정상 상태 확인 완료', NULL, NULL, '127.0.0.1', 'CustomsSystemMonitor/1.0', '/actuator/health', 'GET', 200, 25),
(NOW() - INTERVAL 1 HOUR 15 MINUTE, 'ERROR', 'SYSTEM', '메모리 사용률 95% 초과 - GC 빈발', NULL, NULL, '127.0.0.1', 'CustomsSystemMonitor/1.0', '/actuator/metrics', 'GET', 200, 30),

-- API 관련 로그
(NOW() - INTERVAL 20 MINUTE, 'ERROR', 'API', 'HS코드 조회 API 외부 서버 연결 실패', 2, '김사용자', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/hscode/search', 'GET', 503, 5000),
(NOW() - INTERVAL 35 MINUTE, 'INFO', 'API', 'HS코드 조회 성공: 1234567890', 2, '김사용자', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/hscode/1234567890', 'GET', 200, 280),
(NOW() - INTERVAL 50 MINUTE, 'WARN', 'API', 'API 호출 빈도 제한 임계치 근접', 3, '이담당', '192.168.1.103', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', '/api/v1/declarations', 'GET', 200, 150),

-- 문서 처리 관련 로그
(NOW() - INTERVAL 10 MINUTE, 'INFO', 'DOCUMENT', '수입신고서 업로드 완료: INV-2025-001.pdf', 2, '김사용자', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/declarations/upload', 'POST', 200, 1200),
(NOW() - INTERVAL 25 MINUTE, 'ERROR', 'DOCUMENT', '파일 업로드 실패: 파일 크기 초과 (50MB)', 4, '박업체', '192.168.1.104', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/declarations/upload', 'POST', 413, 500),
(NOW() - INTERVAL 40 MINUTE, 'INFO', 'DOCUMENT', '신고서 검증 완료: D2025010001', 2, '김사용자', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/declarations/validate', 'POST', 200, 800),

-- AI 채팅 관련 로그
(NOW() - INTERVAL 5 MINUTE, 'INFO', 'CHAT', 'AI 챗봇 대화 세션 시작', 2, '김사용자', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/chatbot/chat', 'POST', 200, 450),
(NOW() - INTERVAL 15 MINUTE, 'WARN', 'CHAT', 'AI 응답 생성 시간 초과 (30초)', 2, '김사용자', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', '/api/v1/chatbot/chat', 'POST', 504, 30000),
(NOW() - INTERVAL 55 MINUTE, 'DEBUG', 'CHAT', 'RAG 검색 완료: 관세법 관련 문서 12건 발견', 3, '이담당', '192.168.1.103', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', '/api/v1/chatbot/chat', 'POST', 200, 2800);

-- 통계를 위한 추가 데이터 (지난 일주일간의 로그)
INSERT INTO system_logs (timestamp, level, source, message, ip_address) VALUES
(NOW() - INTERVAL 1 DAY, 'INFO', 'SYSTEM', '일일 백업 작업 완료', '127.0.0.1'),
(NOW() - INTERVAL 1 DAY, 'ERROR', 'SYSTEM', '백업 스토리지 용량 부족 경고', '127.0.0.1'),
(NOW() - INTERVAL 2 DAY, 'WARN', 'API', 'API 응답 지연 감지 (평균 3초)', '127.0.0.1'),
(NOW() - INTERVAL 3 DAY, 'INFO', 'AUTH', '정기 보안 스캔 완료', '127.0.0.1'),
(NOW() - INTERVAL 4 DAY, 'ERROR', 'DOCUMENT', '문서 처리 서비스 일시 중단', '127.0.0.1'),
(NOW() - INTERVAL 5 DAY, 'INFO', 'SYSTEM', '시스템 업데이트 완료 및 재시작', '127.0.0.1'),
(NOW() - INTERVAL 6 DAY, 'WARN', 'AUTH', '비정상적인 로그인 패턴 감지', '192.168.1.200'),
(NOW() - INTERVAL 7 DAY, 'INFO', 'SYSTEM', '주간 성능 보고서 생성 완료', '127.0.0.1');