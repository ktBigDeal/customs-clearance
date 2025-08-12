'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function HomePage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        // 사용자 역할에 따른 리다이렉션
        if (user.role === 'ADMIN') {
          console.log('관리자 사용자 - 관리자 대시보드로 리다이렉션');
          router.replace('/admin/dashboard');
        } else {
          console.log('일반 사용자 - 사용자 대시보드로 리다이렉션');
          router.replace('/dashboard');
        }
      } else {
        router.replace('/login');
      }
    }
  }, [user, isLoading, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center">
      <div className="text-center">
        <div className="text-2xl font-bold text-blue-600 mb-4">
          TradeFlow
        </div>
        <div className="flex items-center justify-center space-x-2">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-gray-600">로딩 중...</span>
        </div>
      </div>
    </div>
  );
}