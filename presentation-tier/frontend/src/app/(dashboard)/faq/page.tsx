'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  Search, 
  ChevronDown, 
  ChevronUp, 
  HelpCircle, 
  ClipboardList,
  Hash,
  Settings,
  MessageCircle,
  FileText,
  AlertCircle,
  CheckCircle,
  Star
} from 'lucide-react';

export default function FAQPage() {
  const { t } = useLanguage();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedFAQ, setExpandedFAQ] = useState<number | null>(null);

  const categories = [
    { id: 'all', name: '전체', icon: HelpCircle, count: 45 },
    { id: 'declaration', name: '신고서 작성', icon: ClipboardList, count: 15 },
    { id: 'hscode', name: 'HS코드', icon: Hash, count: 12 },
    { id: 'system', name: '시스템 이용', icon: Settings, count: 10 },
    { id: 'ai', name: 'AI 기능', icon: MessageCircle, count: 8 }
  ];

  const faqData = [
    {
      id: 1,
      category: 'declaration',
      question: '수입신고서 작성 시 필수 입력 항목은 무엇인가요?',
      answer: `수입신고서 작성 시 다음 항목들은 반드시 입력해야 합니다:
      
• 신고인 정보 (사업자등록번호, 상호, 주소)
• 품목 정보 (품명, HS코드, 원산지)
• 거래 정보 (거래조건, 결제방법, 환율)
• 운송 정보 (운송수단, 적재항, 양륙항)

누락된 항목이 있으면 시스템에서 자동으로 알려드립니다.`,
      tags: ['필수항목', '신고서', '입력'],
      helpful: 127,
      views: 1250
    },
    {
      id: 2,
      category: 'hscode',
      question: 'HS코드를 잘못 선택했을 때 수정할 수 있나요?',
      answer: `네, HS코드는 다음과 같은 경우에 수정 가능합니다:

• 신고서 제출 전: 언제든지 자유롭게 수정 가능
• 제출 후 심사 중: 담당자 승인 하에 수정 가능
• 수리 완료 후: 별도의 정정신고 절차 필요

AI 추천 시스템을 활용하면 정확한 HS코드를 더 쉽게 찾을 수 있습니다.`,
      tags: ['HS코드', '수정', '정정신고'],
      helpful: 95,
      views: 856
    },
    {
      id: 3,
      category: 'system',
      question: '파일 업로드가 안 될 때 어떻게 해야 하나요?',
      answer: `파일 업로드 문제 해결 방법:

1. 파일 형식 확인: PDF, JPG, PNG, XLSX만 지원
2. 파일 크기 확인: 최대 10MB까지 업로드 가능
3. 브라우저 캐시 삭제 후 재시도
4. 다른 브라우저에서 시도해보기
5. 인터넷 연결 상태 확인

문제가 지속되면 고객센터(1544-8888)로 문의해주세요.`,
      tags: ['파일업로드', '오류', '해결방법'],
      helpful: 203,
      views: 1890
    },
    {
      id: 4,
      category: 'ai',
      question: 'AI 상담 서비스는 어떻게 이용하나요?',
      answer: `AI 상담 서비스 이용 방법:

1. 좌측 메뉴에서 'AI 상담' 클릭
2. 채팅창에 궁금한 내용 입력
3. AI가 관련 법규와 사례를 바탕으로 답변 제공
4. 필요시 참고 문서 링크도 함께 제공

24시간 언제든지 이용 가능하며, 복잡한 문의는 전문 상담사에게 연결됩니다.`,
      tags: ['AI상담', '이용방법', '24시간'],
      helpful: 158,
      views: 1456
    },
    {
      id: 5,
      category: 'declaration',
      question: '신고서 임시저장 기능이 있나요?',
      answer: `네, 임시저장 기능을 제공합니다:

• 자동 저장: 5분마다 작성 중인 내용 자동 저장
• 수동 저장: '임시저장' 버튼으로 언제든지 저장
• 저장 기간: 최대 30일간 보관
• 복원 기능: 다음 접속 시 자동으로 복원 여부 안내

임시저장된 신고서는 '나의 신고서' 메뉴에서 확인할 수 있습니다.`,
      tags: ['임시저장', '자동저장', '복원'],
      helpful: 89,
      views: 724
    },
    {
      id: 6,
      category: 'hscode',
      question: 'AI HS코드 추천의 정확도는 어느 정도인가요?',
      answer: `AI HS코드 추천 시스템의 성능:

• 정확도: 약 94.2% (2024년 기준)
• 학습 데이터: 최근 5년간 실제 신고 데이터 100만 건
• 업데이트: 매월 최신 관세율표 반영
• 검증: 관세청 전문가가 지속적으로 모니터링

다만 최종 확인은 사용자가 직접 해주시기 바랍니다.`,
      tags: ['AI추천', '정확도', 'HS코드'],
      helpful: 142,
      views: 1123
    },
    {
      id: 7,
      category: 'system',
      question: '로그인이 안 될 때 해결 방법은?',
      answer: `로그인 문제 해결 순서:

1. 아이디/비밀번호 정확성 확인
2. Caps Lock 상태 확인
3. 브라우저 쿠키 및 캐시 삭제
4. 비밀번호 재설정 시도
5. 다른 브라우저나 기기에서 시도

5회 연속 실패 시 계정이 잠기므로, 고객센터로 문의해주세요.`,
      tags: ['로그인', '비밀번호', '계정잠금'],
      helpful: 76,
      views: 892
    },
    {
      id: 8,
      category: 'ai',
      question: 'AI가 제공하는 정보를 얼마나 신뢰할 수 있나요?',
      answer: `AI 정보의 신뢰도:

• 법령 정보: 최신 관세법 및 고시 기준 99% 정확
• 실무 정보: 실제 업무 사례 기반 95% 이상 정확
• 업데이트: 법령 변경 시 24시간 내 반영
• 검증: 관세청 전문가 팀이 지속 검토

중요한 결정 사항은 담당자와 추가 확인하시기 바랍니다.`,
      tags: ['AI신뢰도', '정확도', '법령정보'],
      helpful: 113,
      views: 967
    }
  ];

  const filteredFAQs = faqData.filter(faq => {
    const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory;
    const matchesSearch = faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         faq.answer.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         faq.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const toggleFAQ = (id: number) => {
    setExpandedFAQ(expandedFAQ === id ? null : id);
  };

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">자주 묻는 질문</h1>
        <p className="text-muted-foreground">
          가장 자주 문의되는 질문들과 답변을 확인해보세요
        </p>
      </div>

      {/* 검색 */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="궁금한 내용을 검색해보세요..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* 카테고리 필터 */}
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => {
          const Icon = category.icon;
          return (
            <Button
              key={category.id}
              variant={selectedCategory === category.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category.id)}
              className="flex items-center gap-2"
            >
              <Icon className="h-4 w-4" />
              {category.name}
              <Badge variant="secondary" className="ml-1">
                {category.count}
              </Badge>
            </Button>
          );
        })}
      </div>

      {/* FAQ 목록 */}
      <div className="space-y-4">
        {filteredFAQs.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <HelpCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">검색 결과가 없습니다.</p>
              <p className="text-sm text-muted-foreground mt-2">
                다른 검색어로 시도하거나 고객센터에 문의해보세요.
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredFAQs.map((faq) => (
            <Card key={faq.id} className="transition-all duration-200 hover:shadow-md">
              <CardHeader 
                className="cursor-pointer"
                onClick={() => toggleFAQ(faq.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg font-medium text-left">
                      {faq.question}
                    </CardTitle>
                    <div className="flex items-center gap-2 mt-2">
                      {faq.tags.map((tag, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        {faq.helpful}
                      </div>
                    </div>
                    {expandedFAQ === faq.id ? (
                      <ChevronUp className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                </div>
              </CardHeader>
              {expandedFAQ === faq.id && (
                <CardContent>
                  <div className="border-t pt-4">
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                      <div className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-gray-800">
                        {faq.answer}
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-6 pt-4 border-t">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>조회수 {faq.views.toLocaleString()}</span>
                        <span>도움됨 {faq.helpful}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          도움됨
                        </Button>
                        <Button size="sm" variant="outline">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          신고
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          ))
        )}
      </div>

      {/* 추가 도움말 */}
      <Card>
        <CardHeader>
          <CardTitle>원하는 답변을 찾지 못하셨나요?</CardTitle>
          <CardDescription>
            다른 방법으로 도움을 받아보세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <Button variant="outline" className="h-auto p-4 flex-col">
              <MessageCircle className="h-6 w-6 mb-2" />
              <span className="font-medium">AI 상담</span>
              <span className="text-xs text-muted-foreground">24시간 이용 가능</span>
            </Button>
            <Button variant="outline" className="h-auto p-4 flex-col">
              <FileText className="h-6 w-6 mb-2" />
              <span className="font-medium">1:1 문의</span>
              <span className="text-xs text-muted-foreground">맞춤형 답변</span>
            </Button>
            <Button variant="outline" className="h-auto p-4 flex-col">
              <HelpCircle className="h-6 w-6 mb-2" />
              <span className="font-medium">고객센터</span>
              <span className="text-xs text-muted-foreground">1544-8888</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}