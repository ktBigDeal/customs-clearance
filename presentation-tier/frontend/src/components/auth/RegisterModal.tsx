'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { authService, type RegisterRequest } from '@/services/auth.service';
import { PrivacyConsentModal } from './PrivacyConsentModal';
import { TermsOfServiceModal } from './TermsOfServiceModal';

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function RegisterModal({ isOpen, onClose, onSuccess }: RegisterModalProps) {
  const [formData, setFormData] = useState<RegisterRequest>({
    username: '',
    password: '',
    name: '',
    email: '',
    role: 'USER',
    company: ''
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    lowercase: false,
    number: false,
    special: false
  });
  
  // 동의 관련 상태
  const [agreedToPrivacy, setAgreedToPrivacy] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);

  if (!isOpen) return null;

  const handleInputChange = (field: keyof RegisterRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
    
    // 비밀번호 유효성 검사
    if (field === 'password') {
      validatePassword(value);
    }
  };

  const validatePassword = (password: string) => {
    setPasswordValidation({
      length: password.length >= 8,
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 유효성 검증
    if (!formData.username.trim()) {
      setError('아이디를 입력해주세요.');
      return;
    }
    
    if (!formData.password.trim()) {
      setError('비밀번호를 입력해주세요.');
      return;
    }
    
    // 비밀번호 규칙 검증
    const isPasswordValid = Object.values(passwordValidation).every(rule => rule);
    if (!isPasswordValid) {
      setError('비밀번호가 보안 규칙을 만족하지 않습니다. 모든 조건을 충족해주세요.');
      return;
    }
    
    if (formData.password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }
    
    if (!agreedToPrivacy) {
      setError('개인정보 수집·이용에 동의해주세요.');
      return;
    }
    
    if (!agreedToTerms) {
      setError('이용약관에 동의해주세요.');
      return;
    }
    
    if (!formData.name.trim()) {
      setError('이름을 입력해주세요.');
      return;
    }
    
    if (!formData.email.trim()) {
      setError('이메일을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await authService.register(formData);
      onSuccess();
      onClose();
      
      // 폼 초기화
      setFormData({
        username: '',
        password: '',
        name: '',
        email: '',
        role: 'USER',
        company: ''
      });
      setConfirmPassword('');
      
    } catch (error: any) {
      setError(error.message || '회원가입 중 오류가 발생했습니다.');
      console.error('Registration error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
      setError('');
      setFormData({
        username: '',
        password: '',
        name: '',
        email: '',
        role: 'USER',
        company: ''
      });
      setConfirmPassword('');
      setAgreedToPrivacy(false);
      setAgreedToTerms(false);
      setShowPrivacyModal(false);
      setShowTermsModal(false);
      setPasswordValidation({
        length: false,
        lowercase: false,
        number: false,
        special: false
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              회원가입
            </h2>
            <button
              onClick={handleClose}
              disabled={isLoading}
              className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 역할 고정 (일반 사용자로만 가입 가능) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                역할
              </label>
              <div className="w-full px-3 py-2 bg-gray-100 border border-gray-200 rounded-lg text-sm text-gray-600">
                일반 사용자 (관리자 계정은 별도 승인이 필요합니다)
              </div>
            </div>

            {/* 아이디 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                아이디 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="아이디를 입력하세요"
                disabled={isLoading}
                required
              />
            </div>

            {/* 이름 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이름 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="이름을 입력하세요"
                disabled={isLoading}
                required
              />
            </div>

            {/* 이메일 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이메일 <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="이메일을 입력하세요"
                disabled={isLoading}
                required
              />
            </div>

            {/* 회사명 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                회사명
              </label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="회사명을 입력하세요 (선택사항)"
                disabled={isLoading}
              />
            </div>

            {/* 비밀번호 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호 <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="비밀번호를 입력하세요"
                disabled={isLoading}
                required
              />
              
              {/* 비밀번호 보안 규칙 */}
              {formData.password && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-700">비밀번호 보안 규칙</h4>
                    <div className="text-xs text-gray-500">
                      {Object.values(passwordValidation).filter(Boolean).length}/4 조건 충족
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className={`flex items-center space-x-2 text-xs ${passwordValidation.length ? 'text-green-600' : 'text-gray-500'}`}>
                      <div className={`w-3 h-3 rounded-full flex items-center justify-center ${passwordValidation.length ? 'bg-green-500' : 'bg-gray-300'}`}>
                        {passwordValidation.length ? (
                          <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                          </svg>
                        ) : null}
                      </div>
                      <span>8자 이상</span>
                    </div>
                    <div className={`flex items-center space-x-2 text-xs ${passwordValidation.lowercase ? 'text-green-600' : 'text-gray-500'}`}>
                      <div className={`w-3 h-3 rounded-full flex items-center justify-center ${passwordValidation.lowercase ? 'bg-green-500' : 'bg-gray-300'}`}>
                        {passwordValidation.lowercase ? (
                          <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                          </svg>
                        ) : null}
                      </div>
                      <span>소문자 포함 (a-z)</span>
                    </div>
                    <div className={`flex items-center space-x-2 text-xs ${passwordValidation.number ? 'text-green-600' : 'text-gray-500'}`}>
                      <div className={`w-3 h-3 rounded-full flex items-center justify-center ${passwordValidation.number ? 'bg-green-500' : 'bg-gray-300'}`}>
                        {passwordValidation.number ? (
                          <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                          </svg>
                        ) : null}
                      </div>
                      <span>숫자 포함 (0-9)</span>
                    </div>
                    <div className={`flex items-center space-x-2 text-xs ${passwordValidation.special ? 'text-green-600' : 'text-gray-500'}`}>
                      <div className={`w-3 h-3 rounded-full flex items-center justify-center ${passwordValidation.special ? 'bg-green-500' : 'bg-gray-300'}`}>
                        {passwordValidation.special ? (
                          <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                          </svg>
                        ) : null}
                      </div>
                      <span>특수문자 포함 (!@#$%^&* 등)</span>
                    </div>
                  </div>
                  
                  {Object.values(passwordValidation).every(Boolean) && (
                    <div className="mt-2 flex items-center space-x-2 text-xs text-green-600 font-medium">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                      </svg>
                      <span>안전한 비밀번호입니다!</span>
                    </div>
                  )}
                </div>
              )}
              
              {!formData.password && (
                <div className="mt-2">
                  <div className="text-xs text-gray-500">
                    보안을 위해 다음 조건을 모두 충족하는 비밀번호를 설정해주세요:
                  </div>
                  <ul className="mt-1 text-xs text-gray-400 ml-2">
                    <li>• 8자 이상</li>
                    <li>• 소문자, 숫자, 특수문자 각각 1개 이상 포함</li>
                  </ul>
                </div>
              )}
            </div>

            {/* 비밀번호 확인 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호 확인 <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="비밀번호를 다시 입력하세요"
                disabled={isLoading}
                required
              />
            </div>

            {/* 약관 및 개인정보 동의 */}
            <div className="space-y-3 pt-4 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900">약관 동의 <span className="text-red-500">*</span></h3>
              
              {/* 개인정보 수집·이용 동의 */}
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  id="privacy-consent"
                  checked={agreedToPrivacy}
                  onChange={(e) => setAgreedToPrivacy(e.target.checked)}
                  className="mt-0.5 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  disabled={isLoading}
                  required
                />
                <div className="flex-1">
                  <label htmlFor="privacy-consent" className="text-sm text-gray-700 cursor-pointer">
                    개인정보 수집·이용에 동의합니다. <span className="text-red-500">*</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowPrivacyModal(true)}
                    className="ml-2 text-xs text-blue-600 hover:text-blue-800 underline"
                    disabled={isLoading}
                  >
                    [내용 보기]
                  </button>
                </div>
              </div>

              {/* 이용약관 동의 */}
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  id="terms-consent"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="mt-0.5 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  disabled={isLoading}
                  required
                />
                <div className="flex-1">
                  <label htmlFor="terms-consent" className="text-sm text-gray-700 cursor-pointer">
                    이용약관에 동의합니다. <span className="text-red-500">*</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowTermsModal(true)}
                    className="ml-2 text-xs text-blue-600 hover:text-blue-800 underline"
                    disabled={isLoading}
                  >
                    [내용 보기]
                  </button>
                </div>
              </div>

              {/* 전체 동의 */}
              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="all-consent"
                    checked={agreedToPrivacy && agreedToTerms}
                    onChange={(e) => {
                      const isChecked = e.target.checked;
                      setAgreedToPrivacy(isChecked);
                      setAgreedToTerms(isChecked);
                    }}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <label htmlFor="all-consent" className="text-sm font-medium text-gray-900 cursor-pointer">
                    모든 약관에 동의합니다.
                  </label>
                </div>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={handleClose}
                disabled={isLoading}
              >
                취소
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>가입 중...</span>
                  </div>
                ) : (
                  '회원가입'
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>

      {/* 개인정보 수집·이용 동의서 모달 */}
      <PrivacyConsentModal
        isOpen={showPrivacyModal}
        onClose={() => setShowPrivacyModal(false)}
        onAgree={() => {
          setAgreedToPrivacy(true);
          setShowPrivacyModal(false);
        }}
      />

      {/* 이용약관 모달 */}
      <TermsOfServiceModal
        isOpen={showTermsModal}
        onClose={() => setShowTermsModal(false)}
        onAgree={() => {
          setAgreedToTerms(true);
          setShowTermsModal(false);
        }}
      />
    </div>
  );
}