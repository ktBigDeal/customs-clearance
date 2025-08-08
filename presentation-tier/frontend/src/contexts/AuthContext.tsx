'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type AuthUser } from '@/services/auth.service';

type UserRole = 'ADMIN' | 'USER';

interface User {
  username: string;
  name: string;
  email: string;
  role: UserRole;
  token: string;
  company?: string;
  lastLogin?: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string, role: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  isAdmin: boolean;
  updateUser: (userData: { name: string; email: string; password?: string }) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // 페이지 로드 시 저장된 사용자 정보 확인
    checkStoredAuth();
  }, []);

  const checkStoredAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        const currentUser = await authService.getCurrentUser();
        if (currentUser) {
          setUser({
            username: currentUser.username,
            name: currentUser.name,
            email: currentUser.email,
            role: currentUser.role as UserRole,
            token: currentUser.token,
            company: currentUser.company,
            lastLogin: currentUser.lastLogin
          });
        }
      }
    } catch (error) {
      console.error('Auth check error:', error);
      authService.logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (username: string, password: string, role: string): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      console.log('🚀 로그인 시작:', { username, role });
      
      // 백엔드 로그인 API 호출
      const token = await authService.login(username, password, role);
      console.log('✅ 토큰 받음:', token ? '토큰 존재' : '토큰 없음');
      
      // 토큰 저장
      authService.setToken(token);
      
      // 사용자 정보 가져오기
      console.log('🔍 사용자 정보 조회 중...');
      const currentUser = await authService.getCurrentUser();
      console.log('👤 사용자 정보:', currentUser);
      
      if (currentUser) {
        const userData: User = {
          username: currentUser.username,
          name: currentUser.name,
          email: currentUser.email,
          role: currentUser.role as UserRole,
          token: currentUser.token,
          company: currentUser.company,
          lastLogin: currentUser.lastLogin
        };

        setUser(userData);
        console.log('💾 사용자 상태 저장 완료');
        
        // 짧은 지연 후 리다이렉션
        setTimeout(() => {
          if (currentUser.role === 'ADMIN') {
            console.log('🔄 관리자 대시보드로 리다이렉션...');
            router.push('/admin/dashboard');
          } else {
            console.log('🔄 사용자 대시보드로 리다이렉션...');
            router.push('/dashboard');
          }
        }, 100);
        
        return true;
      }
      
      console.log('❌ 사용자 정보 없음');
      return false;
    } catch (error) {
      console.error('❌ 로그인 오류:', error);
      return false;
    } finally {
      setIsLoading(false);
      console.log('🏁 로그인 프로세스 완료');
    }
  };

  const updateUser = async (userData: { name: string; email: string; password?: string }): Promise<boolean> => {
    if (!user) return false;

    try {
      const updatedUser = await authService.updateUser(user.username, userData);
      
      // 사용자 정보 업데이트
      setUser(prev => prev ? {
        ...prev,
        name: updatedUser.name,
        email: updatedUser.email
      } : null);
      
      return true;
    } catch (error) {
      console.error('Update user error:', error);
      return false;
    }
  };

  const logout = () => {
    try {
      authService.logout();
      setUser(null);
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const isAdmin = user?.role === 'ADMIN';

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      isLoading,
      isAdmin,
      updateUser
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}