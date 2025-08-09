/**
 * 최근 대화 목록 관리 Hook
 * 
 * 🔄 **주요 역할**: React Query를 활용한 사용자 대화 목록 데이터 관리
 * 
 * **신입 개발자를 위한 설명**:
 * - 이 Hook은 chatbot API에서 사용자의 최근 대화 목록을 가져와 관리합니다
 * - React Query를 사용하여 캐싱, 로딩 상태, 에러 처리를 자동화합니다
 * - 실시간 업데이트와 백그라운드 refetch를 지원합니다
 * 
 * **주요 기능**:
 * - 📋 사용자별 대화 목록 조회
 * - 🔄 자동 캐싱 및 백그라운드 업데이트
 * - ⏳ 로딩 상태 및 에러 상태 관리
 * - 🎯 실시간 데이터 동기화
 * 
 * **사용된 기술**:
 * - React Query: 서버 상태 관리
 * - Chatbot API Client: API 통신
 * - TypeScript: 타입 안전성
 * 
 * @file src/hooks/useRecentConversations.ts
 * @description 최근 대화 목록 데이터 관리 Hook
 * @since 2025-01-09
 * @author Frontend Team
 * @category React Hook
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { chatbotApiClient, ConversationList, ConversationSummary } from '@/lib/chatbot-api';

/**
 * 최근 대화 목록 Hook 옵션
 */
export interface UseRecentConversationsOptions {
  /** 사용자 ID */
  userId: number;
  /** 조회할 대화 수 (기본: 10개) */
  limit?: number;
  /** 자동 refetch 활성화 (기본: true) */
  enabled?: boolean;
  /** refetch 간격 (밀리초, 기본: 30초) */
  refetchInterval?: number;
}

/**
 * 최근 대화 목록 Hook 반환값
 */
export interface UseRecentConversationsReturn {
  /** 대화 목록 데이터 */
  conversations: ConversationSummary[];
  /** 총 대화 수 */
  totalConversations: number;
  /** 로딩 상태 */
  isLoading: boolean;
  /** 에러 상태 */
  isError: boolean;
  /** 에러 객체 */
  error: Error | null;
  /** 수동 refetch 함수 */
  refetch: () => void;
  /** 백그라운드 로딩 상태 */
  isFetching: boolean;
}

/**
 * 최근 대화 목록을 관리하는 React Hook
 * 
 * 사용자의 최근 대화 목록을 React Query로 관리하며,
 * 로딩 상태, 에러 처리, 자동 업데이트 기능을 제공합니다.
 * 
 * @param {UseRecentConversationsOptions} options - Hook 설정 옵션
 * @returns {UseRecentConversationsReturn} 대화 목록 데이터와 상태 정보
 * 
 * @example
 * ```typescript
 * function ChatSidebar() {
 *   const { 
 *     conversations, 
 *     totalConversations, 
 *     isLoading, 
 *     isError,
 *     refetch 
 *   } = useRecentConversations({
 *     userId: 1,
 *     limit: 5
 *   });
 *   
 *   if (isLoading) return <div>로딩 중...</div>;
 *   if (isError) return <div>데이터 로드 실패</div>;
 *   
 *   return (
 *     <div>
 *       <h3>최근 대화 ({totalConversations})</h3>
 *       {conversations.map(conv => (
 *         <div key={conv.id}>{conv.title}</div>
 *       ))}
 *       <button onClick={() => refetch()}>새로고침</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useRecentConversations({
  userId,
  limit = 10,
  enabled = true,
  refetchInterval = 30000, // 30초
}: UseRecentConversationsOptions): UseRecentConversationsReturn {
  
  /**
   * React Query를 사용한 대화 목록 데이터 관리
   * 
   * - queryKey: 사용자 ID와 limit을 기반으로 고유 키 생성
   * - queryFn: chatbot API를 통한 데이터 페칭
   * - 캐싱: 5분간 데이터 캐시, 30초마다 백그라운드 업데이트
   * - 에러 처리: 자동 재시도 (최대 3회)
   */
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<ConversationList, Error>({
    /** 쿼리 키: 사용자별, 조건별로 캐시 분리 */
    queryKey: ['recentConversations', userId, limit],
    
    /** 데이터 페칭 함수 */
    queryFn: async (): Promise<ConversationList> => {
      console.log('[useRecentConversations] 대화 목록 조회 시작:', { userId, limit });
      
      try {
        const result = await chatbotApiClient.getConversationList(userId, 1, limit);
        
        console.log('[useRecentConversations] 대화 목록 조회 성공:', {
          totalConversations: result.total_conversations,
          conversationsCount: result.conversations.length,
          conversations: result.conversations.map(conv => ({
            id: conv.id,
            title: conv.title,
            messageCount: conv.message_count,
            updatedAt: conv.updated_at
          }))
        });
        
        return result;
        
      } catch (err) {
        const error = err as Error;
        console.error('[useRecentConversations] 대화 목록 조회 실패:', error);
        throw error;
      }
    },
    
    /** 쿼리 옵션 */
    enabled,
    
    /** 캐시 시간: 5분 */
    staleTime: 5 * 60 * 1000,
    
    /** 가비지 컬렉션 시간: 10분 */
    gcTime: 10 * 60 * 1000,
    
    /** 백그라운드 refetch 간격 */
    refetchInterval,
    
    /** 윈도우 포커스 시 refetch */
    refetchOnWindowFocus: true,
    
    /** 네트워크 재연결 시 refetch */
    refetchOnReconnect: true,
    
    /** 재시도 설정 */
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    
    /** 에러 경계 설정 */
    throwOnError: false,
  });

  return {
    conversations: data?.conversations || [],
    totalConversations: data?.total_conversations || 0,
    isLoading,
    isError,
    error: error,
    refetch,
    isFetching,
  };
}

