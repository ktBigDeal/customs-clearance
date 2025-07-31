-- Korean Customs Clearance System - Base Tables Migration
-- Version: 1.0
-- Description: Create base tables for customs declarations system
-- Character Set: utf8mb4 for Korean language support

-- Create declarations table
CREATE TABLE declarations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    declaration_number VARCHAR(50) NOT NULL UNIQUE,
    importer_name VARCHAR(255) NOT NULL,
    exporter_name VARCHAR(255) NOT NULL,
    declaration_date DATE NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status ENUM('PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CLEARED') NOT NULL DEFAULT 'PENDING',
    description TEXT,
    country_of_origin VARCHAR(100) NOT NULL,
    port_of_entry VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version BIGINT NOT NULL DEFAULT 0,
    
    INDEX idx_declaration_number (declaration_number),
    INDEX idx_declaration_date (declaration_date),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_importer_name (importer_name),
    INDEX idx_country_of_origin (country_of_origin)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci 
  COMMENT='Customs declarations table with Korean language support';

-- Create users table for system authentication
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role ENUM('ADMIN', 'OFFICER', 'USER', 'READONLY') NOT NULL DEFAULT 'USER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version BIGINT NOT NULL DEFAULT 0,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci 
  COMMENT='System users table with Korean name support';

-- Create documents table for attachments
CREATE TABLE documents (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    declaration_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    document_type ENUM('INVOICE', 'PACKING_LIST', 'CERTIFICATE', 'PERMIT', 'OTHER') NOT NULL,
    uploaded_by BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version BIGINT NOT NULL DEFAULT 0,
    
    FOREIGN KEY (declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_declaration_id (declaration_id),
    INDEX idx_document_type (document_type),
    INDEX idx_uploaded_by (uploaded_by)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci 
  COMMENT='Document attachments for customs declarations';

-- Create audit_logs table for tracking changes
CREATE TABLE audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id BIGINT NOT NULL,
    operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    old_values JSON,
    new_values JSON,
    changed_by BIGINT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_table_record (table_name, record_id),
    INDEX idx_operation (operation),
    INDEX idx_changed_by (changed_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci 
  COMMENT='Audit trail for all data changes';

-- Create declaration_items table for detailed item information
CREATE TABLE declaration_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    declaration_id BIGINT NOT NULL,
    item_sequence INT NOT NULL,
    hs_code VARCHAR(20) NOT NULL,
    item_description TEXT NOT NULL,
    quantity DECIMAL(15,3) NOT NULL,
    unit_of_measure VARCHAR(10) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    country_of_origin VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version BIGINT NOT NULL DEFAULT 0,
    
    FOREIGN KEY (declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
    INDEX idx_declaration_id (declaration_id),
    INDEX idx_hs_code (hs_code),
    INDEX idx_country_of_origin (country_of_origin),
    UNIQUE KEY uk_declaration_sequence (declaration_id, item_sequence)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci 
  COMMENT='Individual items within customs declarations';

-- Create system_settings table for configuration
CREATE TABLE system_settings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type ENUM('STRING', 'NUMBER', 'BOOLEAN', 'JSON') NOT NULL DEFAULT 'STRING',
    description VARCHAR(500),
    is_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version BIGINT NOT NULL DEFAULT 0,
    
    INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci 
  COMMENT='System configuration settings';