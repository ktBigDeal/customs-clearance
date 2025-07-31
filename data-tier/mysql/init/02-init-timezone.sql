-- Set up timezone configuration for Korean Customs Clearance System
-- Korea Standard Time (KST) configuration

-- Set global time zone to Korea Standard Time
SET GLOBAL time_zone = '+09:00';

-- Create timezone configuration for application
USE `customs_clearance_dev_db`;

-- Insert timezone information if timezone tables are available
-- This is optional and depends on mysql_tzinfo_to_sql being loaded
INSERT IGNORE INTO mysql.time_zone_name (Name, Time_zone_id) 
VALUES ('Asia/Seoul', 1);

-- Set session time zone for current connection
SET time_zone = '+09:00';

SELECT 'Korean timezone (KST +09:00) configured successfully' as message;