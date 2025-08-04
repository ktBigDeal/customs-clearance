package com.customs.clearance.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 애플리케이션 상태 확인용 헬스 체크 컨트롤러
 * 
 * 시스템의 정상 동작 여부를 확인할 수 있는 공개 엔드포인트를 제공합니다.
 * 이 컸트롤러는 로드 밸런서, 모니터링 시스템에서 사용할 수 있는
 * 헬스 체크 및 애플리케이션 정보 API를 제공합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>애플리케이션 상태 확인 (UP/DOWN)</li>
 *   <li>서비스 메타데이터 제공</li>
 *   <li>버전 정보 제공</li>
 * </ul>
 * 
 * <p>모든 엔드포인트는 인증 없이 접근 가능한 공개 API입니다.</p>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @since 2024-01-01
 */
@Slf4j
@RestController
@RequestMapping("/public")
@Tag(name = "Health", description = "Health Check API")
public class HealthController {

    @Operation(summary = "Health check", description = "Returns the health status of the application")
    @ApiResponse(responseCode = "200", description = "Application is healthy")
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("timestamp", LocalDateTime.now());
        response.put("service", "customs-clearance-backend");
        response.put("version", "1.0.0");
        
        log.debug("Health check requested");
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Application info", description = "Returns application information")
    @ApiResponse(responseCode = "200", description = "Application information retrieved")
    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> info() {
        Map<String, Object> response = new HashMap<>();
        response.put("application", "Customs Clearance Backend");
        response.put("description", "API Gateway for Customs Clearance System");
        response.put("version", "1.0.0");
        response.put("environment", "development");
        response.put("timestamp", LocalDateTime.now());
        
        return ResponseEntity.ok(response);
    }
}