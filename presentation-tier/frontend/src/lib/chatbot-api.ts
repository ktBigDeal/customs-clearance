/**
 * AI Gateway 챗봇 API 클라이언트
 * 
 * 🤖 **주요 역할**: AI Gateway를 통한 model-chatbot-fastapi 서비스와의 통신
 * 
 * **신입 개발자를 위한 설명**:
 * - 이 파일은 AI Gateway의 챗봇 통합 API와 전용으로 통신하는 클라이언트입니다
 * - 기본 API 클라이언트를 확장하여 챗봇 전용 기능을 제공합니다
 * - 실시간 채팅, 대화 히스토리, 검색 등의 기능을 지원합니다
 * 
 * **아키텍처 흐름**:
 * Frontend → AI Gateway (포트 8000) → model-chatbot-fastapi (포트 8004)
 * 
 * **보안 및 인증**:
 * - 사용자 인증은 presentation-tier/backend에서 처리
 * - AI Gateway는 검증된 user_id를 model-chatbot-fastapi에 전달
 * 
 * @file src/lib/chatbot-api.ts
 * @description AI Gateway 챗봇 통합 API 클라이언트
 * @since 2025-08-08
 * @author Frontend Team
 * @category API 통신
 */

import axios, { AxiosInstance } from 'axios';

/**
 * 챗봇 채팅 요청 데이터 구조
 */
export interface ChatbotRequest {
  /** 사용자 메시지 */
  message: string;
  /** 사용자 ID (백엔드에서 인증 후 전달) */
  user_id?: number;
  /** 기존 대화 세션 ID (새 대화시 null) */
  conversation_id?: string;
  /** 이전 대화 히스토리 포함 여부 */
  include_history?: boolean;
}

/**
 * 챗봇 메시지 정보
 */
export interface ChatbotMessage {
  /** 메시지 ID */
  id: string;
  /** 대화 세션 ID */
  conversation_id: string;
  /** 메시지 역할 (user/assistant) */
  role: 'user' | 'assistant';
  /** 메시지 내용 */
  content: string;
  /** 사용한 AI 에이전트 (assistant 메시지만) */
  agent_used?: string;
  /** 라우팅 정보 (assistant 메시지만) */
  routing_info?: {
    selected_agent: string;
    complexity: number;
    reasoning: string;
  };
  /** 참고 문서 목록 (assistant 메시지만) */
  references?: Array<{
    source: string;
    title: string;
    similarity: number;
    metadata: Record<string, any>;
  }>;
  /** 메시지 생성 시간 */
  timestamp: string;
  /** 추가 메타데이터 */
  extra_metadata?: Record<string, any>;
}

/**
 * 챗봇 채팅 응답 데이터 구조
 */
export interface ChatbotResponse {
  /** 대화 세션 ID */
  conversation_id: string;
  /** 사용자 메시지 정보 */
  user_message: ChatbotMessage;
  /** AI 응답 메시지 정보 */
  assistant_message: ChatbotMessage;
  /** 새로운 대화 여부 */
  is_new_conversation: boolean;
  /** 처리 시간(초) */
  processing_time?: number;
}

/**
 * 대화 히스토리 응답 구조
 */
export interface ConversationHistory {
  /** 대화 세션 ID */
  conversation_id: string;
  /** 메시지 목록 */
  messages: ChatbotMessage[];
  /** 총 메시지 수 */
  total_messages: number;
  /** 대화 시작 시간 */
  created_at?: string;
}

/**
 * 대화 요약 정보
 */
export interface ConversationSummary {
  id: string;
  title?: string;
  message_count: number;
  last_agent_used?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

/**
 * 사용자 대화 목록 응답 구조
 */
export interface ConversationList {
  /** 대화 목록 */
  conversations: ConversationSummary[];
  /** 총 대화 수 */
  total_conversations: number;
  /** 현재 페이지 */
  page?: number;
  /** 페이지 크기 */
  limit?: number;
}

/**
 * 대화 검색 요청 구조
 */
export interface ConversationSearchRequest {
  /** 검색 쿼리 */
  query: string;
  /** 사용자 ID */
  user_id?: number;
  /** 에이전트 타입 필터 */
  agent_type?: string;
  /** 시작 날짜 */
  start_date?: string;
  /** 종료 날짜 */
  end_date?: string;
  /** 결과 수 제한 */
  limit?: number;
  /** 페이지 오프셋 */
  offset?: number;
}

/**
 * AI Gateway 챗봇 API 클라이언트 클래스
 * 
 * AI Gateway의 챗봇 통합 서비스와의 모든 통신을 담당합니다.
 * 실시간 채팅, 대화 관리, 검색 등의 기능을 제공합니다.
 * 
 * @class ChatbotApiClient
 * @example
 * ```typescript
 * import { chatbotApiClient } from '@/lib/chatbot-api';
 * 
 * // 채팅 메시지 전송
 * const response = await chatbotApiClient.sendMessage({
 *   message: '딸기 수입 가능한가요?',
 *   user_id: 1
 * });
 * 
 * // 대화 히스토리 조회
 * const history = await chatbotApiClient.getConversationHistory(
 *   'conv_abc123', 1
 * );
 * ```
 */
class ChatbotApiClient {
  /** Axios 인스턴스 */
  private client: AxiosInstance;

