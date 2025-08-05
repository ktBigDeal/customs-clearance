// src/main/java/com/customs/clearance/entity/Chatting.java
package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.*;

/**
 * 채팅 세션 정보를 나타내는 JPA 엔티티입니다.
 * <p>
 * 하나의 채팅 세션은 사용자와 AI 사이의 메시지 흐름을 포함하며,
 * 생성자 및 수정자의 사용자 ID와 생성/수정 시점을 포함합니다.
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
@Table(name = "chattings")
public class Chatting extends BaseEntity {

    /** 채팅을 생성한 사용자 ID */
    @Column(name = "created_by")
    private Long createdBy;

    /** 채팅을 마지막으로 수정한 사용자 ID */
    @Column(name = "updated_by")
    private Long updatedBy;
}
