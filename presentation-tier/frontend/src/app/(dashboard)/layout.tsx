'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/header';
import { Sidebar } from '@/components/layout/sidebar';
import { useAuth } from '@/contexts/AuthContext';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, isAdmin } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header onMenuClick={() => setSidebarOpen(true)} />

      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        isAdmin={isAdmin}
      />

      {/* Main Content */}
      <main className="fixed top-16 left-0 right-0 bottom-20 lg:left-64 overflow-hidden">
        <div className="h-full p-4 lg:p-6 max-w-7xl mx-auto overflow-auto">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 lg:left-64 bg-white border-t border-gray-200 px-4 py-2 z-20">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-4">
              <span>© 2025 관세청 통관시스템</span>
              <span>•</span>
              <button 
                onClick={() => window.open('/privacy-policy', '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes')}
                className="hover:text-blue-600 transition-colors"
              >
                개인정보처리방침
              </button>
              <span>•</span>
              <button 
                onClick={() => window.open('/terms-of-service', '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes')}
                className="hover:text-blue-600 transition-colors"
              >
                이용약관
              </button>
            </div>
            <div className="hidden sm:block">
              <span>고객센터: 125 | 평일 09:00~18:00</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}