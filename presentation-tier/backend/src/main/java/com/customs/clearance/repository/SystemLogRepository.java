package com.customs.clearance.repository;

import com.customs.clearance.entity.SystemLog;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 시스템 로그 데이터 액세스를 담당하는 레포지토리
 * 
 * 시스템 로그 조회, 필터링, 통계 등의 데이터베이스 작업을 처리합니다.
 * 
 * @author Backend Team
 * @version 1.0
 * @since 2025-08-13
 */
@Repository
public interface SystemLogRepository extends JpaRepository<SystemLog, Long> {

    /**
     * 페이지네이션과 함께 로그를 최신순으로 조회
     */
    Page<SystemLog> findAllByOrderByTimestampDesc(Pageable pageable);

    /**
     * 로그 레벨로 필터링하여 조회
     */
    Page<SystemLog> findByLevelOrderByTimestampDesc(SystemLog.LogLevel level, Pageable pageable);

    /**
     * 소스로 필터링하여 조회
     */
    Page<SystemLog> findBySourceOrderByTimestampDesc(String source, Pageable pageable);

    /**
     * 날짜 범위로 필터링하여 조회
     */
    Page<SystemLog> findByTimestampBetweenOrderByTimestampDesc(
            LocalDateTime startDate, 
            LocalDateTime endDate, 
            Pageable pageable
    );

    /**
     * 메시지 또는 사용자명으로 검색
     */
    @Query("SELECT sl FROM SystemLog sl WHERE " +
           "sl.message LIKE %:keyword% OR " +
           "sl.userName LIKE %:keyword% OR " +
           "sl.source LIKE %:keyword% " +
           "ORDER BY sl.timestamp DESC")
    Page<SystemLog> findByKeywordOrderByTimestampDesc(@Param("keyword") String keyword, Pageable pageable);

    /**
     * 복합 조건으로 로그 검색
     */
    @Query("SELECT sl FROM SystemLog sl WHERE " +
           "(:level IS NULL OR sl.level = :level) AND " +
           "(:source IS NULL OR sl.source = :source) AND " +
           "(:startDate IS NULL OR sl.timestamp >= :startDate) AND " +
           "(:endDate IS NULL OR sl.timestamp <= :endDate) AND " +
           "(:keyword IS NULL OR sl.message LIKE %:keyword% OR sl.userName LIKE %:keyword% OR sl.source LIKE %:keyword%) " +
           "ORDER BY sl.timestamp DESC")
    Page<SystemLog> findByFilters(
            @Param("level") SystemLog.LogLevel level,
            @Param("source") String source,
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate,
            @Param("keyword") String keyword,
            Pageable pageable
    );

    /**
     * 로그 레벨별 개수 조회
     */
    @Query("SELECT sl.level, COUNT(sl) FROM SystemLog sl " +
           "WHERE sl.timestamp >= :startDate GROUP BY sl.level")
    List<Object[]> countByLevelAfterDate(@Param("startDate") LocalDateTime startDate);

    /**
     * 특정 기간 내 에러 로그 개수 조회
     */
    @Query("SELECT COUNT(sl) FROM SystemLog sl WHERE " +
           "sl.level = 'ERROR' AND sl.timestamp >= :startDate")
    Long countErrorsSince(@Param("startDate") LocalDateTime startDate);

    /**
     * 사용자별 로그 조회
     */
    Page<SystemLog> findByUserIdOrderByTimestampDesc(Long userId, Pageable pageable);

    /**
     * IP 주소별 로그 조회
     */
    Page<SystemLog> findByIpAddressOrderByTimestampDesc(String ipAddress, Pageable pageable);

    /**
     * 특정 날짜 이전의 로그 개수 조회
     */
    Long countByTimestampBefore(LocalDateTime cutoffDate);

    /**
     * 특정 날짜 이전의 로그 삭제
     */
    void deleteByTimestampBefore(LocalDateTime cutoffDate);
}