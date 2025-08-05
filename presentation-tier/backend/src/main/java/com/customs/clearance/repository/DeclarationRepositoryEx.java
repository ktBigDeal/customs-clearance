package com.customs.clearance.repository;

import com.customs.clearance.entity.DeclarationEx;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

/**
 * Repository interface for Declaration entity
 */
@Repository
public interface DeclarationRepositoryEx extends JpaRepository<DeclarationEx, Long> {

    /**
     * Find declaration by declaration number
     */
    Optional<DeclarationEx> findByDeclarationNumber(String declarationNumber);

    /**
     * Check if declaration number exists
     */
    boolean existsByDeclarationNumber(String declarationNumber);

    /**
     * Find declarations by status
     */
    List<DeclarationEx> findByStatus(DeclarationEx.DeclarationStatus status);

    /**
     * Find declarations by importer name containing (case insensitive)
     */
    Page<DeclarationEx> findByImporterNameContainingIgnoreCase(String importerName, Pageable pageable);

    /**
     * Find declarations by date range
     */
    @Query("SELECT d FROM Declaration d WHERE d.declarationDate BETWEEN :startDate AND :endDate")
    List<DeclarationEx> findByDeclarationDateBetween(
            @Param("startDate") LocalDate startDate, 
            @Param("endDate") LocalDate endDate);

    /**
     * Find declarations by country of origin
     */
    List<DeclarationEx> findByCountryOfOrigin(String countryOfOrigin);

    /**
     * Find declarations by port of entry
     */
    List<DeclarationEx> findByPortOfEntry(String portOfEntry);

    /**
     * Count declarations by status
     */
    long countByStatus(DeclarationEx.DeclarationStatus status);

    /**
     * Find recent declarations (last 30 days)
     */
    @Query("SELECT d FROM Declaration d WHERE d.declarationDate >= :thirtyDaysAgo ORDER BY d.declarationDate DESC")
    List<DeclarationEx> findRecentDeclarations(@Param("thirtyDaysAgo") LocalDate thirtyDaysAgo);
}