-- Korean Customs Clearance System - Users Table Update
-- Version: 4.0
-- Description: Rename last_login_at column to last_login

-- Rename last_login_at column to last_login if it exists
ALTER TABLE users 
CHANGE COLUMN last_login_at last_login TIMESTAMP NULL COMMENT '마지막 로그인 시간';

-- Add index for better query performance on last_login column
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);