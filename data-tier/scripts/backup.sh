#!/bin/bash

# Korean Customs Clearance System - Database Backup Script
# Automated backup script with retention policy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DB_HOST=${MYSQL_HOST:-mysql}
DB_PORT=${MYSQL_PORT:-3306}
DB_USER=${MYSQL_USER:-root}
DB_PASSWORD=${MYSQL_PASSWORD:-root_password}
DB_NAME=${MYSQL_DATABASE:-customs_clearance_dev_db}
BACKUP_DIR=${BACKUP_DIR:-/backups}
BACKUP_RETAIN_DAYS=${BACKUP_RETAIN_DAYS:-7}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/customs_clearance_backup_${TIMESTAMP}.sql"
BACKUP_FILE_COMPRESSED="$BACKUP_FILE.gz"

echo -e "${YELLOW}Korean Customs Clearance System - Database Backup${NC}"
echo "================================================="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Backup file: $BACKUP_FILE_COMPRESSED"
echo "Retention: $BACKUP_RETAIN_DAYS days"
echo ""

# Function to perform backup
perform_backup() {
    echo -e "${YELLOW}Starting database backup...${NC}"
    
    # Create backup with mysqldump
    if mysqldump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --user="$DB_USER" \
        --password="$DB_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --add-drop-database \
        --default-character-set=utf8mb4 \
        --comments \
        --dump-date \
        "$DB_NAME" > "$BACKUP_FILE"; then
        
        echo -e "${GREEN}✓ Database dump completed${NC}"
    else
        echo -e "${RED}✗ Database dump failed${NC}"
        return 1
    fi
    
    # Compress the backup file
    if gzip "$BACKUP_FILE"; then
        echo -e "${GREEN}✓ Backup compressed: $BACKUP_FILE_COMPRESSED${NC}"
    else
        echo -e "${RED}✗ Backup compression failed${NC}"
        return 1
    fi
    
    # Get file size
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE_COMPRESSED" | awk '{print $5}')
    echo "Backup size: $BACKUP_SIZE"
    
    return 0
}

# Function to clean old backups
cleanup_old_backups() {
    echo -e "\n${YELLOW}Cleaning up old backups...${NC}"
    
    # Find and delete backups older than retention period
    old_backups=$(find "$BACKUP_DIR" -name "customs_clearance_backup_*.sql.gz" -mtime +$BACKUP_RETAIN_DAYS)
    
    if [ -n "$old_backups" ]; then
        echo "Removing old backups:"
        echo "$old_backups"
        find "$BACKUP_DIR" -name "customs_clearance_backup_*.sql.gz" -mtime +$BACKUP_RETAIN_DAYS -delete
        echo -e "${GREEN}✓ Old backups cleaned up${NC}"
    else
        echo "No old backups to clean up"
    fi
}

# Function to verify backup integrity
verify_backup() {
    local backup_file=$1
    
    echo -e "\n${YELLOW}Verifying backup integrity...${NC}"
    
    # Check if file exists and is not empty
    if [ ! -f "$backup_file" ] || [ ! -s "$backup_file" ]; then
        echo -e "${RED}✗ Backup file is missing or empty${NC}"
        return 1
    fi
    
    # Check if gzip file is valid
    if ! gzip -t "$backup_file" 2>/dev/null; then
        echo -e "${RED}✗ Backup file is corrupted${NC}"
        return 1
    fi
    
    # Check if SQL content looks valid
    if zcat "$backup_file" | head -20 | grep -q "MySQL dump"; then
        echo -e "${GREEN}✓ Backup file appears to be valid${NC}"
    else
        echo -e "${RED}✗ Backup file doesn't appear to be a valid MySQL dump${NC}"
        return 1
    fi
    
    return 0
}

# Function to list existing backups
list_backups() {
    echo -e "\n${YELLOW}Existing backups:${NC}"
    echo "=================="
    
    if ls "$BACKUP_DIR"/customs_clearance_backup_*.sql.gz 1> /dev/null 2>&1; then
        ls -lht "$BACKUP_DIR"/customs_clearance_backup_*.sql.gz | while read -r line; do
            filename=$(basename $(echo "$line" | awk '{print $9}'))
            size=$(echo "$line" | awk '{print $5}')
            date=$(echo "$line" | awk '{print $6, $7, $8}')
            echo "$filename ($size) - $date"
        done
    else
        echo "No backups found"
    fi
}

# Function to send notification (if configured)
send_notification() {
    local status=$1
    local message=$2
    
    # This could be extended to send email, Slack, or other notifications
    echo -e "\n${YELLOW}Backup Status: $status${NC}"
    echo "Message: $message"
    echo "Timestamp: $(date)"
    
    # Log to syslog if available
    if command -v logger >/dev/null 2>&1; then
        logger -t "customs-backup" "Backup $status: $message"
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    echo "Starting backup process at $(date)"
    
    # Perform the backup
    if perform_backup; then
        # Verify the backup
        if verify_backup "$BACKUP_FILE_COMPRESSED"; then
            # Clean up old backups
            cleanup_old_backups
            
            # List current backups
            list_backups
            
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            
            send_notification "SUCCESS" "Backup completed successfully in ${duration}s"
            echo -e "\n${GREEN}Backup process completed successfully!${NC}"
            echo "Duration: ${duration} seconds"
            
        else
            send_notification "FAILED" "Backup verification failed"
            echo -e "\n${RED}Backup verification failed!${NC}"
            exit 1
        fi
    else
        send_notification "FAILED" "Backup creation failed"
        echo -e "\n${RED}Backup process failed!${NC}"
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --host HOST         Database host (default: mysql)"
    echo "  --port PORT         Database port (default: 3306)"
    echo "  --database DB       Database name (default: customs_clearance_dev_db)"
    echo "  --user USER         Database user (default: root)"
    echo "  --password PASS     Database password"
    echo "  --backup-dir DIR    Backup directory (default: /backups)"
    echo "  --retain-days N     Retention period in days (default: 7)"
    echo "  --list-only         List existing backups only"
    echo ""
    echo "Environment variables:"
    echo "  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD"
    echo "  MYSQL_DATABASE, BACKUP_DIR, BACKUP_RETAIN_DAYS"
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
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retain-days)
            BACKUP_RETAIN_DAYS="$2"
            shift 2
            ;;
        --list-only)
            list_backups
            exit 0
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