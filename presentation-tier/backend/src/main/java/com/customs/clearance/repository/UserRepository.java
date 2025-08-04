// src/main/java/com/customs/clearance/repository/UserRepository.java
package com.customs.clearance.repository;

import com.customs.clearance.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
/**
 * {@link User} 엔티티에 대한 기본 CRUD 연산을 처리하는 Spring Data JPA 리포지토리입니다.
 * <p>
 * 사용자명으로 사용자를 조회하는 메서드가 추가로 정의되어 있습니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
public interface UserRepository extends JpaRepository<User, Long> {
    /**
     * 주어진 사용자명으로 사용자 정보를 조회합니다.
     *
     * @param username 조회할 사용자명
     * @return 사용자명에 해당하는 {@link User}가 존재하면 {@link Optional}에 담아서 반환,
     *         존재하지 않으면 빈 {@link Optional} 반환
     */
    Optional<User> findByUsername(String username);
}
