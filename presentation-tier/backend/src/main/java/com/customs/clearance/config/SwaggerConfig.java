package com.customs.clearance.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springframework.context.annotation.Configuration;

/** * Swagger 설정을 위한 클래스입니다.
 * <p>
 * OpenAPI 3.0 스펙을 사용하여 API 문서를 생성합니다.
 * Bearer 토큰 인증을 사용하며, JWT 토큰을 통해 API 접근을 보호합니다.
 * <p>
 * Swagger UI를 통해 API 문서를 시각적으로 확인할 수 있습니다.
 * <p> 
 * 이 클래스는 Swagger 설정을 위한 기본 구성을 제공합니다.
 * <p>
 * @author Customs Clearance Team
 * @version 1.0
 * @see OpenAPIDefinition
 * @see SecurityScheme
 * @since 2024-01-01
 */
@Configuration
@OpenAPIDefinition(
    security = @SecurityRequirement(name = "bearerAuth")
)
@SecurityScheme(
    name = "bearerAuth",
    type = SecuritySchemeType.HTTP,
    scheme = "bearer",
    bearerFormat = "JWT"
)
public class SwaggerConfig {
    
}
