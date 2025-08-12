'use client';

import { X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { MainNav } from './main-nav';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  className?: string;
  isAdmin?: boolean;
}

export function Sidebar({ isOpen = true, onClose, className, isAdmin = false }: SidebarProps) {
  const { t } = useLanguage();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 h-screen w-64 transform border-r bg-background transition-transform duration-300 ease-in-out lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          className
        )}
        aria-label="Sidebar navigation"
      >
        <div className="flex h-full flex-col">
          {/* Sidebar Header */}
          <div className="flex h-16 items-center justify-end border-b px-4">
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
                  {isAdmin ? t('admin.adminDashboard') : t('sidebar.mainMenu')}
                </h3>
                <MainNav onItemClick={onClose} isAdmin={isAdmin} />
              </div>

            

              {/* Help & Support */}
              <div>
                <h3 className="mb-3 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('sidebar.help')}
                </h3>
                <div className="space-y-1">
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={() => {
                      window.location.href = '/user-guide';
                      onClose?.();
                    }}
                  >
                    {t('sidebar.userGuide')}
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={() => {
                      window.location.href = '/customer-service';
                      onClose?.();
                    }}
                  >
                    {t('sidebar.customerService')}
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-sm font-normal"
                    onClick={() => {
                      window.location.href = '/faq';
                      onClose?.();
                    }}
                  >
                    {t('sidebar.faq')}
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
              <p>{t('sidebar.version')}</p>
              <p>{t('sidebar.copyright')}</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}