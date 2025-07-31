# Customs Clearance Backend

A Spring Boot 3.x backend API gateway for the customs clearance application, serving as the presentation tier in a 3-tier architecture.

## Technology Stack

- **Java**: 17
- **Spring Boot**: 3.2.1
- **Build Tool**: Maven
- **Database**: MySQL 8.0
- **ORM**: JPA/Hibernate
- **Documentation**: OpenAPI 3 (Swagger UI)
- **Testing**: JUnit 5, Testcontainers
- **Containerization**: Docker

## Architecture

This application follows the 3-tier architecture pattern:
- **Presentation Tier**: RESTful API controllers
- **Application Tier**: Business logic services
- **Data Tier**: JPA repositories and MySQL database

## Key Features

- RESTful API for customs declaration management
- Comprehensive validation and error handling
- OpenAPI documentation with Swagger UI
- Database auditing with JPA
- Containerized deployment with Docker
- Comprehensive test coverage
- Security configuration with Spring Security

## Project Structure

```
src/
├── main/
│   ├── java/com/customs/clearance/
│   │   ├── config/           # Configuration classes
│   │   ├── controller/       # REST controllers
│   │   ├── dto/             # Data Transfer Objects
│   │   ├── entity/          # JPA entities
│   │   ├── exception/       # Exception handling
│   │   ├── repository/      # Data repositories
│   │   ├── service/         # Business logic services
│   │   ├── util/           # Utility classes
│   │   └── CustomsClearanceBackendApplication.java
│   └── resources/
│       ├── application.yml  # Application configuration
│       └── db/migration/    # Database migrations
└── test/                    # Test classes
```

## Getting Started

### Prerequisites

- Java 17 or higher
- Maven 3.6+ or use included Maven wrapper
- MySQL 8.0
- Docker (optional)

### Database Setup

1. Install MySQL 8.0
2. Create database:
```sql
CREATE DATABASE customs_clearance_dev_db;
CREATE USER 'customs_user'@'localhost' IDENTIFIED BY 'customs_password';
GRANT ALL PRIVILEGES ON customs_clearance_dev_db.* TO 'customs_user'@'localhost';
FLUSH PRIVILEGES;
```

### Running the Application

#### Using Maven
```bash
# Clone and navigate to the project
cd presentation-tier/backend

# Run with Maven wrapper
./mvnw spring-boot:run

# Or run with Maven (if installed)
mvn spring-boot:run
```

#### Using Docker
```bash
# Build the Docker image
docker build -t customs-clearance-backend .

# Run the container
docker run -p 8080:8080 \
  -e DB_HOST=host.docker.internal \
  -e DB_USERNAME=customs_user \
  -e DB_PASSWORD=customs_password \
  customs-clearance-backend
```

### Configuration

The application supports multiple profiles:

- **dev** (default): Development environment with H2 database
- **prod**: Production environment with MySQL
- **test**: Test environment with in-memory H2

Environment variables:
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 3306)
- `DB_NAME`: Database name
- `DB_USERNAME`: Database username
- `DB_PASSWORD`: Database password
- `JWT_SECRET`: JWT secret key
- `SERVER_PORT`: Application port (default: 8080)

## API Documentation

Once the application is running, access the API documentation at:
- Swagger UI: http://localhost:8080/api/v1/swagger-ui.html
- OpenAPI Spec: http://localhost:8080/api/v1/api-docs

## API Endpoints

### Health Check
- `GET /api/v1/public/health` - Application health check
- `GET /api/v1/public/info` - Application information

### Declarations
- `POST /api/v1/declarations` - Create new declaration
- `GET /api/v1/declarations` - Get all declarations (paginated)
- `GET /api/v1/declarations/{id}` - Get declaration by ID
- `GET /api/v1/declarations/number/{number}` - Get declaration by number
- `PUT /api/v1/declarations/{id}` - Update declaration
- `PATCH /api/v1/declarations/{id}/status` - Update declaration status
- `DELETE /api/v1/declarations/{id}` - Delete declaration
- `GET /api/v1/declarations/status/{status}` - Get declarations by status
- `GET /api/v1/declarations/search` - Search declarations by importer
- `GET /api/v1/declarations/stats` - Get declaration statistics

## Testing

```bash
# Run all tests
./mvnw test

# Run tests with coverage
./mvnw test jacoco:report

# Run integration tests
./mvnw test -Dtest="*IntegrationTest"
```

## Building for Production

```bash
# Package the application
./mvnw clean package -DskipTests

# Build Docker image
docker build -t customs-clearance-backend:latest .
```

## Security

The application includes:
- CORS configuration for cross-origin requests
- Input validation on all endpoints
- Error handling with proper HTTP status codes
- Security headers configuration
- JWT authentication support (configurable)

## Monitoring

Health check endpoints are available at:
- `/api/v1/actuator/health` - Application health
- `/api/v1/actuator/info` - Application information
- `/api/v1/actuator/metrics` - Application metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.