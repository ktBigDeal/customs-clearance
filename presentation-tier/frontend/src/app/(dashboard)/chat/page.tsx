/**
 * AI 상담 채팅 페이지 컴포넌트 (통관 전문 AI 어시스턴트)
 * 
 * 🤖 **주요 역할**: 사용자와 AI 간의 실시간 채팅으로 통관 업무 지원
 * 
 * **신입 개발자를 위한 설명**:
 * - 이 페이지는 사용자가 AI와 채팅하며 통관 관련 질문을 할 수 있는 곳입니다
 * - 실시간으로 메시지를 주고받으며, 타이핑 인디케이터도 표시됩니다
 * - 자주 묻는 질문을 빠르게 선택할 수 있는 템플릿을 제공합니다
 * - AI 답변에는 참고 문서 링크도 함께 제공됩니다
 * 
 * **사용된 주요 기술**:
 * - React useState: 메시지 목록, 입력값, 로딩 상태 관리
 * - useRef: DOM 요소 직접 접근 (스크롤, 포커스 제어)
 * - useEffect: 메시지 추가 시 자동 스크롤 처리
 * - 비동기 처리: AI 응답 시뮬레이션 (실제로는 API 호출)
 * 
 * **UI/UX 특징**:
 * - 카카오톡 스타일의 채팅 인터페이스
 * - 사용자 메시지는 오른쪽, AI 메시지는 왼쪽 정렬
 * - 타이핑 애니메이션으로 AI가 답변 생성 중임을 표시
 * - 참고 문서를 PDF 아이콘과 함께 제공
 * 
 * @file src/app/(dashboard)/chat/page.tsx
 * @description AI 기반 통관 상담 채팅 시스템
 * @since 2024-01-01
 * @author Frontend Team
 * @category 대시보드 페이지
 * @tutorial 채팅 UI 구현 가이드: https://react.dev/learn/sharing-state-between-components
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { chatbotApiClient } from '@/lib/chatbot-api';
import type { ChatbotResponse, ChatbotMessage } from '@/lib/chatbot-api';
import { ProgressIndicator } from '@/components/chat/ProgressIndicator';
import { AIMessageRenderer } from '@/components/chat/MarkdownRenderer';

/**
 * 채팅 메시지 데이터 구조 정의 (UI용 확장 인터페이스)
 * 
 * ChatbotMessage 타입을 UI에 맞게 확장한 인터페이스입니다.
 * 실제 API 응답 데이터와 UI에 필요한 추가 속성을 모두 포함합니다.
 * 
 * @interface Message
 */
interface Message {
  /** 메시지 고유 식별자 */
  id: string;
  /** 메시지 발송자 타입 (user/assistant) */
  type: 'user' | 'assistant';
  /** 메시지 텍스트 내용 */
  content: string;
  /** 메시지 생성 시간 */
  timestamp: Date;
  /** 참고 문서 목록 (AI 메시지에만 적용) */
  sources?: string[];
  /** 타이핑 중 상태 (AI 응답 대기 시) */
  isTyping?: boolean;
  /** 대화 세션 ID */
  conversation_id?: string;
  /** 사용된 AI 에이전트 */
  agent_used?: string;
  /** 라우팅 정보 */
  routing_info?: {
    selected_agent: string;
    complexity: number;
    reasoning: string;
  };
}

/**
 * AI 상담 채팅 페이지 메인 컴포넌트
 * 
 * 통관 전문 AI와의 실시간 대화를 지원하는 채팅 인터페이스입니다.
 * 좌측에는 메시지 영역, 우측에는 빠른 질문과 최근 대화 목록을 표시합니다.
 * 
 * 주요 기능:
 * - 실시간 메시지 교환
 * - 타이핑 인디케이터
 * - 빠른 질문 템플릿
 * - 참고 문서 링크
 * - 최근 대화 히스토리
 * - 파일 첨부 지원
 * 
 * @returns {JSX.Element} 채팅 페이지 컴포넌트
 */
