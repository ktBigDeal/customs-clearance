// src/main/java/com/customs/clearance/repository/AttachmentRepository.java
package com.customs.clearance.repository;

import com.customs.clearance.entity.Attachment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

/**
 * {@link Attachment} 엔티티에 대한 기본 CRUD 연산을 처리하는 Spring Data JPA 리포지토리입니다.
 * <p>
 * 신고서 ID를 기준으로 첨부파일을 조회하는 메서드가 추가로 정의되어 있습니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
public interface AttachmentRepository extends JpaRepository<Attachment, Long> {

    /**
     * 주어진 신고서 ID에 해당하는 첨부파일 목록을 조회합니다.
     *
     * @param declarationId 첨부파일이 연결된 신고서 ID
     * @return 해당 신고서에 연결된 {@link Attachment} 리스트 반환
     */
    List<Attachment> findByDeclarationId(Long declarationId);
}