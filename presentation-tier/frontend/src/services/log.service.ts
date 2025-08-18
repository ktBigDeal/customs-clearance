/**
 * 사용자 활동 로깅을 위한 서비스
 * 
 * 프론트엔드에서 발생하는 다양한 사용자 활동을 백엔드에 로그로 기록합니다.
 * HS코드 추천, AI 챗봇 사용, OCR 처리 등의 활동을 추적할 수 있습니다.
 * 
 * @author Frontend Team
 * @version 1.0
 * @since 2025-08-18
 */

import { apiClient } from '@/lib/api';

/**
 * 사용자 활동 로그 요청 인터페이스
 */
export interface UserActivityLogRequest {
  action: string;           // 활동 설명 (예: "HS코드 추천 조회")
  source: LogSource;        // 로그 소스 분류
  userId?: number;          // 사용자 ID (선택적)
  userName?: string;        // 사용자명 (선택적)
  processingTime?: number;  // 처리 시간 (밀리초)
  details?: string;         // 추가 상세 정보
}

/**
 * 로그 소스 분류
 */
export type LogSource = 
  | 'HSCODE'      // HS코드 추천/검색
  | 'CHATBOT'     // AI 챗봇
  | 'OCR'         // 문서 OCR 처리
  | 'REPORT'      // 보고서 생성/다운로드
  | 'DECLARATION' // 신고서 관련
  | 'AUTH'        // 인증 관련
  | 'FILE'        // 파일 업로드/다운로드
  | 'SYSTEM';     // 기타 시스템

/**
 * 사용자 활동 로깅 서비스 클래스
 */
class LogService {
  private readonly BASE_URL = '/logs';

  /**
   * 사용자 활동 로그 기록
   * 
   * @param request 로그 기록 요청 정보
   * @returns 기록된 로그 정보
   */
  async logUserActivity(request: UserActivityLogRequest): Promise<void> {
    try {
      await apiClient.post(`${this.BASE_URL}/user-activity`, request);
    } catch (error) {
      console.warn('사용자 활동 로그 기록 실패:', error);
      // 로그 기록 실패가 사용자 경험에 영향을 주지 않도록 에러를 조용히 처리
    }
  }

  /**
   * HS코드 추천 사용 로그
   */
  async logHSCodeRecommendation(query: string, resultsCount: number, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: `HS코드 추천 조회 (검색어: "${query}", 결과: ${resultsCount}개)`,
      source: 'HSCODE',
      userId,
      userName,
      details: `검색어: ${query}, 결과 개수: ${resultsCount}`
    });
  }

  /**
   * HS코드 검색 사용 로그
   */
  async logHSCodeSearch(query: string, resultsCount: number, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: `HS코드 검색 (키워드: "${query}", 결과: ${resultsCount}개)`,
      source: 'HSCODE',
      userId,
      userName,
      details: `검색 키워드: ${query}, 결과 개수: ${resultsCount}`
    });
  }

  /**
   * AI 챗봇 대화 로그
   */
  async logChatbotConversation(question: string, responseLength: number, processingTime: number, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: `AI 챗봇 대화 (질문 길이: ${question.length}자, 응답 길이: ${responseLength}자)`,
      source: 'CHATBOT',
      userId,
      userName,
      processingTime,
      details: `질문: ${question.substring(0, 50)}${question.length > 50 ? '...' : ''}`
    });
  }

  /**
   * OCR 문서 처리 로그
   */
  async logOCRProcessing(fileName: string, fileSize: number, processingTime: number, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: `문서 OCR 처리 (파일: ${fileName})`,
      source: 'OCR',
      userId,
      userName,
      processingTime,
      details: `파일명: ${fileName}, 파일 크기: ${fileSize} bytes`
    });
  }

  /**
   * 보고서 생성 로그
   */
  async logReportGeneration(reportType: string, processingTime: number, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: `${reportType} 보고서 생성`,
      source: 'REPORT',
      userId,
      userName,
      processingTime,
      details: `보고서 유형: ${reportType}`
    });
  }

  /**
   * 보고서 다운로드 로그
   */
  async logReportDownload(reportType: string, format: string, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: `${reportType} 보고서 다운로드 (${format})`,
      source: 'REPORT',
      userId,
      userName,
      details: `보고서 유형: ${reportType}, 포맷: ${format}`
    });
  }

  /**
   * 파일 업로드 로그
   */
  async logFileUpload(fileName: string, fileSize: number, fileType: string, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: `파일 업로드 (${fileName})`,
      source: 'FILE',
      userId,
      userName,
      details: `파일명: ${fileName}, 크기: ${fileSize} bytes, 유형: ${fileType}`
    });
  }

  /**
   * 신고서 작업 로그
   */
  async logDeclarationAction(action: string, declarationId?: number, userId?: number, userName?: string): Promise<void> {
    return this.logUserActivity({
      action: action,
      source: 'DECLARATION',
      userId,
      userName,
      details: declarationId ? `신고서 ID: ${declarationId}` : undefined
    });
  }

  /**
   * 성능 측정과 함께 활동 로그 기록
   * 
   * @param action 활동 설명
   * @param source 로그 소스
   * @param startTime 시작 시간 (Date.now())
   * @param userId 사용자 ID
   * @param userName 사용자명
   * @param details 추가 상세 정보
   */
  async logActivityWithTiming(
    action: string, 
    source: LogSource, 
    startTime: number, 
    userId?: number, 
    userName?: string, 
    details?: string
  ): Promise<void> {
    const processingTime = Date.now() - startTime;
    
    return this.logUserActivity({
      action,
      source,
      userId,
      userName,
      processingTime,
      details
    });
  }
}

// 싱글톤 인스턴스 생성 및 내보내기
export const logService = new LogService();

/**
 * 사용자 정보를 자동으로 포함하는 로그 헬퍼 함수들
 * 
 * 사용 예시:
 * ```typescript
 * import { logHSCodeRecommendation } from '@/services/log.service';
 * 
 * // 사용자 정보 없이 호출
 * await logHSCodeRecommendation("딸기", 5);
 * 
 * // 사용자 정보와 함께 호출
 * await logHSCodeRecommendation("딸기", 5, user.id, user.name);
 * ```
 */

// 현재 로그인한 사용자 정보를 가져오는 헬퍼 함수 (필요시 구현)
function getCurrentUser(): { id?: number; name?: string } {
  // TODO: 실제 인증 시스템에서 현재 사용자 정보 가져오기
  // 예: JWT 토큰에서 사용자 정보 추출하거나 Context에서 가져오기
  return { id: undefined, name: undefined };
}

// 편의 함수들 (사용자 정보 자동 포함)
export const logHSCodeRecommendation = (query: string, resultsCount: number) => {
  const { id, name } = getCurrentUser();
  return logService.logHSCodeRecommendation(query, resultsCount, id, name);
};

export const logChatbotConversation = (question: string, responseLength: number, processingTime: number) => {
  const { id, name } = getCurrentUser();
  return logService.logChatbotConversation(question, responseLength, processingTime, id, name);
};

export const logOCRProcessing = (fileName: string, fileSize: number, processingTime: number) => {
  const { id, name } = getCurrentUser();
  return logService.logOCRProcessing(fileName, fileSize, processingTime, id, name);
};