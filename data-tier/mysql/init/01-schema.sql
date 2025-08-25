-- 데이터베이스 생성 및 설정
USE customs_clearance;

-- 한글 지원을 위한 문자셋 설정
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

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

CREATE TABLE `declarations` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `declaration_number` VARCHAR(50) UNIQUE,
  `declaration_type` ENUM ('IMPORT', 'EXPORT') NOT NULL,
  `status` ENUM ('DRAFT', 'UPDATED', 'SUBMITTED', 'APPROVED', 'REJECTED') DEFAULT 'DRAFT',
  `declaration_details` TEXT,
  `notes` TEXT,
  `created_at` DATETIME DEFAULT (CURRENT_TIMESTAMP),
  `updated_at` DATETIME DEFAULT (CURRENT_TIMESTAMP),
  `created_by` BIGINT,
  `updated_by` BIGINT
);

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

-- 인덱스 생성
CREATE INDEX `idx_declaration_number` ON `declarations` (`declaration_number`);

CREATE INDEX `idx_status` ON `declarations` (`status`);

CREATE INDEX `idx_type` ON `declarations` (`declaration_type`);

CREATE INDEX `idx_created_at` ON `declarations` (`created_at`);

ALTER TABLE `declarations` ADD FOREIGN KEY (`created_by`) REFERENCES `users` (`id`);

ALTER TABLE `declarations` ADD FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`);

ALTER TABLE `attachments` ADD FOREIGN KEY (`declaration_id`) REFERENCES `declarations` (`id`) ON DELETE CASCADE;

ALTER TABLE `attachments` ADD FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`);
