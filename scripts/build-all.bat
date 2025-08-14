@echo off
setlocal enabledelayedexpansion

REM 전체 Docker 이미지 빌드 스크립트 (Windows)
REM Usage: scripts\build-all.bat [dev|prod]

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

echo 🚀 Building all Docker images for %ENVIRONMENT% environment...

REM 프로젝트 루트로 이동
cd /d "%~dp0\.."

REM Docker Compose 파일 선택
if "%ENVIRONMENT%"=="prod" (
    set COMPOSE_FILE=docker-compose.production.yml
) else (
    set COMPOSE_FILE=docker-compose.yml
)

echo Using Docker Compose file: %COMPOSE_FILE%

REM 1. 백엔드 빌드
echo Building Backend (Spring Boot)...
docker build -t customs-backend:%ENVIRONMENT% ./presentation-tier/backend
if errorlevel 1 (
    echo Failed to build backend
    exit /b 1
)

REM 2. AI Gateway 빌드
echo Building AI Gateway...
docker build -t customs-ai-gateway:%ENVIRONMENT% ./application-tier/ai-gateway
if errorlevel 1 (
    echo Failed to build AI Gateway
    exit /b 1
)

REM 3. AI 모델 서비스들 빌드
echo Building AI Model Services...

REM 챗봇 FastAPI 서비스
if "%ENVIRONMENT%"=="prod" (
    docker build --target production -t customs-chatbot-fastapi:%ENVIRONMENT% ./application-tier/models/model-chatbot-fastapi
) else (
    docker build --target development -t customs-chatbot-fastapi:%ENVIRONMENT% ./application-tier/models/model-chatbot-fastapi
)
if errorlevel 1 (
    echo Failed to build chatbot service
    exit /b 1
)

REM OCR 서비스
docker build -t customs-ocr:%ENVIRONMENT% ./application-tier/models/model-ocr
if errorlevel 1 (
    echo Failed to build OCR service
    exit /b 1
)

REM 보고서 생성 서비스
docker build -t customs-report:%ENVIRONMENT% ./application-tier/models/model-report
if errorlevel 1 (
    echo Failed to build Report service
    exit /b 1
)

REM HS코드 추천 서비스
docker build -t customs-hscode:%ENVIRONMENT% ./application-tier/models/model-hscode
if errorlevel 1 (
    echo Failed to build HSCode service
    exit /b 1
)

echo ✅ All Docker images built successfully!

REM 빌드된 이미지 목록 출력
echo Built images:
docker images | findstr customs- | findstr %ENVIRONMENT%

REM Docker Compose로 전체 스택 시작 옵션 제공
set /p REPLY="Do you want to start the full stack with Docker Compose? (y/N): "
if /i "%REPLY%"=="y" (
    echo Starting full stack...
    docker-compose -f %COMPOSE_FILE% up -d
    
    echo 🎉 Full stack is starting up!
    echo Service URLs:
    echo Backend: http://localhost:8080
    echo AI Gateway: http://localhost:8000
    echo Chatbot FastAPI: http://localhost:8004
    echo OCR Service: http://localhost:8001
    echo Report Service: http://localhost:8002
    echo HS Code Service: http://localhost:8003
    
    if "%ENVIRONMENT%"=="dev" (
        echo phpMyAdmin: http://localhost:8081
        echo pgAdmin: http://localhost:5050
    )
    
    echo Use 'docker-compose -f %COMPOSE_FILE% logs -f' to view logs
)

pause