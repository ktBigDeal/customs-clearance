'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'user';
  fallbackPath?: string;
}

export function ProtectedRoute({ 
  children, 
  requiredRole, 
  fallbackPath = '/login' 
}: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        // 인증되지 않은 사용자
        console.log('No user found, redirecting to login...');
        router.replace(fallbackPath as any);
        return;
      }

      if (requiredRole && user.role !== requiredRole) {
        // 권한이 부족한 사용자
        console.log(`User role ${user.role} doesn't match required role ${requiredRole}`);
        if (user.role === 'admin') {
          router.replace('/admin/dashboard');
        } else {
          router.replace('/dashboard');
        }
        return;
      }

      console.log(`User authorized for ${requiredRole || 'any'} access`);
      setIsChecking(false);
    }
  }, [user, isLoading, requiredRole, router, fallbackPath]);

  // 로딩 중이거나 권한 체크 중일 때 로딩 화면 표시
  if (isLoading || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  // 모든 검증을 통과한 경우에만 컴포넌트 렌더링
  return <>{children}</>;
}