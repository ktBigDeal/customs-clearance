package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

/**
 * 공통 기본 엔티티 추상 클래스
 * 
 * 모든 엔티티에서 공통으로 사용되는 감사 필드와 기본 속성을 정의하는 추상 클래스입니다.
 * JPA Auditing 기능을 활용하여 엔티티의 생성/수정 시점을 자동으로 관리합니다.
 * 
 * <p>주요 기능:</p>
 * <ul>
 *   <li>기본 키 (ID) 자동 생성</li>
 *   <li>생성 시점 자동 기록 (createdAt)</li>
 *   <li>수정 시점 자동 업데이트 (updatedAt)</li>
 *   <li>Optimistic Locking을 위한 버전 관리</li>
 * </ul>
 * 
 * <p>이 클래스를 상속받는 모든 엔티티는 자동으로 감사 기능을 포함합니다.</p>
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 * @see AuditingEntityListener
 * @see CreatedDate
 * @see LastModifiedDate
 * @since 2024-01-01
 */
@Data
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Version
    private Long version;
}