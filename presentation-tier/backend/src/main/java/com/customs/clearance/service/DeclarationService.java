package com.customs.clearance.service;

import com.customs.clearance.dto.DeclarationRequestDto;
import com.customs.clearance.dto.DeclarationResponseDto;
import com.customs.clearance.dto.DeclarationStatsDto;
import com.customs.clearance.entity.Declaration;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.time.LocalDate;
import java.util.List;

/**
 * 관세 신고서 비즈니스 로직 서비스 인터페이스
 * 
 * 관세 신고서의 모든 비즈니스 업무를 정의하는 서비스 계층 인터페이스입니다.
 * 이 인터페이스는 컨트롤러와 데이터 액세스 계층 사이의 비즈니스 로직을 추상화합니다.
 * 
 * <p>주요 비즈니스 기능:</p>
 * <ul>
 *   <li>신고서 생명주기 관리 (CRUD)</li>
 *   <li>비즈니스 규칙 검증</li>
 *   <li>데이터 무결성 보장</li>
 *   <li>다양한 검색 및 필터링 기능</li>
 *   <li>통계 정보 생성</li>
 * </ul>
 * 
 * <p>모든 메서드는 트랜잭션 경계 내에서 실행되며, 비즈니스 규칙을 준수합니다.</p>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see DeclarationServiceImpl
 * @see DeclarationRequestDto
 * @see DeclarationResponseDto
 * @since 2024-01-01
 */
public interface DeclarationService {

    /**
     * 새로운 관세 신고서를 생성합니다.
     * 
     * 사용자가 입력한 신고서 정보를 기반으로 새로운 신고서를 생성하고 데이터베이스에 저장합니다.
     * 신고서 번호의 중복 여부를 검사하여 데이터 무결성을 보장합니다.
     * 
     * @param requestDto 생성할 신고서의 상세 정보를 담고 있는 DTO
     * @return 생성된 신고서의 정보를 담고 있는 응답 DTO
     * @throws IllegalArgumentException 신고서 번호가 이미 존재하는 경우
     */
    DeclarationResponseDto createDeclaration(DeclarationRequestDto requestDto);

    /**
     * ID로 신고서를 조회합니다.
     * 
     * 주어진 ID에 해당하는 신고서의 상세 정보를 조회합니다.
     * 존재하지 않는 ID인 경우 예외를 발생시킵니다.
     * 
     * @param id 조회할 신고서의 고유 식별자
     * @return 조회된 신고서의 상세 정보를 담고 있는 응답 DTO
     * @throws ResourceNotFoundException 해당 ID의 신고서가 존재하지 않는 경우
     */
    DeclarationResponseDto getDeclarationById(Long id);

    /**
     * 신고서 번호로 신고서를 조회합니다.
     * 
     * 주어진 신고서 번호에 해당하는 신고서의 상세 정보를 조회합니다.
     * 신고서 번호는 대소문자를 구분하여 정확히 일치해야 합니다.
     * 
     * @param declarationNumber 조회할 신고서 번호
     * @return 조회된 신고서의 상세 정보를 담고 있는 응답 DTO
     * @throws ResourceNotFoundException 해당 번호의 신고서가 존재하지 않는 경우
     */
    DeclarationResponseDto getDeclarationByNumber(String declarationNumber);

    /**
     * 전체 신고서 목록을 페이지네이션과 함께 조회합니다.
     * 
     * 등록된 모든 신고서를 페이지 단위로 조회합니다.
     * 기본적으로 생성일시 내림차순으로 정렬됩니다.
     * 
     * @param pageable 페이지 번호, 사이즈, 정렬 조건을 담고 있는 페이지네이션 정보
     * @return 페이지네이션이 적용된 신고서 목록
     */
    Page<DeclarationResponseDto> getAllDeclarations(Pageable pageable);

    /**
     * 기존 신고서의 정보를 수정합니다.
     * 
     * 주어진 ID에 해당하는 신고서의 정보를 새로운 데이터로 업데이트합니다.
     * 신고서 번호가 변경되는 경우 중복 여부를 검사합니다.
     * 
     * @param id 수정할 신고서의 고유 식별자
     * @param requestDto 수정할 신고서 정보를 담고 있는 DTO
     * @return 수정된 신고서의 정보를 담고 있는 응답 DTO
     * @throws ResourceNotFoundException 해당 ID의 신고서가 존재하지 않는 경우
     * @throws IllegalArgumentException 수정하려는 신고서 번호가 이미 존재하는 경우
     */
    DeclarationResponseDto updateDeclaration(Long id, DeclarationRequestDto requestDto);

