-- Korean Customs Clearance System - Reference Data Migration
-- Version: 2.0
-- Description: Insert reference data and default system settings

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('system.version', '1.0.0', 'STRING', 'System version'),
('system.maintenance_mode', 'false', 'BOOLEAN', 'System maintenance mode flag'),
('system.max_file_size', '10485760', 'NUMBER', 'Maximum file upload size in bytes (10MB)'),
('system.supported_file_types', '["pdf","jpg","jpeg","png","doc","docx","xls","xlsx"]', 'JSON', 'Supported file types for document upload'),
('system.session_timeout', '1800', 'NUMBER', 'Session timeout in seconds (30 minutes)'),
('system.default_currency', 'KRW', 'STRING', 'Default currency for declarations'),
('system.default_timezone', 'Asia/Seoul', 'STRING', 'Default timezone for the system'),
('notification.email_enabled', 'true', 'BOOLEAN', 'Enable email notifications'),
('notification.sms_enabled', 'false', 'BOOLEAN', 'Enable SMS notifications'),
('security.password_min_length', '8', 'NUMBER', 'Minimum password length'),
('security.password_require_special_chars', 'true', 'BOOLEAN', 'Require special characters in password'),
('security.max_login_attempts', '5', 'NUMBER', 'Maximum login attempts before account lockout'),
('security.account_lockout_duration', '900', 'NUMBER', 'Account lockout duration in seconds (15 minutes)'),
('customs.default_processing_days', '5', 'NUMBER', 'Default processing time for declarations in business days'),
('customs.auto_approve_threshold', '1000000', 'NUMBER', 'Auto-approval threshold in KRW'),
('integration.external_api_timeout', '30000', 'NUMBER', 'External API timeout in milliseconds'),
('integration.retry_attempts', '3', 'NUMBER', 'Number of retry attempts for failed API calls');

-- Insert default admin user (password: admin123! - should be changed in production)
-- Password hash is BCrypt encoded
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active) VALUES
('admin', 'admin@customs.gov.kr', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.', '관리자', '시스템', 'ADMIN', true),
('officer1', 'officer1@customs.gov.kr', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.', '김철수', '관리관', 'OFFICER', true),
('user1', 'user1@example.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.', '이영희', '신고자', 'USER', true);

-- Insert some sample Korean ports of entry
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('ports.busan', '부산항', 'STRING', 'Busan Port'),
('ports.incheon', '인천항', 'STRING', 'Incheon Port'),
('ports.pyeongtaek', '평택항', 'STRING', 'Pyeongtaek Port'),
('ports.ulsan', '울산항', 'STRING', 'Ulsan Port'),
('ports.gunsan', '군산항', 'STRING', 'Gunsan Port'),
('ports.mokpo', '목포항', 'STRING', 'Mokpo Port'),
('airports.icn', '인천국제공항', 'STRING', 'Incheon International Airport'),
('airports.gimpo', '김포국제공항', 'STRING', 'Gimpo International Airport'),
('airports.gimhae', '김해국제공항', 'STRING', 'Gimhae International Airport'),
('airports.jeju', '제주국제공항', 'STRING', 'Jeju International Airport');

-- Insert common Korean trading partner countries
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('countries.china', '중국', 'STRING', 'China'),
('countries.japan', '일본', 'STRING', 'Japan'),
('countries.usa', '미국', 'STRING', 'United States'),
('countries.germany', '독일', 'STRING', 'Germany'),
('countries.vietnam', '베트남', 'STRING', 'Vietnam'),
('countries.taiwan', '대만', 'STRING', 'Taiwan'),
('countries.singapore', '싱가포르', 'STRING', 'Singapore'),
('countries.thailand', '태국', 'STRING', 'Thailand'),
('countries.malaysia', '말레이시아', 'STRING', 'Malaysia'),
('countries.indonesia', '인도네시아', 'STRING', 'Indonesia'),
('countries.philippines', '필리핀', 'STRING', 'Philippines'),
('countries.india', '인도', 'STRING', 'India');

-- Insert common currencies
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('currencies.krw', '원', 'STRING', 'Korean Won'),
('currencies.usd', '달러', 'STRING', 'US Dollar'),
('currencies.eur', '유로', 'STRING', 'Euro'),
('currencies.jpy', '엔', 'STRING', 'Japanese Yen'),
('currencies.cny', '위안', 'STRING', 'Chinese Yuan'),
('currencies.gbp', '파운드', 'STRING', 'British Pound');

-- Insert common HS codes for reference
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('hs_codes.8471', '컴퓨터 및 전자제품', 'STRING', 'Computers and electronic equipment'),
('hs_codes.8517', '통신장비', 'STRING', 'Telecommunications equipment'),
('hs_codes.8708', '자동차 부품', 'STRING', 'Automotive parts'),
('hs_codes.3004', '의약품', 'STRING', 'Pharmaceutical products'),
('hs_codes.6403', '신발', 'STRING', 'Footwear'),
('hs_codes.6204', '의류', 'STRING', 'Clothing'),
('hs_codes.0901', '커피', 'STRING', 'Coffee'),
('hs_codes.2106', '식품 첨가물', 'STRING', 'Food additives'),
('hs_codes.8501', '전동기', 'STRING', 'Electric motors'),
('hs_codes.8536', '전기 장치', 'STRING', 'Electrical apparatus');