package com.customs.clearance.controller;

import com.customs.clearance.dto.RegisterRequest;
import com.customs.clearance.dto.UpdateUserRequest;
import com.customs.clearance.dto.UserResponseDto;
import com.customs.clearance.entity.User;
import com.customs.clearance.security.JwtTokenProvider;
import com.customs.clearance.service.UserService;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

/**
 * 사용자 인증 및 관리 관련 API를 제공하는 컨트롤러 클래스입니다.
 * <p>
 * 이 클래스는 사용자 등록, 로그인, 사용자 정보 조회, 수정, 삭제 등의 기능을 제공합니다.
 * 사용자 인증은 JWT 토큰을 사용하며, 역할 기반 접근 제어를 지원합니다.
 * <p>
 * 주요 기능:
 * <ul>
 * <li>사용자 등록 (회원가입)</li>
 * <li>역할별 로그인 엔드포인트</li>
 * <li>전체 사용자 목록 조회 (관리자 전용)</li>
 * <li>사용자 프로필 조회 (본인만)</li>
 * <li>사용자 정보 수정 (본인 또는 관리자)</li>
 * <li>사용자 활성화 상태 변경 (관리자 전용)</li>
 * <li>사용자 삭제 (본인 또는 관리자)</li>
 * </ul>
 * 클라이언트는 Authorization 헤더로 Bearer 토큰을 전달해야 하며,
 * 토큰에서 추출한 사용자명과 역할에 따라 접근 권한이 결정됩니다.
 * <p>
 * 각 엔드포인트는 다음과 같은 역할 기반 접근 제어를 적용합니다:
 * <ul>
 * <li>ADMIN: 전체 사용자 목록 조회, 사용자 활성화 상태 변경, 사용자 삭제</li>
 * <li>USER: 자신의 프로필 조회 및 수정, 사용자 삭제</li>
 * </ul>
 * @author Customs Clearance Team
 * @version 1.0
 */
@RestController
@RequestMapping("/user")
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
        
        // 로그인 성공시 마지막 로그인 시간 업데이트
        userService.updateLastLogin(username);
        
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

        List<UserResponseDto> result = userService.findAllUsers().stream()
            .map(user -> {
                System.out.println("사용자: " + user.getUsername() + ", lastLogin: " + user.getLastLogin()); // 디버깅용
                UserResponseDto dto = new UserResponseDto(
                    user.getId(),
                    user.getUsername(),
                    user.getName(),
                    user.getEmail(),
                    user.getRole(),
                    user.isEnabled(),
                    user.getCompany(),
                    user.getLastLogin()
                );
                System.out.println("DTO 생성 후 - " + user.getUsername() + ", DTO lastLogin: " + dto.getLastLogin()); // 디버깅용
                return dto;
            })
            .collect(Collectors.toList());
            
        System.out.println("최종 응답 리스트 크기: " + result.size()); // 디버깅용
        return result;
    }
    /** * 특정 사용자의 프로필 정보를 조회하는 엔드포인트입니다.
     * 본인만 자신의 정보를 조회할 수 있으며, 다른 사용자의 정보는 접근할 수 없습니다.
     * 클라이언트는 Authorization 헤더로 Bearer 토큰을 전달해야 하며,
     * 토큰에서 추출한 사용자명과 경로 변수의 사용자명이 일치해야 합니다.
     * 비밀번호 정보는 해싱된 상태로 저장되기 때문에 반환하지 않습니다.
     * * @param username 경로 변수로 전달된 사용자명
     * @return 사용자 프로필 정보
     * @throws AccessDeniedException 본인 정보가 아닌 경우
     */
    @GetMapping("/{username}")
    public UserResponseDto getUserProfile(@PathVariable String username) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (!auth.getName().equals(username)) {
            throw new AccessDeniedException("본인 정보만 조회할 수 있습니다.");
        }

        User user = userService.findByUsername(username);
        return new UserResponseDto(user.getId(), user.getUsername(), user.getName(), user.getEmail(), user.getRole(), user.isEnabled(), user.getCompany(), user.getLastLogin());
    }

    /**
     * 관리자가 특정 사용자의 활성화 상태를 변경하는 엔드포인트입니다.
     * 클라이언트는 Authorization 헤더로 Bearer 토큰을 전달해야 하며,
     * 토큰에서 추출한 역할이 ADMIN일 경우에만 접근할 수 있습니다.
     *
     * @param userId  경로 변수로 전달된 사용자 ID
     * @param enabled 활성화 상태 (true: 활성화, false: 비활성화)
     * @throws AccessDeniedException 관리자 권한이 없는 경우
     */
    @PatchMapping("/admin/{userId}")
    public void updateEnableStatus(@PathVariable Long userId, @RequestParam boolean enabled) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        boolean isAdmin = auth.getAuthorities().stream()
            .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));
        if (!isAdmin) throw new AccessDeniedException("관리자 권한 필요");

        User user = userService.findById(userId);
        user.setEnabled(enabled);
        userService.save(user);
    }

    /**
     * 사용자 정보를 수정하는 엔드포인트입니다.
     * 관리자 권한을 가진 사용자는 모든 사용자를 수정할 수 있고,
     * 일반 사용자는 본인 정보만 수정할 수 있습니다.
     * * @param userId 경로 변수로 전달된 사용자 ID
     * @param dto 수정할 사용자 정보 DTO
     * @throws AccessDeniedException 본인 또는 관리자 권한이 아닌 경우
     */
    @PutMapping("/{userId}")
    public void updateUserInfo(@PathVariable Long userId, @RequestBody UpdateUserRequest dto) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        User user = userService.findById(userId);

        boolean isAdmin = auth.getAuthorities().stream()
            .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));

        if (!auth.getName().equals(user.getUsername()) && !isAdmin) {
            throw new AccessDeniedException("본인 또는 관리자만 수정 가능");
        }

        user.setName(dto.getName());
        user.setEmail(dto.getEmail());
        user.setCompany(dto.getCompany());
        if (dto.getPassword() != null && !dto.getPassword().isBlank()) {
            user.setPassword(dto.getPassword());
            userService.updatePassword(user);
            return;
        }

        userService.save(user);
    }

    /**
     * 사용자를 삭제하는 엔드포인트입니다.
     * 클라이언트는 Authorization 헤더로 Bearer 토큰을 전달해야 하며,
     * 토큰에서 추출한 역할이 ADMIN일 경우에만 접근할 수 있습니다.
     *
     * @param userId 경로 변수로 전달된 사용자 ID
     * @throws AccessDeniedException 관리자 권한이 없는 경우
     */
    @DeleteMapping("/{userId}")
    public void deleteUser(@PathVariable Long userId) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        User user = userService.findById(userId);

        boolean isAdmin = auth.getAuthorities().stream()
            .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));

        if (!auth.getName().equals(user.getUsername()) && !isAdmin) {
            throw new AccessDeniedException("본인 또는 관리자만 삭제 가능");
        }

        userService.deleteById(userId);
    }
}