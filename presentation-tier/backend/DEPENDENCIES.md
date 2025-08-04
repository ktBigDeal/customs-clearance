# 의존성 분석 및 설명서

## 📋 개요
이 문서는 관세 통관 시스템 백엔드의 모든 Maven 의존성과 각각의 용도를 상세히 설명합니다.

## 🚀 Spring Boot Starters

### `spring-boot-starter-web`
**용도**: 웹 애플리케이션 개발을 위한 핵심 스타터
- **포함 기능**: Spring MVC, Tomcat 내장 서버, JSON 처리
- **주요 사용**: REST API 엔드포인트 개발
- **프로젝트에서 활용**: DeclarationController, HealthController 등의 REST 컨트롤러 구현

### `spring-boot-starter-data-jpa`
**용도**: JPA 기반 데이터 접근 계층 구현
- **포함 기능**: Spring Data JPA, Hibernate ORM, 트랜잭션 관리
- **주요 사용**: 엔티티 매핑, Repository 패턴 구현
- **프로젝트에서 활용**: Declaration 엔티티, DeclarationRepository 등 데이터 계층

### `spring-boot-starter-validation`
**용도**: Bean Validation을 통한 데이터 검증
- **포함 기능**: Hibernate Validator, JSR-303 어노테이션
- **주요 사용**: DTO 필드 검증, 요청 데이터 유효성 검사
- **프로젝트에서 활용**: DeclarationRequestDto의 @NotNull, @Size 등 검증 어노테이션

### `spring-boot-starter-security`
**용도**: 보안 기능 제공
- **포함 기능**: 인증/인가, CSRF 보호, CORS 설정
- **주요 사용**: API 보안, 세션 관리
- **프로젝트에서 활용**: SecurityConfig 클래스의 보안 정책 설정

### `spring-boot-starter-actuator`
**용도**: 프로덕션 환경 모니터링 및 관리
- **포함 기능**: 헬스 체크, 메트릭 수집, 엔드포인트 노출
- **주요 사용**: 시스템 상태 모니터링, 운영 지표 수집
- **프로젝트에서 활용**: /actuator/health, /actuator/metrics 등 운영 엔드포인트

## 💾 데이터베이스 관련

### `mysql-connector-java` (v8.0.33)
**용도**: MySQL 데이터베이스 연결 드라이버
- **기능**: MySQL 8.0과의 JDBC 연결
- **설정 범위**: runtime (실행 시에만 필요)
- **프로젝트에서 활용**: application.yml의 MySQL 데이터소스 연결

### `h2` (테스트용)
**용도**: 인메모리 테스트 데이터베이스
- **기능**: 테스트 환경에서의 빠른 데이터베이스 처리
- **설정 범위**: test (테스트 시에만 사용)
- **프로젝트에서 활용**: 단위 테스트 및 통합 테스트 데이터 저장

## 📄 JSON 처리

### `jackson-databind`
**용도**: JSON 직렬화/역직렬화
- **기능**: Java 객체 ↔ JSON 변환
- **주요 사용**: REST API 요청/응답 처리
- **프로젝트에서 활용**: DTO 객체의 JSON 변환, API 통신

## 📚 API 문서화

### `springdoc-openapi-starter-webmvc-ui` (v2.3.0)
**용도**: OpenAPI 3.0 기반 API 문서 자동 생성
- **기능**: Swagger UI 제공, API 스펙 문서화
- **접근 경로**: /swagger-ui.html
- **프로젝트에서 활용**: REST API 문서화 및 테스트 인터페이스 제공

## 🛠️ 개발 도구

### `spring-boot-devtools`
**용도**: 개발 편의성 향상
- **기능**: 자동 재시작, LiveReload, 개발 환경 최적화
- **설정 범위**: runtime, optional
- **프로젝트에서 활용**: 개발 중 코드 변경 시 자동 애플리케이션 재시작

### `spring-boot-configuration-processor`
**용도**: 설정 속성 메타데이터 생성
- **기능**: application.yml 자동완성 지원
- **설정 범위**: optional (선택적)
- **프로젝트에서 활용**: IDE에서 설정 파일 편집 시 자동완성 제공

