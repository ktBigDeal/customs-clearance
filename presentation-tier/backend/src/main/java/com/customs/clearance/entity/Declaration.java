package com.customs.clearance.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * Declaration entity representing a customs declaration
 */
@Data
@Entity
@Table(name = "declarations")
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class Declaration extends BaseEntity {

    @NotBlank(message = "Declaration number is required")
    @Column(name = "declaration_number", unique = true, nullable = false)
    private String declarationNumber;

    @NotBlank(message = "Importer name is required")
    @Column(name = "importer_name", nullable = false)
    private String importerName;

    @NotBlank(message = "Exporter name is required")
    @Column(name = "exporter_name", nullable = false)
    private String exporterName;

    @NotNull(message = "Declaration date is required")
    @Column(name = "declaration_date", nullable = false)
    private LocalDate declarationDate;

    @NotNull(message = "Total value is required")
    @Column(name = "total_value", precision = 15, scale = 2, nullable = false)
    private BigDecimal totalValue;

    @NotBlank(message = "Currency is required")
    @Column(name = "currency", length = 3, nullable = false)
    private String currency;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private DeclarationStatus status = DeclarationStatus.PENDING;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @NotBlank(message = "Country of origin is required")
    @Column(name = "country_of_origin", nullable = false)
    private String countryOfOrigin;

    @NotBlank(message = "Port of entry is required")
    @Column(name = "port_of_entry", nullable = false)
    private String portOfEntry;

    public enum DeclarationStatus {
        PENDING,
        UNDER_REVIEW,
        APPROVED,
        REJECTED,
        CLEARED
    }
}