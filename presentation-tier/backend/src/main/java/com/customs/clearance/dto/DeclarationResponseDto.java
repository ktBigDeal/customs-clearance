package com.customs.clearance.dto;

import com.customs.clearance.entity.DeclarationEx;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 관세 신고서 응답용 DTO 클래스
 * 
 * 서버에서 클라이언트로 전송하는 신고서 데이터를 담는 데이터 전송 객체입니다.
 * 엔티티의 모든 정보를 포함하며, 민감한 내부 정보는 제외하고 외부에 노출합니다.
 * 
 * <p>포함되는 주요 정보:</p>
 * <ul>
 *   <li>신고서 기본 정보 (번호, 업체명, 날짜, 금액)</li>
 *   <li>상태 정보 (대기, 심사중, 승인, 거부, 통관완료)</li>
 *   <li>물류 정보 (원산지, 항구, 설명)</li>
 *   <li>감사 정보 (생성일시, 수정일시)</li>
 * </ul>
 * 
 * <p>사용 예시:</p>
 * <pre>
 * GET /api/v1/declarations/{id}
 * GET /api/v1/declarations
 * </pre>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see DeclarationEx
 * @see DeclarationRequestDto
 * @since 2024-01-01
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
    private DeclarationEx.DeclarationStatus status;
    private String description;
    private String countryOfOrigin;
    private String portOfEntry;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}