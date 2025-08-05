-- 테스트 데이터 삽입
USE customs_clearance;

-- 사용자 데이터
INSERT INTO users (username, email, password, name, role) VALUES
('admin', 'admin@customs.go.kr', 'qwer1234', '관리자', 'ADMIN'),
('officer1', 'officer1@customs.go.kr', 'qwer1234', '김관세', 'OFFICER'),
('user1', 'user1@company.com', 'qwer1234', '홍길동', 'USER');

-- -- 국가 코드 데이터
-- INSERT INTO codes (code_type, code, name_ko, name_en, sort_order) VALUES
-- ('COUNTRY', 'KR', '대한민국', 'Korea, Republic of', 1),
-- ('COUNTRY', 'CN', '중국', 'China', 2),
-- ('COUNTRY', 'JP', '일본', 'Japan', 3),
-- ('COUNTRY', 'US', '미국', 'United States', 4),
-- ('COUNTRY', 'DE', '독일', 'Germany', 5),
-- ('COUNTRY', 'GB', '영국', 'United Kingdom', 6),
-- ('COUNTRY', 'FR', '프랑스', 'France', 7),
-- ('COUNTRY', 'VN', '베트남', 'Vietnam', 8),
-- ('COUNTRY', 'TH', '태국', 'Thailand', 9),
-- ('COUNTRY', 'MY', '말레이시아', 'Malaysia', 10);

-- -- 통화 코드 데이터
-- INSERT INTO codes (code_type, code, name_ko, name_en, sort_order) VALUES
-- ('CURRENCY', 'KRW', '원', 'Korean Won', 1),
-- ('CURRENCY', 'USD', '달러', 'US Dollar', 2),
-- ('CURRENCY', 'EUR', '유로', 'Euro', 3),
-- ('CURRENCY', 'JPY', '엔', 'Japanese Yen', 4),
-- ('CURRENCY', 'CNY', '위안', 'Chinese Yuan', 5);

-- -- HS 코드 예시 데이터
-- INSERT INTO codes (code_type, code, name_ko, name_en, sort_order) VALUES
-- ('HS_CODE', '8471', '컴퓨터', 'Computers', 1),
-- ('HS_CODE', '6203', '남성용 의류', 'Men\'s clothing', 2),
-- ('HS_CODE', '9403', '가구', 'Furniture', 3),
-- ('HS_CODE', '3004', '의약품', 'Medicines', 4),
-- ('HS_CODE', '8703', '승용차', 'Passenger cars', 5);

-- -- 항구 코드 데이터
-- INSERT INTO codes (code_type, code, name_ko, name_en, sort_order) VALUES
-- ('PORT', 'KRPUS', '부산항', 'Busan Port', 1),
-- ('PORT', 'KRICN', '인천항', 'Incheon Port', 2),
-- ('PORT', 'KRPTK', '평택항', 'Pyeongtaek Port', 3),
-- ('PORT', 'KRGIM', '김포공항', 'Gimpo Airport', 4),
-- ('PORT', 'KRICX', '인천공항', 'Incheon Airport', 5);

-- 테스트 신고서 데이터
INSERT INTO declarations (
    declaration_number, declaration_type, status, created_by, updated_by
) VALUES
('D2024010001', 'IMPORT', 'SUBMITTED', 3, 3),
 
('D2024010002', 'EXPORT', 'UNDER_REVIEW', 3, 3),
 
('D2024010003', 'IMPORT', 'APPROVED', 3, 3);

-- 신고서 이력 데이터
-- INSERT INTO declaration_history (declaration_id, action, old_status, new_status, comment, created_by) VALUES
-- (1, 'CREATE', NULL, 'DRAFT', '신고서 생성', 3),
-- (1, 'SUBMIT', 'DRAFT', 'SUBMITTED', '신고서 제출', 3),
-- (2, 'CREATE', NULL, 'DRAFT', '신고서 생성', 3),
-- (2, 'SUBMIT', 'DRAFT', 'SUBMITTED', '신고서 제출', 3),
-- (2, 'REVIEW', 'SUBMITTED', 'UNDER_REVIEW', '검토 시작', 2),
-- (3, 'CREATE', NULL, 'DRAFT', '신고서 생성', 3),
-- (3, 'SUBMIT', 'DRAFT', 'SUBMITTED', '신고서 제출', 3),
-- (3, 'APPROVE', 'SUBMITTED', 'APPROVED', '서류 검토 완료 후 승인', 2);