// src/main/java/com/customs/clearance/service/UserService.java
package com.customs.clearance.service;

import com.customs.clearance.dto.RegisterRequest;
import com.customs.clearance.entity.User;
import com.customs.clearance.repository.UserRepository;

import jakarta.transaction.Transactional;

import java.time.LocalDateTime;
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
        user.setCompany(registerRequest.getCompany());
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
     * 사용자의 id를 기준으로 사용자를 조회합니다.
     * @param id 조회할 사용자 ID
     * @return 해당 ID에 매핑되는 {@link User}
     * @throws IllegalArgumentException 사용자가 존재하지 않을 경우 발생
     */
    public User findById(Long id) {
        return userRepository.findById(id)
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

    /**
     * 사용자 정보를 저장합니다. 주로 사용자 등록 및 정보 수정에 사용됩니다.
     *
     * @param user 저장할 {@link User} 엔티티
     * @return 저장된 {@link User} 엔티티
     */
    public User save(User user) {
        return userRepository.save(user);
    }
    /**
     * 사용자 정보를 저장합니다. 비밀번호는 해싱 후 저장됩니다.
     * 
     * @param user 수정할 {@link User} 엔티티
     * @return 수정된 {@link User} 엔티티
     */
    public User updatePassword(User user) {
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        return userRepository.save(user);
    }

    /**
     * 사용자의 마지막 로그인 시간을 업데이트합니다.
     *
     * @param username 로그인한 사용자명
     */
    @Transactional
    public void updateLastLogin(String username) {
        User user = findByUsername(username);
        user.setLastLogin(LocalDateTime.now());
        userRepository.save(user);
    }

    /**
     * 사용자를 삭제합니다.
     *
     * @param userId 삭제할 사용자 ID
     */
    @Transactional
    public void deleteById(Long userId) {
        userRepository.deleteById(userId);
    }
}
