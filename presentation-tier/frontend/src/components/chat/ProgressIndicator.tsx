/**
 * AI 답변 생성 진행상황 표시 컴포넌트
 * 
 * 🔄 **주요 역할**: model-chatbot-fastapi의 실시간 처리 과정을 사용자에게 시각적으로 표시
 * 
 * **신입 개발자를 위한 설명**:
 * - 이 컴포넌트는 AI가 답변을 생성하는 과정을 실시간으로 보여줍니다
 * - Server-Sent Events(SSE)를 사용하여 백엔드의 진행상황을 스트리밍 받습니다
 * - 각 단계별로 다른 아이콘과 색상을 사용하여 시각적 피드백을 제공합니다
 * - 사용자는 AI가 어떤 작업을 하고 있는지 실시간으로 알 수 있습니다
 * 
 * **주요 기능**:
 * - 📡 실시간 진행상황 스트리밍 수신
 * - 🎨 단계별 시각적 표시 (아이콘, 색상, 애니메이션)
 * - 📋 상세 정보 표시 (단계, 메시지, 세부사항)
 * - 🔄 자동 스크롤 및 최신 상태 유지
 * - ⚡ 연결 상태 관리 (연결/해제/오류 처리)
 * 
 * **사용된 기술**:
 * - Server-Sent Events (SSE): 실시간 데이터 스트리밍
 * - React useState/useEffect: 상태 관리 및 생명주기
 * - Tailwind CSS: 반응형 스타일링
 * - 애니메이션: 부드러운 전환 효과
 * 
 * @file src/components/chat/ProgressIndicator.tsx
 * @description AI 답변 생성 과정 실시간 표시 컴포넌트
 * @since 2025-01-09
 * @author Frontend Team
 * @category 채팅 컴포넌트
 */

'use client';

import { useState, useEffect, useRef } from 'react';

/**
 * 진행상황 데이터 구조
 */
interface ProgressStep {
  /** 타임스탬프 */
  timestamp: string;
  /** 대화 ID */
  conversation_id: string;
  /** 현재 단계 */
  step: string;
  /** 사용자 친화적 메시지 */
  message: string;
  /** 상세 정보 */
  details: string;
}

/**
 * 진행상황 표시기 컴포넌트 Props
 */
interface ProgressIndicatorProps {
  /** 추적할 대화 ID */
  conversationId: string | null;
  /** 표시 여부 */
  isVisible: boolean;
  /** 진행상황 완료 시 콜백 */
  onComplete?: () => void;
  /** 오류 발생 시 콜백 */
  onError?: (error: string) => void;
}

/**
 * 단계별 시각적 스타일 정의
 */
const stepStyles = {
  '연결': { icon: '📡', color: 'text-blue-500', bg: 'bg-blue-50' },
  '대화 준비': { icon: '⚙️', color: 'text-purple-500', bg: 'bg-purple-50' },
  '대화 생성': { icon: '💬', color: 'text-green-500', bg: 'bg-green-50' },
  'AI 분석': { icon: '🧠', color: 'text-indigo-500', bg: 'bg-indigo-50' },
  '응답 생성': { icon: '✨', color: 'text-yellow-500', bg: 'bg-yellow-50' },
  '완료': { icon: '✅', color: 'text-green-600', bg: 'bg-green-100' },
  '오류': { icon: '❌', color: 'text-red-500', bg: 'bg-red-50' },
  'heartbeat': { icon: '💓', color: 'text-gray-400', bg: 'bg-gray-50' },
};

/**
 * AI 답변 생성 진행상황 표시 컴포넌트
 * 
 * Server-Sent Events를 통해 실시간으로 AI 처리 과정을 표시합니다.
 * 각 단계별로 적절한 아이콘과 색상을 사용하여 시각적 피드백을 제공합니다.
 * 
 * @param {ProgressIndicatorProps} props - 컴포넌트 속성
 * @returns {JSX.Element} 진행상황 표시 컴포넌트
 * 
 * @example
 * ```tsx
 * <ProgressIndicator
 *   conversationId="conv_123"
 *   isVisible={isLoading}
 *   onComplete={() => setIsLoading(false)}
 *   onError={(error) => console.error('Progress error:', error)}
 * />
 * ```
 */