/**
 * 대화 시간 포맷팅 유틸리티 함수
 * 
 * 대화 업데이트 시간을 사용자 친화적인 형태로 변환합니다.
 * 
 * @param {string} timestamp - ISO 타임스탬프
 * @returns {string} 포맷된 시간 문자열
 * 
 * @example
 * ```typescript
 * formatConversationTime('2025-01-09T10:30:00Z') // "2시간 전"
 * formatConversationTime('2025-01-08T10:30:00Z') // "어제"  
 * formatConversationTime('2025-01-02T10:30:00Z') // "1주 전"
 * ```
 */
export function formatConversationTime(timestamp: string): string {
  const now = new Date();
  const conversationTime = new Date(timestamp);
  const diffInMs = now.getTime() - conversationTime.getTime();
  
  // 밀리초를 시간 단위로 변환
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  const diffInWeeks = Math.floor(diffInDays / 7);
  const diffInMonths = Math.floor(diffInDays / 30);

  if (diffInMinutes < 1) {
    return '방금 전';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}분 전`;
  } else if (diffInHours < 24) {
    return `${diffInHours}시간 전`;
  } else if (diffInDays === 1) {
    return '어제';
  } else if (diffInDays < 7) {
    return `${diffInDays}일 전`;
  } else if (diffInWeeks < 4) {
    return `${diffInWeeks}주 전`;
  } else if (diffInMonths < 12) {
    return `${diffInMonths}개월 전`;
  } else {
    return conversationTime.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
}

/**
 * 대화 제목 생성 유틸리티 함수
 * 
 * 대화에 제목이 없는 경우 기본 제목을 생성합니다.
 * 
 * @param {ConversationSummary} conversation - 대화 정보
 * @returns {string} 대화 제목
 * 
 * @example
 * ```typescript
 * const conversation = { id: '123', title: null, message_count: 5 };
 * generateConversationTitle(conversation); // "새로운 대화 (5개 메시지)"
 * ```
 */
export function generateConversationTitle(conversation: ConversationSummary): string {
  if (conversation.title) {
    return conversation.title;
  }
  
  // 기본 제목 생성
  if (conversation.message_count === 0) {
    return '새로운 대화';
  } else if (conversation.message_count === 1) {
    return '새로운 질문';
  } else {
    return `대화 (${conversation.message_count}개 메시지)`;
  }
}