  /**
   * ChatbotApiClient 생성자
   * 
   * AI Gateway의 챗봇 API 엔드포인트에 맞춰 설정된 Axios 인스턴스를 생성합니다.
   */
  constructor() {
    const baseURL = process.env.NEXT_PUBLIC_AI_GATEWAY_URL || 'http://localhost:8000';
    
    // 디버깅을 위한 환경변수 확인
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      console.log('[Chatbot API] Initializing with baseURL:', baseURL);
      console.log('[Chatbot API] Environment variable NEXT_PUBLIC_AI_GATEWAY_URL:', process.env.NEXT_PUBLIC_AI_GATEWAY_URL);
    }
    
    this.client = axios.create({
      /** AI Gateway 베이스 URL */
      baseURL,
      /** 요청 타임아웃 (30초 - AI 응답 대기 시간 고려) */
      timeout: 30000,
      /** 기본 HTTP 헤더 */
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * 요청/응답 인터셉터 설정
   * 
   * 인증 토큰 추가, 에러 처리, 로깅 등을 설정합니다.
   */
  private setupInterceptors() {
    // 요청 인터셉터 - 인증 토큰 추가
    this.client.interceptors.request.use(
      (config) => {
        // JWT 토큰이 있으면 Authorization 헤더에 추가
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // 요청 시작 시간 기록
        config.metadata = { requestStartedAt: Date.now() };
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터 - 에러 처리 및 로깅
    this.client.interceptors.response.use(
      (response) => {
        // 개발 환경에서 응답 시간 로깅
        if (process.env.NODE_ENV === 'development') {
          const duration = Date.now() - (response.config.metadata?.requestStartedAt || 0);
          console.log(`[Chatbot API] ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`);
        }
        
        return response;
      },
      (error) => {
        if (error.response) {
          // 서버 응답 에러 처리
          const errorMessage = error.response.data?.message || '챗봇 서비스에 일시적인 문제가 발생했습니다.';
          
          switch (error.response.status) {
            case 401:
              this.handleUnauthorized();
              break;
            case 403:
              throw new Error('챗봇 서비스 이용 권한이 없습니다.');
            case 429:
              throw new Error('요청이 너무 많습니다. 잠시 후 다시 시도해주세요.');
            case 500:
              throw new Error('챗봇 서비스에 일시적인 문제가 발생했습니다.');
            default:
              throw new Error(errorMessage);
          }
        } else if (error.request) {
          // 네트워크 에러
          console.error('[Chatbot API] Network Error Details:', {
            baseURL: error.config?.baseURL,
            url: error.config?.url,
            method: error.config?.method,
            timeout: error.config?.timeout,
            fullURL: `${error.config?.baseURL}${error.config?.url}`
          });
          throw new Error(`네트워크 연결 실패: ${error.config?.baseURL}${error.config?.url}`);
        } else {
          // 요청 설정 에러
          throw new Error('요청 처리 중 오류가 발생했습니다.');
        }
      }
    );
  }

  /**
   * 인증 토큰 조회
   */
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  /**
   * 인증 오류 처리
   */
  private handleUnauthorized() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
  }

  /**
   * 챗봇과 메시지 주고받기
   * 
   * 사용자 메시지를 AI Gateway를 통해 model-chatbot-fastapi로 전송하고
   * AI 응답을 받아 반환합니다.
   * 
   * @param {ChatbotRequest} request - 채팅 요청 데이터
   * @returns {Promise<ChatbotResponse>} AI 응답 데이터
   * 
   * @example
   * ```typescript
   * const response = await chatbotApiClient.sendMessage({
   *   message: 'HS코드 분류 방법을 알고 싶어요',
   *   user_id: 1,
   *   conversation_id: 'conv_123', // 기존 대화 계속
   *   include_history: true
   * });
   * 
   * console.log('AI 응답:', response.assistant_message.content);
   * console.log('사용된 에이전트:', response.assistant_message.agent_used);
   * ```
   * 
   * @throws {Error} API 호출 실패 시
   */
  async sendMessage(request: ChatbotRequest): Promise<ChatbotResponse> {
    const response = await this.client.post<ChatbotResponse>(
      '/api/v1/chatbot/chat',
      request
    );
    return response.data;
  }

  /**
   * 대화 히스토리 조회
   * 
   * 특정 대화 세션의 메시지 히스토리를 조회합니다.
   * 
   * @param {string} conversationId - 대화 세션 ID
   * @param {number} userId - 사용자 ID
   * @param {number} [limit=50] - 조회할 메시지 수
   * @param {number} [offset=0] - 메시지 오프셋
   * @returns {Promise<ConversationHistory>} 대화 히스토리 데이터
   * 
   * @example
   * ```typescript
   * const history = await chatbotApiClient.getConversationHistory(
   *   'conv_abc123', 
   *   1, 
   *   50, 
   *   0
   * );
   * 
   * console.log(`총 ${history.total_messages}개의 메시지`);
   * history.messages.forEach(msg => {
   *   console.log(`${msg.role}: ${msg.content}`);
   * });
   * ```
   */
  async getConversationHistory(
    conversationId: string,
    userId: number,
    limit: number = 50,
    offset: number = 0
  ): Promise<ConversationHistory> {
    const response = await this.client.get<ConversationHistory>(
      `/api/v1/chatbot/conversations/${conversationId}/messages`,
      {
        params: { user_id: userId, limit, offset }
      }
    );
    return response.data;
  }

  /**
   * 사용자의 대화 목록 조회
   * 
   * 특정 사용자의 모든 대화 세션 목록을 조회합니다.
   * 
   * @param {number} userId - 사용자 ID
   * @param {number} [page=1] - 페이지 번호 (1부터 시작)
   * @param {number} [limit=20] - 조회할 대화 수
   * @returns {Promise<ConversationList>} 대화 목록 데이터
   * 
   * @example
   * ```typescript
   * const conversations = await chatbotApiClient.getConversationList(1, 1, 10);
   * 
   * console.log(`총 ${conversations.total_conversations}개의 대화`);
   * conversations.conversations.forEach(conv => {
   *   console.log(`${conv.title || '제목 없음'} - ${conv.message_count}개 메시지`);
   * });
   * ```
   */
  async getConversationList(
    userId: number,
    page: number = 1,
    limit: number = 20
  ): Promise<ConversationList> {
    const response = await this.client.get<ConversationList>(
      `/api/v1/chatbot/conversations/user/${userId}`,
      {
        params: { page, limit }
      }
    );
    return response.data;
  }

  /**
   * 대화 전문검색
   * 
   * 사용자의 대화 히스토리에서 특정 키워드를 검색합니다.
   * 
   * @param {ConversationSearchRequest} request - 검색 요청 데이터
   * @returns {Promise<any>} 검색 결과 데이터
   * 
   * @example
   * ```typescript
   * const searchResults = await chatbotApiClient.searchConversations({
   *   query: 'HS코드',
   *   user_id: 1,
   *   agent_type: 'law_agent',
   *   limit: 10
   * });
   * ```
   */
  async searchConversations(request: ConversationSearchRequest): Promise<any> {
    const response = await this.client.post(
      '/api/v1/chatbot/conversations/search',
      request
    );
    return response.data;
  }

  /**
   * 대화 세션 삭제
   * 
   * 사용자의 대화 세션을 삭제합니다. 실제로는 소프트 삭제가 수행되어
   * 대화가 비활성화되고 목록에서 제외됩니다.
   * 
   * @param {string} conversationId - 삭제할 대화 세션 ID
   * @param {number} userId - 사용자 ID (권한 검증용)
   * @returns {Promise<void>} 삭제 성공 시 void, 실패 시 예외 발생
   * 
   * @example
   * ```typescript
   * try {
   *   await chatbotApiClient.deleteConversation('conv_abc123', 1);
   *   console.log('대화가 성공적으로 삭제되었습니다');
   * } catch (error) {
   *   console.error('대화 삭제 실패:', error.message);
   * }
   * ```
   * 
   * @throws {Error} 대화를 찾을 수 없거나 권한이 없는 경우
   */
  async deleteConversation(conversationId: string, userId: number): Promise<void> {
    await this.client.delete(`/api/v1/chatbot/conversations/${conversationId}`, {
      params: { user_id: userId }
    });
  }

  /**
   * 챗봇 서비스 헬스 체크
   * 
   * AI Gateway와 model-chatbot-fastapi 서비스의 상태를 확인합니다.
   * 
   * @returns {Promise<any>} 헬스 체크 결과
   * 
   * @example
   * ```typescript
   * const health = await chatbotApiClient.healthCheck();
   * console.log('챗봇 서비스 상태:', health.status);
   * ```
   */
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/api/v1/chatbot/health');
    return response.data;
  }
}

// 싱글톤 인스턴스 생성 및 내보내기
export const chatbotApiClient = new ChatbotApiClient();

// Axios 설정 확장 (TypeScript)
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      requestStartedAt: number;
    };
  }
}