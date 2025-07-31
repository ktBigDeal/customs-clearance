package com.customs.clearance.dto;

import com.customs.clearance.entity.Declaration;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * DTO for declaration responses
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DeclarationResponseDto {

    private Long id;
    private String declarationNumber;
    private String importerName;
    private String exporterName;
    private LocalDate declarationDate;
    private BigDecimal totalValue;
    private String currency;
    private Declaration.DeclarationStatus status;
    private String description;
    private String countryOfOrigin;
    private String portOfEntry;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}