-- 데이터베이스 생성 및 설정
USE customs_clearance;

-- 한글 지원을 위한 문자셋 설정
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 사용자 테이블
-- CREATE TABLE users (
--     id BIGINT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(50) NOT NULL UNIQUE,
--     email VARCHAR(100) NOT NULL UNIQUE,
--     password VARCHAR(255) NOT NULL,
--     name VARCHAR(100) NOT NULL,
--     role ENUM('USER', 'ADMIN', 'OFFICER') DEFAULT 'USER',
--     enabled BOOLEAN DEFAULT TRUE,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `users` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(50) UNIQUE NOT NULL,
  `email` VARCHAR(100) UNIQUE NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `role` ENUM ('USER', 'ADMIN', 'OFFICER') DEFAULT 'USER',
  `enabled` BOOLEAN DEFAULT true,
  `created_at` DATETIME DEFAULT (CURRENT_TIMESTAMP),
  `updated_at` DATETIME DEFAULT (CURRENT_TIMESTAMP)
);

-- 채팅 히스토리 테이블
CREATE TABLE `chattings` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `created_by` BIGINT,
  `updated_by` BIGINT,
  `created_at` DATETIME DEFAULT (CURRENT_TIMESTAMP),
  `updated_at` DATETIME DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE `messages` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `chatting_id` BIGINT,
  `role` ENUM ('USER', 'AI') NOT NULL,
  `contents` TEXT,
  `created_at` DATETIME DEFAULT (CURRENT_TIMESTAMP)
);


-- 신고서 테이블
-- CREATE TABLE declarations (
--     id BIGINT AUTO_INCREMENT PRIMARY KEY,
--     declaration_number VARCHAR(50) NOT NULL UNIQUE,
--     declaration_type ENUM('IMPORT', 'EXPORT', 'TRANSIT') NOT NULL,
--     status ENUM('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'PENDING_DOCUMENTS', 'APPROVED', 'REJECTED', 'CANCELLED', 'CLEARED') DEFAULT 'DRAFT',
--     company_name VARCHAR(200) NOT NULL,
--     declarant_name VARCHAR(100) NOT NULL,
--     declarant_email VARCHAR(100),
--     declarant_phone VARCHAR(20),
--     goods_description TEXT,
--     total_value DECIMAL(15,2),
--     currency VARCHAR(3) DEFAULT 'KRW',
--     weight DECIMAL(10,3),
--     quantity INTEGER,
--     hs_code VARCHAR(20),
--     origin_country VARCHAR(3),
--     destination_country VARCHAR(3),
--     port_of_entry VARCHAR(100),
--     expected_arrival DATETIME,
--     submitted_at DATETIME,
--     processed_at DATETIME,
--     completed_at DATETIME,
--     notes TEXT,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     created_by BIGINT,
--     updated_by BIGINT,
--     INDEX idx_declaration_number (declaration_number),
--     INDEX idx_status (status),
--     INDEX idx_type (declaration_type),
--     INDEX idx_created_at (created_at),
--     FOREIGN KEY (created_by) REFERENCES users(id),
--     FOREIGN KEY (updated_by) REFERENCES users(id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `declarations` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `declaration_number` VARCHAR(50) UNIQUE,
  `declaration_type` ENUM ('IMPORT', 'EXPORT') NOT NULL,
  `status` ENUM ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'PENDING_DOCUMENTS', 'APPROVED', 'REJECTED', 'CANCELLED', 'CLEARED') DEFAULT 'DRAFT',
  `declaration_details` TEXT,
  `notes` TEXT,
  `created_at` DATETIME DEFAULT (CURRENT_TIMESTAMP),
  `updated_at` DATETIME DEFAULT (CURRENT_TIMESTAMP),
  `created_by` BIGINT,
  `updated_by` BIGINT
);

-- 첨부파일 테이블
-- CREATE TABLE attachments (
--     id BIGINT AUTO_INCREMENT PRIMARY KEY,
--     declaration_id BIGINT NOT NULL,
--     filename VARCHAR(255) NOT NULL,
--     original_filename VARCHAR(255) NOT NULL,
--     file_path VARCHAR(500) NOT NULL,
--     file_size BIGINT NOT NULL,
--     content_type VARCHAR(100),
--     uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     uploaded_by BIGINT,
--     FOREIGN KEY (declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
--     FOREIGN KEY (uploaded_by) REFERENCES users(id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `attachments` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `declaration_id` BIGINT NOT NULL,
  `filename` VARCHAR(255) NOT NULL,
  `original_filename` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `file_size` BIGINT NOT NULL,
  `content_type` VARCHAR(100),
  `uploaded_at` DATETIME DEFAULT (CURRENT_TIMESTAMP),
  `uploaded_by` BIGINT
);



-- 신고서 이력 테이블
-- CREATE TABLE declaration_history (
--     id BIGINT AUTO_INCREMENT PRIMARY KEY,
--     declaration_id BIGINT NOT NULL,
--     action VARCHAR(50) NOT NULL,
--     old_status VARCHAR(50),
--     new_status VARCHAR(50),
--     comment TEXT,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     created_by BIGINT,
--     FOREIGN KEY (declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
--     FOREIGN KEY (created_by) REFERENCES users(id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 코드 테이블 (국가, HS코드 등)
-- CREATE TABLE codes (
--     id BIGINT AUTO_INCREMENT PRIMARY KEY,
--     code_type VARCHAR(50) NOT NULL,
--     code VARCHAR(20) NOT NULL,
--     name_ko VARCHAR(200) NOT NULL,
--     name_en VARCHAR(200),
--     description TEXT,
--     enabled BOOLEAN DEFAULT TRUE,
--     sort_order INTEGER DEFAULT 0,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     UNIQUE KEY uk_code_type_code (code_type, code),
--     INDEX idx_code_type (code_type),
--     INDEX idx_enabled (enabled)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 인덱스 생성
CREATE INDEX `idx_declaration_number` ON `declarations` (`declaration_number`);

CREATE INDEX `idx_status` ON `declarations` (`status`);

CREATE INDEX `idx_type` ON `declarations` (`declaration_type`);

CREATE INDEX `idx_created_at` ON `declarations` (`created_at`);

ALTER TABLE `declarations` ADD FOREIGN KEY (`created_by`) REFERENCES `users` (`id`);

ALTER TABLE `declarations` ADD FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`);

ALTER TABLE `chattings` ADD FOREIGN KEY (`created_by`) REFERENCES `users` (`id`);

ALTER TABLE `messages` ADD FOREIGN KEY (`chatting_id`) REFERENCES `chattings` (`id`);

ALTER TABLE `attachments` ADD FOREIGN KEY (`declaration_id`) REFERENCES `declarations` (`id`) ON DELETE CASCADE;

ALTER TABLE `attachments` ADD FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`);
