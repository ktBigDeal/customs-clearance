-- Korean Customs Clearance System Database Initialization
-- This script runs when MySQL container starts for the first time

-- Set default character set and collation for Korean support
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create development database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `customs_clearance_dev_db` 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Create production database if it doesn't exist  
CREATE DATABASE IF NOT EXISTS `customs_clearance_prod_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create test database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `customs_clearance_test_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Grant privileges to customs_user for all databases
GRANT ALL PRIVILEGES ON `customs_clearance_dev_db`.* TO 'customs_user'@'%';
GRANT ALL PRIVILEGES ON `customs_clearance_prod_db`.* TO 'customs_user'@'%';
GRANT ALL PRIVILEGES ON `customs_clearance_test_db`.* TO 'customs_user'@'%';

-- Create read-only user for reporting/analytics
CREATE USER IF NOT EXISTS 'customs_readonly'@'%' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON `customs_clearance_dev_db`.* TO 'customs_readonly'@'%';
GRANT SELECT ON `customs_clearance_prod_db`.* TO 'customs_readonly'@'%';

-- Create backup user for mysqldump operations
CREATE USER IF NOT EXISTS 'customs_backup'@'%' IDENTIFIED BY 'backup_password';
GRANT SELECT, SHOW VIEW, TRIGGER, LOCK TABLES, EVENT ON `customs_clearance_dev_db`.* TO 'customs_backup'@'%';
GRANT SELECT, SHOW VIEW, TRIGGER, LOCK TABLES, EVENT ON `customs_clearance_prod_db`.* TO 'customs_backup'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;

-- Log successful initialization
SELECT 'Korean Customs Clearance System databases initialized successfully' as message;