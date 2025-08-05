// src/main/java/com/customs/clearance/controller/AuthController.java
package com.customs.clearance.controller;

import com.customs.clearance.entity.User;
import com.customs.clearance.security.JwtTokenProvider;
import com.customs.clearance.service.UserService;
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
     * @param username 등록할 사용자명
     * @param password 등록할 사용자의 평문 비밀번호
     */
    @PostMapping("/register")
    public void register(@RequestParam String username, @RequestParam String password) {
        userService.register(username, password);
    }

    /**
     * 로그인 요청을 처리하고 인증이 성공하면 JWT를 발급합니다.
     *
     * @param username 로그인할 사용자명
     * @param password 로그인할 평문 비밀번호
     * @return 발급된 JWT 토큰 문자열
     */
    @PostMapping("/login")
    public String login(@RequestParam String username, @RequestParam String password) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(username, password));
        SecurityContextHolder.getContext().setAuthentication(authentication);
        return tokenProvider.generateToken(username);
    }
}
