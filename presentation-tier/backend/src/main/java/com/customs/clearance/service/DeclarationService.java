package com.customs.clearance.service;

import com.customs.clearance.dto.DeclarationRequestDto;
import com.customs.clearance.dto.DeclarationResponseDto;
import com.customs.clearance.dto.DeclarationStatsDto;
import com.customs.clearance.entity.Declaration;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.time.LocalDate;
import java.util.List;

/**
 * Service interface for Declaration operations
 */
public interface DeclarationService {

    /**
     * Create a new declaration
     */
    DeclarationResponseDto createDeclaration(DeclarationRequestDto requestDto);

    /**
     * Get declaration by ID
     */
    DeclarationResponseDto getDeclarationById(Long id);

    /**
     * Get declaration by declaration number
     */
    DeclarationResponseDto getDeclarationByNumber(String declarationNumber);

    /**
     * Get all declarations with pagination
     */
    Page<DeclarationResponseDto> getAllDeclarations(Pageable pageable);

    /**
     * Update declaration
     */
    DeclarationResponseDto updateDeclaration(Long id, DeclarationRequestDto requestDto);

    /**
     * Update declaration status
     */
    DeclarationResponseDto updateDeclarationStatus(Long id, Declaration.DeclarationStatus status);

    /**
     * Delete declaration
     */
    void deleteDeclaration(Long id);

    /**
     * Get declarations by status
     */
    List<DeclarationResponseDto> getDeclarationsByStatus(Declaration.DeclarationStatus status);

    /**
     * Search declarations by importer name
     */
    Page<DeclarationResponseDto> searchByImporterName(String importerName, Pageable pageable);

    /**
     * Get declarations by date range
     */
    List<DeclarationResponseDto> getDeclarationsByDateRange(LocalDate startDate, LocalDate endDate);

    /**
     * Get declarations by country of origin
     */
    List<DeclarationResponseDto> getDeclarationsByCountry(String countryOfOrigin);

    /**
     * Get recent declarations (last 30 days)
     */
    List<DeclarationResponseDto> getRecentDeclarations();

    /**
     * Get declaration statistics
     */
    DeclarationStatsDto getDeclarationStats();
}