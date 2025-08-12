'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  Phone, 
  Mail, 
  MessageCircle, 
  Clock, 
  MapPin, 
  FileText,
  Headphones,
  ExternalLink
} from 'lucide-react';

export default function CustomerServicePage() {
  const { t } = useLanguage();

  const contactMethods = [
    {
      icon: Phone,
      title: t('customerService.phone'),
      value: '1544-8888',
      description: t('customerService.phoneDesc'),
      available: '평일 09:00 - 18:00',
      status: 'available'
    },
    {
      icon: Mail,
      title: t('customerService.email'),
      value: 'help@customs.go.kr',
      description: t('customerService.emailDesc'),
      available: '24시간 접수',
      status: 'available'
    },
    {
      icon: MessageCircle,
      title: t('customerService.liveChat'),
      value: t('customerService.startChat'),
      description: t('customerService.liveChatDesc'),
      available: '평일 09:00 - 17:00',
      status: 'available'
    }
  ];

  const faqCategories = [
    {
      title: '신고서 작성',
      count: 12,
      items: [
        '수입신고서 작성 방법',
        '수출신고서 필수 항목',
        '신고서 수정 및 취소'
      ]
    },
    {
      title: 'HS코드 분류',
      count: 8,
      items: [
        'HS코드 검색 방법',
        '품목분류 문의',
        'AI 추천 활용법'
      ]
    },
    {
      title: '시스템 이용',
      count: 15,
      items: [
        '로그인 문제 해결',
        '파일 업로드 오류',
        '브라우저 호환성'
      ]
    }
  ];

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{t('customerService.title')}</h1>
        <p className="text-muted-foreground">
          {t('customerService.subtitle')}
        </p>
      </div>

      {/* 연락처 정보 */}
      <div className="grid gap-6 md:grid-cols-3">
        {contactMethods.map((method, index) => {
          const Icon = method.icon;
          return (
            <Card key={index} className="relative">
              <CardHeader className="flex flex-row items-center space-y-0 pb-2">
                <div className="flex items-center space-x-2">
                  <div className="p-2 bg-customs-100 rounded-lg">
                    <Icon className="h-5 w-5 text-customs-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{method.title}</CardTitle>
                    <Badge variant="secondary" className="text-xs">
                      {method.available}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="font-semibold text-customs-700 mb-2">{method.value}</p>
                <p className="text-sm text-muted-foreground">{method.description}</p>
                <Button className="w-full mt-4" variant="outline">
                  <Icon className="h-4 w-4 mr-2" />
                  {method.title} 이용하기
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 1:1 문의하기 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {t('customerService.inquiry')}
          </CardTitle>
          <CardDescription>
            {t('customerService.inquiryDesc')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium mb-2 block">이름</label>
                <Input placeholder="홍길동" />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">이메일</label>
                <Input type="email" placeholder="example@email.com" />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">문의 유형</label>
              <select className="w-full p-2 border border-input rounded-md">
                <option>신고서 작성 문의</option>
                <option>HS코드 분류 문의</option>
                <option>시스템 오류 신고</option>
                <option>기타 문의</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">제목</label>
              <Input placeholder="문의 제목을 입력해주세요" />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">문의 내용</label>
              <Textarea 
                placeholder="상세한 문의 내용을 입력해주세요" 
                rows={5}
              />
            </div>
            <Button className="w-full">
              <Mail className="h-4 w-4 mr-2" />
              문의하기
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* 자주 묻는 질문 */}
      <Card>
        <CardHeader>
          <CardTitle>{t('customerService.faq')}</CardTitle>
          <CardDescription>
            {t('customerService.faqDesc')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {faqCategories.map((category, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold">{category.title}</h3>
                  <Badge variant="outline">{category.count}개</Badge>
                </div>
                <ul className="space-y-2">
                  {category.items.map((item, itemIndex) => (
                    <li key={itemIndex}>
                      <Button 
                        variant="ghost" 
                        className="w-full justify-start p-0 h-auto text-sm text-left"
                      >
                        {item}
                      </Button>
                    </li>
                  ))}
                </ul>
                <Button variant="outline" className="w-full mt-3" size="sm">
                  <ExternalLink className="h-3 w-3 mr-1" />
                  더보기
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 운영시간 및 공지사항 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              운영시간
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>전화 상담</span>
                <span className="font-medium">평일 09:00 - 18:00</span>
              </div>
              <div className="flex justify-between">
                <span>이메일 접수</span>
                <span className="font-medium">24시간</span>
              </div>
              <div className="flex justify-between">
                <span>라이브 채팅</span>
                <span className="font-medium">평일 09:00 - 17:00</span>
              </div>
              <div className="text-sm text-muted-foreground mt-4">
                * 주말 및 공휴일은 휴무입니다
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              찾아오시는 길
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="font-medium">관세청 고객지원센터</p>
              <p className="text-sm text-muted-foreground">
                서울특별시 중구 소공로 120<br />
                관세청 본청 2층
              </p>
              <div className="text-sm">
                <p><strong>지하철:</strong> 2호선 을지로입구역 7번 출구</p>
                <p><strong>버스:</strong> 100, 101, 103, 104번</p>
              </div>
              <Button variant="outline" size="sm" className="w-full">
                <MapPin className="h-3 w-3 mr-1" />
                지도에서 보기
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}