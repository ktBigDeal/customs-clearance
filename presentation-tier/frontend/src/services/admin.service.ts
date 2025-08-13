/**
 * 관리자 기능을 위한 API 서비스
 * 
 * 관리자 전용 기능들(로그 조회, 시스템 통계 등)에 대한 API 호출을 담당합니다.
 * 
 * @author Frontend Team
 * @version 1.0 
 * @since 2025-08-13
 */

import { apiClient } from '@/lib/api';

/**
 * 시스템 로그 관련 타입 정의
 */
export interface SystemLog {
  id: number;
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  source: string;
  message: string;
  userId?: number;
  userName?: string;
  ipAddress?: string;
  userAgent?: string;
  requestUri?: string;
  httpMethod?: string;
  statusCode?: number;
  processingTime?: number;
}

export interface LogSearchRequest {
  keyword?: string;
  level?: string;
  source?: string;
  dateFilter?: 'today' | 'week' | 'month' | 'all';
  page?: number;
  size?: number;
  startDate?: string;
  endDate?: string;
}

export interface LogListResponse {
  logs: SystemLog[];
  totalCount: number;
  page: number;
  size: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface LogStats {
  totalLogs: number;
  errorCount: number;
  warnCount: number;
  infoCount: number;
  debugCount: number;
  errorRate: number;
}

export interface CreateLogRequest {
  level: string;
  source: string;
  message: string;
  userId?: number;
  userName?: string;
  ipAddress?: string;
  userAgent?: string;
  requestUri?: string;
  httpMethod?: string;
  statusCode?: number;
  processingTime?: number;
}

/**
 * 관리자 서비스 클래스
 */
class AdminService {
  private readonly BASE_URL = '/api/v1/admin';


  /**
   * 시스템 로그 목록 조회 (POST 방식 - 복잡한 검색 조건)
   * 
   * @param request 검색 조건
   * @returns 로그 목록과 페이지네이션 정보
   */
  async getLogs(request: LogSearchRequest): Promise<LogListResponse> {
    try {
      const response = await apiClient.post<LogListResponse, LogSearchRequest>(
        `${this.BASE_URL}/logs/search`,
        {
          keyword: request.keyword || undefined,
          level: request.level || 'all',
          source: request.source || 'all',
          dateFilter: request.dateFilter || 'today',
          page: request.page || 0,
          size: request.size || 20,
          startDate: request.startDate,
          endDate: request.endDate
        }
      );
      return response;
    } catch (error) {
      console.error('로그 조회 실패:', error);
      throw new Error('로그 데이터를 불러오는데 실패했습니다.');
    }
  }

  /**
   * 시스템 로그 목록 조회 (GET 방식 - 간단한 조건)
   * 
   * @param params 검색 파라미터
   * @returns 로그 목록과 페이지네이션 정보
   */
  async getLogsSimple(params: {
    page?: number;
    size?: number;
    keyword?: string;
    level?: string;
    source?: string;
    dateFilter?: string;
  }): Promise<LogListResponse> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page !== undefined) queryParams.append('page', params.page.toString());
      if (params.size !== undefined) queryParams.append('size', params.size.toString());
      if (params.keyword) queryParams.append('keyword', params.keyword);
      if (params.level) queryParams.append('level', params.level);
      if (params.source) queryParams.append('source', params.source);
      if (params.dateFilter) queryParams.append('dateFilter', params.dateFilter);