### `lombok`
**용도**: 보일러플레이트 코드 자동 생성
- **기능**: @Getter, @Setter, @ToString 등 어노테이션을 통한 코드 생성
- **설정 범위**: optional
- **프로젝트에서 활용**: Entity, DTO 클래스의 코드 간소화

## 🧪 테스트 관련

### `spring-boot-starter-test`
**용도**: 테스트 프레임워크 통합
- **포함 기능**: JUnit 5, Mockito, AssertJ, Spring Test
- **설정 범위**: test
- **프로젝트에서 활용**: 단위 테스트 및 통합 테스트 작성

### `spring-security-test`
**용도**: Spring Security 테스트 지원
- **기능**: 보안 관련 테스트 유틸리티
- **설정 범위**: test
- **프로젝트에서 활용**: 인증/인가 기능 테스트

### `testcontainers-junit-jupiter`
**용도**: 컨테이너 기반 통합 테스트
- **기능**: Docker 컨테이너를 이용한 실제 환경 테스트
- **설정 범위**: test
- **프로젝트에서 활용**: 실제 데이터베이스와 유사한 환경에서의 테스트

### `testcontainers-mysql`
**용도**: MySQL 컨테이너 테스트 지원
- **기능**: 테스트용 MySQL 컨테이너 자동 관리
- **설정 범위**: test
- **프로젝트에서 활용**: 프로덕션과 동일한 MySQL 환경에서의 테스트

## 🔧 Maven 플러그인

### `spring-boot-maven-plugin`
**용도**: Spring Boot 애플리케이션 빌드 및 실행
- **기능**: 실행 가능한 JAR 파일 생성, 개발 서버 실행
- **주요 명령**: `./mvnw spring-boot:run`

### `maven-compiler-plugin` (v3.11.0)
**용도**: Java 컴파일러 설정
- **기능**: Java 17 소스/타겟 버전 설정
- **프로젝트 설정**: source=17, target=17

### `maven-surefire-plugin` (v3.2.2)
**용도**: 단위 테스트 실행
- **기능**: JUnit 테스트 실행 및 결과 리포트 생성
- **주요 명령**: `./mvnw test`

### `jacoco-maven-plugin` (v0.8.11)
**용도**: 코드 커버리지 측정
- **기능**: 테스트 커버리지 분석 및 리포트 생성
- **출력**: target/site/jacoco/index.html

## 📊 의존성 통계

### 카테고리별 분포
- **Spring Boot Starters**: 5개 (핵심 기능)
- **데이터베이스**: 2개 (MySQL + 테스트용 H2)
- **개발 도구**: 3개 (devtools, lombok, configuration-processor)
- **테스트**: 4개 (JUnit, Security Test, TestContainers)
- **문서화**: 1개 (OpenAPI/Swagger)
- **JSON 처리**: 1개 (Jackson)

### 총 의존성 수
- **운영 의존성**: 8개
- **테스트 의존성**: 4개
- **개발 도구**: 3개
- **Maven 플러그인**: 4개

## 🎯 아키텍처 관점 분석

### 3-Tier 아키텍처 지원
- **Presentation Layer**: spring-boot-starter-web, springdoc-openapi
- **Business Layer**: spring-boot-starter-validation, spring-security
- **Data Layer**: spring-boot-starter-data-jpa, mysql-connector-java

### 품질 보증
- **테스트**: 포괄적인 테스트 도구 스택
- **코드 품질**: Lombok을 통한 코드 간소화
- **모니터링**: Actuator를 통한 운영 지표 수집
- **문서화**: 자동 API 문서 생성

### 보안 고려사항
- **인증/인가**: Spring Security 통합
- **데이터 검증**: Bean Validation 적용
- **운영 보안**: Actuator 엔드포인트 보안 설정

이 의존성 구성은 엔터프라이즈급 Spring Boot 애플리케이션의 모범 사례를 따르며, 개발 생산성과 운영 안정성을 모두 고려한 설계입니다.