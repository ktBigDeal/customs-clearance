package com.customs.clearance.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 사용자 정보를 업데이트하기 위한 요청 DTO 클래스입니다.
 * <p>
 * 사용자 이름, 이메일, 비밀번호를 포함하며, 비밀번호는 선택 사항입니다.
 * @author Customs Clearance Team
 * @version 1.0
 */

@Data
public class UpdateUserRequest {
    @NotBlank 
    private String name;
    
    @Email 
    @NotBlank
    private String email;

    private String password;
    
    private String company;

}