export default function ChatPage() {
  const { t } = useLanguage();
  
  /** 채팅 메시지 목록 */
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: `# 안녕하세요! 👋

**통관 AI 상담사**입니다. 수출입 관련 궁금한 사항이나 통관 절차에 대해 무엇이든 물어보세요.

## 🔍 도움을 드릴 수 있는 분야:

- **HS코드 분류** - 품목별 관세코드 확인
- **관세 계산** - 관세율 및 부가세 산정
- **통관 절차** - 필요서류 및 신고방법
- **FTA 활용** - 특혜관세 적용방법
- **원산지 증명** - 원산지증명서 발급

*궁금한 점이 있으시면 언제든 말씀해 주세요!*`,
      timestamp: new Date(),
    }
  ]);
  
  /** 입력 중인 메시지 내용 */
  const [inputValue, setInputValue] = useState('');
  
  /** AI 응답 로딩 상태 */
  const [isLoading, setIsLoading] = useState(false);
  
  /** 현재 대화 세션 ID */
  const [conversationId, setConversationId] = useState<string | null>(null);
  
  /** 사용자 ID (실제로는 인증 시스템에서 가져와야 함) */
  const [userId] = useState<number>(1); // TODO: 실제 인증된 사용자 ID로 교체
  
  /** 메시지 목록 하단 참조 (자동 스크롤용) */
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  /** 텍스트 입력 필드 참조 */
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  /** 메시지 컨테이너 참조 (스크롤 감지용) */
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  
  /** 사용자가 수동으로 스크롤했는지 여부 */
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  
  /** 초기 로드 완료 여부 */
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  /**
   * ChatbotMessage를 UI Message로 변환하는 유틸리티 함수
   */
  const convertChatbotMessageToMessage = (chatbotMsg: ChatbotMessage): Message => {
    return {
      id: chatbotMsg.id,
      type: chatbotMsg.role,
      content: chatbotMsg.content,
      timestamp: new Date(chatbotMsg.timestamp),
      sources: chatbotMsg.references?.map(ref => ref.title) || [],
      conversation_id: chatbotMsg.conversation_id,
      agent_used: chatbotMsg.agent_used,
      routing_info: chatbotMsg.routing_info,
    };
  };

  /**
   * 사용자가 하단 근처에 있는지 확인
   */
  const isNearBottom = () => {
    const container = messagesContainerRef.current;
    if (!container) return true;
    
    const threshold = 100; // 하단에서 100px 이내
    return (
      container.scrollTop + container.clientHeight >= 
      container.scrollHeight - threshold
    );
  };

  /**
   * 메시지 목록 하단으로 자동 스크롤
   * 메시지 컨테이너만 스크롤하고 헤더/사이드바는 고정
   */
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  /**
   * 스크롤 이벤트 핸들러
   */
  const handleScroll = () => {
    const container = messagesContainerRef.current;
    if (!container) return;

    // 사용자가 하단 근처에 있으면 자동 스크롤 활성화
    setIsUserScrolling(!isNearBottom());
  };

  // 초기 로드 완료 처리
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitialLoad(false);
    }, 1000); // 1초 후에 자동 스크롤 활성화 (더 안전한 타이밍)
    
    return () => clearTimeout(timer);
  }, []);

  // 메시지가 추가될 때 조건부 자동 스크롤 (새로운 메시지가 실제로 추가된 경우만)
  useEffect(() => {
    // 초기 로드 중에는 자동 스크롤 하지 않음
    if (isInitialLoad) return;
    
    // 메시지가 1개 이하면 스크롤하지 않음 (초기 메시지만 있는 경우)
    if (messages.length <= 1) return;
    
    // 사용자가 스크롤 중이 아니거나 하단 근처에 있을 때만 자동 스크롤
    if (!isUserScrolling || isNearBottom()) {
      const timer = setTimeout(() => {
        scrollToBottom();
      }, 100); // 약간의 지연을 두어 DOM 업데이트 완료 후 실행
      
      return () => clearTimeout(timer);
    }
  }, [messages, isUserScrolling, isInitialLoad]);

  /**
   * 메시지 전송 핸들러
   * 
   * 사용자 메시지를 AI Gateway를 통해 model-chatbot-fastapi로 전송하고
   * AI 응답을 받아 화면에 표시합니다.
   * 
   * @param {React.FormEvent} e - 폼 제출 이벤트
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const messageContent = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    // 1단계: 사용자 메시지 먼저 표시
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: messageContent,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // 2단계: 약간의 지연 후 타이핑 인디케이터 표시
    setTimeout(() => {
      const typingMessage: Message = {
        id: 'typing',
        type: 'assistant',
        content: '',
        timestamp: new Date(),
        isTyping: true,
      };
      setMessages(prev => [...prev, typingMessage]);
    }, 300);

    try {
      // AI Gateway를 통한 실제 API 호출
      const response: ChatbotResponse = await chatbotApiClient.sendMessage({
        message: messageContent,
        user_id: userId,
        conversation_id: conversationId || undefined,
        include_history: true,
      });

      // 대화 세션 ID 업데이트 (새 대화인 경우)
      if (response.is_new_conversation && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // AI 응답 메시지만 UI 형식으로 변환 (사용자 메시지는 이미 추가됨)
      const assistantMessage = convertChatbotMessageToMessage(response.assistant_message);

      // 3단계: 타이핑 인디케이터 제거하고 AI 응답 메시지 추가
      setMessages(prev => [
        ...prev.filter(msg => msg.id !== 'typing'),
        assistantMessage
      ]);

      console.log('[Chat] AI 응답 완료:', {
        conversation_id: response.conversation_id,
        agent_used: response.assistant_message.agent_used,
        processing_time: response.processing_time,
        is_new_conversation: response.is_new_conversation
      });
      
    } catch (error) {
      console.error('[Chat] API 호출 실패:', error);
      
      // 타이핑 인디케이터 제거하고 에러 메시지 추가 (사용자 메시지는 이미 추가됨)
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `죄송합니다. 일시적인 오류가 발생했습니다.\n\n오류 내용: ${error instanceof Error ? error.message : '알 수 없는 오류'}\n\n잠시 후 다시 시도해 주세요.`,
        timestamp: new Date(),
        sources: [],
      };
      
      setMessages(prev => [
        ...prev.filter(msg => msg.id !== 'typing'),
        errorMessage
      ]);
      
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 키보드 입력 핸들러
   * 
   * Enter 키로 메시지 전송, Shift+Enter로 줄바꿈을 지원합니다.
   * 
   * @param {React.KeyboardEvent} e - 키보드 이벤트
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  /**
   * 빠른 질문 선택 핸들러
   * 
   * @param {string} question - 선택된 질문 텍스트
   */
  const handleQuickQuestion = (question: string) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  /** 빠른 질문 템플릿 목록 */
  const quickQuestions = [
    'HS코드 분류 방법이 궁금해요',
    '수입신고서 작성 시 필요한 서류는?',
    '원산지증명서는 언제 필요한가요?',
    'FTA 특혜관세 적용 조건은?',
    '통관 소요시간은 얼마나 걸리나요?',
    '관세 계산 방법을 알고 싶어요'
  ];

  /** 최근 대화 목록 (실제 환경에서는 API에서 로드) */
  const recentChats = [
    { title: 'HS코드 관련 질문', time: '2시간 전' },
    { title: '수출신고서 작성법', time: '어제' },
    { title: '원산지증명서 발급', time: '2일 전' },
    { title: 'FTA 활용 방법', time: '1주 전' }
  ];

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-6rem)]">
        <Card className="h-full overflow-hidden rounded-lg">
          <div className="flex h-full">
            {/* Chat Messages Area */}
            <div className="flex-1 flex flex-col">
              {/* Chat Header */}
              <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-500 to-indigo-600 relative rounded-t-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 flex items-center justify-center bg-white/20 rounded-full">
                    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      {t('chat.aiConsultant')}
                    </h2>
                    <p className="text-sm text-blue-100">
                      {t('chat.serviceDesc')}
                    </p>
                  </div>
                   <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span className="text-sm text-blue-100">
                      {t('chat.online')}
                    </span>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div 
                ref={messagesContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto p-6 space-y-6"
              >
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-2xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                      {message.type === 'assistant' && (
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="w-8 h-8 flex items-center justify-center bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full">
                            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                            </svg>
                          </div>
                          <div className="flex flex-col">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium text-gray-700">
                                {t('chat.aiConsultant')}
                              </span>
                              {message.agent_used && (
                                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                                  {message.agent_used.replace('_agent', '').replace('_', ' ')}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-500">
                                {message.timestamp.toLocaleTimeString('ko-KR', { 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })}
                              </span>
                              {message.routing_info?.complexity && (
                                <span className="text-xs text-gray-400">
                                  • 복잡도: {Math.round(message.routing_info.complexity * 100)}%
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                      
                      <div className={`rounded-2xl px-4 py-3 ${
                        message.type === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-50 text-gray-800 border border-gray-100'
                      }`}>
                        {message.isTyping ? (
                          <div className="flex items-center space-x-2">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                            </div>
                            <span className="text-sm text-gray-500">
                              {t('chat.generating')}
                            </span>
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap">
                            {message.type === 'assistant' ? (
                              <AIMessageRenderer content={message.content} />
                            ) : (
                              message.content
                            )}
                          </div>
                        )}
                      </div>

                      {message.type === 'user' && (
                        <div className="flex items-center justify-end space-x-2 mt-2">
                          <span className="text-xs text-gray-500">
                            {message.timestamp.toLocaleTimeString('ko-KR', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </span>
                          <span className="text-sm font-medium text-gray-700">
                            홍길동
                          </span>
                          <div className="w-8 h-8 flex items-center justify-center bg-blue-600 rounded-full">
                            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                            </svg>
                          </div>
                        </div>
                      )}

                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
                          <div className="flex items-center space-x-2 mb-3">
                            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                            </svg>
                            <span className="text-sm font-medium text-blue-800">
                              {t('chat.references')}
                            </span>
                          </div>
                          <div className="space-y-2">
                            {message.sources.map((source, index) => (
                              <button
                                key={index}
                                className="flex items-center space-x-2 w-full text-left p-2 hover:bg-blue-100 rounded-lg transition-colors"
                              >
                                <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                                </svg>
                                <span className="text-sm text-blue-700 hover:text-blue-800">{source}</span>
                                <svg className="w-3 h-3 text-blue-500 ml-auto" fill="currentColor" viewBox="0 0 24 24">
                                  <path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z"/>
                                </svg>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* 진행상황 표시기 */}
                {isLoading && (
                  <div className="flex justify-center my-4">
                    <ProgressIndicator
                      conversationId={conversationId || "new"}
                      isVisible={isLoading}
                      onComplete={() => {
                        console.log('[Chat] Progress completed');
                      }}
                      onError={(error) => {
                        console.error('[Chat] Progress error:', error);
                      }}
                    />
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-gray-100 p-4">
                <form onSubmit={handleSubmit} className="flex items-end space-x-4">
                  <div className="flex-1">
                    <textarea
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={t('chat.placeholder')}
                      className="w-full px-4 py-3 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
                      rows={1}
                      style={{minHeight: '48px', maxHeight: '120px'}}
                      disabled={isLoading}
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={!inputValue.trim() || isLoading}
                    className="w-12 h-12 rounded-2xl"
                  >
                    {isLoading ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/>
                      </svg>
                    )}
                  </Button>
                </form>
                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center space-x-4">
                    <button className="flex items-center space-x-2 text-sm text-gray-500 hover:text-blue-600 transition-colors">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                      </svg>
                      <span>{t('chat.fileAttach')}</span>
                    </button>

                  </div>
                  <p className="text-xs text-gray-400">
                    {t('chat.inputHelp')}
                  </p>
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="w-80 border-l border-gray-100 bg-gray-50/50 rounded-tr-lg">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  {t('chat.quickQuestions')}
                </h3>
                <div className="space-y-3">
                  {quickQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickQuestion(question)}
                      className="w-full text-left p-3 bg-white rounded-xl hover:bg-blue-50 border border-gray-100 hover:border-blue-200 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M15.07,11.25L14.17,12.17C13.45,12.89 13,13.5 13,15H11V14.5C11,13.39 11.45,12.39 12.17,11.67L13.41,10.41C13.78,10.05 14,9.55 14,9C14,7.89 13.1,7 12,7A2,2 0 0,0 10,9H8A4,4 0 0,1 12,5A4,4 0 0,1 16,9C16,10.25 15.56,11.42 14.83,12.35L15.07,11.25M13,19H11V17H13V19Z"/>
                        </svg>
                        <span className="text-sm text-gray-700">{question}</span>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="mt-8">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    {t('chat.recentChats')}
                  </h3>
                  <div className="space-y-2">
                    {recentChats.map((chat, index) => (
                      <button
                        key={index}
                        className="w-full text-left p-3 rounded-lg hover:bg-white transition-colors"
                      >
                        <div className="text-sm font-medium text-gray-700 mb-1">{chat.title}</div>
                        <div className="text-xs text-gray-500">{chat.time}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-8 p-4 bg-blue-50 rounded-xl border border-blue-100">
                  <div className="flex items-center space-x-2 mb-2">
                    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12,18.5L10.25,16.75L14.75,12.25L10.25,7.75L12,6L18,12L12,18.5M6,6H8V18H6V6Z"/>
                    </svg>
                    <span className="text-sm font-medium text-blue-800">
                      {t('chat.help')}
                    </span>
                  </div>
                  <p className="text-xs text-blue-700">
                    {t('chat.helpDesc')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}