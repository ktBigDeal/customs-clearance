'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { RegisterModal } from '@/components/auth/RegisterModal';

type UserType = 'USER' | 'ADMIN';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  
  const [userType, setUserType] = useState<UserType>('USER');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      setError('아이디와 비밀번호를 모두 입력해주세요.');
      return;
    }

    setError('');

    try {
      const success = await login(username, password, userType);
      
      if (!success) {
        setError('로그인에 실패했습니다. 아이디, 비밀번호, 역할을 확인해주세요.');
      }
      // 성공시 AuthContext에서 자동으로 리다이렉션됨
      
    } catch (error: any) {
      setError(error.message || '로그인 중 오류가 발생했습니다. 다시 시도해주세요.');
      console.error('Login error:', error);
    }
  };

  const handleUserTypeChange = (type: UserType) => {
    setUserType(type);
    setError('');
  };

  const handleRegisterSuccess = () => {
    setError('');
    alert('회원가입이 완료되었습니다. 로그인해주세요.');
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
              onClick={() => handleUserTypeChange('USER')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all whitespace-nowrap ${
                userType === 'USER'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              일반 사용자
            </button>
            <button
              type="button"
              onClick={() => handleUserTypeChange('ADMIN')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all whitespace-nowrap ${
                userType === 'ADMIN'
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
              {userType === 'ADMIN' 
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
                아이디
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="아이디를 입력하세요"
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
              disabled={isLoading || !username.trim() || !password.trim()}
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
                <div>관리자: admin2 / admin1234</div>
                <div>사용자: user2 / qwer1234</div>
              </div>
            </div>

            {/* Register Button */}
            <div className="mt-4">
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={() => setShowRegister(true)}
                disabled={isLoading}
              >
                회원가입
              </Button>
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

      {/* Register Modal */}
      <RegisterModal 
        isOpen={showRegister}
        onClose={() => setShowRegister(false)}
        onSuccess={handleRegisterSuccess}
      />
    </div>
  );
}