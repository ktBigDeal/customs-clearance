'use client';

import { X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { MainNav } from './main-nav';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  className?: string;
}

export function Sidebar({ isOpen = true, onClose, className }: SidebarProps) {

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 h-full w-64 transform border-r bg-background transition-transform duration-300 ease-in-out lg:static lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          className
        )}
        aria-label="Sidebar navigation"
      >
        <div className="flex h-full flex-col">
          {/* Sidebar Header */}
          <div className="flex h-16 items-center justify-between border-b px-4">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-md bg-customs-600 flex items-center justify-center">
                <span className="text-white font-bold text-xs">KCS</span>
              </div>
              <span className="font-semibold text-sm">관세청 시스템</span>
            </div>
            {/* Close button for mobile */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Navigation */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-6">
              {/* Main Navigation */}
              <div>
                <h3 className="mb-3 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  주요 메뉴
                </h3>
                <MainNav onItemClick={onClose} />
              </div>

              {/* Quick Actions */}
              <div>
                <h3 className="mb-3 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  빠른 작업
                </h3>
                <div className="space-y-1">
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={onClose}
                  >
                    새 신고서 작성
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={onClose}
                  >
                    서류 업로드
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={onClose}
                  >
                    진행 상황 확인
                  </Button>
                </div>
              </div>

              {/* Help & Support */}
              <div>
                <h3 className="mb-3 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  도움말
                </h3>
                <div className="space-y-1">
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={onClose}
                  >
                    사용자 가이드
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={onClose}
                  >
                    고객센터
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={onClose}
                  >
                    FAQ
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="border-t p-4">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <div className="h-8 w-8 rounded-full bg-customs-100 flex items-center justify-center">
                <span className="text-customs-600 text-xs font-semibold">
                  KCS
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">
                  한국관세청
                </p>
                <p className="text-xs truncate">
                  Korea Customs Service
                </p>
              </div>
            </div>
            <div className="mt-3 text-xs text-muted-foreground">
              <p>버전 1.0.0</p>
              <p>© 2024 한국관세청</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}