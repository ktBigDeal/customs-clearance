'use client';

import { BarChart3, FileText, Home, Settings, MessageCircle, Shield, Users, History, Hash, ClipboardList } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';

interface MainNavProps {
  className?: string;
  onItemClick?: (() => void) | undefined;
  isAdmin?: boolean;
}

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  description?: string;
}

export function MainNav({ className, onItemClick, isAdmin = false }: MainNavProps) {
  const pathname = usePathname();
  const { t } = useLanguage();

  const userNavItems: NavItem[] = [
    {
      title: t('sidebar.dashboard'),
      href: '/dashboard',
      icon: Home,
      description: t('sidebar.dashboard.desc'),
    },
    {
      title: t('sidebar.report'),
      href: '/report',
      icon: ClipboardList,
      description: t('sidebar.report.desc'),
    },
    {
      title: t('sidebar.chat'),
      href: '/chat',
      icon: MessageCircle,
      description: t('sidebar.chat.desc'),
    },
    {
      title: t('sidebar.hscode'),
      href: '/hscode',
      icon: Hash,
      description: t('sidebar.hscode.desc'),
    },
  ];

  const adminNavItems: NavItem[] = [
    {
      title: t('admin.dashboard'),
      href: '/admin/dashboard',
      icon: Shield,
      description: '시스템 전반적인 관리 현황',
    },
    {
      title: t('admin.userManagement'),
      href: '/admin/users',
      icon: Users,
      description: '사용자 계정 및 권한 관리',
    },
    {
      title: t('admin.documentManagement'),
      href: '/admin/documents',
      icon: FileText,
      description: '문서 처리 상태 관리',
    },
    {
      title: t('admin.systemSettings'),
      href: '/admin/settings',
      icon: Settings,
      description: '시스템 환경 설정',
    },
    {
      title: t('admin.logViewer'),
      href: '/admin/logs',
      icon: History,
      description: '시스템 로그 조회',
    },
  ];

  const navItems = isAdmin ? adminNavItems : userNavItems;

  return (
    <nav
      className={cn('flex flex-col space-y-1', className)}
      role="navigation"
      aria-label="Main navigation"
    >
      {navItems.map((item) => {
        const isActive = pathname.startsWith(item.href);
        const Icon = item.icon;

        const linkProps: any = {
          href: item.href as any,
          className: cn(
            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
            'hover:bg-accent hover:text-accent-foreground',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
            isActive
              ? 'bg-customs-50 text-customs-700 shadow-sm border-r-2 border-customs-600'
              : 'text-muted-foreground hover:text-foreground'
          ),
          'aria-current': isActive ? 'page' : undefined,
        };

        if (onItemClick) {
          linkProps.onClick = onItemClick;
        }

        return (
          <Link key={item.href} {...linkProps}>
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