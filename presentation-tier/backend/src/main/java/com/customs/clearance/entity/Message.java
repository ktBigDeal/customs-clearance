// src/main/java/com/customs/clearance/entity/Message.java
package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.*;

/**
 * 채팅 메시지를 나타내는 JPA 엔티티입니다.
 * <p>
 * 각 메시지는 사용자 또는 AI가 작성하며, 특정 채팅 세션에 속합니다.
 * 메시지 내용과 발신 주체(role), 생성 시각을 포함합니다.
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
@Table(name = "messages")
public class Message extends BaseEntity {

    /** 연결된 채팅 세션 ID */
    @Column(name = "chatting_id", nullable = false)
    private Long chattingId;

    /** 메시지를 보낸 주체 (USER 또는 AI) */
    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false)
    private Role role;

    /** 메시지 본문 내용 */
    @Column(name = "contents", columnDefinition = "TEXT")
    private String contents;

    /** 메시지를 보낸 주체의 역할을 정의하는 열거형 */
    public enum Role {
        USER, AI
    }
}
