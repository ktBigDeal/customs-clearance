// src/main/java/com/customs/clearance/security/JwtTokenProvider.java
package com.customs.clearance.security;

import io.jsonwebtoken.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.Date;

/**
 * JWT(Json Web Token)를 생성하고 파싱·검증하는 유틸리티 클래스입니다.
 * <p>
 * 애플리케이션의 프로퍼티에서 시크릿 키와 토큰 만료 시간을 주입받아 서명을 수행합니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */

@Component
public class JwtTokenProvider {
    /** JWT 서명에 사용할 시크릿 키 (Base64 인코딩된 문자열 권장) */
    @Value("${customs.clearance.security.jwt.secret}")
    private String jwtSecret;

    /** JWT 만료 시간(밀리초) */
    @Value("${customs.clearance.security.jwt.expiration}")
    private long jwtExpirationMs;

    /**
     * 사용자명과 역할을 담은 JWT 토큰을 생성합니다.
     *
     * @param username 토큰의 subject로 설정할 사용자명
     * @param role 토큰에 포함할 사용자 역할
     * @return 생성된 JWT 문자열
     */
    public String generateToken(String username, String role) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + jwtExpirationMs);

        return Jwts.builder()
                .setSubject(username)
                .claim("role", role)
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(SignatureAlgorithm.HS256, jwtSecret)
                .compact();
    }


    /**
     * JWT로부터 사용자명을 추출합니다.
     *
     * @param token 파싱할 JWT
     * @return JWT의 subject에 해당하는 username
     */
    public String getUsernameFromToken(String token) {
        return Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(token)
                .getBody().getSubject();
    }

    /** 토큰에서 역할 클레임 추출 */
    public String getRoleFromToken(String token) {
        Claims claims = Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(token).getBody();
        Object role = claims.get("role");
        return role != null ? role.toString() : null;
    }

     /**
     * 주어진 JWT가 유효한지 검증합니다.
     *
     * @param token 검증할 JWT
     * @return 토큰이 유효하면 {@code true}, 그렇지 않으면 {@code false}
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            // 토큰 파싱 오류 또는 만료
            return false;
        }
    }
}
