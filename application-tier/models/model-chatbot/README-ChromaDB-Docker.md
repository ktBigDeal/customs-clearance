# ChromaDB Docker 연결 가이드

model-chatbot이 data-tier의 ChromaDB Docker 컨테이너와 연결하는 방법을 설명합니다.

## 🎯 목적

기존의 로컬 파일 기반 ChromaDB 대신 data-tier에서 실행되는 ChromaDB Docker 서비스를 사용하여:
- 데이터 중앙화 및 공유
- 더 나은 확장성과 성능  
- 운영 환경 일관성

## 🚀 빠른 시작

### 1. ChromaDB Docker 서비스 시작

```bash
# data-tier로 이동
cd ../../../data-tier

# ChromaDB 컨테이너 시작
docker-compose up -d chromadb

# 상태 확인
docker-compose ps chromadb
curl http://localhost:8011/api/v2/heartbeat
```

### 2. model-chatbot 환경 설정

```bash
# model-chatbot 디렉토리에서
cd application-tier/models/model-chatbot

# Docker 모드 환경변수 설정
cp .env.docker .env

# 또는 기존 .env 파일에 추가:
echo "CHROMADB_MODE=docker" >> .env
echo "CHROMADB_HOST=localhost" >> .env  
echo "CHROMADB_PORT=8011" >> .env
```

### 3. 연결 테스트

```bash
# 연결 테스트 실행
python test_docker_chromadb.py

# 성공 시 기존 RAG 시스템 사용
python src/rag/unified_cli.py
```

## 📋 환경변수 설정

### Docker 모드 (.env 파일)
```bash
# 필수
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# ChromaDB Docker 연결
CHROMADB_MODE=docker
CHROMADB_HOST=localhost  
CHROMADB_PORT=8011

# 선택적
HF_TOKEN=hf_your-huggingface-token-here
```

### 로컬 모드 (기본값)
```bash
# 필수
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# 로컬 모드 (기본값, 설정하지 않아도 됨)
CHROMADB_MODE=local

# 선택적
HF_TOKEN=hf_your-huggingface-token-here
```

## 🔧 코드 변경사항

### config.py
- `get_chromadb_config()` 함수 추가
- 환경변수 기반 연결 모드 선택

### vector_store.py  
- `LangChainVectorStore` 클래스 확장
- Docker HTTP 연결 지원
- 기존 로컬 모드와 호환성 유지

### 주요 개선점
- 자동 모드 감지 및 연결
- 상세한 오류 처리 및 진단
- 기존 코드와 100% 호환성

## 🧪 테스트 스크립트

### test_docker_chromadb.py
전체 연결 과정을 테스트하고 문제를 진단합니다.

```bash
# Docker 모드 테스트
python test_docker_chromadb.py --mode docker

# 로컬 모드 테스트  
python test_docker_chromadb.py --mode local

# 사용자 정의 설정 테스트
python test_docker_chromadb.py --host localhost --port 8011
```

## 🔍 문제 해결

### ChromaDB 컨테이너 확인
```bash
cd ../../../data-tier
docker-compose ps chromadb
docker-compose logs chromadb
```

### 네트워크 연결 확인
```bash
# API 응답 테스트
curl http://localhost:8011/api/v2/heartbeat
curl http://localhost:8011/api/v2/version

# 포트 확인
netstat -an | grep 8011
```

### 일반적인 문제

1. **컨테이너가 시작되지 않음**
   - data-tier에서 `docker-compose up -d chromadb`
   - 로그 확인: `docker-compose logs chromadb`

2. **포트 접근 불가**
   - 포트 8011이 사용 중인지 확인
   - 방화벽 설정 확인

3. **연결 시간 초과**
   - ChromaDB 컨테이너 재시작
   - Docker 네트워크 상태 확인

4. **데이터 없음**
   - 기존 data/chroma_db 데이터가 Docker 볼륨에 마운트되었는지 확인
   - docker-compose.yml의 볼륨 설정 점검

## 📊 성능 및 장점

### Docker 모드 장점
- ✅ 중앙화된 데이터 관리
- ✅ 여러 서비스 간 데이터 공유
- ✅ 확장성과 성능 향상
- ✅ 백업과 복구 용이성
- ✅ 운영 환경 일관성

### 로컬 모드 장점  
- ✅ 빠른 개발 테스트
- ✅ 네트워크 의존성 없음
- ✅ 단순한 설정
- ✅ 낮은 리소스 사용량

## 🔄 모드 전환

언제든지 환경변수만 변경하여 모드를 전환할 수 있습니다:

```bash
# Docker 모드로 전환
echo "CHROMADB_MODE=docker" >> .env

# 로컬 모드로 전환  
echo "CHROMADB_MODE=local" >> .env
# 또는 CHROMADB_MODE 줄을 삭제
```

기존 코드는 수정 없이 자동으로 새로운 모드를 사용합니다.