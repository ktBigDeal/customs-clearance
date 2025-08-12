// src/main/java/com/customs/clearance/security/JwtAuthenticationFilter.java
package com.customs.clearance.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * 각 요청마다 JWT 토큰을 추출해 인증을 수행하는 Spring Security 필터입니다.
 * <p>
 * {@link JwtTokenProvider}를 이용해 토큰 유효성을 검사하고,
 * 인증이 유효한 경우 {@link SecurityContextHolder}에 사용자 정보를 설정합니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider tokenProvider;
    private final CustomUserDetailsService userDetailsService;
    
    /**
     * 생성자에서 토큰 제공자와 사용자 상세 정보 서비스를 주입받습니다.
     *
     * @param tokenProvider JWT 생성 및 검증 유틸리티
     * @param userDetailsService 사용자명을 기반으로 {@link UserDetails}를 조회하는 서비스
     */
    public JwtAuthenticationFilter(JwtTokenProvider tokenProvider,
                                   CustomUserDetailsService userDetailsService) {
        this.tokenProvider = tokenProvider;
        this.userDetailsService = userDetailsService;
    }

    @Override
    protected void doFilterInternal(@NonNull HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain filterChain) throws java.io.IOException, jakarta.servlet.ServletException {
        String jwt = parseJwt(request);
        if (StringUtils.hasText(jwt) && tokenProvider.validateToken(jwt)) {
            String username = tokenProvider.getUsernameFromToken(jwt);
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            UsernamePasswordAuthenticationToken authentication =
                new UsernamePasswordAuthenticationToken(
                    userDetails, null, userDetails.getAuthorities());
            authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }
        filterChain.doFilter(request, response);
    }

    /**
     * HTTP 요청의 Authorization 헤더에서 Bearer 토큰을 추출합니다.
     *
     * @param request 현재 HTTP 요청
     * @return "Bearer " 접두사를 제거한 토큰 문자열, 없으면 {@code null}
     */
    private String parseJwt(HttpServletRequest request) {
        String headerAuth = request.getHeader("Authorization");
        if (StringUtils.hasText(headerAuth) && headerAuth.startsWith("Bearer ")) {
            return headerAuth.substring(7);
        }
        return null;
    }
}
