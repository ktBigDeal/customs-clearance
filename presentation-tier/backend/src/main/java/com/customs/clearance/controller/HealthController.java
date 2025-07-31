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
 * Health check controller for public endpoints
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