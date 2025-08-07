#!/bin/bash

# Neo4j Setup Script for Customs Clearance System
# This script helps manage Neo4j database initialization and maintenance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NEO4J_CONTAINER="customs-neo4j"
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="neo4j123"

# Helper functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if Neo4j container exists and is running
check_neo4j_container() {
    if ! docker ps | grep -q $NEO4J_CONTAINER; then
        print_warning "Neo4j container is not running"
        return 1
    fi
    print_success "Neo4j container is running"
    return 0
}

# Wait for Neo4j to be ready
wait_for_neo4j() {
    print_info "Waiting for Neo4j to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "RETURN 1" >/dev/null 2>&1; then
            print_success "Neo4j is ready!"
            return 0
        fi
        
        print_info "Attempt $attempt/$max_attempts - Neo4j not ready yet, waiting..."
        sleep 5
        ((attempt++))
    done
    
    print_error "Neo4j failed to start after $max_attempts attempts"
    return 1
}

# Initialize Neo4j with sample data
init_neo4j() {
    print_info "Initializing Neo4j with sample data..."
    
    if ! check_neo4j_container; then
        print_error "Neo4j container is not running. Please start it first with: docker-compose up -d neo4j"
        exit 1
    fi
    
    if ! wait_for_neo4j; then
        print_error "Failed to connect to Neo4j"
        exit 1
    fi
    
    # Execute initialization script
    print_info "Executing initialization script..."
    docker exec -i $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD < ../neo4j/import/init.cypher
    
    if [ $? -eq 0 ]; then
        print_success "Neo4j initialization completed successfully!"
    else
        print_error "Neo4j initialization failed"
        exit 1
    fi
}

# Show Neo4j status
show_status() {
    print_info "Neo4j Status:"
    
    if check_neo4j_container; then
        echo -e "  Container Status: ${GREEN}Running${NC}"
        echo -e "  Web Interface: ${BLUE}http://localhost:7474${NC}"
        echo -e "  Bolt Protocol: ${BLUE}bolt://localhost:7687${NC}"
        echo -e "  Username: ${YELLOW}neo4j${NC}"
        echo -e "  Password: ${YELLOW}neo4j123${NC}"
        
        # Get database info
        local db_info=$(docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "CALL db.info()" 2>/dev/null | head -n 3 || echo "Unable to get database info")
        echo -e "  Database Info:\n$db_info"
    else
        echo -e "  Container Status: ${RED}Not Running${NC}"
        echo -e "  To start: ${YELLOW}docker-compose up -d neo4j${NC}"
    fi
}

# Test Neo4j connection and sample queries
test_connection() {
    print_info "Testing Neo4j connection and running sample queries..."
    
    if ! check_neo4j_container; then
        print_error "Neo4j container is not running"
        exit 1
    fi
    
    if ! wait_for_neo4j; then
        print_error "Failed to connect to Neo4j"
        exit 1
    fi
    
    print_info "Running sample queries..."
    
    # Test query 1: Check GDS version
    print_info "1. Checking GDS plugin version:"
    docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "RETURN gds.version() as GDSVersion" || print_warning "GDS plugin not available"
    
    # Test query 2: Count nodes
    print_info "2. Counting all nodes:"
    docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "MATCH (n) RETURN labels(n) as NodeType, count(n) as Count ORDER BY Count DESC"
    
    # Test query 3: Show relationships
    print_info "3. Showing relationship types:"
    docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "MATCH ()-[r]->() RETURN DISTINCT type(r) as RelationshipType ORDER BY RelationshipType"
    
    # Test query 4: Sample declaration query
    print_info "4. Sample declarations with companies:"
    docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "MATCH (d:Declaration)-[:DECLARED_BY]->(c:Company) RETURN d.declaration_id, d.status, c.name LIMIT 5"
    
    print_success "Connection test completed!"
}

# Run GDS examples
test_gds() {
    print_info "Testing GDS (Graph Data Science) capabilities..."
    
    if ! check_neo4j_container; then
        print_error "Neo4j container is not running"
        exit 1
    fi
    
    if ! wait_for_neo4j; then
        print_error "Failed to connect to Neo4j"
        exit 1
    fi
    
    # Check if GDS is available
    print_info "Checking GDS availability..."
    if docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "RETURN gds.version()" >/dev/null 2>&1; then
        print_success "GDS plugin is available!"
        
        print_info "Running GDS example queries..."
        docker exec -i $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD < ../neo4j/import/gds-examples.cypher
        
        if [ $? -eq 0 ]; then
            print_success "GDS examples completed successfully!"
        else
            print_warning "Some GDS examples may have failed - this is normal for Community Edition"
        fi
    else
        print_error "GDS plugin is not available"
        print_info "Make sure to restart Neo4j container after configuration changes"
    fi
}

# Backup Neo4j data
backup_data() {
    print_info "Creating Neo4j data backup..."
    
    local backup_dir="../backups/neo4j"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="neo4j_backup_$timestamp.dump"
    
    mkdir -p "$backup_dir"
    
    if check_neo4j_container; then
        docker exec $NEO4J_CONTAINER neo4j-admin dump --database=neo4j --to=/tmp/$backup_file
        docker cp $NEO4J_CONTAINER:/tmp/$backup_file "$backup_dir/$backup_file"
        print_success "Backup created: $backup_dir/$backup_file"
    else
        print_error "Neo4j container is not running"
        exit 1
    fi
}

# Clean Neo4j data
clean_data() {
    print_warning "This will delete ALL data in Neo4j database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning Neo4j data..."
        docker exec $NEO4J_CONTAINER cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD "MATCH (n) DETACH DELETE n"
        print_success "Neo4j data cleaned"
    else
        print_info "Operation cancelled"
    fi
}

# Show help
show_help() {
    echo "Neo4j Management Script for Customs Clearance System"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  init      Initialize Neo4j with sample data"
    echo "  status    Show Neo4j status and connection info"
    echo "  test      Test connection and run sample queries"
    echo "  gds       Test GDS (Graph Data Science) capabilities"
    echo "  backup    Create a backup of Neo4j data"
    echo "  clean     Clean all data from Neo4j (destructive!)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 init     # Initialize database with sample data"
    echo "  $0 status   # Check if Neo4j is running"
    echo "  $0 test     # Test connection and run queries"
    echo "  $0 gds      # Test GDS plugin and run graph algorithms"
}

# Main script logic
main() {
    case "${1:-help}" in
        "init")
            check_docker
            init_neo4j
            ;;
        "status")
            check_docker
            show_status
            ;;
        "test")
            check_docker
            test_connection
            ;;
        "gds")
            check_docker
            test_gds
            ;;
        "backup")
            check_docker
            backup_data
            ;;
        "clean")
            check_docker
            clean_data
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"