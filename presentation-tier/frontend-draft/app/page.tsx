
'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function Home() {
  const [activeTab, setActiveTab] = useState('login');
  const [userType, setUserType] = useState('user');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (email && password) {
      setActiveTab('dashboard');
    }
  };

  const handleLogout = () => {
    setActiveTab('login');
    setEmail('');
    setPassword('');
  };

  if (activeTab === 'dashboard') {
    return <Dashboard userType={userType} onLogout={handleLogout} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white">
      {/* Header with Logo */}
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold text-blue-600" style={{fontFamily: 'var(--font-pacifico)'}}>
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
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          {/* User Type Selection */}
          <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
            <button
              onClick={() => setUserType('user')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all whitespace-nowrap cursor-pointer ${
                userType === 'user'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              일반 사용자
            </button>
            <button
              onClick={() => setUserType('admin')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all whitespace-nowrap cursor-pointer ${
                userType === 'admin'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              관리자
            </button>
          </div>

          {/* Login Form */}
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">로그인</h1>
            <p className="text-gray-600">
              {userType === 'admin' ? '관리자 계정으로 로그인하세요' : '계정에 로그인하세요'}
            </p>
          </div>

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
                required
              />
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors whitespace-nowrap cursor-pointer"
            >
              로그인
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link href="#" className="text-sm text-blue-600 hover:text-blue-700 cursor-pointer">
              비밀번호를 잊으셨나요?
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function Dashboard({ userType, onLogout }: { userType: string; onLogout: () => void }) {
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [showUploadModal, setShowUploadModal] = useState(false);

  const statusSummary = {
    total: 247,
    pending: 12,
    processing: 8,
    completed: 221,
    error: 6
  };

  const documents = [
    {
      id: 1,
      name: '수입신고서_ABC무역_2024001.pdf',
      uploadDate: '2024-01-15 14:30',
      type: '수입신고서',
      status: 'completed',
      result: '승인완료',
      downloadUrl: '#'
    },
    {
      id: 2,
      name: '원산지증명서_DEF상사_240114.pdf',
      uploadDate: '2024-01-14 16:45',
      type: '원산지증명서',
      status: 'processing',
      result: '처리중',
      downloadUrl: '#'
    },
    {
      id: 3,
      name: '포장명세서_GHI무역_240113.xlsx',
      uploadDate: '2024-01-13 11:20',
      type: '포장명세서',
      status: 'error',
      result: '서류 불일치',
      downloadUrl: '#'
    },
    {
      id: 4,
      name: '상업송장_JKL Trading_240112.pdf',
      uploadDate: '2024-01-12 09:15',
      type: '상업송장',
      status: 'completed',
      result: '승인완료',
      downloadUrl: '#'
    },
    {
      id: 5,
      name: '수출신고서_MNO상사_240111.pdf',
      uploadDate: '2024-01-11 15:20',
      type: '수출신고서',
      status: 'pending',
      result: '처리 대기',
      downloadUrl: '#'
    },
    {
      id: 6,
      name: '화물관리번호_PQR무역_240110.pdf',
      uploadDate: '2024-01-10 13:45',
      type: '화물관리번호',
      status: 'completed',
      result: '승인완료',
      downloadUrl: '#'
    },
    {
      id: 7,
      name: '통관위임장_STU Trading_240109.pdf',
      uploadDate: '2024-01-09 10:30',
      type: '통관위임장',
      status: 'processing',
      result: '검토중',
      downloadUrl: '#'
    },
    {
      id: 8,
      name: '수입신고서_VWX상사_240108.pdf',
      uploadDate: '2024-01-08 14:15',
      type: '수입신고서',
      status: 'completed',
      result: '승인완료',
      downloadUrl: '#'
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <div className="w-2 h-2 bg-gray-400 rounded-full"></div>;
      case 'processing':
        return <i className="ri-loader-4-line w-4 h-4 text-blue-500 animate-spin"></i>;
      case 'completed':
        return <i className="ri-check-line w-4 h-4 text-green-500"></i>;
      case 'error':
        return <i className="ri-alert-line w-4 h-4 text-red-500"></i>;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return '처리 대기';
      case 'processing':
        return '처리중';
      case 'completed':
        return '완료됨';
      case 'error':
        return '오류';
      default:
        return '';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-gray-600';
      case 'processing':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const statusMatch = filterStatus === 'all' || doc.status === filterStatus;
    const typeMatch = filterType === 'all' || doc.type === filterType;
    return statusMatch && typeMatch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <div className="text-2xl font-bold text-blue-600" style={{fontFamily: 'var(--font-pacifico)'}}>
                TradeFlow
              </div>
              <nav className="flex space-x-6">
                <Link href="#" className="text-blue-600 font-medium cursor-pointer border-b-2 border-blue-600 pb-1">대시보드</Link>
                <Link href="/import-declaration" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">수입신고서 작성</Link>
                <Link href="#" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">문서 관리</Link>
                <Link href="#" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">신고 내역</Link>
                {userType === 'admin' && (
                  <Link href="#" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">사용자 관리</Link>
                )}
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setShowUploadModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors whitespace-nowrap cursor-pointer flex items-center space-x-2"
              >
                <i className="ri-upload-line w-4 h-4"></i>
                <span>문서 업로드</span>
              </button>
              <Link href="/chat" className="bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors whitespace-nowrap cursor-pointer flex items-center space-x-2">
                <i className="ri-robot-2-line w-4 h-4"></i>
                <span>AI 상담</span>
              </Link>
              <Link href="/chat" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">최근 질문</Link>
              <span className="text-sm text-gray-600">
                {userType === 'admin' ? '관리자' : '일반사용자'} | 홍길동님
              </span>
              <button 
                onClick={onLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 transition-colors whitespace-nowrap cursor-pointer flex items-center space-x-2"
              >
                <i className="ri-logout-box-line w-4 h-4"></i>
                <span>로그아웃</span>
              </button>
              <button className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 cursor-pointer">
                <i className="ri-notification-line w-5 h-5"></i>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">총 문서 수</p>
                <p className="text-2xl font-bold text-gray-900">{statusSummary.total}</p>
              </div>
              <div className="w-12 h-12 flex items-center justify-center bg-blue-100 rounded-lg">
                <i className="ri-file-list-line w-6 h-6 text-blue-600"></i>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">처리 대기</p>
                <p className="text-2xl font-bold text-gray-900">{statusSummary.pending}</p>
              </div>
              <div className="w-12 h-12 flex items-center justify-center bg-gray-100 rounded-lg">
                <i className="ri-time-line w-6 h-6 text-gray-600"></i>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">처리중</p>
                <p className="text-2xl font-bold text-gray-900">{statusSummary.processing}</p>
              </div>
              <div className="w-12 h-12 flex items-center justify-center bg-blue-100 rounded-lg">
                <i className="ri-loader-4-line w-6 h-6 text-blue-600"></i>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">완료됨</p>
                <p className="text-2xl font-bold text-gray-900">{statusSummary.completed}</p>
              </div>
              <div className="w-12 h-12 flex items-center justify-center bg-green-100 rounded-lg">
                <i className="ri-check-line w-6 h-6 text-green-600"></i>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">오류</p>
                <p className="text-2xl font-bold text-gray-900">{statusSummary.error}</p>
              </div>
              <div className="w-12 h-12 flex items-center justify-center bg-red-100 rounded-lg">
                <i className="ri-alert-line w-6 h-6 text-red-600"></i>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-8">
          {/* Filters Sidebar */}
          <div className="w-64 space-y-6">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">필터</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">문서 종류</label>
                  <select 
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm pr-8"
                  >
                    <option value="all">전체</option>
                    <option value="수입신고서">수입신고서</option>
                    <option value="수출신고서">수출신고서</option>
                    <option value="원산지증명서">원산지증명서</option>
                    <option value="상업송장">상업송장</option>
                    <option value="포장명세서">포장명세서</option>
                    <option value="화물관리번호">화물관리번호</option>
                    <option value="통관위임장">통관위임장</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">처리 상태</label>
                  <div className="space-y-2">
                    {[
                      { value: 'all', label: '전체', count: statusSummary.total },
                      { value: 'pending', label: '처리 대기', count: statusSummary.pending },
                      { value: 'processing', label: '처리중', count: statusSummary.processing },
                      { value: 'completed', label: '완료됨', count: statusSummary.completed },
                      { value: 'error', label: '오류', count: statusSummary.error }
                    ].map((status) => (
                      <label key={status.value} className="flex items-center space-x-3 cursor-pointer">
                        <input
                          type="radio"
                          name="status"
                          value={status.value}
                          checked={filterStatus === status.value}
                          onChange={(e) => setFilterStatus(e.target.value)}
                          className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700 flex-1">{status.label}</span>
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                          {status.count}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Documents Table */}
          <div className="flex-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">문서 목록</h2>
                  <div className="text-sm text-gray-600">
                    총 {filteredDocuments.length}개 문서
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        문서명
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        업로드 일자
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        문서 종류
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        처리 상태
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        처리 결과
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        다운로드
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredDocuments.map((doc) => (
                      <tr key={doc.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 flex items-center justify-center bg-blue-100 rounded-lg">
                              <i className="ri-file-text-line w-4 h-4 text-blue-600"></i>
                            </div>
                            <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                              {doc.name}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {doc.uploadDate}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                            {doc.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`flex items-center space-x-2 ${getStatusColor(doc.status)}`}>
                            {getStatusIcon(doc.status)}
                            <span className="text-sm font-medium">
                              {getStatusText(doc.status)}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {doc.result}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {doc.status === 'completed' ? (
                            <button className="w-8 h-8 flex items-center justify-center text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer">
                              <i className="ri-download-line w-4 h-4"></i>
                            </button>
                          ) : (
                            <button className="w-8 h-8 flex items-center justify-center text-gray-400 cursor-not-allowed">
                              <i className="ri-download-line w-4 h-4"></i>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {filteredDocuments.length === 0 && (
                <div className="text-center py-12">
                  <i className="ri-file-list-line w-12 h-12 text-gray-300 mx-auto mb-4"></i>
                  <p className="text-gray-500">선택한 조건에 맞는 문서가 없습니다.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold">문서 업로드</h3>
              <button 
                onClick={() => setShowUploadModal(false)}
                className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 cursor-pointer"
              >
                <i className="ri-close-line w-5 h-5"></i>
              </button>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center mb-6">
              <i className="ri-upload-cloud-line w-16 h-16 text-gray-400 mx-auto mb-4"></i>
              <p className="text-lg text-gray-600 mb-2">파일을 드래그하거나 클릭하여 업로드</p>
              <p className="text-sm text-gray-500">PDF, Excel, Word 파일만 지원 (최대 10MB)</p>
            </div>

            <div className="space-y-3 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">문서 종류</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm pr-8">
                  <option>문서 종류를 선택하세요</option>
                  <option>수입신고서</option>
                  <option>수출신고서</option>
                  <option>원산지증명서</option>
                  <option>상업송장</option>
                  <option>포장명세서</option>
                  <option>화물관리번호</option>
                  <option>통관위임장</option>
                </select>
              </div>
            </div>

            <div className="flex space-x-3">
              <button 
                onClick={() => setShowUploadModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 whitespace-nowrap cursor-pointer"
              >
                취소
              </button>
              <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 whitespace-nowrap cursor-pointer">
                업로드 시작
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