      const response = await apiClient.get<LogListResponse>(
        `${this.BASE_URL}/logs?${queryParams.toString()}`
      );
      return response;
    } catch (error) {
      console.error('로그 조회 실패:', error);
      throw new Error('로그 데이터를 불러오는데 실패했습니다.');
    }
  }

  /**
   * 로그 통계 조회
   * 
   * @param dateFilter 통계 기간
   * @returns 로그 통계 정보
   */
  async getLogStats(dateFilter: string = 'today'): Promise<LogStats> {
    try {
      const response = await apiClient.get<LogStats>(
        `${this.BASE_URL}/logs/stats?dateFilter=${dateFilter}`
      );
      return response;
    } catch (error) {
      console.error('로그 통계 조회 실패:', error);
      throw new Error('로그 통계 데이터를 불러오는데 실패했습니다.');
    }
  }

  /**
   * 테스트용 로그 생성
   * 
   * @param request 생성할 로그 정보
   * @returns 생성된 로그 정보
   */
  async createTestLog(request: CreateLogRequest): Promise<SystemLog> {
    try {
      const response = await apiClient.post<SystemLog, CreateLogRequest>(
        `${this.BASE_URL}/logs`,
        request
      );
      return response;
    } catch (error) {
      console.error('테스트 로그 생성 실패:', error);
      throw new Error('테스트 로그 생성에 실패했습니다.');
    }
  }

  /**
   * 관리자 API 상태 확인
   * 
   * @returns API 상태 메시지
   */
  async healthCheck(): Promise<string> {
    try {
      const response = await apiClient.get<string>(`${this.BASE_URL}/health`);
      return response;
    } catch (error) {
      console.error('관리자 API 상태 확인 실패:', error);
      throw new Error('관리자 API 상태 확인에 실패했습니다.');
    }
  }

  /**
   * 로그 데이터를 CSV 파일로 내보내기 (클라이언트 측)
   * 
   * @param logs 내보낼 로그 데이터
   * @param filename 파일명 (기본값: 현재 날짜)
   */
  exportLogsToCSV(logs: SystemLog[], filename?: string): void {
    try {
      const headers = [
        '시간', '레벨', '소스', '메시지', '사용자', 'IP주소', 
        '요청 URI', 'HTTP 메서드', '상태 코드', '처리 시간(ms)'
      ];

      const csvContent = [
        headers.join(','),
        ...logs.map(log => [
          log.timestamp,
          log.level,
          log.source,
          `"${log.message.replace(/"/g, '""')}"`, // CSV 따옴표 이스케이프
          log.userName || '',
          log.ipAddress || '',
          log.requestUri || '',
          log.httpMethod || '',
          log.statusCode || '',
          log.processingTime || ''
        ].join(','))
      ].join('\n');

      const blob = new Blob(['\uFEFF' + csvContent], { 
        type: 'text/csv;charset=utf-8;' 
      });
      
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      
      link.setAttribute('href', url);
      link.setAttribute('download', 
        filename || `system_logs_${new Date().toISOString().split('T')[0]}.csv`
      );
      link.style.visibility = 'hidden';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('CSV 내보내기 실패:', error);
      throw new Error('CSV 파일 생성에 실패했습니다.');
    }
  }

  /**
   * 날짜 필터를 사용자 친화적인 텍스트로 변환
   * 
   * @param dateFilter 날짜 필터 값
   * @returns 사용자 친화적인 텍스트
   */
  getDateFilterLabel(dateFilter: string): string {
    const labels: { [key: string]: string } = {
      'today': '오늘',
      'week': '이번 주',
      'month': '이번 달',
      'year': '올해',
      'all': '전체 기간'
    };
    return labels[dateFilter] || '알 수 없음';
  }

  /**
   * 로그 레벨에 따른 색상 스타일 반환
   * 
   * @param level 로그 레벨
   * @returns CSS 클래스 문자열
   */
  getLevelColorClass(level: string): string {
    const colorClasses: { [key: string]: string } = {
      'ERROR': 'bg-red-100 text-red-800',
      'WARN': 'bg-yellow-100 text-yellow-800',
      'INFO': 'bg-blue-100 text-blue-800',
      'DEBUG': 'bg-gray-100 text-gray-800'
    };
    return colorClasses[level] || 'bg-gray-100 text-gray-800';
  }

  /**
   * 처리 시간을 사용자 친화적인 형태로 포맷
   * 
   * @param processingTime 처리 시간 (밀리초)
   * @returns 포맷된 문자열
   */
  formatProcessingTime(processingTime?: number): string {
    if (!processingTime) return '-';
    
    if (processingTime < 1000) {
      return `${processingTime}ms`;
    } else if (processingTime < 60000) {
      return `${(processingTime / 1000).toFixed(2)}s`;
    } else {
      const minutes = Math.floor(processingTime / 60000);
      const seconds = ((processingTime % 60000) / 1000).toFixed(0);
      return `${minutes}m ${seconds}s`;
    }
  }
}

// 싱글톤 인스턴스 생성 및 내보내기
export const adminService = new AdminService();