package com.customs.clearance.controller;

import com.customs.clearance.dto.DeclarationRequestDto;
import com.customs.clearance.dto.DeclarationResponseDto;
import com.customs.clearance.dto.DeclarationStatsDto;
import com.customs.clearance.entity.DeclarationEx;
import com.customs.clearance.service.DeclarationServiceEx;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

/**
 * 관세 신고서 관리 REST 컨트롤러
 * 
 * 관세 신고서의 CRUD 업무 및 다양한 검색 기능을 제공하는 REST API 엔드포인트를 정의합니다.
 * 이 컨트롤러는 전체 관세 통관 시스템의 핵심 비즈니스 로직을 담당합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>신고서 생성, 조회, 수정, 삭제 (CRUD)</li>
 *   <li>상태별, 국가별, 날짜별 검색</li>
 *   <li>수입업체명 기반 검색</li>
 *   <li>통계 정보 제공</li>
 *   <li>페이지네이션 지원</li>
 * </ul>
 * 
 * <p>API 버전: v1</p>
 * <p>기본 경로: /declarations</p>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see DeclarationServiceEx
 * @see DeclarationRequestDto
 * @see DeclarationResponseDto
 * @since 2024-01-01
 */
@Slf4j
@RestController
@RequestMapping("/declarations")
@RequiredArgsConstructor
@Tag(name = "Declaration", description = "Customs Declaration Management API")
public class DeclarationControllerEx {

    private final DeclarationServiceEx declarationService;

