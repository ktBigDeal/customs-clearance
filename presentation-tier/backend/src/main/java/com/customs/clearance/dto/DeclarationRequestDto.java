package com.customs.clearance.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 관세 신고서 생성/수정 요청용 DTO 클래스
 * 
 * 클라이언트로부터 받는 신고서 데이터를 담는 데이터 전송 객체입니다.
 * Bean Validation API를 통해 입력 데이터의 유효성을 검증하고 비즈니스 규칙을 적용합니다.
 * 
 * <p>주요 검증 규칙:</p>
 * <ul>
 *   <li>신고서 번호: 필수, 50자 이내</li>
 *   <li>수입/수출업체명: 필수, 100자 이내</li>
 *   <li>신고일자: 필수, 미래 날짜 불가</li>
 *   <li>총 금액: 필수, 0.01 이상, 소수점 2자리</li>
 *   <li>통화 코드: 3자리 대문자 알파벳</li>
 *   <li>원산지/항구: 필수, 50자 이내</li>
 * </ul>
 * 
 * <p>사용 예시:</p>
 * <pre>
 * POST /api/v1/declarations
 * PUT /api/v1/declarations/{id}
 * </pre>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see Declaration
 * @see DeclarationResponseDto
 * @since 2024-01-01
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