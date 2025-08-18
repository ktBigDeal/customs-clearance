// src/main/java/com/customs/clearance/entity/User.java
package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
/**
 * 사용자 정보를 나타내는 JPA 엔티티입니다.
 * <p>
 * 시스템에 등록된 사용자의 식별자, 사용자명, 비밀번호를 보유합니다.
 * 비밀번호는 {@link org.springframework.security.crypto.password.PasswordEncoder}를 통해
 * 해싱된 값으로 저장되어야 합니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
@Entity
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
@Table(name = "users", uniqueConstraints = @UniqueConstraint(columnNames = "username"))
public class User extends BaseEntity {
    /** 로그인에 사용할 사용자명(중복 불가) */
    @Column(name = "username", nullable = false, unique = true)
    private String username;

    /** 해싱된 비밀번호 */
    @Column(name = "password", nullable = false)
    private String password;    // BCrypt 해시 저장

    /** 사용자 이름 */
    @Column(name = "name", nullable = false)
    private String name;

    /** 사용자 역할 (예: ADMIN, USER 등) */
    @Column(name = "role", nullable = false)
    private String role;

    /** 사용자 이메일 */
    @Column(name = "email", nullable = false, unique = true)
    private String email;

    /** 사용자 활성화 상태 */
    @Column(name = "enabled", columnDefinition = "TINYINT(1) default 1")
    private boolean enabled = true;

    /** 회사명 */
    @Column(name = "company")
    private String company;

    /** 마지막 로그인 시간 */
    @Column(name = "last_login")
    private LocalDateTime lastLogin;
}
