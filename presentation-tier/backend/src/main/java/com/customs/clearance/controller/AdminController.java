package com.customs.clearance.controller;

import com.customs.clearance.dto.SystemLogDto;
import com.customs.clearance.service.SystemLogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 관리자 기능을 위한 REST API 컨트롤러
 * 
 * 관리자 전용 기능들(로그 조회, 시스템 통계 등)을 제공합니다.
 * ADMIN 권한이 있는 사용자만 접근할 수 있습니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-13
 */
@Tag(name = "Admin", description = "관리자 전용 API")
@Slf4j
@RestController
@RequestMapping("/admin")
@RequiredArgsConstructor
@CrossOrigin(origins = {"http://localhost:3000", "http://localhost:3001"})
public class AdminController {

    private final SystemLogService systemLogService;

    /**
     * 시스템 로그 목록 조회
     * 
     * 관리자가 시스템 로그를 조회할 수 있는 API입니다.
     * 다양한 필터링 옵션을 지원하여 원하는 로그만 조회할 수 있습니다.
     * 
     * @param request 검색 조건 (키워드, 레벨, 소스, 날짜 등)
     * @return 조회된 로그 목록과 페이지네이션 정보
     */
    @Operation(
        summary = "시스템 로그 조회", 
        description = "관리자용 시스템 로그 목록을 페이지네이션으로 조회합니다. 키워드, 로그 레벨, 소스, 날짜 범위 등으로 필터링할 수 있습니다."
    )
    @PostMapping("/logs/search")
    public ResponseEntity<SystemLogDto.ListResponse> getLogs(
            @Parameter(description = "로그 검색 조건") 
            @RequestBody SystemLogDto.SearchRequest request) {
        
        log.info("관리자 로그 조회 요청: page={}, size={}, keyword={}, level={}, source={}", 
                request.getPage(), request.getSize(), request.getKeyword(), 
                request.getLevel(), request.getSource());
        
        SystemLogDto.ListResponse response = systemLogService.getLogs(request);
        
        log.info("관리자 로그 조회 완료: 총 {}개 로그, {}페이지", 
                response.getTotalCount(), response.getTotalPages());
        
        return ResponseEntity.ok(response);
    }

    /**
     * 간편한 로그 조회 (GET 방식)
     * 
     * 기본적인 필터링으로 로그를 조회하는 간단한 API입니다.
     * 
     * @param page 페이지 번호 (0부터 시작)
     * @param size 페이지 크기
     * @param keyword 검색 키워드
     * @param level 로그 레벨 필터
     * @param source 소스 필터  
     * @param dateFilter 날짜 필터
     * @return 조회된 로그 목록
     */
    @Operation(
        summary = "간편 로그 조회", 
        description = "GET 방식으로 시스템 로그를 간편하게 조회합니다."
    )
    @GetMapping("/logs")
    public ResponseEntity<SystemLogDto.ListResponse> getLogsSimple(
            @Parameter(description = "페이지 번호 (0부터 시작)") 
            @RequestParam(defaultValue = "0") int page,
            
            @Parameter(description = "페이지 크기") 
            @RequestParam(defaultValue = "20") int size,
            
            @Parameter(description = "검색 키워드") 
            @RequestParam(required = false) String keyword,
            
            @Parameter(description = "로그 레벨 (ERROR, WARN, INFO, DEBUG, all)") 
            @RequestParam(defaultValue = "all") String level,
            
            @Parameter(description = "소스 필터") 
            @RequestParam(defaultValue = "all") String source,
            
            @Parameter(description = "날짜 필터 (today, week, month, all)") 
            @RequestParam(defaultValue = "today") String dateFilter) {
        
        SystemLogDto.SearchRequest request = SystemLogDto.SearchRequest.builder()
                .page(page)
                .size(size)
                .keyword(keyword)
                .level(level)
                .source(source)
                .dateFilter(dateFilter)
                .build();
        
        return ResponseEntity.ok(systemLogService.getLogs(request));
    }

    /**
     * 로그 통계 조회
     * 
     * 로그 레벨별 개수, 에러율 등의 통계 정보를 조회합니다.
     * 
     * @param dateFilter 통계 기간 (today, week, month, all)
     * @return 로그 통계 정보
     */
    @Operation(
        summary = "로그 통계 조회", 
        description = "로그 레벨별 개수, 에러율 등의 통계 정보를 조회합니다."
    )
    @GetMapping("/logs/stats")
    public ResponseEntity<SystemLogDto.StatsResponse> getLogStats(
            @Parameter(description = "통계 기간 (today, week, month, all)") 
            @RequestParam(defaultValue = "today") String dateFilter) {
        
        log.info("로그 통계 조회 요청: dateFilter={}", dateFilter);
        
        SystemLogDto.StatsResponse stats = systemLogService.getStats(dateFilter);
        
        log.info("로그 통계 조회 완료: 전체 {}개, 에러 {}개, 에러율 {}%", 
                stats.getTotalLogs(), stats.getErrorCount(), stats.getErrorRate());
        
        return ResponseEntity.ok(stats);
    }

    /**
     * 새 로그 생성 (테스트용)
     * 
     * 테스트 목적으로 새로운 로그를 생성합니다.
     * 실제 운영환경에서는 시스템에서 자동으로 로그가 생성됩니다.
     * 
     * @param request 생성할 로그 정보
     * @return 생성된 로그 정보
     */
    @Operation(
        summary = "테스트 로그 생성", 
        description = "테스트 목적으로 새로운 시스템 로그를 생성합니다."
    )
    @PostMapping("/logs")
    public ResponseEntity<SystemLogDto.Response> createLog(
            @Parameter(description = "생성할 로그 정보") 
            @RequestBody SystemLogDto.CreateRequest request) {
        
        log.info("테스트 로그 생성 요청: level={}, source={}, message={}", 
                request.getLevel(), request.getSource(), request.getMessage());
        
        SystemLogDto.Response response = systemLogService.createLog(request);
        
        log.info("테스트 로그 생성 완료: id={}", response.getId());
        
        return ResponseEntity.ok(response);
    }

    /**
     * 헬스체크용 엔드포인트
     */
    @Operation(summary = "관리자 API 상태 확인", description = "관리자 API의 상태를 확인합니다.")
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Admin API is running");
    }
}