    /**
     * 신고서의 상태를 업데이트합니다.
     * 
     * 주어진 ID에 해당하는 신고서의 상태만을 선택적으로 업데이트합니다.
     * 다른 정보는 변경되지 않으며, 상태 전이 규칙을 검증합니다.
     * 
     * @param id 상태를 업데이트할 신고서의 고유 식별자
     * @param status 새로운 신고서 상태 (PENDING, UNDER_REVIEW, APPROVED, REJECTED, CLEARED)
     * @return 상태가 업데이트된 신고서의 정보를 담고 있는 응답 DTO
     * @throws ResourceNotFoundException 해당 ID의 신고서가 존재하지 않는 경우
     */
    DeclarationResponseDto updateDeclarationStatus(Long id, Declaration.DeclarationStatus status);

    /**
     * 신고서를 삭제합니다.
     * 
     * 주어진 ID에 해당하는 신고서를 데이터베이스에서 영구적으로 삭제합니다.
     * 삭제 전에 비즈니스 규칙 검증을 수행합니다.
     * 
     * @param id 삭제할 신고서의 고유 식별자
     * @throws ResourceNotFoundException 해당 ID의 신고서가 존재하지 않는 경우
     */
    void deleteDeclaration(Long id);

    /**
     * 특정 상태의 신고서 목록을 조회합니다.
     * 
     * 주어진 상태에 해당하는 모든 신고서를 조회합니다.
     * 상태별 업무 상황을 모니터링하는데 유용합니다.
     * 
     * @param status 조회할 신고서 상태
     * @return 해당 상태의 신고서 목록
     */
    List<DeclarationResponseDto> getDeclarationsByStatus(Declaration.DeclarationStatus status);

    /**
     * 수입업체명으로 신고서를 검색합니다.
     * 
     * 수입업체명에 특정 문자열이 포함된 신고서를 검색합니다.
     * 대소문자를 구분하지 않으며, 부분 일치 검색을 지원합니다.
     * 
     * @param importerName 검색할 수입업체명 (부분 일치 지원)
     * @param pageable 페이지네이션 정보
     * @return 검색 조건에 맞는 신고서 목록 (페이지네이션 적용)
     */
    Page<DeclarationResponseDto> searchByImporterName(String importerName, Pageable pageable);

    /**
     * 날짜 범위로 신고서를 조회합니다.
     * 
     * 시작일과 종료일 사이에 신고된 모든 신고서를 조회합니다.
     * 날짜 범위는 양쪽 끝점을 모두 포함합니다.
     * 
     * @param startDate 조회 시작일 (포함)
     * @param endDate 조회 종료일 (포함)
     * @return 날짜 범위에 해당하는 신고서 목록
     */
    List<DeclarationResponseDto> getDeclarationsByDateRange(LocalDate startDate, LocalDate endDate);

    /**
     * 원산지 국가별로 신고서를 조회합니다.
     * 
     * 특정 국가에서 수입된 모든 신고서를 조회합니다.
     * 국가명은 정확한 대소문자 일치로 검색됩니다.
     * 
     * @param countryOfOrigin 조회할 원산지 국가명
     * @return 해당 국가에서 수입된 신고서 목록
     */
    List<DeclarationResponseDto> getDeclarationsByCountry(String countryOfOrigin);

    /**
     * 최근 30일 간의 신고서를 조회합니다.
     * 
     * 현재 날짜를 기준으로 30일 이내에 신고된 모든 신고서를 조회합니다.
     * 주로 대시보드나 최근 업무 현황 모니터링에 사용됩니다.
     * 
     * @return 최근 30일 간의 신고서 목록 (생성일시 내림차순)
     */
    List<DeclarationResponseDto> getRecentDeclarations();

    /**
     * 신고서 통계 정보를 조회합니다.
     * 
     * 전체 신고서 건수, 상태별 건수 등의 통계 정보를 제공합니다.
     * 대시보드 및 리포트 기능에서 활용됩니다.
     * 
     * @return 전체 및 상태별 신고서 통계 정보
     */
    DeclarationStatsDto getDeclarationStats();
}