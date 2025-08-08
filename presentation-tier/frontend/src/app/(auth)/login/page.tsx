'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';

type UserType = 'user' | 'admin';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  
  const [userType, setUserType] = useState<UserType>('user');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim() || !password.trim()) {
      setError('이메일과 비밀번호를 모두 입력해주세요.');
      return;
    }

    setError('');

    try {
      const success = await login(email, password);
      
      if (!success) {
        setError('로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.');
      }
      // 성공시 AuthContext에서 자동으로 리다이렉션됨
      
    } catch (error) {
      setError('로그인 중 오류가 발생했습니다. 다시 시도해주세요.');
      console.error('Login error:', error);
    }
  };

  const handleUserTypeChange = (type: UserType) => {
    setUserType(type);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white">
      {/* Header with Logo */}
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold text-blue-600">
              TradeFlow
            </div>
            <div className="text-sm text-gray-500">
              통관 자동화 시스템
            </div>
          </div>
        </div>
      </header>

      {/* Main Login Section */}
      <div className="flex items-center justify-center min-h-[calc(100vh-80px)] px-6">
        <Card className="w-full max-w-md p-8">
          {/* User Type Selection */}
          <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
            <button
              type="button"
              onClick={() => handleUserTypeChange('user')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all whitespace-nowrap ${
                userType === 'user'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              일반 사용자
            </button>
            <button
              type="button"
              onClick={() => handleUserTypeChange('admin')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all whitespace-nowrap ${
                userType === 'admin'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              관리자
            </button>
          </div>

          {/* Login Form Header */}
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              로그인
            </h1>
            <p className="text-gray-600">
              {userType === 'admin' 
                ? '관리자 계정으로 로그인하세요'
                : '계정에 로그인하세요'
              }
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이메일
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="이메일을 입력하세요"
                disabled={isLoading}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="비밀번호를 입력하세요"
                disabled={isLoading}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || !email.trim() || !password.trim()}
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>로그인 중...</span>
                </div>
              ) : (
                '로그인'
              )}
            </Button>

            {/* Demo Credentials */}
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm font-medium text-blue-800 mb-2">테스트 계정:</p>
              <div className="text-xs text-blue-600 space-y-1">
                <div>관리자: admin@customs.go.kr / admin123</div>
                <div>사용자: user@company.com / user123</div>
              </div>
            </div>
          </form>

          {/* Forgot Password Link */}
          <div className="mt-6 text-center">
            <button 
              type="button"
              onClick={() => alert('비밀번호 찾기 기능은 개발 중입니다.')}
              className="text-sm text-blue-600 hover:text-blue-700 transition-colors"
            >
              비밀번호를 잊으셨나요?
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
}