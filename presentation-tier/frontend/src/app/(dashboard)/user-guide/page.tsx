'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  BookOpen, 
  PlayCircle, 
  Download, 
  FileText,
  Users,
  Settings,
  MessageCircle,
  Hash,
  ClipboardList,
  ChevronRight,
  Clock,
  Video
} from 'lucide-react';

export default function UserGuidePage() {
  const { t } = useLanguage();

  const guideCategories = [
    {
      icon: ClipboardList,
      title: '보고서 생성 가이드',
      description: '수출입 신고서 작성부터 제출까지',
      lessons: 5,
      duration: '25분',
      level: 'beginner',
      items: [
        '보고서 생성 시작하기',
        '필수 서류 업로드',
        'AI 자동 분석 활용',
        '신고서 검토 및 수정',
        '최종 제출하기'
      ]
    },
    {
      icon: Hash,
      title: 'HS코드 추천 시스템',
      description: 'AI 기반 품목분류 및 HS코드 검색',
      lessons: 4,
      duration: '20분',
      level: 'beginner',
      items: [
        'HS코드 기본 이해',
        'AI 추천 시스템 사용법',
        '품목 검색 및 분류',
        '정확한 코드 선택 방법'
      ]
    },
    {
      icon: MessageCircle,
      title: 'AI 상담 활용법',
      description: '통관 전문 AI와 효과적인 소통',
      lessons: 3,
      duration: '15분',
      level: 'beginner',
      items: [
        'AI 상담 시작하기',
        '효과적인 질문 방법',
        '답변 활용 및 저장'
      ]
    },
    {
      icon: Settings,
      title: '시스템 설정 및 관리',
      description: '계정 관리 및 개인화 설정',
      lessons: 6,
      duration: '30분',
      level: 'intermediate',
      items: [
        '계정 설정 관리',
        '언어 및 표시 설정',
        '알림 설정',
        '보안 설정',
        '데이터 내보내기',
        '시스템 환경설정'
      ]
    }
  ];

  const quickStartGuides = [
    {
      title: '첫 신고서 작성하기',
      description: '처음 사용자를 위한 단계별 가이드',
      duration: '10분',
      type: 'video'
    },
    {
      title: '파일 업로드 방법',
      description: '지원 파일 형식 및 업로드 방법',
      duration: '5분',
      type: 'article'
    },
    {
      title: '자주 발생하는 오류 해결',
      description: '일반적인 문제와 해결 방법',
      duration: '8분',
      type: 'article'
    },
    {
      title: 'AI 기능 활용 팁',
      description: 'AI 상담과 추천 시스템 활용법',
      duration: '12분',
      type: 'video'
    }
  ];

  const downloadResources = [
    {
      title: '사용자 매뉴얼 (PDF)',
      description: '전체 시스템 사용법 매뉴얼',
      size: '2.5MB',
      version: 'v1.0'
    },
    {
      title: 'HS코드 분류표',
      description: '최신 관세율표 및 HS코드 목록',
      size: '1.8MB',
      version: '2024년'
    },
    {
      title: '서류 양식 모음',
      description: '수출입 관련 필수 서류 양식',
      size: '850KB',
      version: 'v2.1'
    },
    {
      title: '단축키 가이드',
      description: '업무 효율성을 위한 단축키 모음',
      size: '124KB',
      version: 'v1.0'
    }
  ];

  const getLevelBadge = (level: string) => {
    const colors = {
      beginner: 'bg-green-100 text-green-800',
      intermediate: 'bg-yellow-100 text-yellow-800',
      advanced: 'bg-red-100 text-red-800'
    };
    const labels = {
      beginner: '초급',
      intermediate: '중급',
      advanced: '고급'
    };
    return (
      <Badge className={colors[level as keyof typeof colors]}>
        {labels[level as keyof typeof labels]}
      </Badge>
    );
  };

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{t('userGuide.title')}</h1>
        <p className="text-muted-foreground">
          {t('userGuide.subtitle')}
        </p>
      </div>

      {/* 빠른 시작 가이드 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlayCircle className="h-5 w-5" />
            빠른 시작 가이드
          </CardTitle>
          <CardDescription>
            처음 사용자를 위한 필수 가이드들
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {quickStartGuides.map((guide, index) => (
              <div key={index} className="p-4 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {guide.type === 'video' ? 
                      <Video className="h-4 w-4 text-customs-600" /> : 
                      <FileText className="h-4 w-4 text-customs-600" />
                    }
                    <h3 className="font-semibold">{guide.title}</h3>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground mb-2">{guide.description}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {guide.duration}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 상세 가이드 카테고리 */}
      <div className="grid gap-6 md:grid-cols-2">
        {guideCategories.map((category, index) => {
          const Icon = category.icon;
          return (
            <Card key={index} className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-customs-100 rounded-lg">
                      <Icon className="h-5 w-5 text-customs-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{category.title}</CardTitle>
                      <CardDescription>{category.description}</CardDescription>
                    </div>
                  </div>
                  {getLevelBadge(category.level)}
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{category.lessons}개 레슨</span>
                  <span>•</span>
                  <span>{category.duration}</span>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 mb-4">
                  {category.items.map((item, itemIndex) => (
                    <li key={itemIndex} className="flex items-center gap-2 text-sm">
                      <div className="h-1.5 w-1.5 bg-customs-600 rounded-full"></div>
                      {item}
                    </li>
                  ))}
                </ul>
                <Button className="w-full">
                  <BookOpen className="h-4 w-4 mr-2" />
                  학습 시작하기
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 다운로드 자료 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            다운로드 자료
          </CardTitle>
          <CardDescription>
            오프라인에서도 활용할 수 있는 가이드 자료
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {downloadResources.map((resource, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-semibold">{resource.title}</h3>
                    <p className="text-sm text-muted-foreground">{resource.description}</p>
                  </div>
                  <Badge variant="outline">{resource.version}</Badge>
                </div>
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-muted-foreground">{resource.size}</span>
                  <Button size="sm" variant="outline">
                    <Download className="h-3 w-3 mr-1" />
                    다운로드
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 추가 도움말 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              커뮤니티 지원
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              다른 사용자들과 경험을 공유하고 도움을 받으세요
            </p>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <MessageCircle className="h-4 w-4 mr-2" />
                사용자 포럼 방문
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Users className="h-4 w-4 mr-2" />
                사용자 그룹 참여
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              직접 문의
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              가이드로 해결되지 않는 문제가 있으신가요?
            </p>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <MessageCircle className="h-4 w-4 mr-2" />
                고객센터 문의
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <FileText className="h-4 w-4 mr-2" />
                1:1 문의하기
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}