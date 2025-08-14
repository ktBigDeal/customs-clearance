#!/bin/bash

# 전체 Docker 이미지 빌드 스크립트
# Usage: ./scripts/build-all.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}

echo "🚀 Building all Docker images for ${ENVIRONMENT} environment..."

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# Docker Compose 파일 선택
if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.production.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

echo -e "${BLUE}Using Docker Compose file: ${COMPOSE_FILE}${NC}"

# 1. 백엔드 빌드
echo -e "${GREEN}Building Backend (Spring Boot)...${NC}"
docker build -t customs-backend:${ENVIRONMENT} ./presentation-tier/backend

# 2. AI Gateway 빌드
echo -e "${GREEN}Building AI Gateway...${NC}"
docker build -t customs-ai-gateway:${ENVIRONMENT} ./application-tier/ai-gateway

# 3. AI 모델 서비스들 빌드
echo -e "${GREEN}Building AI Model Services...${NC}"

# 챗봇 FastAPI 서비스
if [ "$ENVIRONMENT" = "prod" ]; then
    docker build --target production -t customs-chatbot-fastapi:${ENVIRONMENT} ./application-tier/models/model-chatbot-fastapi
else
    docker build --target development -t customs-chatbot-fastapi:${ENVIRONMENT} ./application-tier/models/model-chatbot-fastapi
fi

# OCR 서비스
docker build -t customs-ocr:${ENVIRONMENT} ./application-tier/models/model-ocr

# 보고서 생성 서비스
docker build -t customs-report:${ENVIRONMENT} ./application-tier/models/model-report

# HS코드 추천 서비스
docker build -t customs-hscode:${ENVIRONMENT} ./application-tier/models/model-hscode

echo -e "${GREEN}✅ All Docker images built successfully!${NC}"

# 빌드된 이미지 목록 출력
echo -e "${BLUE}Built images:${NC}"
docker images | grep customs- | grep ${ENVIRONMENT}

# Docker Compose로 전체 스택 시작 옵션 제공
read -p "Do you want to start the full stack with Docker Compose? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Starting full stack...${NC}"
    docker-compose -f ${COMPOSE_FILE} up -d
    
    echo -e "${GREEN}🎉 Full stack is starting up!${NC}"
    echo -e "${BLUE}Service URLs:${NC}"
    echo "Backend: http://localhost:8080"
    echo "AI Gateway: http://localhost:8000"
    echo "Chatbot FastAPI: http://localhost:8004"
    echo "OCR Service: http://localhost:8001"
    echo "Report Service: http://localhost:8002"
    echo "HS Code Service: http://localhost:8003"
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        echo "phpMyAdmin: http://localhost:8081"
        echo "pgAdmin: http://localhost:5050"
    fi
    
    echo -e "${BLUE}Use 'docker-compose -f ${COMPOSE_FILE} logs -f' to view logs${NC}"
fi