package com.customs.clearance.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * DTO for declaration creation/update requests
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DeclarationRequestDto {

    @NotBlank(message = "Declaration number is required")
    @Size(max = 50, message = "Declaration number must not exceed 50 characters")
    private String declarationNumber;

    @NotBlank(message = "Importer name is required")
    @Size(max = 100, message = "Importer name must not exceed 100 characters")
    private String importerName;

    @NotBlank(message = "Exporter name is required")
    @Size(max = 100, message = "Exporter name must not exceed 100 characters")
    private String exporterName;

    @NotNull(message = "Declaration date is required")
    @PastOrPresent(message = "Declaration date cannot be in the future")
    private LocalDate declarationDate;

    @NotNull(message = "Total value is required")
    @DecimalMin(value = "0.01", message = "Total value must be greater than 0")
    @Digits(integer = 13, fraction = 2, message = "Total value format is invalid")
    private BigDecimal totalValue;

    @NotBlank(message = "Currency is required")
    @Size(min = 3, max = 3, message = "Currency must be 3 characters")
    @Pattern(regexp = "^[A-Z]{3}$", message = "Currency must be a valid 3-letter code")
    private String currency;

    @Size(max = 1000, message = "Description must not exceed 1000 characters")
    private String description;

    @NotBlank(message = "Country of origin is required")
    @Size(max = 50, message = "Country of origin must not exceed 50 characters")
    private String countryOfOrigin;

    @NotBlank(message = "Port of entry is required")
    @Size(max = 50, message = "Port of entry must not exceed 50 characters")
    private String portOfEntry;
}