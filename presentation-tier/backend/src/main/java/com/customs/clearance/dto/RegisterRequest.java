package com.customs.clearance.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 사용자 회원가입 요청을 표현하는 데이터 전송 객체(DTO)입니다.
 * 사용자명, 비밀번호, 이름, 이메일 및 역할을 포함합니다.
 * <p>
 * 유효성 검사를 위해 각 필드에 제약 조건을 추가하였습니다.
 * * @author Customs Clearance Team
 * @version 1.0
 * @see jakarta.validation.constraints.NotBlank
 * @see jakarta.validation.constraints.Email
 * @since 2024-01-01
 */
@Data
public class RegisterRequest {
    @NotBlank(message = "Username is required")
    private String username;

    @NotBlank(message = "Password is required")
    private String password;

    @NotBlank(message = "Name is required")
    private String name;

    @Email(message = "Email should be valid")
    @NotBlank(message = "Email is required")
    private String email;

    @NotBlank(message = "Role is required")
    private String role;
}
