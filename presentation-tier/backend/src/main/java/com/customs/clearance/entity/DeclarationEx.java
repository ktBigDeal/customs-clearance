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
 * 관세 신고서 엔티티 클래스
 * 
 * 관세 신고서의 모든 데이터를 나타내는 JPA 엔티티입니다.
 * 수입/수출 신고서에 필요한 모든 필수 정보와 비즈니스 규칙을 포함합니다.
 * 
 * <p>주요 데이터 필드:</p>
 * <ul>
 *   <li>신고서 번호 (고유값, 중복 불가)</li>
 *   <li>수입업체 및 수출업체 정보</li>
 *   <li>신고 날짜 및 총 금액</li>
 *   <li>상태 관리 (PENDING → UNDER_REVIEW → APPROVED/REJECTED → CLEARED)</li>
 *   <li>원산지 및 통관 항구 정보</li>
 * </ul>
 * 
 * <p>데이터 무결성 및 검증:</p>
 * <ul>
 *   <li>Bean Validation API를 통한 필드 검증</li>
 *   <li>신고서 번호 유니크 제약</li>
 *   <li>금액 정밀도 설정 (15자리, 소수점 2자리)</li>
 * </ul>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see BaseEntity
 * @see DeclarationStatus
 * @since 2024-01-01
 */
@Data
@Entity
@Table(name = "declarations")
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class DeclarationEx extends BaseEntity {

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