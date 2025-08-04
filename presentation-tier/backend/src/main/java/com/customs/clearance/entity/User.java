// src/main/java/com/customs/clearance/entity/User.java
package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.*;
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
public class User {
     /** 사용자 고유 식별자 */
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 로그인에 사용할 사용자명(중복 불가) */
    @Column(nullable = false, unique = true)
    private String username;

    /** 해싱된 비밀번호 */
    @Column(nullable = false)
    private String password;    // BCrypt 해시 저장

    // 역할(Role)이나 추가 필드를 여기에 정의할 수 있습니다.
}
