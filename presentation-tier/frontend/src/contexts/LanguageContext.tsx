'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Language = 'ko' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
}

export function LanguageProvider({ children }: LanguageProviderProps) {
  const [language, setLanguageState] = useState<Language>('ko');

  useEffect(() => {
    // 로컬스토리지에서 저장된 언어 설정 불러오기
    const savedLanguage = localStorage.getItem('language') as Language;
    if (savedLanguage && (savedLanguage === 'ko' || savedLanguage === 'en')) {
      setLanguageState(savedLanguage);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);
  };

  const t = (key: string): string => {
    const translations: Record<Language, Record<string, string>> = {
      ko: {
        // 헤더
        'header.title': '관세청 통관시스템',
        'header.subtitle': 'Korea Customs Service',
        'header.language': '언어 설정',
        'header.korean': '한국어',
        'header.english': 'English',
        'header.notifications': '알림',
        'header.profile': '프로필',
        'header.settings': '설정',
        'header.logout': '로그아웃',
        
        // 사이드바
        'sidebar.title': '관세청 시스템',
        'sidebar.mainMenu': '주요 메뉴',
        'sidebar.dashboard': '대시보드',
        'sidebar.dashboard.desc': '시스템 현황 및 주요 지표',
        'sidebar.chat': 'AI 상담',
        'sidebar.chat.desc': '통관 전문 AI 상담 서비스',
        'sidebar.report': '보고서 생성',
        'sidebar.report.desc': '수출입 신고서 생성 및 관리',
        'sidebar.hscode': 'HS코드 추천',
        'sidebar.hscode.desc': 'AI 기반 HS코드 분류 및 추천',
        'sidebar.quickActions': '빠른 작업',
        'sidebar.newDeclaration': '새 신고서 작성',
        'sidebar.uploadDoc': '서류 업로드',
        'sidebar.checkStatus': '진행 상황 확인',
        'sidebar.help': '도움말',
        'sidebar.userGuide': '사용자 가이드',
        'sidebar.customerService': '고객센터',
        'sidebar.faq': 'FAQ',
        'sidebar.version': '버전 1.0.0',
        'sidebar.copyright': '© 2024 한국관세청',
        
        // 대시보드
        'dashboard.title': '대시보드',
        'dashboard.subtitle': '관세 통관 시스템에 오신 것을 환영합니다',
        'dashboard.totalDeclarations': '총 신고서',
        'dashboard.pendingReview': '대기 중인 신고서',
        'dashboard.approved': '승인된 신고서',
        'dashboard.rejected': '거부된 신고서',
        'dashboard.recentDeclarations': '최근 신고서',
        'dashboard.quickActions': '빠른 작업',
        'dashboard.newDeclaration': '새 신고서 작성',
        'dashboard.viewDeclarations': '신고서 조회',
        'dashboard.uploadDocuments': '필수 서류',
        
        // 채팅
        'chat.title': 'AI 상담',
        'chat.subtitle': '통관 관련 궁금한 점을 AI에게 문의하세요',
        'chat.send': '전송',
        
        // 로그인
        'login.title': '로그인',
        'login.subtitle': '관세청 통관시스템에 로그인하세요',
        'login.email': '이메일',
        'login.password': '비밀번호',
        'login.loginButton': '로그인',
        'login.forgotPassword': '비밀번호를 잊으셨나요?',
        
        // 공통
        'common.loading': '로딩 중...',
        'common.error': '오류가 발생했습니다',
        'common.success': '성공적으로 완료되었습니다',
        'common.cancel': '취소',
        'common.confirm': '확인',
        'common.save': '저장',
        'common.edit': '수정',
        'common.delete': '삭제',
        'common.search': '검색',

        // 대시보드 상세 번역
        'dashboard.stats.totalDeclarations': '총 신고서',
        'dashboard.stats.pendingDeclarations': '대기 중인 신고서',
        'dashboard.stats.approvedDeclarations': '승인된 신고서',
        'dashboard.stats.rejectedDeclarations': '거부된 신고서',
        'dashboard.status.approved': '승인됨',
        'dashboard.status.cleared': '통관완료',
        'dashboard.status.underReview': '검토중',
        'dashboard.status.pendingDocuments': '서류대기',
        'dashboard.status.rejected': '거부됨',
        'dashboard.type.import': '수입',
        'dashboard.type.export': '수출',
        'dashboard.viewAllDeclarations': '전체 신고서 보기',
        'dashboard.monthlyReport': '월간 리포트',
        'dashboard.avgProcessingTime': '평균 처리 시간',
        'dashboard.thisMonth': '이번 달',
        'dashboard.lastMonth': '지난 달',
        'dashboard.improvement': '개선',

        // 채팅 페이지 번역 (레이블만)
        'chat.aiConsultant': '통관 AI 상담사',
        'chat.serviceDesc': '수출입 전문 상담 서비스',
        'chat.online': '온라인',
        'chat.placeholder': '통관 관련 궁금한 사항을 입력하세요...',
        'chat.generating': '답변을 생성중입니다...',
        'chat.userName': '홍길동',
        'chat.references': '참고 문서',
        'chat.fileAttach': '파일 첨부',
        'chat.voiceInput': '음성 입력',
        'chat.inputHelp': 'Enter로 전송, Shift+Enter로 줄바꿈',
        'chat.quickQuestions': '빠른 질문',
        'chat.recentChats': '최근 대화',
        'chat.help': '도움말',
        'chat.helpDesc': '더 정확한 답변을 위해 구체적인 상황과 함께 질문해 주세요.',

        // 고객센터 페이지 번역
        'customerService.title': '고객센터',
        'customerService.subtitle': '궁금한 점이나 문제가 있으시면 언제든지 문의해주세요',
        'customerService.phone': '전화 상담',
        'customerService.phoneDesc': '전문 상담사와 직접 통화',
        'customerService.email': '이메일 문의',
        'customerService.emailDesc': '상세한 문의 내용 전송',
        'customerService.liveChat': '실시간 채팅',
        'customerService.liveChatDesc': '즉시 답변 받기',
        'customerService.startChat': '채팅 시작하기',
        'customerService.inquiry': '1:1 문의하기',
        'customerService.inquiryDesc': '구체적인 문의사항을 남겨주시면 빠르게 답변드리겠습니다',
        'customerService.faq': '자주 묻는 질문',
        'customerService.faqDesc': '다른 사용자들이 자주 묻는 질문들을 확인해보세요',

        // 사용자 가이드 페이지 번역
        'userGuide.title': '사용자 가이드',
        'userGuide.subtitle': '시스템을 효율적으로 활용하는 방법을 배워보세요',

        // 관리자 페이지 번역
        'admin.dashboard': '관리자 대시보드',
        'admin.systemOverview': '시스템 전체 현황 및 통계 관리',
        'admin.permission': '관리자 권한',
        'admin.fullAccess': '전체 접근',
        'admin.systemOperational': '관리자 시스템 정상 운영 중',
        'admin.systemStatistics': '시스템 통계',
        'admin.systemHealth': '시스템 상태',
        'admin.uptime': '가동률',
        'admin.successRate': '성공률',
        'admin.avgResponseTime': '평균 응답시간',
        'admin.systemResources': '시스템 리소스',
        'admin.memory': '메모리',
        'admin.storage': '저장소',
        'admin.live': '실시간',
        'admin.quickStats': '빠른 통계',
        'admin.onlineUsers': '접속 중인 사용자',
        'admin.todayProcessed': '오늘 처리 건수',
        'admin.apiCallsHour': '시간당 API 호출',
        'admin.errorRate': '오류율',
        'admin.systemLoad': '시스템 부하',
        'admin.userManagement': '사용자 관리',
        'admin.documentManagement': '문서 관리',
        'admin.templateManagement': '템플릿 관리',
        'admin.systemSettings': '시스템 설정',
        'admin.logViewer': '로그 조회',
        'admin.systemTitle': '통관 자동화 시스템',
        'admin.adminDashboard': '관리자 대시보드',
        'admin.monthlyProcessingChart': '월별 처리량 및 API 사용량',
        'admin.documentProcessing': '문서 처리',
        'admin.apiCalls': 'API 호출',
        'admin.recentActivity': '최근 활동',
        'admin.activeUsers': '활성 사용자',
        'admin.processedDocs': '처리된 문서',
        'admin.apiCallsToday': '오늘 API 호출',
        'admin.errorCount': '오류 발생',
        
        // 대시보드 추가 번역
        'dashboard.inProgress': '진행 중',
        'dashboard.completed': '완료',
        'dashboard.rejected': '반려',
        'dashboard.monthlyProcessing': '월별 처리 현황',
        'dashboard.statusDistribution': '상태별 분포',
        
        // 공통 추가 번역
        'common.currentTime': '현재 시각',
        'common.count': '건',
        'common.dataLoadFailed': '데이터 로딩 실패',
        'common.retry': '다시 시도',
        'common.refresh': '새로고침',
        'common.loadingChartData': '차트 데이터 로딩 중...',
      },
      en: {
        // Header
        'header.title': 'Korea Customs Service System',
        'header.subtitle': 'Korea Customs Service',
        'header.language': 'Language Settings',
        'header.korean': '한국어',
        'header.english': 'English',
        'header.notifications': 'Notifications',
        'header.profile': 'Profile',
        'header.settings': 'Settings',
        'header.logout': 'Logout',
        
        // Sidebar
        'sidebar.title': 'Customs System',
        'sidebar.mainMenu': 'Main Menu',
        'sidebar.dashboard': 'Dashboard',
        'sidebar.dashboard.desc': 'System status and key metrics',
        'sidebar.chat': 'AI Consultation',
        'sidebar.chat.desc': 'Professional AI consultation service',
        'sidebar.report': 'Report Generation',
        'sidebar.report.desc': 'Import/Export declaration creation and management',
        'sidebar.hscode': 'HS Code Recommendation',
        'sidebar.hscode.desc': 'AI-based HS code classification and recommendation',
        'sidebar.quickActions': 'Quick Actions',
        'sidebar.newDeclaration': 'New Declaration',
        'sidebar.uploadDoc': 'Upload Documents',
        'sidebar.checkStatus': 'Check Status',
        'sidebar.help': 'Help & Support',
        'sidebar.userGuide': 'User Guide',
        'sidebar.customerService': 'Customer Service',
        'sidebar.faq': 'FAQ',
        'sidebar.version': 'Version 1.0.0',
        'sidebar.copyright': '© 2024 Korea Customs Service',
        
        // Dashboard
        'dashboard.title': 'Dashboard',
        'dashboard.subtitle': 'Welcome to Korea Customs Service System',
        'dashboard.totalDeclarations': 'Total Declarations',
        'dashboard.pendingReview': 'Pending Review',
        'dashboard.approved': 'Approved',
        'dashboard.rejected': 'Rejected',
        'dashboard.recentDeclarations': 'Recent Declarations',
        'dashboard.quickActions': 'Quick Actions',
        'dashboard.newDeclaration': 'New Declaration',
        'dashboard.viewDeclarations': 'View Declarations',
        'dashboard.uploadDocuments': 'Required Documents',
        
        // Chat
        'chat.title': 'AI Consultation',
        'chat.subtitle': 'Ask AI about customs and trade regulations',
        'chat.send': 'Send',
        
        // Login
        'login.title': 'Login',
        'login.subtitle': 'Sign in to Korea Customs Service System',
        'login.email': 'Email',
        'login.password': 'Password',
        'login.loginButton': 'Sign In',
        'login.forgotPassword': 'Forgot your password?',
        
        // Common
        'common.loading': 'Loading...',
        'common.error': 'An error occurred',
        'common.success': 'Successfully completed',
        'common.cancel': 'Cancel',
        'common.confirm': 'Confirm',
        'common.save': 'Save',
        'common.edit': 'Edit',
        'common.delete': 'Delete',
        'common.search': 'Search',

        // Dashboard detailed translations
        'dashboard.stats.totalDeclarations': 'Total Declarations',
        'dashboard.stats.pendingDeclarations': 'Pending Declarations',
        'dashboard.stats.approvedDeclarations': 'Approved Declarations',
        'dashboard.stats.rejectedDeclarations': 'Rejected Declarations',
        'dashboard.status.approved': 'Approved',
        'dashboard.status.cleared': 'Cleared',
        'dashboard.status.underReview': 'Under Review',
        'dashboard.status.pendingDocuments': 'Pending Documents',
        'dashboard.status.rejected': 'Rejected',
        'dashboard.type.import': 'Import',
        'dashboard.type.export': 'Export',
        'dashboard.viewAllDeclarations': 'View All Declarations',
        'dashboard.monthlyReport': 'Monthly Report',
        'dashboard.avgProcessingTime': 'Average Processing Time',
        'dashboard.thisMonth': 'This Month',
        'dashboard.lastMonth': 'Last Month',
        'dashboard.improvement': 'improvement',

        // Chat page translations (labels only)
        'chat.aiConsultant': 'Customs AI Consultant',
        'chat.serviceDesc': 'Professional Import/Export Consultation Service',
        'chat.online': 'Online',
        'chat.generating': 'Generating response...',
        'chat.userName': 'Hong Gildong',
        'chat.references': 'Reference Documents',
        'chat.fileAttach': 'Attach File',
        'chat.voiceInput': 'Voice Input',
        'chat.inputHelp': 'Press Enter to send, Shift+Enter for new line',
        'chat.quickQuestions': 'Quick Questions',
        'chat.recentChats': 'Recent Chats',
        'chat.help': 'Help',
        'chat.helpDesc': 'For more accurate answers, please provide specific details with your question.',

        // Customer Service page translations
        'customerService.title': 'Customer Service',
        'customerService.subtitle': 'Contact us anytime if you have questions or issues',
        'customerService.phone': 'Phone Support',
        'customerService.phoneDesc': 'Direct call with professional consultants',
        'customerService.email': 'Email Inquiry',
        'customerService.emailDesc': 'Send detailed inquiry',
        'customerService.liveChat': 'Live Chat',
        'customerService.liveChatDesc': 'Get instant answers',
        'customerService.startChat': 'Start Chat',
        'customerService.inquiry': '1:1 Inquiry',
        'customerService.inquiryDesc': 'Leave your specific questions and we will respond quickly',
        'customerService.faq': 'Frequently Asked Questions',
        'customerService.faqDesc': 'Check questions frequently asked by other users',

        // User Guide page translations
        'userGuide.title': 'User Guide',
        'userGuide.subtitle': 'Learn how to use the system efficiently',

        // Admin pages translations
        'admin.dashboard': 'Admin Dashboard',
        'admin.systemOverview': 'System Overview and Statistics Management',
        'admin.permission': 'Admin Permission',
        'admin.fullAccess': 'Full Access',
        'admin.systemOperational': 'Admin System Operational',
        'admin.systemStatistics': 'System Statistics',
        'admin.systemHealth': 'System Health',
        'admin.uptime': 'Uptime',
        'admin.successRate': 'Success Rate',
        'admin.avgResponseTime': 'Avg Response Time',
        'admin.systemResources': 'System Resources',
        'admin.memory': 'Memory',
        'admin.storage': 'Storage',
        'admin.live': 'Live',
        'admin.quickStats': 'Quick Stats',
        'admin.onlineUsers': 'Online Users',
        'admin.todayProcessed': 'Today Processed',
        'admin.apiCallsHour': 'API Calls/Hour',
        'admin.errorRate': 'Error Rate',
        'admin.systemLoad': 'System Load',
        'admin.userManagement': 'User Management',
        'admin.documentManagement': 'Document Management',
        'admin.templateManagement': 'Template Management',
        'admin.systemSettings': 'System Settings',
        'admin.logViewer': 'Log Viewer',
        'admin.systemTitle': 'Customs Automation System',
        'admin.adminDashboard': 'Administrator Dashboard',
        'admin.monthlyProcessingChart': 'Monthly Processing & API Usage',
        'admin.documentProcessing': 'Document Processing',
        'admin.apiCalls': 'API Calls',
        'admin.recentActivity': 'Recent Activity',
        'admin.activeUsers': 'Active Users',
        'admin.processedDocs': 'Processed Documents',
        'admin.apiCallsToday': 'API Calls Today',
        'admin.errorCount': 'Error Count',
        
        // Dashboard additional translations
        'dashboard.inProgress': 'In Progress',
        'dashboard.completed': 'Completed',
        'dashboard.rejected': 'Rejected',
        'dashboard.monthlyProcessing': 'Monthly Processing',
        'dashboard.statusDistribution': 'Status Distribution',
        
        // Common additional translations
        'common.currentTime': 'Current Time',
        'common.count': 'items',
        'common.dataLoadFailed': 'Data Load Failed',
        'common.retry': 'Retry',
        'common.refresh': 'Refresh',
        'common.loadingChartData': 'Loading chart data...',
      }
    };

    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}