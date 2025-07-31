-- Korean Customs Clearance System - Sample Data Migration
-- Version: 3.0
-- Description: Insert sample Korean customs declarations and test data

-- Sample Korean customs declarations
INSERT INTO declarations (
    declaration_number, importer_name, exporter_name, declaration_date, 
    total_value, currency, status, description, country_of_origin, port_of_entry
) VALUES
-- Sample Declaration 1: Electronics Import
('D2024010001', '주식회사 한국전자', 'Samsung Electronics Co., Ltd.', '2024-01-15', 
 15000000.00, 'KRW', 'APPROVED', '스마트폰 및 전자제품', '중국', '인천항'),

-- Sample Declaration 2: Automotive Parts
('D2024010002', '현대자동차부품', 'Hyundai Motor Parts Co.', '2024-01-16', 
 8500000.00, 'KRW', 'CLEARED', '자동차 엔진 부품', '독일', '부산항'),

-- Sample Declaration 3: Fashion Import
('D2024010003', '패션코리아', 'Fashion Italy S.r.l.', '2024-01-17', 
 2200000.00, 'KRW', 'UNDER_REVIEW', '고급 의류 및 액세서리', '이탈리아', '인천국제공항'),

-- Sample Declaration 4: Food Products
('D2024010004', '농협무역', 'California Foods Inc.', '2024-01-18', 
 3800000.00, 'KRW', 'PENDING', '견과류 및 건과일', '미국', '인천항'),

-- Sample Declaration 5: Pharmaceutical
('D2024010005', '대한약품', 'Pfizer Deutschland GmbH', '2024-01-19', 
 12000000.00, 'KRW', 'APPROVED', '의약품 원료', '독일', '인천국제공항'),

-- Sample Declaration 6: Machinery
('D2024010006', '산업기계', 'KOMATSU Ltd.', '2024-01-20', 
 45000000.00, 'KRW', 'REJECTED', '건설장비 및 부품', '일본', '부산항'),

-- Sample Declaration 7: Textiles
('D2024010007', '섬유무역', 'Vietnam Textile Co.', '2024-01-21', 
 6700000.00, 'KRW', 'APPROVED', '면직물 및 원단', '베트남', '인천항'),

-- Sample Declaration 8: Coffee Import
('D2024010008', '커피로스터스', 'Brazilian Coffee Exports', '2024-01-22', 
 1800000.00, 'KRW', 'CLEARED', '원두커피 및 커피제품', '브라질', '부산항');

-- Sample declaration items for the first declaration
INSERT INTO declaration_items (
    declaration_id, item_sequence, hs_code, item_description, 
    quantity, unit_of_measure, unit_price, total_value, country_of_origin
) VALUES
-- Items for Declaration D2024010001 (Electronics)
(1, 1, '8517120000', '스마트폰 갤럭시 S24', 100.000, 'EA', 1200000.00, 120000000.00, '중국'),
(1, 2, '8517700000', '무선 이어폰', 200.000, 'EA', 150000.00, 30000000.00, '중국'),
(1, 3, '8504400000', '휴대폰 충전기', 150.000, 'EA', 80000.00, 12000000.00, '중국');

-- Items for Declaration D2024010002 (Automotive)
INSERT INTO declaration_items (
    declaration_id, item_sequence, hs_code, item_description, 
    quantity, unit_of_measure, unit_price, total_value, country_of_origin
) VALUES
(2, 1, '8708100000', '자동차 범퍼', 50.000, 'EA', 450000.00, 22500000.00, '독일'),
(2, 2, '8708210000', '안전벨트', 100.000, 'EA', 180000.00, 18000000.00, '독일'),
(2, 3, '8708999000', '기타 자동차 부품', 25.000, 'KG', 32000.00, 800000.00, '독일');

-- Sample users for testing (passwords are BCrypt hashed 'password123')
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active) VALUES
('kim.officer', 'kim.officer@customs.gov.kr', '$2a$10$N.zmdr9k7uOCQb1TPa7nMO7ZO5IUQp3blw.YqJyQ8.4zzzIuq0NZ.', '김민수', '', 'OFFICER', true),
('lee.admin', 'lee.admin@customs.gov.kr', '$2a$10$N.zmdr9k7uOCQb1TPa7nMO7ZO5IUQp3blw.YqJyQ8.4zzzIuq0NZ.', '이영희', '', 'ADMIN', true),
('park.user', 'park.user@company.co.kr', '$2a$10$N.zmdr9k7uOCQb1TPa7nMO7ZO5IUQp3blw.YqJyQ8.4zzzIuq0NZ.', '박철수', '', 'USER', true),
('choi.readonly', 'choi.readonly@customs.gov.kr', '$2a$10$N.zmdr9k7uOCQb1TPa7nMO7ZO5IUQp3blw.YqJyQ8.4zzzIuq0NZ.', '최수진', '', 'READONLY', true);

