# AI Gateway for Customs Clearance System

FastAPI-based AI Gateway and Model Serving API for the Korean Customs Clearance System.

## Features

- **AI Model Management**: CRUD operations for AI models
- **Document Processing**: Process customs documents using AI models
- **Risk Assessment**: Assess risk levels for customs declarations
- **Validation**: Validate customs declaration data
- **Health Checks**: Comprehensive health monitoring
- **Authentication**: Basic authentication middleware
- **CORS Support**: Cross-origin resource sharing
- **Batch Processing**: Support for batch operations
- **Monitoring**: Request logging and metrics

## Quick Start

### Using Docker Compose (Recommended)

1. Copy environment file:
```bash
cp .env.example .env
```

2. Start all services:
```bash
docker-compose up -d
```

3. Check health:
```bash
curl http://localhost:8000/health
```

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the application:
```bash
python main.py
```

## API Endpoints

### Health Checks
- `GET /health` - Comprehensive health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

### Model Management
- `GET /api/v1/models` - List all models
- `GET /api/v1/models/{model_id}` - Get model info
- `POST /api/v1/models/{model_id}/predict` - Single prediction
- `POST /api/v1/models/{model_id}/batch-predict` - Batch prediction
- `PUT /api/v1/models/{model_id}` - Update model

### AI Gateway
- `POST /api/v1/gateway/process-document` - Process document
- `POST /api/v1/gateway/assess-risk` - Risk assessment
- `POST /api/v1/gateway/validate` - Validate declaration

## Architecture

```
AI Gateway (Port 8000)
├── Health Check Endpoints
├── Model Management API
├── AI Gateway API
├── Authentication Middleware
├── Request Logging
└── CORS Support

Model Services
├── Document Classifier (Port 8001)
├── Text Extractor (Port 8002)
└── Shared Utilities

External Dependencies
├── Spring Boot Backend (Port 8080)
├── PostgreSQL Database
└── Redis Cache
```

## Configuration

Key environment variables:

- `DEBUG`: Enable debug mode
- `SPRING_BOOT_BASE_URL`: Spring Boot backend URL
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Authentication secret
- `CORS_ORIGINS`: Allowed CORS origins

## Development

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest
```

3. Format code:
```bash
black .
```

4. Type checking:
```bash
mypy .
```

## Model Integration

The AI Gateway can integrate with any ML model that implements the standard inference interface:

- Health check endpoint
- Prediction endpoint
- Batch prediction endpoint
- Standard request/response schemas

## Monitoring

- Health checks at `/health`
- Request logging with structured JSON
- Metrics endpoint (if enabled)
- Docker health checks

## Security

- Authentication middleware
- Request validation
- Input sanitization
- CORS configuration
- Rate limiting
- Trusted host middleware

## Deployment

### Development
```bash
docker-compose up -d
```

### Production
- Use proper secrets management
- Configure TLS/SSL
- Set up reverse proxy
- Enable monitoring
- Configure log aggregation

## API Documentation

When running in debug mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc