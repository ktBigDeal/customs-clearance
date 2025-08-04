package com.customs.clearance.service.impl;

import com.customs.clearance.dto.DeclarationRequestDto;
import com.customs.clearance.dto.DeclarationResponseDto;
import com.customs.clearance.dto.DeclarationStatsDto;
import com.customs.clearance.entity.Declaration;
import com.customs.clearance.exception.ResourceNotFoundException;
import com.customs.clearance.repository.DeclarationRepository;
import com.customs.clearance.service.DeclarationService;
import com.customs.clearance.util.DeclarationMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 관세 신고서 비즈니스 로직 서비스 구현체
 * 
 * 관세 신고서의 모든 비즈니스 로직을 구현하는 서비스 계층 구현체입니다.
 * 데이터 액세스, 데이터 변환, 비즈니스 규칙 검증 등을 담당합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>데이터 무결성 보장 (중복 방지, 제약 조건 검증)</li>
 *   <li>트랜잭션 관리 및 예외 처리</li>
 *   <li>DTO ↔ Entity 변환 로직</li>
 *   <li>로깅 및 모니터링</li>
 *   <li>비즈니스 규칙 적용</li>
 * </ul>
 * 
 * <p>모든 조회 메서드는 읽기 전용 트랜잭션에서 실행되며,</p>
 * <p>생성/수정/삭제 메서드는 쓰기 트랜잭션에서 실행됩니다.</p>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see DeclarationService
 * @see DeclarationRepository
 * @see DeclarationMapper
 * @since 2024-01-01
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DeclarationServiceImpl implements DeclarationService {

    private final DeclarationRepository declarationRepository;
    private final DeclarationMapper declarationMapper;

    @Override
    @Transactional
    public DeclarationResponseDto createDeclaration(DeclarationRequestDto requestDto) {
        log.info("Creating declaration with number: {}", requestDto.getDeclarationNumber());
        
        if (declarationRepository.existsByDeclarationNumber(requestDto.getDeclarationNumber())) {
            throw new IllegalArgumentException("Declaration number already exists: " + requestDto.getDeclarationNumber());
        }

        Declaration declaration = declarationMapper.toEntity(requestDto);
        Declaration savedDeclaration = declarationRepository.save(declaration);
        
        log.info("Declaration created successfully with ID: {}", savedDeclaration.getId());
        return declarationMapper.toResponseDto(savedDeclaration);
    }

    @Override
    public DeclarationResponseDto getDeclarationById(Long id) {
        log.info("Fetching declaration with ID: {}", id);
        Declaration declaration = declarationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Declaration not found with ID: " + id));
        return declarationMapper.toResponseDto(declaration);
    }

    @Override
    public DeclarationResponseDto getDeclarationByNumber(String declarationNumber) {
        log.info("Fetching declaration with number: {}", declarationNumber);
        Declaration declaration = declarationRepository.findByDeclarationNumber(declarationNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Declaration not found with number: " + declarationNumber));
        return declarationMapper.toResponseDto(declaration);
    }

    @Override
    public Page<DeclarationResponseDto> getAllDeclarations(Pageable pageable) {
        log.info("Fetching all declarations with pagination: page={}, size={}", pageable.getPageNumber(), pageable.getPageSize());
        Page<Declaration> declarations = declarationRepository.findAll(pageable);
        return declarations.map(declarationMapper::toResponseDto);
    }

    @Override
    @Transactional
    public DeclarationResponseDto updateDeclaration(Long id, DeclarationRequestDto requestDto) {
        log.info("Updating declaration with ID: {}", id);
        
        Declaration existingDeclaration = declarationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Declaration not found with ID: " + id));

        // Check if declaration number is being changed and already exists
        if (!existingDeclaration.getDeclarationNumber().equals(requestDto.getDeclarationNumber()) &&
            declarationRepository.existsByDeclarationNumber(requestDto.getDeclarationNumber())) {
            throw new IllegalArgumentException("Declaration number already exists: " + requestDto.getDeclarationNumber());
        }

        declarationMapper.updateEntityFromDto(requestDto, existingDeclaration);
        Declaration updatedDeclaration = declarationRepository.save(existingDeclaration);
        
        log.info("Declaration updated successfully with ID: {}", updatedDeclaration.getId());
        return declarationMapper.toResponseDto(updatedDeclaration);
    }

    @Override
    @Transactional
    public DeclarationResponseDto updateDeclarationStatus(Long id, Declaration.DeclarationStatus status) {
        log.info("Updating declaration status for ID: {} to status: {}", id, status);
        
        Declaration declaration = declarationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Declaration not found with ID: " + id));

        declaration.setStatus(status);
        Declaration updatedDeclaration = declarationRepository.save(declaration);
        
        log.info("Declaration status updated successfully for ID: {}", id);
        return declarationMapper.toResponseDto(updatedDeclaration);
    }

    @Override
    @Transactional
    public void deleteDeclaration(Long id) {
        log.info("Deleting declaration with ID: {}", id);
        
        if (!declarationRepository.existsById(id)) {
            throw new ResourceNotFoundException("Declaration not found with ID: " + id);
        }

        declarationRepository.deleteById(id);
        log.info("Declaration deleted successfully with ID: {}", id);
    }

    @Override
    public List<DeclarationResponseDto> getDeclarationsByStatus(Declaration.DeclarationStatus status) {
        log.info("Fetching declarations with status: {}", status);
        List<Declaration> declarations = declarationRepository.findByStatus(status);
        return declarations.stream()
                .map(declarationMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    @Override
    public Page<DeclarationResponseDto> searchByImporterName(String importerName, Pageable pageable) {
        log.info("Searching declarations by importer name: {}", importerName);
        Page<Declaration> declarations = declarationRepository.findByImporterNameContainingIgnoreCase(importerName, pageable);
        return declarations.map(declarationMapper::toResponseDto);
    }

    @Override
    public List<DeclarationResponseDto> getDeclarationsByDateRange(LocalDate startDate, LocalDate endDate) {
        log.info("Fetching declarations between dates: {} and {}", startDate, endDate);
        List<Declaration> declarations = declarationRepository.findByDeclarationDateBetween(startDate, endDate);
        return declarations.stream()
                .map(declarationMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    @Override
    public List<DeclarationResponseDto> getDeclarationsByCountry(String countryOfOrigin) {
        log.info("Fetching declarations for country: {}", countryOfOrigin);
        List<Declaration> declarations = declarationRepository.findByCountryOfOrigin(countryOfOrigin);
        return declarations.stream()
                .map(declarationMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    @Override
    public List<DeclarationResponseDto> getRecentDeclarations() {
        log.info("Fetching recent declarations (last 30 days)");
        LocalDate thirtyDaysAgo = LocalDate.now().minusDays(30);
        List<Declaration> declarations = declarationRepository.findRecentDeclarations(thirtyDaysAgo);
        return declarations.stream()
                .map(declarationMapper::toResponseDto)
                .collect(Collectors.toList());
    }

    @Override
    public DeclarationStatsDto getDeclarationStats() {
        log.info("Fetching declaration statistics");
        
        return new DeclarationStatsDto(
                declarationRepository.count(),
                declarationRepository.countByStatus(Declaration.DeclarationStatus.PENDING),
                declarationRepository.countByStatus(Declaration.DeclarationStatus.UNDER_REVIEW),
                declarationRepository.countByStatus(Declaration.DeclarationStatus.APPROVED),
                declarationRepository.countByStatus(Declaration.DeclarationStatus.REJECTED),
                declarationRepository.countByStatus(Declaration.DeclarationStatus.CLEARED)
        );
    }
}