-- Sample documents
INSERT INTO documents (
    declaration_id, filename, original_filename, file_path, file_size, 
    content_type, document_type, uploaded_by
) VALUES
(1, 'invoice_001.pdf', '세금계산서_001.pdf', '/uploads/2024/01/invoice_001.pdf', 2048576, 'application/pdf', 'INVOICE', 1),
(1, 'packing_001.pdf', '포장명세서_001.pdf', '/uploads/2024/01/packing_001.pdf', 1536000, 'application/pdf', 'PACKING_LIST', 1),
(2, 'certificate_002.pdf', '원산지증명서_002.pdf', '/uploads/2024/01/certificate_002.pdf', 1024000, 'application/pdf', 'CERTIFICATE', 2),
(3, 'invoice_003.pdf', '상업송장_003.pdf', '/uploads/2024/01/invoice_003.pdf', 3072000, 'application/pdf', 'INVOICE', 3),
(4, 'permit_004.pdf', '수입허가서_004.pdf', '/uploads/2024/01/permit_004.pdf', 2560000, 'application/pdf', 'PERMIT', 1);

-- Sample audit logs
INSERT INTO audit_logs (
    table_name, record_id, operation, old_values, new_values, changed_by, ip_address, user_agent
) VALUES
('declarations', 1, 'INSERT', NULL, 
 '{"declaration_number": "D2024010001", "status": "PENDING", "importer_name": "주식회사 한국전자"}', 
 1, '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
 
('declarations', 1, 'UPDATE', 
 '{"status": "PENDING"}', 
 '{"status": "APPROVED"}', 
 2, '192.168.1.101', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
 
('declarations', 2, 'INSERT', NULL, 
 '{"declaration_number": "D2024010002", "status": "PENDING", "importer_name": "현대자동차부품"}', 
 2, '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
 
('declarations', 6, 'UPDATE', 
 '{"status": "UNDER_REVIEW"}', 
 '{"status": "REJECTED"}', 
 2, '192.168.1.101', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

-- Additional Korean reference data
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
-- Korean company types
('company_types.corporation', '주식회사', 'STRING', 'Corporation (주식회사)'),
('company_types.limited', '유한회사', 'STRING', 'Limited Company (유한회사)'),
('company_types.partnership', '합명회사', 'STRING', 'Partnership (합명회사)'),
('company_types.individual', '개인사업자', 'STRING', 'Individual Business (개인사업자)'),

-- Common Korean trade terms
('trade_terms.fob', 'FOB (본선인도조건)', 'STRING', 'Free on Board'),
('trade_terms.cif', 'CIF (운임보험료포함조건)', 'STRING', 'Cost, Insurance and Freight'),
('trade_terms.exw', 'EXW (공장인도조건)', 'STRING', 'Ex Works'),
('trade_terms.ddp', 'DDP (관세지급인도조건)', 'STRING', 'Delivered Duty Paid'),

-- Korean units of measure
('units.kg', '킬로그램', 'STRING', 'Kilogram'),
('units.mt', '미터톤', 'STRING', 'Metric Ton'),
('units.ea', '개', 'STRING', 'Each/Piece'),
('units.box', '박스', 'STRING', 'Box'),
('units.carton', '카톤', 'STRING', 'Carton'),
('units.pallet', '팔레트', 'STRING', 'Pallet'),

-- Korean customs procedures
('procedures.general', '일반통관', 'STRING', 'General Customs Clearance'),
('procedures.simplified', '간이통관', 'STRING', 'Simplified Customs Clearance'),
('procedures.bonded', '보세운송', 'STRING', 'Bonded Transportation'),
('procedures.duty_free', '면세통관', 'STRING', 'Duty-Free Clearance'),

-- Korean notification templates
('notifications.approval_subject', '통관 승인 알림', 'STRING', 'Customs Clearance Approval Notification'),
('notifications.rejection_subject', '통관 반려 알림', 'STRING', 'Customs Clearance Rejection Notification'),
('notifications.review_subject', '심사 중 알림', 'STRING', 'Under Review Notification'),

-- Korean error messages
('errors.invalid_hs_code', '유효하지 않은 HS코드입니다', 'STRING', 'Invalid HS Code'),
('errors.missing_document', '필수 서류가 누락되었습니다', 'STRING', 'Required document is missing'),
('errors.value_mismatch', '신고금액이 일치하지 않습니다', 'STRING', 'Declared value does not match'),
('errors.unauthorized_access', '접근 권한이 없습니다', 'STRING', 'Unauthorized access');