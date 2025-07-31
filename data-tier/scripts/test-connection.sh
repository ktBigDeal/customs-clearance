#!/bin/bash

# Korean Customs Clearance System - Database Connection Test Script
# This script tests MySQL database connectivity and Korean character support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}
DB_NAME=${DB_NAME:-customs_clearance_dev_db}
DB_USER=${DB_USER:-customs_user}
DB_PASSWORD=${DB_PASSWORD:-customs_password}

echo -e "${YELLOW}Korean Customs Clearance System - Database Connection Test${NC}"
echo "============================================================"

# Function to test connection
test_connection() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local database=$5
    
    echo -e "\n${YELLOW}Testing connection to MySQL...${NC}"
    echo "Host: $host"
    echo "Port: $port"
    echo "Database: $database"
    echo "User: $user"
    
    # Test basic connection
    if mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SELECT 1;" 2>/dev/null; then
        echo -e "${GREEN}✓ Basic connection successful${NC}"
    else
        echo -e "${RED}✗ Basic connection failed${NC}"
        return 1
    fi
    
    # Test database existence
    if mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "USE $database; SELECT 1;" 2>/dev/null; then
        echo -e "${GREEN}✓ Database '$database' accessible${NC}"
    else
        echo -e "${RED}✗ Database '$database' not accessible${NC}"
        return 1
    fi
    
    return 0
}

# Function to test Korean character support
test_korean_support() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local database=$5
    
    echo -e "\n${YELLOW}Testing Korean character support...${NC}"
    
    # Test character set configuration
    charset_result=$(mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SHOW VARIABLES LIKE 'character_set%';" 2>/dev/null)
    if echo "$charset_result" | grep -q "utf8mb4"; then
        echo -e "${GREEN}✓ UTF8MB4 character set configured${NC}"
    else
        echo -e "${RED}✗ UTF8MB4 character set not configured${NC}"
        return 1
    fi
    
    # Test collation configuration
    collation_result=$(mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SHOW VARIABLES LIKE 'collation%';" 2>/dev/null)
    if echo "$collation_result" | grep -q "utf8mb4_unicode_ci"; then
        echo -e "${GREEN}✓ UTF8MB4 Unicode collation configured${NC}"
    else
        echo -e "${RED}✗ UTF8MB4 Unicode collation not configured${NC}"
        return 1
    fi
    
    # Test Korean text insertion and retrieval
    mysql -h "$host" -P "$port" -u "$user" -p"$password" "$database" << 'EOF' 2>/dev/null
DROP TABLE IF EXISTS test_korean;
CREATE TABLE test_korean (
    id INT AUTO_INCREMENT PRIMARY KEY,
    korean_text VARCHAR(255)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO test_korean (korean_text) VALUES 
('안녕하세요'),
('한국 관세청'),
('통관 신고서'),
('수입업체: 주식회사 한국무역'),
('수출업체: Samsung Electronics Co., Ltd.');
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Korean text insertion successful${NC}"
    else
        echo -e "${RED}✗ Korean text insertion failed${NC}"
        return 1
    fi
    
    # Verify Korean text retrieval
    korean_text=$(mysql -h "$host" -P "$port" -u "$user" -p"$password" "$database" -e "SELECT korean_text FROM test_korean WHERE korean_text = '안녕하세요';" 2>/dev/null | tail -n +2)
    if [ "$korean_text" = "안녕하세요" ]; then
        echo -e "${GREEN}✓ Korean text retrieval successful${NC}"
    else
        echo -e "${RED}✗ Korean text retrieval failed${NC}"
        return 1
    fi
    
    # Clean up test table
    mysql -h "$host" -P "$port" -u "$user" -p"$password" "$database" -e "DROP TABLE IF EXISTS test_korean;" 2>/dev/null
    
    return 0
}

# Function to test table existence
test_tables() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local database=$5
    
    echo -e "\n${YELLOW}Testing table existence...${NC}"
    
    tables=("declarations" "users" "documents" "audit_logs" "declaration_items" "system_settings")
    
    for table in "${tables[@]}"; do
        if mysql -h "$host" -P "$port" -u "$user" -p"$password" "$database" -e "DESCRIBE $table;" 2>/dev/null >/dev/null; then
            echo -e "${GREEN}✓ Table '$table' exists${NC}"
        else
            echo -e "${YELLOW}⚠ Table '$table' does not exist (may need migration)${NC}"
        fi
    done
    
    return 0
}

# Function to show database info
show_database_info() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local database=$5
    
    echo -e "\n${YELLOW}Database Information:${NC}"
    echo "===================="
    
    # MySQL version
    version=$(mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SELECT VERSION();" 2>/dev/null | tail -n +2)
    echo "MySQL Version: $version"
    
    # Current time zone
    timezone=$(mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SELECT @@time_zone, NOW();" 2>/dev/null | tail -n +2)
    echo "Time Zone: $timezone"
    
    # Database size
    size=$(mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Database Size (MB)' FROM information_schema.tables WHERE table_schema='$database';" 2>/dev/null | tail -n +2)
    echo "Database Size: ${size:-0} MB"
    
    # Table count
    table_count=$(mysql -h "$host" -P "$port" -u "$user" -p"$password" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$database';" 2>/dev/null | tail -n +2)
    echo "Table Count: ${table_count:-0}"
}

# Main execution
main() {
    echo "Starting database connection tests..."
    
    # Load environment variables if .env file exists
    if [ -f "../.env" ]; then
        echo "Loading environment variables from .env file..."
        source ../.env
        DB_HOST=${DB_HOST:-$MYSQL_HOST}
        DB_NAME=${DB_NAME:-$MYSQL_DATABASE}
        DB_USER=${DB_USER:-$MYSQL_USER}
        DB_PASSWORD=${DB_PASSWORD:-$MYSQL_PASSWORD}
    fi
    
    # Test connection
    if ! test_connection "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" "$DB_NAME"; then
        echo -e "\n${RED}Connection test failed. Please check your configuration.${NC}"
        exit 1
    fi
    
    # Test Korean support
    if ! test_korean_support "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" "$DB_NAME"; then
        echo -e "\n${RED}Korean character support test failed.${NC}"
        exit 1
    fi
    
    # Test tables
    test_tables "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" "$DB_NAME"
    
    # Show database info
    show_database_info "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" "$DB_NAME"
    
    echo -e "\n${GREEN}All database tests completed successfully!${NC}"
    echo -e "${GREEN}Korean Customs Clearance System database is ready.${NC}"
}

# Script usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --host HOST         Database host (default: localhost)"
    echo "  --port PORT         Database port (default: 3306)"
    echo "  --database DB       Database name (default: customs_clearance_dev_db)"
    echo "  --user USER         Database user (default: customs_user)"
    echo "  --password PASS     Database password (default: customs_password)"
    echo ""
    echo "Environment variables can also be set in ../.env file"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --host)
            DB_HOST="$2"
            shift 2
            ;;
        --port)
            DB_PORT="$2"
            shift 2
            ;;
        --database)
            DB_NAME="$2"
            shift 2
            ;;
        --user)
            DB_USER="$2"
            shift 2
            ;;
        --password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run main function
main