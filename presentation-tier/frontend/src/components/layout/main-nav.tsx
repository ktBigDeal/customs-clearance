'use client';

import { BarChart3, FileText, Home, Settings } from 'lucide-react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

interface MainNavProps {
  className?: string;
  onItemClick?: () => void;
}

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  description?: string;
}

export function MainNav({ className, onItemClick }: MainNavProps) {
  const t = useTranslations();
  const pathname = usePathname();

  const navItems: NavItem[] = [
    {
      title: t('navigation.dashboard'),
      href: '/dashboard',
      icon: Home,
      description: '시스템 현황 및 주요 지표',
    },
    {
      title: t('navigation.declarations'),
      href: '/declarations',
      icon: FileText,
      description: '수출입 신고서 관리',
    },
    {
      title: t('navigation.analytics'),
      href: '/analytics',
      icon: BarChart3,
      description: '통계 및 분석 리포트',
    },
    {
      title: t('navigation.settings'),
      href: '/settings',
      icon: Settings,
      description: '시스템 설정 및 환경설정',
    },
  ];

  return (
    <nav
      className={cn('flex flex-col space-y-1', className)}
      role="navigation"
      aria-label="Main navigation"
    >
      {navItems.map((item) => {
        const isActive = pathname.startsWith(item.href);
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onItemClick}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
              'hover:bg-accent hover:text-accent-foreground',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              isActive
                ? 'bg-customs-50 text-customs-700 shadow-sm border-r-2 border-customs-600'
                : 'text-muted-foreground hover:text-foreground'
            )}
            aria-current={isActive ? 'page' : undefined}
          >
            <Icon
              className={cn(
                'h-4 w-4 flex-shrink-0',
                isActive ? 'text-customs-600' : 'text-current'
              )}
              aria-hidden="true"
            />
            <div className="flex flex-col min-w-0">
              <span className="truncate">{item.title}</span>
              {item.description && (
                <span className="text-xs text-muted-foreground truncate">
                  {item.description}
                </span>
              )}
            </div>
          </Link>
        );
      })}
    </nav>
  );
}