    @Operation(summary = "Create a new declaration", description = "Creates a new customs declaration")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "Declaration created successfully"),
            @ApiResponse(responseCode = "400", description = "Invalid input data"),
            @ApiResponse(responseCode = "409", description = "Declaration number already exists")
    })
    @PostMapping
    public ResponseEntity<DeclarationResponseDto> createDeclaration(
            @Valid @RequestBody DeclarationRequestDto requestDto) {
        log.info("Creating new declaration with number: {}", requestDto.getDeclarationNumber());
        DeclarationResponseDto response = declarationService.createDeclaration(requestDto);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @Operation(summary = "Get declaration by ID", description = "Retrieves a declaration by its ID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Declaration found"),
            @ApiResponse(responseCode = "404", description = "Declaration not found")
    })
    @GetMapping("/{id}")
    public ResponseEntity<DeclarationResponseDto> getDeclarationById(
            @Parameter(description = "Declaration ID") @PathVariable Long id) {
        log.info("Fetching declaration with ID: {}", id);
        DeclarationResponseDto response = declarationService.getDeclarationById(id);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get declaration by number", description = "Retrieves a declaration by its declaration number")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Declaration found"),
            @ApiResponse(responseCode = "404", description = "Declaration not found")
    })
    @GetMapping("/number/{declarationNumber}")
    public ResponseEntity<DeclarationResponseDto> getDeclarationByNumber(
            @Parameter(description = "Declaration number") @PathVariable String declarationNumber) {
        log.info("Fetching declaration with number: {}", declarationNumber);
        DeclarationResponseDto response = declarationService.getDeclarationByNumber(declarationNumber);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get all declarations", description = "Retrieves all declarations with pagination")
    @ApiResponse(responseCode = "200", description = "Declarations retrieved successfully")
    @GetMapping
    public ResponseEntity<Page<DeclarationResponseDto>> getAllDeclarations(
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("Fetching all declarations with pagination");
        Page<DeclarationResponseDto> response = declarationService.getAllDeclarations(pageable);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Update declaration", description = "Updates an existing declaration")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Declaration updated successfully"),
            @ApiResponse(responseCode = "400", description = "Invalid input data"),
            @ApiResponse(responseCode = "404", description = "Declaration not found"),
            @ApiResponse(responseCode = "409", description = "Declaration number already exists")
    })
    @PutMapping("/{id}")
    public ResponseEntity<DeclarationResponseDto> updateDeclaration(
            @Parameter(description = "Declaration ID") @PathVariable Long id,
            @Valid @RequestBody DeclarationRequestDto requestDto) {
        log.info("Updating declaration with ID: {}", id);
        DeclarationResponseDto response = declarationService.updateDeclaration(id, requestDto);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Update declaration status", description = "Updates the status of a declaration")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Status updated successfully"),
            @ApiResponse(responseCode = "404", description = "Declaration not found"),
            @ApiResponse(responseCode = "400", description = "Invalid status")
    })
    @PatchMapping("/{id}/status")
    public ResponseEntity<DeclarationResponseDto> updateDeclarationStatus(
            @Parameter(description = "Declaration ID") @PathVariable Long id,
            @Parameter(description = "New status") @RequestParam DeclarationEx.DeclarationStatus status) {
        log.info("Updating status for declaration ID: {} to status: {}", id, status);
        DeclarationResponseDto response = declarationService.updateDeclarationStatus(id, status);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Delete declaration", description = "Deletes a declaration by ID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "204", description = "Declaration deleted successfully"),
            @ApiResponse(responseCode = "404", description = "Declaration not found")
    })
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteDeclaration(
            @Parameter(description = "Declaration ID") @PathVariable Long id) {
        log.info("Deleting declaration with ID: {}", id);
        declarationService.deleteDeclaration(id);
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "Get declarations by status", description = "Retrieves declarations filtered by status")
    @ApiResponse(responseCode = "200", description = "Declarations retrieved successfully")
    @GetMapping("/status/{status}")
    public ResponseEntity<List<DeclarationResponseDto>> getDeclarationsByStatus(
            @Parameter(description = "Declaration status") @PathVariable DeclarationEx.DeclarationStatus status) {
        log.info("Fetching declarations with status: {}", status);
        List<DeclarationResponseDto> response = declarationService.getDeclarationsByStatus(status);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Search declarations by importer", description = "Searches declarations by importer name")
    @ApiResponse(responseCode = "200", description = "Search results retrieved successfully")
    @GetMapping("/search")
    public ResponseEntity<Page<DeclarationResponseDto>> searchByImporterName(
            @Parameter(description = "Importer name to search") @RequestParam String importerName,
            @PageableDefault(size = 20) Pageable pageable) {
        log.info("Searching declarations by importer name: {}", importerName);
        Page<DeclarationResponseDto> response = declarationService.searchByImporterName(importerName, pageable);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get declarations by date range", description = "Retrieves declarations within a date range")
    @ApiResponse(responseCode = "200", description = "Declarations retrieved successfully")
    @GetMapping("/date-range")
    public ResponseEntity<List<DeclarationResponseDto>> getDeclarationsByDateRange(
            @Parameter(description = "Start date (yyyy-MM-dd)") 
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @Parameter(description = "End date (yyyy-MM-dd)") 
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {
        log.info("Fetching declarations between dates: {} and {}", startDate, endDate);
        List<DeclarationResponseDto> response = declarationService.getDeclarationsByDateRange(startDate, endDate);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get declarations by country", description = "Retrieves declarations by country of origin")
    @ApiResponse(responseCode = "200", description = "Declarations retrieved successfully")
    @GetMapping("/country/{country}")
    public ResponseEntity<List<DeclarationResponseDto>> getDeclarationsByCountry(
            @Parameter(description = "Country of origin") @PathVariable String country) {
        log.info("Fetching declarations for country: {}", country);
        List<DeclarationResponseDto> response = declarationService.getDeclarationsByCountry(country);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get recent declarations", description = "Retrieves declarations from the last 30 days")
    @ApiResponse(responseCode = "200", description = "Recent declarations retrieved successfully")
    @GetMapping("/recent")
    public ResponseEntity<List<DeclarationResponseDto>> getRecentDeclarations() {
        log.info("Fetching recent declarations");
        List<DeclarationResponseDto> response = declarationService.getRecentDeclarations();
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get declaration statistics", description = "Retrieves statistics about declarations")
    @ApiResponse(responseCode = "200", description = "Statistics retrieved successfully")
    @GetMapping("/stats")
    public ResponseEntity<DeclarationStatsDto> getDeclarationStats() {
        log.info("Fetching declaration statistics");
        DeclarationStatsDto response = declarationService.getDeclarationStats();
        return ResponseEntity.ok(response);
    }
}