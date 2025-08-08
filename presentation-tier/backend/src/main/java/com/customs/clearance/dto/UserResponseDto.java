package com.customs.clearance.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import java.time.LocalDateTime;

/** * 사용자 정보를 응답하기 위한 DTO 클래스입니다.
 * <p>
 * 사용자 ID, 사용자명, 이름, 이메일, 역할 및 활성화 상태를 포함합니다.
 * 해싱된 비밀번호는 포함하지 않습니다.
 * @author Customs Clearance Team
 * @version 1.0
 */
@Data
@AllArgsConstructor
public class UserResponseDto {
    private Long id;
    private String username;
    private String name;
    private String email;
    private String role;
    private Boolean enabled;
    private String company;
    private LocalDateTime lastLogin;
}