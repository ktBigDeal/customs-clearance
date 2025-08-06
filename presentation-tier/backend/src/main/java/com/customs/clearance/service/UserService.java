// src/main/java/com/customs/clearance/service/UserService.java
package com.customs.clearance.service;

import com.customs.clearance.dto.RegisterRequest;
import com.customs.clearance.entity.User;
import com.customs.clearance.repository.UserRepository;

import java.util.List;
import java.util.Optional;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
/**
 * 사용자와 관련된 비즈니스 로직을 담당하는 서비스 클래스입니다.
 * <p>
 * 회원가입(등록) 및 사용자 조회 기능을 제공합니다. 비밀번호는
 * {@link PasswordEncoder}를 사용하여 안전하게 해싱 후 저장합니다.
 *
 * @author Customs Clearance Team
 * @version 1.0
 */
@Service
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository,
                       PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

     /**
     * 새 사용자를 등록합니다. 이미 동일한 사용자명이 존재할 경우 예외를 발생시킵니다.
     *
     * @param registerRequest 사용자 등록 요청 DTO
     * @return 저장된 {@link User} 엔티티
     * @throws IllegalArgumentException 사용자명이 중복될 경우 발생
     */

    public User register(RegisterRequest registerRequest) {
        Optional<User> existingUser = userRepository.findByUsername(registerRequest.getUsername());
        if (existingUser.isPresent()) {
            throw new IllegalArgumentException("이미 존재하는 사용자명입니다.");
        }
        User user = new User();
        user.setUsername(registerRequest.getUsername());
        user.setPassword(passwordEncoder.encode(registerRequest.getPassword()));
        user.setName(registerRequest.getName());
        user.setEmail(registerRequest.getEmail());
        user.setRole(registerRequest.getRole());
        return userRepository.save(user);
    }

    /**
     * 사용자명을 기준으로 사용자를 조회합니다.
     *
     * @param username 조회할 사용자명
     * @return 해당 사용자명에 매핑되는 {@link User}
     * @throws IllegalArgumentException 사용자가 존재하지 않을 경우 발생
     */
    public User findByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));
    }

    /**
     * 시스템에 등록된 모든 사용자를 조회합니다.
     *
     * @return 사용자 목록
     */
    public List<User> findAllUsers() {
    return userRepository.findAll();
}
}
