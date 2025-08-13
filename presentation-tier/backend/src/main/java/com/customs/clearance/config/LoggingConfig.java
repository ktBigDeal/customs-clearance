package com.customs.clearance.config;

import com.customs.clearance.service.SystemLogService;
import com.customs.clearance.entity.SystemLog;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.context.event.EventListener;
import org.springframework.boot.context.event.ApplicationFailedEvent;

/**
 * 로깅 관련 설정 클래스
 * 
 * AOP를 활성화하고 애플리케이션 생명주기 이벤트를 
 * 자동으로 로깅하는 기능을 제공합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-14
 */
@Slf4j
@Configuration
@EnableAspectJAutoProxy
@RequiredArgsConstructor
public class LoggingConfig {

    private final SystemLogService systemLogService;

    /**
     * 애플리케이션 시작 완료 시 로그 저장
     */
    @EventListener
    public void handleApplicationReady(ApplicationReadyEvent event) {
        log.info("애플리케이션이 성공적으로 시작되었습니다");
        
        try {
            systemLogService.logSystemEvent(
                "APPLICATION",
                "Spring Boot 애플리케이션이 성공적으로 시작되었습니다",
                SystemLog.LogLevel.INFO
            );
        } catch (Exception e) {
            log.error("애플리케이션 시작 로그 저장 실패: {}", e.getMessage());
        }
    }

    /**
     * 애플리케이션 시작 실패 시 로그 저장
     */
    @EventListener
    public void handleApplicationFailed(ApplicationFailedEvent event) {
        log.error("애플리케이션 시작 실패: {}", event.getException().getMessage());
        
        try {
            systemLogService.logSystemEvent(
                "APPLICATION",
                "애플리케이션 시작 실패: " + event.getException().getMessage(),
                SystemLog.LogLevel.ERROR
            );
        } catch (Exception e) {
            log.error("애플리케이션 실패 로그 저장 실패: {}", e.getMessage());
        }
    }
}