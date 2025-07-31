# Data Tier - MySQL Database

관세청 통관시스템의 데이터 계층입니다.

## 구조

```
data-tier/
├── docker-compose.yml          # MySQL 컨테이너 설정
├── mysql/
│   ├── config/
│   │   └── my.cnf             # MySQL 설정 (한글 지원)
│   └── init/
│       ├── 01-schema.sql      # 데이터베이스 스키마
│       └── 02-seed-data.sql   # 초기 테스트 데이터
├── scripts/
│   └── test-connection.py     # DB 연결 테스트 스크립트
└── README.md
```

## 설치 및 실행

### 1. Docker Compose로 MySQL 실행

```bash
cd data-tier
docker-compose up -d
```

### 2. 서비스 확인

- **MySQL**: http://localhost:3306
- **phpMyAdmin**: http://localhost:8081

### 3. 연결 정보

- **Host**: localhost
- **Port**: 3306
- **Database**: customs_clearance
- **Username**: customs_user
- **Password**: customs_pass

## 데이터베이스 스키마

### 주요 테이블

1. **users** - 사용자 관리
2. **declarations** - 통관 신고서
3. **attachments** - 첨부파일
4. **declaration_history** - 신고서 이력
5. **codes** - 코드 관리 (국가, 통화, HS코드 등)

### 문자셋 설정

- 한글 지원을 위해 **utf8mb4** 사용
- 시간대: Asia/Seoul (+09:00)

## 테스트

### Python으로 연결 테스트

```bash
# 의존성 설치
pip install mysql-connector-python

# 연결 테스트 실행
python scripts/test-connection.py
```

### Spring Boot에서 연결

`application.yml` 설정:

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/customs_clearance?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Seoul
    username: customs_user
    password: customs_pass
    driver-class-name: com.mysql.cj.jdbc.Driver
```

## 초기 데이터

### 테스트 사용자

- **admin** (관리자): admin@customs.go.kr / admin123
- **officer1** (검사관): officer1@customs.go.kr / officer123  
- **user1** (사용자): user1@company.com / user123

### 테스트 신고서

- 3건의 샘플 신고서 (수입/수출/경유)
- 다양한 상태 (제출, 검토중, 승인)

## 관리

### 백업

```bash
docker exec customs-mysql mysqldump -u customs_user -p customs_clearance > backup.sql
```

### 복원

```bash
docker exec -i customs-mysql mysql -u customs_user -p customs_clearance < backup.sql
```

### 로그 확인

```bash
docker logs customs-mysql
```