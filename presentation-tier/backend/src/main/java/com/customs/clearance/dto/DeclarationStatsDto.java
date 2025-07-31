package com.customs.clearance.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO for declaration statistics
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DeclarationStatsDto {
    private long totalDeclarations;
    private long pendingDeclarations;
    private long underReviewDeclarations;
    private long approvedDeclarations;
    private long rejectedDeclarations;
    private long clearedDeclarations;
}