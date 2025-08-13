package com.customs.clearance.aspect;

import com.customs.clearance.entity.SystemLog;
import com.customs.clearance.service.SystemLogService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.ProceedingJoinPoint;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.time.LocalDateTime;

/**
 * 시스템 로그를 자동으로 수집하는 AOP Aspect
 * 
 * 컨트롤러의 모든 요청/응답과 에러를 자동으로 캡처하여 
 * system_logs 테이블에 저장합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-14
 */
@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class SystemLogAspect {

    private final SystemLogService systemLogService;

    /**
     * 중요한 비즈니스 API만 대상으로 하는 포인트컷 (관리자 로그, 로그인 제외)
     */
    @Pointcut("within(com.customs.clearance.controller..*) && " +
              "!within(com.customs.clearance.controller.AdminController) && " +
              "!execution(* com.customs.clearance.controller.AuthController.getUserProfile(..))")
    public void importantControllerMethods() {}

    /**
     * 인증 관련 중요 메서드만 대상
     */
    @Pointcut("execution(* com.customs.clearance.controller.AuthController.login(..)) || " +
              "execution(* com.customs.clearance.controller.AuthController.register(..)) || " +
              "execution(* com.customs.clearance.controller.AuthController.updateUserInfo(..))")
    public void authMethods() {}

    /**
     * 서비스 계층의 중요한 비즈니스 로직만 대상
     */
    @Pointcut("within(com.customs.clearance.service..*) && " +
              "!within(com.customs.clearance.service.SystemLogService) && " +
              "!execution(* *.get*(..))")  // getter 메서드 제외
    public void importantServiceMethods() {}

    /**
     * 중요한 비즈니스 API 로깅
     */
    @Around("importantControllerMethods()")
    public Object logImportantControllerMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        long startTime = System.currentTimeMillis();
        String methodName = joinPoint.getSignature().getName();
        String className = joinPoint.getTarget().getClass().getSimpleName();
        
        HttpServletRequest request = getCurrentRequest();
        String ipAddress = getClientIpAddress(request);
        String userAgent = request != null ? request.getHeader("User-Agent") : null;
        String requestUri = request != null ? request.getRequestURI() : null;
        String httpMethod = request != null ? request.getMethod() : null;

        try {
            // 메서드 실행
            Object result = joinPoint.proceed();
            
            // 성공 로그 저장
            long processingTime = System.currentTimeMillis() - startTime;
            
            // 사용자 정보 추출
            String[] userInfo = extractUserInfo();
            String userId = userInfo[0];
            String userName = userInfo[1];
            
            systemLogService.logUserActivity(
                "BUSINESS",
                String.format("%s 작업 완료", getBusinessActionName(className, methodName)),
                userId != null ? Long.parseLong(userId) : null,
                userName,
                ipAddress,
                userAgent,
                requestUri,
                httpMethod,
                200,
                processingTime
            );
            
            return result;
            
        } catch (Exception e) {
            // 에러 로그 저장
            long processingTime = System.currentTimeMillis() - startTime;
            
            systemLogService.logSystemEvent(
                "BUSINESS_ERROR",
                String.format("%s 작업 실패: %s", getBusinessActionName(className, methodName), e.getMessage()),
                SystemLog.LogLevel.ERROR
            );
            
            throw e;
        }
    }

    /**
     * 인증 관련 메서드 로깅
     */
    @Around("authMethods()")
    public Object logAuthMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName();
        HttpServletRequest request = getCurrentRequest();
        String ipAddress = getClientIpAddress(request);
        
        try {
            Object result = joinPoint.proceed();
            
            // 로그인/회원가입 성공
            systemLogService.logUserActivity(
                "AUTH",
                getAuthActionMessage(methodName, true),
                null, // 인증 전이므로 userId 없음
                getAttemptedUsername(joinPoint.getArgs()),
                ipAddress,
                request != null ? request.getHeader("User-Agent") : null,
                request != null ? request.getRequestURI() : null,
                request != null ? request.getMethod() : null,
                200,
                null
            );
            
            return result;
            
        } catch (Exception e) {
            // 로그인/회원가입 실패
            systemLogService.logUserActivity(
                "AUTH_FAILURE",
                getAuthActionMessage(methodName, false) + " - " + e.getMessage(),
                null,
                getAttemptedUsername(joinPoint.getArgs()),
                ipAddress,
                request != null ? request.getHeader("User-Agent") : null,
                request != null ? request.getRequestURI() : null,
                request != null ? request.getMethod() : null,
                401,
                null
            );
            
            throw e;
        }
    }

    /**
     * 서비스 에러 로깅 (중요한 비즈니스 로직만)
     */
    @AfterThrowing(pointcut = "importantServiceMethods()", throwing = "ex")
    public void logServiceError(JoinPoint joinPoint, Exception ex) {
        String methodName = joinPoint.getSignature().getName();
        String className = joinPoint.getTarget().getClass().getSimpleName();
        
        systemLogService.logSystemEvent(
            "SERVICE",
            String.format("%s.%s 서비스 에러: %s", className, methodName, ex.getMessage()),
            SystemLog.LogLevel.ERROR
        );
    }

    /**
     * 애플리케이션 시작 시 로그 저장
     */
    @EventListener(org.springframework.boot.context.event.ApplicationReadyEvent.class)
    public void logApplicationStart() {
        systemLogService.logSystemEvent(
            "APPLICATION",
            "애플리케이션이 성공적으로 시작되었습니다",
            SystemLog.LogLevel.INFO
        );
    }

    /**
     * 현재 HTTP 요청 정보 가져오기
     */
    private HttpServletRequest getCurrentRequest() {
        try {
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            return attributes != null ? attributes.getRequest() : null;
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 클라이언트 IP 주소 추출 (프록시 고려)
     */
    private String getClientIpAddress(HttpServletRequest request) {
        if (request == null) return null;
        
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty() && !"unknown".equalsIgnoreCase(xForwardedFor)) {
            return xForwardedFor.split(",")[0].trim();
        }
        
        String xRealIp = request.getHeader("X-Real-IP");
        if (xRealIp != null && !xRealIp.isEmpty() && !"unknown".equalsIgnoreCase(xRealIp)) {
            return xRealIp;
        }
        
        return request.getRemoteAddr();
    }

    /**
     * SecurityContext에서 사용자 정보 추출
     */
    private String[] extractUserInfo() {
        try {
            org.springframework.security.core.Authentication authentication = 
                org.springframework.security.core.context.SecurityContextHolder.getContext().getAuthentication();
            
            if (authentication != null && authentication.isAuthenticated() && 
                !"anonymousUser".equals(authentication.getPrincipal())) {
                
                Object principal = authentication.getPrincipal();
                if (principal instanceof org.springframework.security.core.userdetails.UserDetails) {
                    org.springframework.security.core.userdetails.UserDetails userDetails = 
                        (org.springframework.security.core.userdetails.UserDetails) principal;
                    return new String[]{null, userDetails.getUsername()}; // userId, userName
                } else {
                    return new String[]{null, principal.toString()};
                }
            }
        } catch (Exception e) {
            log.warn("사용자 정보 추출 실패: {}", e.getMessage());
        }
        return new String[]{null, null};
    }

    /**
     * 비즈니스 액션명 생성
     */
    private String getBusinessActionName(String className, String methodName) {
        // 컨트롤러별로 의미있는 액션명 생성
        if (className.contains("Declaration")) {
            return switch (methodName) {
                case "createDeclaration" -> "수출입 신고서 생성";
                case "updateDeclaration" -> "수출입 신고서 수정";
                case "deleteDeclaration" -> "수출입 신고서 삭제";
                case "uploadAttachment" -> "첨부파일 업로드";
                default -> "신고서 관련 작업";
            };
        } else if (className.contains("Auth")) {
            return switch (methodName) {
                case "updateUserInfo" -> "사용자 정보 수정";
                case "changePassword" -> "비밀번호 변경";
                default -> "계정 관리 작업";
            };
        }
        return className + "." + methodName;
    }

    /**
     * 인증 액션 메시지 생성
     */
    private String getAuthActionMessage(String methodName, boolean success) {
        String action = switch (methodName) {
            case "login" -> "로그인";
            case "register" -> "회원가입";
            case "updateUserInfo" -> "사용자 정보 수정";
            default -> "인증 작업";
        };
        return action + (success ? " 성공" : " 실패");
    }

    /**
     * 인증 시도한 사용자명 추출
     */
    private String getAttemptedUsername(Object[] args) {
        try {
            for (Object arg : args) {
                if (arg != null) {
                    // 리플렉션을 사용해 username 또는 email 필드 찾기
                    try {
                        java.lang.reflect.Field usernameField = arg.getClass().getDeclaredField("username");
                        usernameField.setAccessible(true);
                        Object username = usernameField.get(arg);
                        if (username != null) {
                            return username.toString();
                        }
                    } catch (Exception e) {
                        // username 필드가 없으면 email 시도
                        try {
                            java.lang.reflect.Field emailField = arg.getClass().getDeclaredField("email");
                            emailField.setAccessible(true);
                            Object email = emailField.get(arg);
                            if (email != null) {
                                return email.toString();
                            }
                        } catch (Exception ex) {
                            // 둘 다 없으면 무시
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("사용자명 추출 실패: {}", e.getMessage());
        }
        return "알 수 없음";
    }
}