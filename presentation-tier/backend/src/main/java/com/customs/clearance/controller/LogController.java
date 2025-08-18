package com.customs.clearance.controller;

import com.customs.clearance.dto.SystemLogDto;
import com.customs.clearance.service.SystemLogService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 프론트엔드에서 사용자 활동 로그를 기록하기 위한 컨트롤러
 * 
 * 사용자가 수행하는 다양한 활동(HS코드 추천, AI 챗봇 사용 등)을 
 * 프론트엔드에서 직접 로깅할 수 있도록 지원합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-18
 */
@Slf4j
@RestController
@RequestMapping("/logs")
@RequiredArgsConstructor
@CrossOrigin(origins = {"http://localhost:3000", "http://localhost:3001"})
public class LogController {

    private final SystemLogService systemLogService;

    /**
     * 사용자 활동 로그 기록
     * 
     * 프론트엔드에서 사용자의 다양한 활동을 로그로 기록합니다.
     * IP 주소, User-Agent 등 HTTP 요청 정보는 자동으로 추출됩니다.
     * 
     * @param request 로그 기록 요청 정보
     * @param httpRequest HTTP 요청 객체 (자동 주입)
     * @return 기록된 로그 정보
     */
    @PostMapping("/user-activity")
    public ResponseEntity<SystemLogDto.Response> logUserActivity(
            @RequestBody UserActivityLogRequest request,
            HttpServletRequest httpRequest) {
        
        // HTTP 요청에서 정보 추출
        String ipAddress = getClientIpAddress(httpRequest);
        String userAgent = httpRequest.getHeader("User-Agent");
        String requestUri = httpRequest.getRequestURI();
        String httpMethod = httpRequest.getMethod();
        
        log.info("사용자 활동 로그 기록: action={}, userId={}, source={}", 
                request.getAction(), request.getUserId(), request.getSource());
        
        // 로그 생성 요청 객체 생성
        SystemLogDto.CreateRequest logRequest = SystemLogDto.CreateRequest.builder()
                .level("INFO")
                .source(request.getSource())
                .message(request.getAction() + " 완료")
                .userId(request.getUserId())
                .userName(request.getUserName())
                .ipAddress(ipAddress)
                .userAgent(userAgent)
                .requestUri(requestUri)
                .httpMethod(httpMethod)
                .statusCode(200)
                .processingTime(request.getProcessingTime())
                .build();
        
        SystemLogDto.Response response = systemLogService.createLog(logRequest);
        
        return ResponseEntity.ok(response);
    }

    /**
     * 클라이언트 IP 주소 추출 (프록시 고려)
     */
    private String getClientIpAddress(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty() && !"unknown".equalsIgnoreCase(xForwardedFor)) {
            return xForwardedFor.split(",")[0].trim();
        }
        
        String xRealIp = request.getHeader("X-Real-IP");
        if (xRealIp != null && !xRealIp.isEmpty() && !"unknown".equalsIgnoreCase(xRealIp)) {
            return xRealIp;
        }
        
        return request.getRemoteAddr();
    }

    /**
     * 사용자 활동 로그 요청 DTO
     */
    public static class UserActivityLogRequest {
        private String action;          // 예: "HS코드 추천 조회", "AI 챗봇 대화"
        private String source;          // 예: "HSCODE", "CHATBOT", "OCR"
        private Long userId;            // 사용자 ID
        private String userName;        // 사용자명
        private Long processingTime;    // 처리 시간 (밀리초)
        private String details;         // 추가 상세 정보

        // Getters and Setters
        public String getAction() { return action; }
        public void setAction(String action) { this.action = action; }
        
        public String getSource() { return source; }
        public void setSource(String source) { this.source = source; }
        
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public String getUserName() { return userName; }
        public void setUserName(String userName) { this.userName = userName; }
        
        public Long getProcessingTime() { return processingTime; }
        public void setProcessingTime(Long processingTime) { this.processingTime = processingTime; }
        
        public String getDetails() { return details; }
        public void setDetails(String details) { this.details = details; }
    }
}