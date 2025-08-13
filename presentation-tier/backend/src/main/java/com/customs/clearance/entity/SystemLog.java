package com.customs.clearance.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

/**
 * 시스템 로그 정보를 저장하는 JPA 엔티티
 * 
 * 시스템의 모든 주요 활동과 오류를 기록하여 관리자가 시스템 상태를 
 * 모니터링하고 문제를 진단할 수 있도록 합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-13
 */
@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Table(name = "system_logs")
public class SystemLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 로그 발생 시간 */
    @Column(name = "timestamp", nullable = false)
    private LocalDateTime timestamp;

    /** 로그 레벨 (INFO, WARN, ERROR, DEBUG) */
    @Enumerated(EnumType.STRING)
    @Column(name = "level", nullable = false)
    private LogLevel level;

    /** 로그 소스 (AUTH, SYSTEM, API, DOCUMENT, CHAT 등) */
    @Column(name = "source", length = 50)
    private String source;

    /** 로그 메시지 */
    @Column(name = "message", columnDefinition = "TEXT")
    private String message;

    /** 관련된 사용자 ID */
    @Column(name = "user_id")
    private Long userId;

    /** 사용자명 */
    @Column(name = "user_name", length = 100)
    private String userName;

    /** 클라이언트 IP 주소 */
    @Column(name = "ip_address", length = 45)
    private String ipAddress;

    /** 사용자 에이전트 정보 */
    @Column(name = "user_agent", length = 500)
    private String userAgent;

    /** 요청 URI */
    @Column(name = "request_uri", length = 500)
    private String requestUri;

    /** HTTP 메서드 */
    @Column(name = "http_method", length = 10)
    private String httpMethod;

    /** 응답 상태 코드 */
    @Column(name = "status_code")
    private Integer statusCode;

    /** 처리 시간 (밀리초) */
    @Column(name = "processing_time")
    private Long processingTime;

    /** 로그 레벨 열거형 */
    public enum LogLevel {
        DEBUG, INFO, WARN, ERROR
    }
}