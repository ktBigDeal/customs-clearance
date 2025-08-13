package com.customs.clearance.dto;

import com.customs.clearance.entity.Declaration;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.*;

import java.time.LocalDateTime;

/**
 * 관리자용 신고서 조회 DTO
 * 
 * 사용자 정보가 포함된 신고서 정보를 관리자에게 제공합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-14
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeclarationAdminDto {
    
    private Long id;
    private String declarationNumber;
    private String declarationType;
    private String status;
    private String declarationDetails;
    private String notes;
    
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createdAt;
    
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updatedAt;
    
    // 사용자 정보 필드들
    private Long userId;
    private String userName;
    private String userEmail;
    private String userCompany;
    
    /**
     * Declaration 엔티티를 관리자용 DTO로 변환
     * (사용자 정보는 별도로 설정 필요)
     */
    public static DeclarationAdminDto fromEntity(Declaration declaration) {
        return DeclarationAdminDto.builder()
                .id(declaration.getId())
                .declarationNumber(declaration.getDeclarationNumber())
                .declarationType(declaration.getDeclarationType().name())
                .status(declaration.getStatus().name())
                .declarationDetails(declaration.getDeclarationDetails())
                .notes(declaration.getNotes())
                .createdAt(declaration.getCreatedAt())
                .updatedAt(declaration.getUpdatedAt())
                .userId(declaration.getCreatedBy())
                .build();
    }
    
    /**
     * 사용자 정보 설정
     */
    public DeclarationAdminDto withUserInfo(String userName, String userEmail, String userCompany) {
        this.userName = userName;
        this.userEmail = userEmail;
        this.userCompany = userCompany;
        return this;
    }
}