export function ProgressIndicator({
  conversationId,
  isVisible,
  onComplete,
  onError
}: ProgressIndicatorProps) {
  /** 진행상황 단계 목록 */
  const [steps, setSteps] = useState<ProgressStep[]>([]);
  /** 현재 진행 중인 단계 */
  const [currentStep, setCurrentStep] = useState<string>('');
  /** 연결 상태 */
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  /** EventSource 참조 */
  const eventSourceRef = useRef<EventSource | null>(null);
  /** 진행상황 컨테이너 참조 (자동 스크롤용) */
  const containerRef = useRef<HTMLDivElement>(null);

  /**
   * 진행상황 스트림 연결 시작
   */
  const connectToProgressStream = () => {
    if (!conversationId || !isVisible) return;

    // 기존 연결이 있으면 종료
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setConnectionStatus('connecting');
    setSteps([]); // 이전 단계들 초기화

    // model-chatbot-fastapi SSE 엔드포인트에 연결
    const eventSource = new EventSource(
      `http://localhost:8004/api/v1/progress/stream/${conversationId}`
    );
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('[Progress] SSE connection opened');
      setConnectionStatus('connected');
    };

    eventSource.onmessage = (event) => {
      try {
        const progressData: ProgressStep = JSON.parse(event.data);
        console.log('[Progress] Received:', progressData);

        // heartbeat 메시지는 표시하지 않음
        if (progressData.step === 'heartbeat') return;

        setSteps(prev => [...prev, progressData]);
        setCurrentStep(progressData.step);

        // 자동 스크롤
        setTimeout(() => {
          if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
          }
        }, 100);

        // 완료 단계에서 콜백 호출
        if (progressData.step === '완료' && onComplete) {
          setTimeout(() => {
            onComplete();
          }, 2000); // 2초 후 완료 처리
        }

      } catch (error) {
        console.error('[Progress] Failed to parse SSE data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('[Progress] SSE error:', error);
      setConnectionStatus('error');
      
      if (onError) {
        onError('진행상황 연결에 문제가 발생했습니다');
      }

      // 연결 재시도 (3초 후)
      setTimeout(() => {
        if (isVisible && conversationId) {
          connectToProgressStream();
        }
      }, 3000);
    };

    eventSource.addEventListener('close', () => {
      console.log('[Progress] SSE connection closed');
      setConnectionStatus('disconnected');
    });
  };

  /**
   * 컴포넌트 마운트/언마운트 및 상태 변경 시 연결 관리
   */
  useEffect(() => {
    if (isVisible && conversationId) {
      connectToProgressStream();
    } else {
      // 연결 종료
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setConnectionStatus('disconnected');
      setSteps([]);
      setCurrentStep('');
    }

    // 컴포넌트 언마운트 시 정리
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [isVisible, conversationId]);

  if (!isVisible) return null;

  return (
    <div className="w-full max-w-md mx-auto bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {/* 헤더 */}
        <div className="px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <h3 className="text-sm font-medium">AI 답변 생성 중</h3>
            <div className="ml-auto flex items-center space-x-1">
              {connectionStatus === 'connected' && (
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              )}
              {connectionStatus === 'connecting' && (
                <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
              )}
              {connectionStatus === 'error' && (
                <div className="w-2 h-2 bg-red-400 rounded-full"></div>
              )}
            </div>
          </div>
        </div>

        {/* 진행상황 목록 */}
        <div 
          ref={containerRef}
          className="max-h-48 overflow-y-auto p-4 space-y-3"
        >
          {steps.length === 0 && connectionStatus === 'connecting' && (
            <div className="flex items-center space-x-3 text-gray-500">
              <div className="w-6 h-6 border-2 border-blue-200 border-t-blue-500 rounded-full animate-spin"></div>
              <span className="text-sm">진행상황 연결 중...</span>
            </div>
          )}

          {steps.map((step, index) => {
            const style = stepStyles[step.step as keyof typeof stepStyles] || stepStyles['heartbeat'];
            const isLatest = index === steps.length - 1;
            
            return (
              <div
                key={`${step.timestamp}-${index}`}
                className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${
                  isLatest ? 'bg-blue-50 border border-blue-200' : style.bg
                }`}
              >
                <div className={`text-xl ${isLatest ? 'animate-bounce' : ''}`}>
                  {style.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h4 className={`text-sm font-medium ${style.color}`}>
                      {step.step}
                    </h4>
                    <span className="text-xs text-gray-400">
                      {new Date(step.timestamp).toLocaleTimeString('ko-KR', {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {step.message}
                  </p>
                  {step.details && (
                    <p className="text-xs text-gray-500 mt-1">
                      {step.details}
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          {connectionStatus === 'error' && (
            <div className="flex items-center space-x-3 text-red-500 p-3 bg-red-50 rounded-lg">
              <span className="text-xl">⚠️</span>
              <div>
                <p className="text-sm font-medium">연결 오류</p>
                <p className="text-xs">자동으로 재연결을 시도합니다...</p>
              </div>
            </div>
          )}
        </div>
    </div>
  );
}