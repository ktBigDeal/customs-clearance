package com.customs.clearance.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 웹 관련 설정 컨피그레이션 클래스
 * 
 * Spring MVC의 웹 관련 설정을 커스터마이징하는 클래스입니다.
 * CORS 매핑, 인터셈터, 메시지 컨버터 등의 웹 MVC 설정을 제공합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>CORS 매핑 설정 (교차 원점 리소스 공유)</li>
 *   <li>API 경로별 접근 규칙 정의</li>
 *   <li>프론트엔드 애플리케이션과의 안전한 통신 보장</li>
 * </ul>
 * 
 * <p>이 설정은 SecurityConfig의 CORS 설정과 함께 작동하여 완전한 CORS 지원을 제공합니다.</p>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see WebMvcConfigurer
 * @see CorsRegistry
 * @since 2024-01-01
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(
                    "https://customs-backend-java.up.railway.app",
                    "https://customs-clearance-s3ro.vercel.app",
                    "http://localhost:3000",
                    "http://localhost:8080",
                    "https://vercel.app"
                )
                .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true);
    }
}