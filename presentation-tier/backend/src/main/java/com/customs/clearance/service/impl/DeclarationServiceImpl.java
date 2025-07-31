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
 * Implementation of DeclarationService
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