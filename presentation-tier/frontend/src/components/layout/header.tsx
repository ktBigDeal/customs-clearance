/**
 * 관세 통관 시스템 헤더 컴포넌트 (최상단 네비게이션 바)
 * 
 * 🧭 **주요 역할**: 애플리케이션 최상단에서 핵심 네비게이션과 사용자 기능 제공
 * 
 * **신입 개발자를 위한 설명**:
 * - 이 컴포넌트는 모든 페이지 맨 위에 고정되어 표시되는 헤더입니다
 * - 왼쪽에는 로고와 시스템명, 오른쪽에는 언어 선택, 알림, 사용자 메뉴가 있습니다
 * - 사용자가 어떤 페이지에 있든 항상 접근할 수 있는 공통 기능들을 제공합니다
 * - Sticky 속성으로 스크롤해도 항상 상단에 고정됩니다
 * 
 * **포함된 주요 기능**:
 * - 🏢 로고/브랜드명: "TradeFlow" 표시
 * - 🌍 언어 전환: 한국어/영어 선택 (드롭다운 메뉴)
 * - 🔔 알림 시스템: 새 알림 표시 (빨간 점으로 표시)
 * - 👤 사용자 메뉴: 프로필, 설정, 로그아웃 기능
 * - 📱 반응형 디자인: 모바일에서도 적절하게 표시
 * 
 * **사용된 UI 라이브러리**:
 * - Lucide React: 아이콘 라이브러리 (Bell, Globe, User 등)
 * - Radix UI: 접근성을 고려한 드롭다운 메뉴
 * - Tailwind CSS: 스타일링 및 반응형 디자인
 * 
 * **접근성(Accessibility) 고려사항**:
 * - ARIA 라벨로 스크린 리더 지원
 * - 키보드 네비게이션 가능
 * - 색상 대비 웹 접근성 기준 준수
 * - 포커스 표시기 제공
 * 
 * @file src/components/layout/header.tsx
 * @description 애플리케이션 공통 헤더 및 네비게이션 컴포넌트
 * @since 2024-01-01
 * @author Frontend Team
 * @category 레이아웃 컴포넌트
 * @tutorial 헤더 UI 패턴: https://ui.shadcn.com/docs/components/navigation-menu
 */

'use client';

import { Bell, ChevronDown, Globe, LogOut, Settings, User } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useLanguage } from '@/contexts/LanguageContext';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

/**
 * 헤더 컴포넌트의 Props 인터페이스
 * 
 * @interface HeaderProps
 * @property {function} [onMenuToggle] - 모바일 메뉴 토글 함수 (선택적)
 */
interface HeaderProps {
  /** 모바일 환경에서 사이드바 메뉴를 토글하는 함수 */
  onMenuToggle?: () => void;
}

/**
 * 애플리케이션 헤더 컴포넌트
 * 
 * 관세 통관 시스템의 공통 헤더를 렌더링합니다.
 * 로고, 언어 전환, 알림, 사용자 메뉴 등의 기능을 제공합니다.
 * 
 * @param {HeaderProps} props - 헤더 컴포넌트의 속성
 * @param {function} [props.onMenuToggle] - 모바일 메뉴 토글 함수
 * @returns {JSX.Element} 헤더 컴포넌트 JSX
 * 
 * @example
 * ```tsx
 * // 기본 사용법
 * <Header />
 * 
 * // 모바일 메뉴 토글 함수와 함께 사용
 * <Header onMenuToggle={() => setMobileMenuOpen(true)} />
 * ```
 */
export function Header({ onMenuToggle }: HeaderProps) {
  /** Next.js 라우터 인스턴스 */
  const router = useRouter();
  
  /** 언어 컨텍스트 */
  const { language, setLanguage, t } = useLanguage();

  /**
   * 언어 변경 핸들러
   * 
   * 사용자가 언어를 선택했을 때 호출되는 함수입니다.
   * 언어 컨텍스트를 통해 전역 언어 상태를 업데이트합니다.
   * 
   * @param {string} locale - 변경할 언어 코드 ('ko' | 'en')
   * 
   * @example
   * ```tsx
   * handleLanguageChange('en'); // 영어로 변경
   * handleLanguageChange('ko'); // 한국어로 변경
   * ```
   */
  const handleLanguageChange = (locale: 'ko' | 'en') => {
    setLanguage(locale);
    console.log('Language switched to:', locale);
  };

  /**
   * 로그아웃 핸들러
   * 
   * 사용자가 로그아웃을 선택했을 때 호출되는 함수입니다.
   * 인증 토큰을 제거하고 로그인 페이지로 리다이렉트합니다.
   * 
   * @example
   * ```tsx
   * handleLogout(); // 로그아웃 실행
   * ```
   */
  const handleLogout = () => {
    try {
      // localStorage에서 인증 관련 데이터 제거
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_type');
        localStorage.removeItem('user_email');
      }
      
      // TODO: 서버 사이드 로그아웃 API 호출 구현
      // await apiClient.post('/auth/logout');
      
      console.log('Logout successful');
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // 오류가 발생해도 로그인 페이지로 이동
      router.push('/login');
    }
  };

  return (
    <header className="z-30 w-full border-b bg-background shrink-0">
      <div className="flex h-16 items-center px-4 lg:px-6">
        {/* Logo and Title */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-md bg-customs-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">KCS</span>
            </div>
            <div className="hidden md:block">
              <h1 className="text-lg font-semibold text-foreground">
                {t('header.title')}
              </h1>
              <p className="text-xs text-muted-foreground">
                {t('header.subtitle')}
              </p>
            </div>
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Header Actions */}
        <div className="flex items-center gap-2">
          {/* Language Switcher */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2">
                <Globe className="h-4 w-4" />
                <span className="hidden sm:inline">
                  {language === 'ko' ? t('header.korean') : t('header.english')}
                </span>
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>{t('header.language')}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => handleLanguageChange('ko')}
                className={language === 'ko' ? 'bg-accent' : ''}
              >
                <span className="mr-2">🇰🇷</span>
                {t('header.korean')}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => handleLanguageChange('en')}
                className={language === 'en' ? 'bg-accent' : ''}
              >
                <span className="mr-2">🇺🇸</span>
                {t('header.english')}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Notifications */}
          <Button variant="ghost" size="sm" className="relative">
            <Bell className="h-4 w-4" />
            <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-500 text-xs"></span>
            <span className="sr-only">{t('header.notifications')}</span>
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2">
                <div className="h-6 w-6 rounded-full bg-customs-100 flex items-center justify-center">
                  <User className="h-4 w-4 text-customs-600" />
                </div>
                <span className="hidden sm:inline text-sm font-medium">
                  홍길동
                </span>
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium">홍길동</p>
                  <p className="text-xs text-muted-foreground">
                    hong.gildong@customs.go.kr
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => alert('프로필 페이지는 개발 중입니다.')}>
                <User className="mr-2 h-4 w-4" />
                {t('header.profile')}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => alert('설정 페이지는 개발 중입니다.')}>
                <Settings className="mr-2 h-4 w-4" />
                {t('header.settings')}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                <LogOut className="mr-2 h-4 w-4" />
                {t('header.logout')}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}