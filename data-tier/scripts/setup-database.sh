#!/bin/bash

# Korean Customs Clearance System - Database Setup Script
# Automated setup and initialization script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_TIER_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DATA_TIER_DIR")"

echo -e "${BLUE}Korean Customs Clearance System - Database Setup${NC}"
echo "================================================="
echo "Script Directory: $SCRIPT_DIR"
echo "Data Tier Directory: $DATA_TIER_DIR"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Function to check if Docker is running
check_docker() {
    echo -e "${YELLOW}Checking Docker...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        echo "Please install Docker from https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker is not running${NC}"
        echo "Please start Docker Desktop or Docker daemon"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose is not installed${NC}"
        echo "Please install Docker Compose"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker is ready${NC}"
}

# Function to create .env file from template
create_env_file() {
    echo -e "\n${YELLOW}Setting up environment configuration...${NC}"
    
    cd "$DATA_TIER_DIR"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp ".env.example" ".env"
            echo -e "${GREEN}✓ Created .env file from template${NC}"
            echo -e "${YELLOW}⚠ Please review and update .env file with your settings${NC}"
        else
            echo -e "${RED}✗ .env.example file not found${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ .env file already exists${NC}"
    fi
}

# Function to start MySQL container
start_mysql() {
    echo -e "\n${YELLOW}Starting MySQL container...${NC}"
    
    cd "$DATA_TIER_DIR"
    
    # Stop any existing containers
    docker-compose down --remove-orphans
    
    # Pull latest images
    docker-compose pull mysql
    
    # Start MySQL container
    docker-compose up -d mysql
    
    echo -e "${GREEN}✓ MySQL container started${NC}"
    echo "Waiting for MySQL to be ready..."
    
    # Wait for MySQL to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T mysql mysqladmin ping -h localhost --silent; then
            echo -e "${GREEN}✓ MySQL is ready${NC}"
            break
        fi
        
        echo "Attempt $attempt/$max_attempts - Waiting for MySQL..."
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo -e "${RED}✗ MySQL failed to start within timeout${NC}"
        docker-compose logs mysql
        exit 1
    fi
}

# Function to test database connection
test_connection() {
    echo -e "\n${YELLOW}Testing database connection...${NC}"
    
    cd "$SCRIPT_DIR"
    
    # Test with bash script
    if [ -f "test-connection.sh" ]; then
        chmod +x test-connection.sh
        if ./test-connection.sh; then
            echo -e "${GREEN}✓ Connection test passed${NC}"
        else
            echo -e "${RED}✗ Connection test failed${NC}"
            exit 1
        fi
    fi
    
    # Test with Python script if available
    if command -v python3 &> /dev/null && [ -f "test-connection.py" ]; then
        echo -e "\n${YELLOW}Running Python connection test...${NC}"
        python3 test-connection.py
    fi
}

# Function to run Spring Boot migrations
run_migrations() {
    echo -e "\n${YELLOW}Running database migrations...${NC}"
    
    local backend_dir="$PROJECT_ROOT/presentation-tier/backend"
    
    if [ -d "$backend_dir" ]; then
        cd "$backend_dir"
        
        # Check if Maven wrapper exists
        if [ -f "mvnw" ]; then
            chmod +x mvnw
            echo "Running Flyway migrations with Maven..."
            
            # Set environment variables for Maven
            export DB_HOST=localhost
            export DB_PORT=3306
            export DB_NAME=customs_clearance_dev_db
            export DB_USERNAME=customs_user
            export DB_PASSWORD=customs_password
            
            if ./mvnw flyway:migrate -Dflyway.url=jdbc:mysql://localhost:3306/customs_clearance_dev_db -Dflyway.user=customs_user -Dflyway.password=customs_password; then
                echo -e "${GREEN}✓ Database migrations completed${NC}"
            else
                echo -e "${RED}✗ Database migrations failed${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠ Maven wrapper not found, skipping migrations${NC}"
            echo "You can run migrations manually with: ./mvnw flyway:migrate"
        fi
    else
        echo -e "${YELLOW}⚠ Backend directory not found, skipping migrations${NC}"
    fi
}

# Function to generate sample data
generate_sample_data() {
    echo -e "\n${YELLOW}Generating sample data...${NC}"
    
    cd "$SCRIPT_DIR"
    
    if command -v python3 &> /dev/null && [ -f "generate-sample-data.py" ]; then
        # Install required Python packages
        if ! python3 -c "import mysql.connector" 2>/dev/null; then
            echo "Installing mysql-connector-python..."
            pip3 install mysql-connector-python || pip install mysql-connector-python
        fi
        
        python3 generate-sample-data.py --count 10
        echo -e "${GREEN}✓ Sample data generated${NC}"
    else
        echo -e "${YELLOW}⚠ Python3 or sample data generator not available${NC}"
    fi
}

# Function to show database info
show_database_info() {
    echo -e "\n${BLUE}Database Setup Complete!${NC}"
    echo "========================"
    echo ""
    echo "MySQL Container: customs-clearance-mysql"
    echo "Database: customs_clearance_dev_db"
    echo "Host: localhost"
    echo "Port: 3306"
    echo "Username: customs_user"
    echo "Password: customs_password"
    echo ""
    echo "Management URLs:"
    echo "- PhpMyAdmin: http://localhost:8081 (if enabled with --admin profile)"
    echo ""
    echo "Useful Commands:"
    echo "- View logs: docker-compose logs mysql"
    echo "- Stop database: docker-compose down"
    echo "- Restart database: docker-compose restart mysql"
    echo "- Backup database: ./scripts/backup.sh"
    echo "- Test connection: ./scripts/test-connection.sh"
    echo ""
    echo "Next Steps:"
    echo "1. Update .env file with your preferred settings"
    echo "2. Run Spring Boot application for full integration"
    echo "3. Access the application frontend"
    echo ""
}

# Function to cleanup on error
cleanup_on_error() {
    echo -e "\n${RED}Setup failed. Cleaning up...${NC}"
    cd "$DATA_TIER_DIR"
    docker-compose down --remove-orphans
    exit 1
}

# Main execution
main() {
    # Parse command line arguments
    local skip_sample_data=false
    local enable_admin=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-sample-data)
                skip_sample_data=true
                shift
                ;;
            --admin)
                enable_admin=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --skip-sample-data  Skip generating sample data"
                echo "  --admin            Enable PhpMyAdmin interface"
                echo "  -h, --help         Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Trap errors
    trap cleanup_on_error ERR
    
    # Execute setup steps
    check_docker
    create_env_file
    start_mysql
    test_connection
    
    # Optional: Start PhpMyAdmin
    if [ "$enable_admin" = true ]; then
        echo -e "\n${YELLOW}Starting PhpMyAdmin...${NC}"
        cd "$DATA_TIER_DIR"
        docker-compose --profile admin up -d phpmyadmin
        echo -e "${GREEN}✓ PhpMyAdmin started at http://localhost:8081${NC}"
    fi
    
    # Run migrations if backend exists
    run_migrations
    
    # Generate sample data unless skipped
    if [ "$skip_sample_data" = false ]; then
        generate_sample_data
    fi
    
    # Show final information
    show_database_info
    
    echo -e "${GREEN}Database setup completed successfully!${NC}"
}

# Run main function
main "$@"