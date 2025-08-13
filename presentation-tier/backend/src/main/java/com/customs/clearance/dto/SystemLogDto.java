package com.customs.clearance.dto;

import com.customs.clearance.entity.SystemLog;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 시스템 로그 관련 DTO 클래스들
 * 
 * API 요청/응답에서 사용되는 데이터 전송 객체들을 정의합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-13
 */
public class SystemLogDto {

    /**
     * 로그 응답 DTO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Response {
        private Long id;
        
        @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
        private LocalDateTime timestamp;
        
        private String level;
        private String source;
        private String message;
        private Long userId;
        private String userName;
        private String ipAddress;
        private String userAgent;
        private String requestUri;
        private String httpMethod;
        private Integer statusCode;
        private Long processingTime;

        /**
         * Entity를 DTO로 변환
         */
        public static Response from(SystemLog log) {
            return Response.builder()
                    .id(log.getId())
                    .timestamp(log.getTimestamp())
                    .level(log.getLevel().name())
                    .source(log.getSource())
                    .message(log.getMessage())
                    .userId(log.getUserId())
                    .userName(log.getUserName())
                    .ipAddress(log.getIpAddress())
                    .userAgent(log.getUserAgent())
                    .requestUri(log.getRequestUri())
                    .httpMethod(log.getHttpMethod())
                    .statusCode(log.getStatusCode())
                    .processingTime(log.getProcessingTime())
                    .build();
        }
    }

    /**
     * 로그 목록 응답 DTO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ListResponse {
        private List<Response> logs;
        private long totalCount;
        private int page;
        private int size;
        private int totalPages;
        private boolean hasNext;
        private boolean hasPrevious;
    }

    /**
     * 로그 검색 요청 DTO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SearchRequest {
        private String keyword;
        private String level;
        private String source;
        private String dateFilter; // today, week, month, all
        private int page = 0;
        private int size = 20;
        
        @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
        private LocalDateTime startDate;
        
        @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
        private LocalDateTime endDate;
    }

    /**
     * 로그 통계 응답 DTO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class StatsResponse {
        private Long totalLogs;
        private Long errorCount;
        private Long warnCount;
        private Long infoCount;
        private Long debugCount;
        private Double errorRate;
    }

    /**
     * 로그 생성 요청 DTO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CreateRequest {
        private String level;
        private String source;
        private String message;
        private Long userId;
        private String userName;
        private String ipAddress;
        private String userAgent;
        private String requestUri;
        private String httpMethod;
        private Integer statusCode;
        private Long processingTime;
    }
}