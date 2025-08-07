// src/main/java/com/customs/clearance/entity/Attachment.java
package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

/**
 * 신고 첨부 파일 정보를 나타내는 JPA 엔티티입니다.
 * <p>
 * 각 첨부 파일은 특정 신고(Declaration)에 연결되며,
 * 업로드 시각, 업로더 정보, 파일 경로, 크기 등의 메타데이터를 포함합니다.
 * 
 * 이 클래스는 {@link BaseEntity}를 상속받아 ID, 생성/수정일, 버전 관리 기능을 자동으로 포함합니다.
 * 
 * @author Customs Clearance Team
 * @version 1.0
 */
@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "attachments")
public class Attachment extends BaseEntity {

    /** 첨부된 신고 ID */
    @Column(name = "declaration_id", nullable = false)
    private Long declarationId;

    /** 저장된 파일명 */
    @Column(name = "filename", length = 255, nullable = false)
    private String filename;

    /** 업로드 시 사용자가 업로드한 원본 파일명 */
    @Column(name = "original_filename", length = 255, nullable = false)
    private String originalFilename;

    /** 서버에 저장된 파일 경로 */
    @Column(name = "file_path", length = 500, nullable = false)
    private String filePath;

    /** 파일 크기 (바이트 단위) */
    @Column(name = "file_size", nullable = false)
    private Long fileSize;

    /** 파일의 MIME 타입 */
    @Column(name = "content_type", length = 100)
    private String contentType;

    /** 파일이 업로드된 시각 */
    @Column(name = "uploaded_at", columnDefinition = "DATETIME DEFAULT CURRENT_TIMESTAMP", insertable = false, updatable = false)
    private LocalDateTime uploadedAt;

    /** 파일을 업로드한 사용자 ID */
    @Column(name = "uploaded_by")
    private Long uploadedBy;

    public Attachment(Long declarationId, String filename, String originalFilename, String filePath, Long fileSize, String contentType, Long uploadedBy) {
        this.declarationId = declarationId;
        this.filename = filename;
        this.originalFilename = originalFilename;
        this.filePath = filePath;
        this.fileSize = fileSize;
        this.contentType = contentType;
        this.uploadedBy = uploadedBy;
    }

}
