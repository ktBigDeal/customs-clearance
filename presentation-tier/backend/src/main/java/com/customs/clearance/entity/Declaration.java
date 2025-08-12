// src/main/java/com/customs/clearance/entity/Declaration.java
package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.*;

/**
 * 수입/수출 신고 정보를 나타내는 JPA 엔티티입니다.
 * <p>
 * 각 신고는 고유 번호, 신고 유형, 상태, 상세 정보, 비고 등을 포함합니다.
 * 생성자/수정자 정보 및 생성/수정 시점은 {@link BaseEntity}를 통해 자동으로 관리됩니다.
 * 
 * @author Customs Clearance Team
 * @version 1.0
 */
@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "declarations", uniqueConstraints = @UniqueConstraint(columnNames = "declaration_number"))
public class Declaration extends BaseEntity {

    /** 수입 또는 수출 신고 고유 번호 */
    @Column(name = "declaration_number", length = 50, nullable = false, unique = true)
    private String declarationNumber;

    /** 신고 유형 (IMPORT 또는 EXPORT) */
    @Enumerated(EnumType.STRING)
    @Column(name = "declaration_type", nullable = false)
    private DeclarationType declarationType;

    /** 신고 상태 */
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private DeclarationStatus status = DeclarationStatus.DRAFT;

    /** 신고 상세 내용 */
    @Column(name = "declaration_details", columnDefinition = "TEXT")
    private String declarationDetails;

    /** 기타 비고 사항 */
    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    /** 신고를 생성한 사용자 ID */
    @Column(name = "created_by")
    private Long createdBy;

    /** 신고를 마지막으로 수정한 사용자 ID */
    @Column(name = "updated_by")
    private Long updatedBy;

    /** 신고 유형 ENUM */
    public enum DeclarationType {
        IMPORT, EXPORT
    }

    /** 신고 상태 ENUM */
    public enum DeclarationStatus {
        DRAFT,
        UPDATED,
        SUBMITTED,
        APPROVED,
        REJECTED
    }
}
