// src/main/java/com/customs/clearance/repository/ChattingRepository.java
package com.customs.clearance.repository;

import com.customs.clearance.entity.Chatting;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * {@link Chatting} 엔티티에 대한 기본 CRUD 연산을 처리하는 Spring Data JPA 리포지토리입니다.
 * <p>
 * 추가적인 메서드는 현재 정의되어 있지 않습니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
public interface ChattingRepository extends JpaRepository<Chatting, Long> {
}