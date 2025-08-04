package com.customs.clearance;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * 관세 통관 시스템 백엔드 API 게이트웨이 메인 애플리케이션 클래스
 * 
 * 이 애플리케이션은 관세 통관 업무를 위한 3-tier 아키텍처에서 
 * 프레젠테이션 계층 API 게이트웨이 역할을 담당합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>Spring Boot 기반 REST API 서버</li>
 *   <li>JPA 오디팅 기능 활성화 (생성/수정 일시 자동 관리)</li>
 *   <li>트랜잭션 관리 활성화</li>
 *   <li>관세 신고서 관리 API 제공</li>
 * </ul>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @since 2024-01-01
 */
@SpringBootApplication
@EnableJpaAuditing
@EnableTransactionManagement
public class CustomsClearanceBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(CustomsClearanceBackendApplication.class, args);
    }
}