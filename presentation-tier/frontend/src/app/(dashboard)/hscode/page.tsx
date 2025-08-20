'use client';

import { useState, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { logService } from '@/services/log.service';
import { recommendHSCode } from '@/lib/api';

interface HSCodeRecommendation {
  hs_code: string;
  name_kr: string;
  name_en?: string;
  description?: string;
  confidence: number;
  keyword_score?: number;
  semantic_score?: number;
  hybrid_score?: number;
  chapter: string;
  heading: string;
  subheading: string;
  data_source: string;
  is_standard_match: boolean;
  llm_analysis?: {
    reasoning: string;
    confidence: number;
    llm_rerank?: {
      score: number;
      reason: string;
    };
    llm_direct?: {
      confidence: number;
      reason: string;
    };
    search_only?: {
      confidence: number;
      reason: string;
    };
    enhanced_search?: {
      analysis_type: string;
      confidence: number;
      reason: string;
      data_quality: string;
    };
  };
}

interface SearchInfo {
  query: string;
  expanded_query?: string;
  search_time_ms?: number;
  total_candidates?: number;
  method?: string;
  llm_used?: boolean;
}

interface RecommendResponse {
  success: boolean;
  message: string;
  recommendations: HSCodeRecommendation[];
  search_info: SearchInfo;
}

class HSCodeAPI {
  private baseURL = 'https://hscode-recommend-service-805290929724.asia-northeast3.run.app/';
  
  async recommendHSCode(request: {
    query: string;
    material?: string;
    usage?: string;
    mode?: string;
    top_k?: number;
    use_llm?: boolean;
    include_details?: boolean;
  }): Promise<RecommendResponse> {
    const response = await fetch(`${this.baseURL}/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }
}

export default function HSCodePage() {
  const [query, setQuery] = useState('');
  const [material, setMaterial] = useState('');
  const [usage, setUsage] = useState('');
  const [results, setResults] = useState<HSCodeRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchInfo, setSearchInfo] = useState<SearchInfo | null>(null);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  
  const hsCodeAPI = new HSCodeAPI();
  const resultsRef = useRef<HTMLDivElement>(null);

  const toggleCardExpansion = (index: number) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedCards(newExpanded);
  };

  const handleRecommend = useCallback(async () => {
    if (!query.trim()) return;

    const startTime = Date.now();
    setLoading(true);
    try {
      const response = await hsCodeAPI.recommendHSCode({
        query: query.trim(),
        material: material.trim() || undefined,
        usage: usage.trim() || undefined,
        mode: 'llm',
        top_k: 5,
        use_llm: true,
        include_details: true
      });

      if (response.success) {
        console.log('API 응답 데이터:', response); // 디버깅용
        setResults(response.recommendations);
        setSearchInfo(response.search_info);
        
        // 검색 기록에 추가
        const newQuery = query.trim();
        setSearchHistory(prev => {
          const filtered = prev.filter(item => item !== newQuery);
          return [newQuery, ...filtered].slice(0, 5);
        });
        
        // 결과로 스크롤
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);

        // HS코드 추천 성공 로그 기록
        await logService.logHSCodeRecommendation(
          newQuery,
          response.recommendations.length,
          1, // TODO: 실제 사용자 ID로 변경
          'test_user' // TODO: 실제 사용자명으로 변경
        );
      }
    } catch (error) {
      console.error('HS 코드 추천 실패:', error);
      
      // 에러 타입에 따른 메시지 처리
      let errorMessage = 'HS 코드 추천 중 오류가 발생했습니다.';
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        errorMessage = 'API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.\n\n서버 실행: cd application-tier/models/model-hscode && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8003';
      } else if (error instanceof Error) {
        errorMessage = `오류: ${error.message}`;
      }
      
      alert(errorMessage);

      // HS코드 추천 실패 로그 기록
      await logService.logUserActivity({
        action: `HS코드 추천 실패 (검색어: "${query.trim()}")`,
        source: 'HSCODE',
        userId: 1, // TODO: 실제 사용자 ID로 변경
        userName: 'test_user', // TODO: 실제 사용자명으로 변경
        details: `에러: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
      });
    } finally {
      setLoading(false);
    }
  }, [query, material, usage]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      e.preventDefault();
      handleRecommend();
    }
  };

  const handleQuickSearch = (searchQuery: string) => {
    setQuery(searchQuery);
  };

  const handleHistoryClick = (historyQuery: string) => {
    setQuery(historyQuery);
  };

  const quickSearches = [
    '스테인레스 볼트',
    '엘이디 전구',
    '플라스틱 용기',
    '자동차 부품',
    '의료기기',
    '화장품'
  ];

  return (
    <ProtectedRoute requiredRole="USER">
      <div className="h-full">
        <Card className="h-full overflow-hidden">
          <div className="flex h-full">
            {/* Main Content */}
            <div className="flex-1 flex flex-col">
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-green-500 to-emerald-600 relative">

                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 flex items-center justify-center bg-white/20 rounded-full">
                    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M9 11H7v6h2v-6zm4 0h-2v6h2v-6zm4 0h-2v6h2v-6zM4 3v2h16V3H4zm0 16h16v2H4v-2zM2 7h20v8H2V7z"/>
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      HS코드 추천 서비스
                    </h2>
                    <p className="text-sm text-green-100">
                      AI 기반 정확한 HS코드 분류 및 추천
                    </p>
               <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-sm text-green-100">AI 분석 준비완료</span>
                  </div>
                  </div>
                </div>
              </div>

              {/* Search Form */}
              <div className="p-6 border-b border-gray-100">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="md:col-span-1">
                    <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-1">
                      상품명 *
                    </label>
                    <input
                      id="query"
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="예: 스테인레스 볼트"
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      maxLength={500}
                      disabled={loading}
                    />
                  </div>
                  
                  <div className="md:col-span-1">
                    <label htmlFor="material" className="block text-sm font-medium text-gray-700 mb-1">
                      재질 (선택)
                    </label>
                    <input
                      id="material"
                      type="text"
                      value={material}
                      onChange={(e) => setMaterial(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="예: 스테인레스강, 플라스틱"
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      maxLength={100}
                      disabled={loading}
                    />
                  </div>
                  
                  <div className="md:col-span-1">
                    <label htmlFor="usage" className="block text-sm font-medium text-gray-700 mb-1">
                      용도 (선택)
                    </label>
                    <input
                      id="usage"
                      type="text"
                      value={usage}
                      onChange={(e) => setUsage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="예: 산업용, 가정용"
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      maxLength={100}
                      disabled={loading}
                    />
                  </div>
                </div>
                
                <div className="flex justify-center">
                  <Button
                    onClick={handleRecommend}
                    disabled={loading || !query.trim()}
                    className="px-8 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:bg-gray-300"
                  >
                    {loading ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>AI 분석 중...</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                        </svg>
                        <span>HS코드 추천받기</span>
                      </div>
                    )}
                  </Button>
                </div>
              </div>

              {/* Search Info */}
              {searchInfo && !loading && (
                <div className="px-6 py-3 bg-green-50 border-b border-green-100">
                  <div className="flex items-center justify-between text-sm text-green-700">
                    <div className="flex items-center space-x-4">
                      <span>검색어: "{searchInfo.query}"</span>
                      <span>검색 시간: {searchInfo.search_time_ms?.toFixed(1)}ms</span>
                      <span>후보: {searchInfo.total_candidates}개</span>
                    </div>
                    {searchInfo.llm_used && (
                      <div className="flex items-center space-x-1">
                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        <span>AI 분석 완료</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Results */}
              <div className="flex-1 overflow-y-auto p-6" ref={resultsRef}>
                {results.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      추천 결과 ({results.length}개)
                    </h3>
                    
                    {results.map((rec, index) => {
                      const isExpanded = expandedCards.has(index);
                      const hasLongDescription = rec.description && rec.description.length > 150;
                      
                      return (
                        <Card key={index} className="p-4 hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h4 className="text-lg font-bold text-blue-600">{rec.hs_code}</h4>
                              <div className="flex items-center space-x-2 mt-1">
                                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                  신뢰도: {(rec.confidence * 100).toFixed(1)}%
                                </span>
                                {rec.is_standard_match && (
                                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                    표준품명 매칭
                                  </span>
                                )}
                              </div>
                            </div>
                            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                              <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/>
                              </svg>
                            </button>
                          </div>
                          
                          <div className="mb-3">
                            <h5 className="font-medium text-gray-900">{rec.name_kr}</h5>
                            {rec.name_en && (
                              <p className="text-sm text-gray-600 mt-1">{rec.name_en}</p>
                            )}
                          </div>
                          
                          {rec.description && (
                            <div className="mb-3">
                              <p className={`text-sm text-gray-700 ${!isExpanded && hasLongDescription ? 'overflow-hidden' : ''}`}
                                 style={!isExpanded && hasLongDescription ? {
                                   display: '-webkit-box',
                                   WebkitLineClamp: 2,
                                   WebkitBoxOrient: 'vertical',
                                   overflow: 'hidden'
                                 } : {}}>
                                {rec.description}
                              </p>
                              {hasLongDescription && (
                                <button
                                  onClick={() => toggleCardExpansion(index)}
                                  className="text-sm text-blue-600 hover:text-blue-800 mt-1 flex items-center space-x-1"
                                >
                                  <span>{isExpanded ? '접기' : '더 보기'}</span>
                                  <svg 
                                    className={`w-3 h-3 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                                    fill="currentColor" 
                                    viewBox="0 0 24 24"
                                  >
                                    <path d="M7 10l5 5 5-5z"/>
                                  </svg>
                                </button>
                              )}
                            </div>
                          )}
                          
                          <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                            <div>
                              <span className="text-gray-500">챕터:</span>
                              <span className="ml-1 font-medium">{rec.chapter}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">헤딩:</span>
                              <span className="ml-1 font-medium">{rec.heading}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">서브헤딩:</span>
                              <span className="ml-1 font-medium">{rec.subheading}</span>
                            </div>
                          </div>
                          
                          {/* AI 분석 근거 - 다양한 분석 유형 지원 */}
                          {rec.llm_analysis && (
                            <div className="mt-4 space-y-2">
                              {/* LLM 재순위 분석 */}
                              {rec.llm_analysis.llm_rerank && (
                                <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-2">
                                      <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                      </svg>
                                      <span className="text-sm font-medium text-blue-800">
                                        AI 재순위 분석
                                        {rec.llm_analysis.llm_rerank.reason?.includes('유사매칭') && (
                                          <span className="ml-2 px-2 py-1 text-xs bg-blue-200 text-blue-800 rounded">유사매칭</span>
                                        )}
                                        {rec.llm_analysis.llm_rerank.reason?.includes('광범위매칭') && (
                                          <span className="ml-2 px-2 py-1 text-xs bg-indigo-200 text-indigo-800 rounded">광범위매칭</span>
                                        )}
                                      </span>
                                    </div>
                                    <span className="text-xs text-blue-600">
                                      점수: {rec.llm_analysis.llm_rerank.score}/10
                                    </span>
                                  </div>
                                  <p className="text-sm text-blue-700">{rec.llm_analysis.llm_rerank.reason}</p>
                                </div>
                              )}
                              
                              {/* LLM 직접 제안 */}
                              {rec.llm_analysis.llm_direct && (
                                <div className="p-3 bg-green-50 rounded-lg border border-green-100">
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-2">
                                      <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                      </svg>
                                      <span className="text-sm font-medium text-green-800">AI 직접 제안</span>
                                    </div>
                                    <span className="text-xs text-green-600">
                                      확신도: {rec.llm_analysis.llm_direct.confidence}/10
                                    </span>
                                  </div>
                                  <p className="text-sm text-green-700">{rec.llm_analysis.llm_direct.reason}</p>
                                </div>
                              )}
                              
                              {/* 검색엔진 기반 폴백 (기존) */}
                              {rec.llm_analysis.search_only && (
                                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-2">
                                      <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                                      </svg>
                                      <span className="text-sm font-medium text-gray-800">검색엔진 기반</span>
                                    </div>
                                    <span className="text-xs text-gray-600">
                                      점수: {rec.llm_analysis.search_only.confidence}/10
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-700">{rec.llm_analysis.search_only.reason}</p>
                                </div>
                              )}

                              {/* 개선된 검색엔진 분석 (NEW!) */}
                              {rec.llm_analysis.enhanced_search && (
                                <div className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-2">
                                      <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                                      </svg>
                                      <span className="text-sm font-medium text-purple-800">
                                        {rec.llm_analysis.enhanced_search.analysis_type}
                                      </span>
                                      <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                                        품질: {rec.llm_analysis.enhanced_search.data_quality}
                                      </span>
                                    </div>
                                    <span className="text-xs text-purple-600">
                                      신뢰도: {rec.llm_analysis.enhanced_search.confidence}/10
                                    </span>
                                  </div>
                                  <p className="text-sm text-purple-700">{rec.llm_analysis.enhanced_search.reason}</p>
                                </div>
                              )}
                            </div>
                          )}
                          
                          
                          {(rec.keyword_score || rec.semantic_score || rec.hybrid_score) && (
                            <div className="mt-3 flex space-x-4 text-xs text-gray-500">
                              {rec.keyword_score && (
                                <span>키워드: {(rec.keyword_score * 100).toFixed(1)}%</span>
                              )}
                              {rec.semantic_score && (
                                <span>의미: {(rec.semantic_score * 100).toFixed(1)}%</span>
                              )}
                              {rec.hybrid_score && (
                                <span>통합: {(rec.hybrid_score * 100).toFixed(1)}%</span>
                              )}
                            </div>
                          )}
                        </Card>
                      );
                    })}
                  </div>
                )}
                
                {results.length === 0 && !loading && (
                  <div className="text-center py-12">
                    <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                    </svg>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">HS코드 추천을 시작해보세요</h3>
                    <p className="text-gray-500">상품명을 입력하면 AI가 최적의 HS코드를 추천해드립니다.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Sidebar */}
            <div className="w-80 border-l border-gray-100 bg-gray-50/50">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  빠른 검색
                </h3>
                <div className="space-y-2 mb-8">
                  {quickSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickSearch(search)}
                      className="w-full text-left p-3 bg-white rounded-lg hover:bg-green-50 border border-gray-100 hover:border-green-200 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                        </svg>
                        <span className="text-sm text-gray-700">{search}</span>
                      </div>
                    </button>
                  ))}
                </div>

                {searchHistory.length > 0 && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      최근 검색
                    </h3>
                    <div className="space-y-2">
                      {searchHistory.map((historyQuery, index) => (
                        <button
                          key={index}
                          onClick={() => handleHistoryClick(historyQuery)}
                          className="w-full text-left p-3 rounded-lg hover:bg-white transition-colors"
                        >
                          <div className="flex items-center space-x-3">
                            <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
                            </svg>
                            <span className="text-sm text-gray-600">{historyQuery}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className="p-4 bg-green-50 rounded-xl border border-green-100">
                  <div className="flex items-center space-x-2 mb-2">
                    <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12,2A7,7 0 0,1 19,9C19,11.38 17.81,13.47 16,14.74V17A1,1 0 0,1 15,18H9A1,1 0 0,1 8,17V14.74C6.19,13.47 5,11.38 5,9A7,7 0 0,1 12,2M9,21V20H15V21A1,1 0 0,1 14,22H10A1,1 0 0,1 9,21M12,4A5,5 0 0,0 7,9C7,10.68 7.84,12.17 9.17,13.05L10,13.63V16H14V13.63L14.83,13.05C16.16,12.17 17,10.68 17,9A5,5 0 0,0 12,4Z"/>
                    </svg>
                    <span className="text-sm font-medium text-green-800">
                      사용 팁
                    </span>
                  </div>
                  <ul className="text-xs text-green-700 space-y-1">
                    <li>• 구체적인 상품명일수록 정확한 추천</li>
                    <li>• 재질과 용도를 함께 입력하면 더 정확</li>
                    <li>• AI 분석 근거를 참고해보세요</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </ProtectedRoute>
  );
}