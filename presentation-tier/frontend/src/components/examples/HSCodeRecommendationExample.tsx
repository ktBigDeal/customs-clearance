/**
 * HS코드 추천 컴포넌트 사용 예시
 * 
 * 사용자 활동 로깅이 적용된 HS코드 추천 기능의 예시입니다.
 * 실제 컴포넌트에서 이와 같은 방식으로 로깅을 적용할 수 있습니다.
 * 
 * @author Frontend Team
 * @version 1.0
 * @since 2025-08-18
 */

'use client';

import { useState } from 'react';
import { logService } from '@/services/log.service';

interface HSCodeResult {
  code: string;
  description: string;
  rate: number;
}

export function HSCodeRecommendationExample() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<HSCodeResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    const startTime = Date.now();
    setIsLoading(true);

    try {
      // 실제 HS코드 추천 API 호출 (예시)
      const response = await fetch(`http://localhost:8000/api/v1/hscode/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      setResults(data.results || []);

      // 사용자 활동 로그 기록
      await logService.logHSCodeRecommendation(
        query,
        data.results?.length || 0,
        1, // 실제로는 현재 로그인한 사용자 ID
        'test_user' // 실제로는 현재 로그인한 사용자명
      );

      console.log('HS코드 추천 로그 기록 완료');

    } catch (error) {
      console.error('HS코드 추천 실패:', error);
      
      // 실패한 경우에도 로그 기록
      await logService.logUserActivity({
        action: `HS코드 추천 실패 (검색어: "${query}")`,
        source: 'HSCODE',
        userId: 1,
        userName: 'test_user',
        details: `에러: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      });

    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">HS코드 추천</h2>
      
      <div className="space-y-4">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            상품명을 입력하세요
          </label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 딸기, 노트북, 화장품"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>

        <button
          onClick={handleSearch}
          disabled={isLoading || !query.trim()}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? '추천 중...' : 'HS코드 추천 받기'}
        </button>

        {results.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-3">추천 결과</h3>
            <div className="space-y-2">
              {results.map((result, index) => (
                <div
                  key={index}
                  className="p-3 border border-gray-200 rounded-md hover:bg-gray-50"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-mono text-sm text-blue-600">{result.code}</div>
                      <div className="text-gray-800">{result.description}</div>
                    </div>
                    <div className="text-sm text-gray-500">
                      관세율: {result.rate}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 챗봇 대화 컴포넌트 사용 예시
 */
export function ChatbotExample() {
  const [messages, setMessages] = useState<Array<{type: 'user' | 'bot', content: string}>>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);

    const startTime = Date.now();

    try {
      // 실제 챗봇 API 호출 (예시)
      const response = await fetch(`http://localhost:8000/api/v1/chatbot/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage, userId: 1 }),
      });

      const data = await response.json();
      const botResponse = data.response || '죄송합니다. 응답을 생성할 수 없습니다.';
      
      setMessages(prev => [...prev, { type: 'bot', content: botResponse }]);

      // 챗봇 대화 로그 기록
      const processingTime = Date.now() - startTime;
      await logService.logChatbotConversation(
        userMessage,
        botResponse.length,
        processingTime,
        1, // 실제로는 현재 로그인한 사용자 ID
        'test_user' // 실제로는 현재 로그인한 사용자명
      );

      console.log('챗봇 대화 로그 기록 완료');

    } catch (error) {
      console.error('챗봇 응답 실패:', error);
      
      setMessages(prev => [...prev, { 
        type: 'bot', 
        content: '죄송합니다. 일시적인 오류가 발생했습니다.' 
      }]);

      // 실패한 경우에도 로그 기록
      await logService.logUserActivity({
        action: `AI 챗봇 대화 실패`,
        source: 'CHATBOT',
        userId: 1,
        userName: 'test_user',
        details: `질문: ${userMessage}, 에러: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      });

    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">AI 관세 상담 챗봇</h2>
      
      <div className="border border-gray-300 rounded-lg h-96 overflow-y-auto p-4 mb-4 bg-gray-50">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`mb-3 ${message.type === 'user' ? 'text-right' : 'text-left'}`}
          >
            <div
              className={`inline-block max-w-xs lg:max-w-md px-3 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-800 border'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="text-left">
            <div className="inline-block max-w-xs px-3 py-2 bg-gray-200 text-gray-600 rounded-lg">
              AI가 응답을 생성하고 있습니다...
            </div>
          </div>
        )}
      </div>

      <div className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="관세에 대해 궁금한 것을 물어보세요..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          disabled={isLoading}
        />
        <button
          onClick={handleSendMessage}
          disabled={isLoading || !input.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          전송
        </button>
      </div>
    </div>
  );
}

/**
 * 실제 사용 방법 요약:
 * 
 * 1. HS코드 추천/검색 시:
 *    await logService.logHSCodeRecommendation(query, results.length, userId, userName);
 * 
 * 2. AI 챗봇 대화 시:
 *    await logService.logChatbotConversation(question, response.length, processingTime, userId, userName);
 * 
 * 3. OCR 문서 처리 시:
 *    await logService.logOCRProcessing(fileName, fileSize, processingTime, userId, userName);
 * 
 * 4. 보고서 생성/다운로드 시:
 *    await logService.logReportGeneration(reportType, processingTime, userId, userName);
 *    await logService.logReportDownload(reportType, format, userId, userName);
 * 
 * 5. 파일 업로드 시:
 *    await logService.logFileUpload(fileName, fileSize, fileType, userId, userName);
 * 
 * 6. 성능 측정과 함께:
 *    const startTime = Date.now();
 *    // ... 작업 수행 ...
 *    await logService.logActivityWithTiming('작업 설명', 'HSCODE', startTime, userId, userName);
 */