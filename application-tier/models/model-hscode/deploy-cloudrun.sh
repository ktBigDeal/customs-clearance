#!/bin/bash

# Cloud Run 배포 스크립트
# HS코드 추천 서비스와 US-KR 변환 서비스를 Cloud Run에 배포

set -e

# 프로젝트 설정
PROJECT_ID="customs-clearance-system"
REGION="asia-northeast3"
DOCKER_REGISTRY="asia-northeast3-docker.pkg.dev"
REPO_NAME="docker-repo"

# 색상 출력 함수
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Docker 이미지 빌드 및 푸시 함수
build_and_push() {
    local service_name=$1
    local dockerfile=$2
    local image_tag="${DOCKER_REGISTRY}/${PROJECT_ID}/${REPO_NAME}/${service_name}:latest"
    
    print_info "Building Docker image for ${service_name}..."
    docker build -f ${dockerfile} -t ${image_tag} .
    
    print_info "Pushing Docker image for ${service_name}..."
    docker push ${image_tag}
    
    print_success "Docker image for ${service_name} pushed successfully"
}

# Cloud Run 서비스 배포 함수
deploy_service() {
    local service_name=$1
    local yaml_file=$2
    
    print_info "Deploying ${service_name} to Cloud Run..."
    gcloud run services replace ${yaml_file} \
        --region=${REGION} \
        --project=${PROJECT_ID}
    
    print_success "${service_name} deployed to Cloud Run successfully"
}

# 메인 실행
main() {
    print_info "Starting Cloud Run deployment process..."
    
    # Docker 인증
    print_info "Configuring Docker authentication..."
    gcloud auth configure-docker ${DOCKER_REGISTRY}
    
    # 1. HS코드 추천 서비스 빌드 및 배포
    print_info "=== HS Code Recommendation Service ==="
    build_and_push "hscode-recommender" "Dockerfile"
    deploy_service "HS Code Recommendation Service" "cloudrun-hscode-recommend.yaml"
    
    # 2. US-KR 변환 서비스 빌드 및 배포
    print_info "=== US-KR Converter Service ==="
    build_and_push "hscode-us-converter" "Dockerfile.us-convert"
    deploy_service "US-KR Converter Service" "cloudrun-us-convert.yaml"
    
    print_success "All services deployed successfully!"
    
    # 서비스 URL 출력
    print_info "Getting service URLs..."
    echo ""
    echo "=== Service URLs ==="
    
    HSCODE_URL=$(gcloud run services describe hscode-recommend-service --region=${REGION} --project=${PROJECT_ID} --format="value(status.url)")
    USCONVERT_URL=$(gcloud run services describe hscode-us-convert-service --region=${REGION} --project=${PROJECT_ID} --format="value(status.url)")
    
    echo "HS Code Recommendation Service: ${HSCODE_URL}"
    echo "US-KR Converter Service: ${USCONVERT_URL}"
    echo ""
    echo "API Documentation:"
    echo "HS Code Service Docs: ${HSCODE_URL}/docs"
    echo "US-KR Converter Docs: ${USCONVERT_URL}/docs"
}

# 스크립트 실행
main "$@"