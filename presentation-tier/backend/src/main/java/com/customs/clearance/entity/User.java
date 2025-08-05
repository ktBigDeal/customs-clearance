// src/main/java/com/customs/clearance/entity/User.java
package com.customs.clearance.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
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
public class User extends BaseEntity {
    /** 로그인에 사용할 사용자명(중복 불가) */
    @NotBlank(message = "Username is required")
    @Column(name = "username", nullable = false, unique = true)
    private String username;

    /** 해싱된 비밀번호 */
    @NotBlank(message = "Password is required")
    @ToString.Exclude // 비밀번호는 출력하지 않도록 설정
    @EqualsAndHashCode.Exclude // 비밀번호는 비교에서 제외
    @Column(name = "password", nullable = false)
    private String password;    // BCrypt 해시 저장

    // 역할(Role)이나 추가 필드를 여기에 정의할 수 있습니다.

    /** 사용자 이름 */
    @NotBlank(message = "Name is required")
    @Column(name = "name", nullable = false)
    private String name;

    /** 사용자 역할 (예: ADMIN, OFFICER, USER 등) */
    @NotBlank(message = "Role is required")
    @Column(name = "role", nullable = false)
    private String role; // 예: ADMIN, OFFICER, USER 등

    /** 사용자 이메일 */
    @NotBlank(message = "Email is required")
    @Email(message = "Email should be valid")
    @Column(name = "email", nullable = false, unique = true)
    private String email;

    @Column(name = "enabled")
    private boolean enabled = true; // 사용자 활성화 상태 (기본값: true)
}
