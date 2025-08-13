package com.customs.clearance.service;

import com.customs.clearance.dto.SystemLogDto;
import com.customs.clearance.entity.SystemLog;
import com.customs.clearance.repository.SystemLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * 시스템 로그 관련 비즈니스 로직을 처리하는 서비스
 * 
 * 로그 조회, 생성, 통계 등의 기능을 제공합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-13
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class SystemLogService {

    private final SystemLogRepository systemLogRepository;

    /**
     * 로그 목록을 페이지네이션으로 조회
     */
    public SystemLogDto.ListResponse getLogs(SystemLogDto.SearchRequest request) {
        Pageable pageable = PageRequest.of(request.getPage(), request.getSize());
        
        // 날짜 필터 처리
        LocalDateTime startDate = getStartDateFromFilter(request.getDateFilter(), request.getStartDate());
        LocalDateTime endDate = request.getEndDate() != null ? request.getEndDate() : LocalDateTime.now();
        
        // 로그 레벨 변환
        SystemLog.LogLevel level = null;
        if (request.getLevel() != null && !request.getLevel().equals("all")) {
            try {
                level = SystemLog.LogLevel.valueOf(request.getLevel().toUpperCase());
            } catch (IllegalArgumentException e) {
                log.warn("Invalid log level: {}", request.getLevel());
            }
        }

        // 소스 필터 처리
        String source = request.getSource() != null && !request.getSource().equals("all") 
                ? request.getSource() : null;

        // 검색어 처리
        String keyword = request.getKeyword() != null && !request.getKeyword().trim().isEmpty() 
                ? request.getKeyword().trim() : null;

        // 복합 조건으로 검색
        Page<SystemLog> logPage = systemLogRepository.findByFilters(
                level, source, startDate, endDate, keyword, pageable
        );

        // DTO 변환
        List<SystemLogDto.Response> logs = logPage.getContent().stream()
                .map(SystemLogDto.Response::from)
                .toList();

        return SystemLogDto.ListResponse.builder()
                .logs(logs)
                .totalCount(logPage.getTotalElements())
                .page(logPage.getNumber())
                .size(logPage.getSize())
                .totalPages(logPage.getTotalPages())
                .hasNext(logPage.hasNext())
                .hasPrevious(logPage.hasPrevious())
                .build();
    }

    /**
     * 로그 통계 조회
     */
    public SystemLogDto.StatsResponse getStats(String dateFilter) {
        LocalDateTime startDate = getStartDateFromFilter(dateFilter, null);
        
        // 전체 로그 수
        long totalLogs = systemLogRepository.count();
        
        // 레벨별 통계
        List<Object[]> levelStats = systemLogRepository.countByLevelAfterDate(startDate);
        
        long errorCount = 0;
        long warnCount = 0;
        long infoCount = 0;
        long debugCount = 0;
        
        for (Object[] stat : levelStats) {
            SystemLog.LogLevel level = (SystemLog.LogLevel) stat[0];
            Long count = (Long) stat[1];
            
            switch (level) {
                case ERROR -> errorCount = count;
                case WARN -> warnCount = count;
                case INFO -> infoCount = count;
                case DEBUG -> debugCount = count;
            }
        }
        
        // 에러율 계산 (전체 로그 중 에러 로그의 비율)
        double errorRate = totalLogs > 0 ? (double) errorCount / totalLogs * 100 : 0;
        
        return SystemLogDto.StatsResponse.builder()
                .totalLogs(totalLogs)
                .errorCount(errorCount)
                .warnCount(warnCount)
                .infoCount(infoCount)
                .debugCount(debugCount)
                .errorRate(Math.round(errorRate * 100.0) / 100.0) // 소수점 2자리까지
                .build();
    }

    /**
     * 새로운 로그 생성
     */
    @Transactional
    public SystemLogDto.Response createLog(SystemLogDto.CreateRequest request) {
        SystemLog.LogLevel level;
        try {
            level = SystemLog.LogLevel.valueOf(request.getLevel().toUpperCase());
        } catch (IllegalArgumentException e) {
            level = SystemLog.LogLevel.INFO;
        }

        SystemLog log = SystemLog.builder()
                .timestamp(LocalDateTime.now())
                .level(level)
                .source(request.getSource())
                .message(request.getMessage())
                .userId(request.getUserId())
                .userName(request.getUserName())
                .ipAddress(request.getIpAddress())
                .userAgent(request.getUserAgent())
                .requestUri(request.getRequestUri())
                .httpMethod(request.getHttpMethod())
                .statusCode(request.getStatusCode())
                .processingTime(request.getProcessingTime())
                .build();

        SystemLog savedLog = systemLogRepository.save(log);
        return SystemLogDto.Response.from(savedLog);
    }

    /**
     * 날짜 필터를 실제 날짜로 변환
     */
    private LocalDateTime getStartDateFromFilter(String dateFilter, LocalDateTime customStartDate) {
        if (customStartDate != null) {
            return customStartDate;
        }
        
        LocalDateTime now = LocalDateTime.now();
        
        return switch (dateFilter) {
            case "today" -> now.toLocalDate().atStartOfDay();
            case "week" -> now.minusWeeks(1);
            case "month" -> now.minusMonths(1);
            case "year" -> now.minusYears(1);
            default -> now.minusDays(30); // 기본값: 30일 전
        };
    }

    /**
     * 시스템 이벤트를 로그로 기록하는 헬퍼 메서드
     */
    @Transactional
    public void logSystemEvent(String source, String message, SystemLog.LogLevel level) {
        SystemLog log = SystemLog.builder()
                .timestamp(LocalDateTime.now())
                .level(level)
                .source(source)
                .message(message)
                .build();
        
        systemLogRepository.save(log);
    }

    /**
     * 사용자 활동을 로그로 기록하는 헬퍼 메서드
     */
    @Transactional
    public void logUserActivity(String source, String message, Long userId, String userName, 
                               String ipAddress, String userAgent, String requestUri, 
                               String httpMethod, Integer statusCode, Long processingTime) {
        SystemLog log = SystemLog.builder()
                .timestamp(LocalDateTime.now())
                .level(SystemLog.LogLevel.INFO)
                .source(source)
                .message(message)
                .userId(userId)
                .userName(userName)
                .ipAddress(ipAddress)
                .userAgent(userAgent)
                .requestUri(requestUri)
                .httpMethod(httpMethod)
                .statusCode(statusCode)
                .processingTime(processingTime)
                .build();
        
        systemLogRepository.save(log);
    }
}