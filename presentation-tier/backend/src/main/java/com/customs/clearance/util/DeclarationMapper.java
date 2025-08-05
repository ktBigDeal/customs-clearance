package com.customs.clearance.util;

import com.customs.clearance.dto.DeclarationRequestDto;
import com.customs.clearance.dto.DeclarationResponseDto;
import com.customs.clearance.entity.DeclarationEx;
import org.springframework.stereotype.Component;

/**
 * Mapper utility for Declaration entity and DTOs
 */
@Component
public class DeclarationMapper {

    /**
     * Convert DeclarationRequestDto to Declaration entity
     */
    public DeclarationEx toEntity(DeclarationRequestDto dto) {
        if (dto == null) {
            return null;
        }

        DeclarationEx declaration = new DeclarationEx();
        declaration.setDeclarationNumber(dto.getDeclarationNumber());
        declaration.setImporterName(dto.getImporterName());
        declaration.setExporterName(dto.getExporterName());
        declaration.setDeclarationDate(dto.getDeclarationDate());
        declaration.setTotalValue(dto.getTotalValue());
        declaration.setCurrency(dto.getCurrency());
        declaration.setDescription(dto.getDescription());
        declaration.setCountryOfOrigin(dto.getCountryOfOrigin());
        declaration.setPortOfEntry(dto.getPortOfEntry());
        declaration.setStatus(DeclarationEx.DeclarationStatus.PENDING);

        return declaration;
    }

    /**
     * Convert Declaration entity to DeclarationResponseDto
     */
    public DeclarationResponseDto toResponseDto(DeclarationEx entity) {
        if (entity == null) {
            return null;
        }

        DeclarationResponseDto dto = new DeclarationResponseDto();
        dto.setId(entity.getId());
        dto.setDeclarationNumber(entity.getDeclarationNumber());
        dto.setImporterName(entity.getImporterName());
        dto.setExporterName(entity.getExporterName());
        dto.setDeclarationDate(entity.getDeclarationDate());
        dto.setTotalValue(entity.getTotalValue());
        dto.setCurrency(entity.getCurrency());
        dto.setStatus(entity.getStatus());
        dto.setDescription(entity.getDescription());
        dto.setCountryOfOrigin(entity.getCountryOfOrigin());
        dto.setPortOfEntry(entity.getPortOfEntry());
        dto.setCreatedAt(entity.getCreatedAt());
        dto.setUpdatedAt(entity.getUpdatedAt());

        return dto;
    }

    /**
     * Update entity from DTO (for update operations)
     */
    public void updateEntityFromDto(DeclarationRequestDto dto, DeclarationEx entity) {
        if (dto == null || entity == null) {
            return;
        }

        entity.setDeclarationNumber(dto.getDeclarationNumber());
        entity.setImporterName(dto.getImporterName());
        entity.setExporterName(dto.getExporterName());
        entity.setDeclarationDate(dto.getDeclarationDate());
        entity.setTotalValue(dto.getTotalValue());
        entity.setCurrency(dto.getCurrency());
        entity.setDescription(dto.getDescription());
        entity.setCountryOfOrigin(dto.getCountryOfOrigin());
        entity.setPortOfEntry(dto.getPortOfEntry());
    }
}