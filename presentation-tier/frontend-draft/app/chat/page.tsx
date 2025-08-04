'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
  isTyping?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '안녕하세요! 통관 AI 상담사입니다. 수출입 관련 궁금한 사항이나 통관 절차에 대해 무엇이든 물어보세요.',
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 샘플 응답 데이터
  const sampleResponses = [
    {
      content: 'HS코드는 전 세계적으로 통용되는 상품분류체계로, 수출입 신고 시 반드시 필요합니다. 정확한 HS코드 분류를 위해서는 상품의 재질, 용도, 가공정도 등을 고려해야 합니다.\n\n일반적인 HS코드 확인 방법:\n1. 관세청 수출입 통합정보망(UNI-PASS) 활용\n2. 관세율표 검색 서비스 이용\n3. 전문 무역업체 또는 관세사 상담\n\n정확한 HS코드 분류는 관세 부과와 직결되므로 신중하게 결정하시기 바랍니다.',
      sources: ['수출입통합정보망 가이드.pdf', 'HS코드 분류 매뉴얼.pdf', '관세법 시행령.pdf']
    },
    {
      content: '수입신고서 작성 시 필수 구비서류는 다음과 같습니다:\n\n1. 상업송장(Commercial Invoice)\n2. 포장명세서(Packing List)\n3. 선하증권 또는 항공화물운송장(B/L, AWB)\n4. 원산지증명서(필요시)\n5. 기타 법정서류(품목에 따라 상이)\n\n서류 준비 시 주의사항:\n- 모든 서류는 원본 또는 공증된 사본이어야 함\n- 서류 간 내용 불일치가 없도록 확인\n- 필수 기재사항 누락 방지',
      sources: ['수입신고 가이드북.pdf', '통관서류 체크리스트.xlsx', '관세법 실무매뉴얼.pdf']
    },
    {
      content: '원산지증명서는 상품의 생산국가를 증명하는 공식 문서입니다. FTA 특혜관세 적용을 위해서는 반드시 필요합니다.\n\n원산지증명서 종류:\n1. 일반원산지증명서\n2. FTA원산지증명서\n3. 자율증명(승인수출업체)\n\n발급 절차:\n1. 해당국 상공회의소 또는 공인기관 신청\n2. 생산 관련 서류 제출\n3. 검토 및 발급\n\n주의: 허위 원산지증명서 사용 시 법적 처벌을 받을 수 있습니다.',
      sources: ['FTA 활용 가이드.pdf', '원산지 규정 해설서.pdf', '자유무역협정 실무.pdf']
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // 타이핑 인디케이터 표시
    const typingMessage: Message = {
      id: 'typing',
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isTyping: true,
    };
    setMessages(prev => [...prev, typingMessage]);

    // 샘플 응답 시뮬레이션
    setTimeout(() => {
      const randomResponse = sampleResponses[Math.floor(Math.random() * sampleResponses.length)];
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: randomResponse.content,
        timestamp: new Date(),
        sources: randomResponse.sources,
      };

      setMessages(prev => prev.filter(msg => msg.id !== 'typing').concat(assistantMessage));
      setIsLoading(false);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <Link href="/" className="text-2xl font-bold text-blue-600" style={{fontFamily: 'var(--font-pacifico)'}}>
                TradeFlow
              </Link>
              <nav className="flex space-x-6">
                <Link href="/" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">대시보드</Link>
                <Link href="#" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">문서 관리</Link>
                <Link href="#" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">신고 내역</Link>
                <Link href="#" className="text-blue-600 font-medium cursor-pointer border-b-2 border-blue-600 pb-1">AI 상담</Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">일반사용자 | 홍길동님</span>
              <button className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 cursor-pointer">
                <i className="ri-notification-line w-5 h-5"></i>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden" style={{height: 'calc(100vh - 200px)'}}>
          <div className="flex h-full">
            {/* Chat Messages Area */}
            <div className="flex-1 flex flex-col">
              {/* Chat Header */}
              <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-500 to-indigo-600">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 flex items-center justify-center bg-white/20 rounded-full">
                    <i className="ri-robot-2-line w-6 h-6 text-white"></i>
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">통관 AI 상담사</h2>
                    <p className="text-sm text-blue-100">수출입 전문 상담 서비스</p>
                  </div>
                  <div className="ml-auto flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span className="text-sm text-blue-100">온라인</span>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-2xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                      {message.type === 'assistant' && (
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="w-8 h-8 flex items-center justify-center bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full">
                            <i className="ri-robot-2-line w-4 h-4 text-white"></i>
                          </div>
                          <span className="text-sm font-medium text-gray-700">통관 AI 상담사</span>
                          <span className="text-xs text-gray-500">
                            {message.timestamp.toLocaleTimeString('ko-KR', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </span>
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
                            <span className="text-sm text-gray-500">답변을 생성중입니다...</span>
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap">{message.content}</div>
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
                          <span className="text-sm font-medium text-gray-700">홍길동</span>
                          <div className="w-8 h-8 flex items-center justify-center bg-blue-600 rounded-full">
                            <i className="ri-user-line w-4 h-4 text-white"></i>
                          </div>
                        </div>
                      )}

                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
                          <div className="flex items-center space-x-2 mb-3">
                            <i className="ri-file-text-line w-4 h-4 text-blue-600"></i>
                            <span className="text-sm font-medium text-blue-800">참고 문서</span>
                          </div>
                          <div className="space-y-2">
                            {message.sources.map((source, index) => (
                              <button
                                key={index}
                                className="flex items-center space-x-2 w-full text-left p-2 hover:bg-blue-100 rounded-lg transition-colors cursor-pointer"
                              >
                                <i className="ri-file-pdf-line w-4 h-4 text-red-500"></i>
                                <span className="text-sm text-blue-700 hover:text-blue-800">{source}</span>
                                <i className="ri-external-link-line w-3 h-3 text-blue-500 ml-auto"></i>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
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
                      placeholder="통관 관련 궁금한 사항을 입력하세요..."
                      className="w-full px-4 py-3 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
                      rows={1}
                      style={{minHeight: '48px', maxHeight: '120px'}}
                      disabled={isLoading}
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={!inputValue.trim() || isLoading}
                    className="w-12 h-12 flex items-center justify-center bg-blue-600 text-white rounded-2xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors cursor-pointer"
                  >
                    {isLoading ? (
                      <i className="ri-loader-4-line w-5 h-5 animate-spin"></i>
                    ) : (
                      <i className="ri-send-plane-line w-5 h-5"></i>
                    )}
                  </button>
                </form>
                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center space-x-4">
                    <button className="flex items-center space-x-2 text-sm text-gray-500 hover:text-blue-600 cursor-pointer">
                      <i className="ri-attachment-line w-4 h-4"></i>
                      <span>파일 첨부</span>
                    </button>
                    <button className="flex items-center space-x-2 text-sm text-gray-500 hover:text-blue-600 cursor-pointer">
                      <i className="ri-mic-line w-4 h-4"></i>
                      <span>음성 입력</span>
                    </button>
                  </div>
                  <p className="text-xs text-gray-400">
                    Enter로 전송, Shift+Enter로 줄바꿈
                  </p>
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="w-80 border-l border-gray-100 bg-gray-50/50">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">빠른 질문</h3>
                <div className="space-y-3">
                  {[
                    'HS코드 분류 방법이 궁금해요',
                    '수입신고서 작성 시 필요한 서류는?',
                    '원산지증명서는 언제 필요한가요?',
                    'FTA 특혜관세 적용 조건은?',
                    '통관 소요시간은 얼마나 걸리나요?',
                    '관세 계산 방법을 알고 싶어요'
                  ].map((question, index) => (
                    <button
                      key={index}
                      onClick={() => setInputValue(question)}
                      className="w-full text-left p-3 bg-white rounded-xl hover:bg-blue-50 border border-gray-100 hover:border-blue-200 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center space-x-3">
                        <i className="ri-question-line w-4 h-4 text-blue-500"></i>
                        <span className="text-sm text-gray-700">{question}</span>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="mt-8">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">최근 대화</h3>
                  <div className="space-y-2">
                    {[
                      { title: 'HS코드 관련 질문', time: '2시간 전' },
                      { title: '수출신고서 작성법', time: '어제' },
                      { title: '원산지증명서 발급', time: '2일 전' },
                      { title: 'FTA 활용 방법', time: '1주 전' }
                    ].map((chat, index) => (
                      <button
                        key={index}
                        className="w-full text-left p-3 rounded-lg hover:bg-white transition-colors cursor-pointer"
                      >
                        <div className="text-sm font-medium text-gray-700 mb-1">{chat.title}</div>
                        <div className="text-xs text-gray-500">{chat.time}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-8 p-4 bg-blue-50 rounded-xl border border-blue-100">
                  <div className="flex items-center space-x-2 mb-2">
                    <i className="ri-lightbulb-line w-4 h-4 text-blue-600"></i>
                    <span className="text-sm font-medium text-blue-800">도움말</span>
                  </div>
                  <p className="text-xs text-blue-700">
                    더 정확한 답변을 위해 구체적인 상황과 함께 질문해 주세요.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}