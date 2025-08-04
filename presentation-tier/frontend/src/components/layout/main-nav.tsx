'use client';

import { BarChart3, FileText, Home, Settings, MessageCircle } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

interface MainNavProps {
  className?: string;
  onItemClick?: (() => void) | undefined;
}

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  description?: string;
}

export function MainNav({ className, onItemClick }: MainNavProps) {
  const pathname = usePathname();

  const navItems: NavItem[] = [
    {
      title: '대시보드',
      href: '/dashboard',
      icon: Home,
      description: '시스템 현황 및 주요 지표',
    },
    {
      title: 'AI 상담',
      href: '/chat',
      icon: MessageCircle,
      description: '통관 전문 AI 상담 서비스',
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

        const linkProps: any = {
          key: item.href,
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
          <Link {...linkProps}>
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