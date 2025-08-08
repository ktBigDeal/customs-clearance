'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

type UserRole = 'admin' | 'user';

interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  company?: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

// Mock 사용자 데이터 (실제 환경에서는 API에서 가져옴)
const mockUsers = [
  {
    id: '1',
    email: 'admin@customs.go.kr',
    password: 'admin123',
    name: '관리자',
    role: 'admin' as UserRole,
    company: '한국관세청'
  },
  {
    id: '2',
    email: 'user@company.com',
    password: 'user123',
    name: '홍길동',
    role: 'user' as UserRole,
    company: '(주)무역회사'
  }
];

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // 페이지 로드 시 저장된 사용자 정보 확인
    checkStoredAuth();
  }, []);

  const checkStoredAuth = () => {
    try {
      const storedUser = localStorage.getItem('auth_user');
      const storedToken = localStorage.getItem('auth_token');
      
      if (storedUser && storedToken) {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check error:', error);
      // 잘못된 데이터가 있으면 클리어
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      // Mock 인증 (실제 환경에서는 API 호출)
      const foundUser = mockUsers.find(u => u.email === email && u.password === password);
      
      if (foundUser) {
        const userData: User = {
          id: foundUser.id,
          name: foundUser.name,
          email: foundUser.email,
          role: foundUser.role,
          company: foundUser.company
        };

        // 사용자 정보와 토큰 저장
        localStorage.setItem('auth_user', JSON.stringify(userData));
        localStorage.setItem('auth_token', 'mock_jwt_token_' + foundUser.id);
        
        setUser(userData);
        
        // 짧은 지연 후 리다이렉션 (상태 업데이트 완료 후)
        setTimeout(() => {
          // 역할별 리다이렉션
          if (foundUser.role === 'admin') {
            console.log('Redirecting to admin dashboard...');
            router.push('/admin/dashboard');
          } else {
            console.log('Redirecting to user dashboard...');
            router.push('/dashboard');
          }
        }, 100);
        
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('Login error:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    try {
      // 저장된 데이터 제거
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_token');
      
      setUser(null);
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      isLoading,
      isAdmin
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