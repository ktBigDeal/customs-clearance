package com.customs.clearance.repository;

import com.customs.clearance.entity.Declaration;
import com.customs.clearance.entity.Declaration.DeclarationStatus;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

/**
 * {@link Declaration} 엔티티에 대한 기본 CRUD 연산을 처리하는 Spring Data JPA 리포지토리입니다.
 * <p>
 * 신고번호로 단건 조회하는 기능이 포함되어 있습니다.
 * 
 * @author Customs Clearance Team
 * @version 1.0
 */
public interface DeclarationRepository extends JpaRepository<Declaration, Long> {
    /**
     * 고유한 신고번호로 신고 정보를 조회합니다.
     *
     * @param declarationNumber 조회할 신고번호
     * @return 해당 신고번호에 대한 {@link Declaration}, 존재하지 않을 경우 빈 {@link Optional}
     */
    Optional<Declaration> findByDeclarationNumber(String declarationNumber);

    List<Declaration> findAllByCreatedBy(Long createdBy);

    List<Declaration> findAllByCreatedByAndStatus(Long createdBy, DeclarationStatus status);

    List<Declaration> findAllByStatus(DeclarationStatus status);

}
