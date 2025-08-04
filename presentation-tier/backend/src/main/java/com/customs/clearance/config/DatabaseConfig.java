package com.customs.clearance.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * 데이터베이스 설정 관리 컨피그레이션 클래스
 * 
 * JPA 저장소와 트랜잭션 관리를 위한 스프링 데이터 접근 설정을 정의합니다.
 * 이 설정은 관세 통관 시스템의 데이터 층 기반 구성을 제공합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>JPA Repository 활성화 및 스캔 패키지 지정</li>
 *   <li>트랜잭션 관리 기능 활성화</li>
 *   <li>데이터베이스 연결 및 성능 최적화 기반 마련</li>
 * </ul>
 * 
 * <p>데이터베이스 설정은 application.yml에서 관리되며,</p>
 * <p>필요에 따라 추가적인 데이터베이스 설정을 이 클래스에 추가할 수 있습니다.</p>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see EnableJpaRepositories
 * @see EnableTransactionManagement
 * @since 2024-01-01
 */
@Configuration
@EnableJpaRepositories(basePackages = "com.customs.clearance.repository")
@EnableTransactionManagement
public class DatabaseConfig {
    // 추가적인 데이터베이스 설정을 여기에 추가할 수 있습니다
    // 예: DataSource Bean, EntityManagerFactory Bean, 연결 풀 설정 등
}