// src/main/java/com/customs/clearance/security/CustomUserDetailsService.java
package com.customs.clearance.security;

import com.customs.clearance.entity.User;
import com.customs.clearance.repository.UserRepository;
import org.springframework.security.core.userdetails.*;
import org.springframework.stereotype.Service;

/**
 * 사용자명을 기반으로 {@link UserDetails}를 조회하는 서비스 구현체입니다.
 * <p>
 * Spring Security는 인증 과정에서 {@link UserDetailsService}를 통해 사용자 정보를 로드합니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
@Service
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    public CustomUserDetailsService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) {
        User user = userRepository.findByUsername(username)
            .orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다."));
            // 역할(Role)이 있다면 GrantedAuthority 목록에 추가할 수 있습니다.
            return new org.springframework.security.core.userdetails.User(
            user.getUsername(),
            user.getPassword(),
            java.util.List.of()); // 필요한 경우 ROLE 추가
    }
}
