// src/main/java/com/customs/clearance/controller/AuthController.java
package com.customs.clearance.controller;

import com.customs.clearance.dto.RegisterRequest;
import com.customs.clearance.dto.UserResponseDto;
import com.customs.clearance.entity.User;
import com.customs.clearance.security.JwtTokenProvider;
import com.customs.clearance.service.UserService;

import io.swagger.v3.oas.annotations.security.SecurityRequirement;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

/**
 * 인증과 관련된 REST 엔드포인트를 제공하는 컨트롤러입니다.
 * <p>
 * 회원가입과 로그인 기능을 담당하며, 로그인 성공 시 JWT 토큰을 발급하여 반환합니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider tokenProvider;
    private final UserService userService;

    public AuthController(AuthenticationManager authenticationManager,
                          JwtTokenProvider tokenProvider,
                          UserService userService) {
        this.authenticationManager = authenticationManager;
        this.tokenProvider = tokenProvider;
        this.userService = userService;
    }

    /**
     * 새로운 사용자를 등록합니다.
     *
     * @body RegisterRequest 사용자 등록 요청 DTO
     */
    @PostMapping("/register")
    public void register(@RequestBody RegisterRequest registerRequest) {
        userService.register(registerRequest);
    }

    /**
     * 역할별 로그인 엔드포인트.
     * 예: /auth/login/admin, /auth/login/officer, /auth/login/user
     *
     * @param role     기대하는 사용자 역할 (ADMIN, OFFICER, USER 등)
     * @param username 사용자명
     * @param password 비밀번호
     * @return 역할이 일치할 경우 발급된 JWT
     * @throws org.springframework.security.access.AccessDeniedException 역할 불일치 시
     */
    @PostMapping("/login/{role}")
    public String loginByRole(@PathVariable String role,
                              @RequestParam String username,
                              @RequestParam String password) {
        // 기본 인증
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(username, password));
        SecurityContextHolder.getContext().setAuthentication(authentication);

        // 역할 검증
        User user = userService.findByUsername(username);
        String userRole = user.getRole();
        if (userRole == null || !userRole.equalsIgnoreCase(role)) {
            throw new org.springframework.security.access.AccessDeniedException("해당 역할로 로그인할 수 없습니다.");
        }
        // 역할이 일치하면 역할 포함 JWT 발급
        return tokenProvider.generateToken(username, role);
    }

    /**
 * 관리자만 전체 사용자 목록을 조회할 수 있는 엔드포인트입니다.
 *
 * 클라이언트는 Authorization 헤더로 Bearer 토큰을 전달해야 하며,
 * 토큰에서 추출한 역할이 ADMIN일 경우에만 응답합니다.
 *
 * @param token Authorization 헤더의 JWT 토큰
 * @return 전체 사용자 목록
 */
@GetMapping("/users")
public List<UserResponseDto> getAllUsers() {
    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
    if (auth == null || !auth.isAuthenticated()) {
        throw new AccessDeniedException("인증되지 않았습니다.");
    }

    boolean isAdmin = auth.getAuthorities().stream()
        .anyMatch(grantedAuthority -> grantedAuthority.getAuthority().equals("ROLE_ADMIN"));

    if (!isAdmin) {
        throw new AccessDeniedException("관리자 권한이 필요합니다.");
    }

    return userService.findAllUsers().stream()
        .map(user -> new UserResponseDto(
            user.getId(),
            user.getUsername(),
            user.getName(),
            user.getEmail(),
            user.getRole(),
            user.isEnabled()
        ))
        .collect(Collectors.toList());
}

}
