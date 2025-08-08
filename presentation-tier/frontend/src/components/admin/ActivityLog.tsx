'use client';

import { User, AlertTriangle, Settings, Info } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

interface ActivityItem {
  id: number;
  type: 'user' | 'error' | 'system';
  message: string;
  time: string;
}

const activities: ActivityItem[] = [
  { id: 1, type: 'user', message: '새 사용자 가입: admin@company-a.com', time: '5분 전' },
  { id: 2, type: 'error', message: 'API 호출 제한 초과 - Company B', time: '12분 전' },
  { id: 3, type: 'system', message: '신고서 템플릿 업데이트 완료', time: '1시간 전' },
  { id: 4, type: 'user', message: '문서 처리 완료: 수입신고서 #2024-001', time: '2시간 전' },
  { id: 5, type: 'error', message: 'LLM API 응답 지연 감지', time: '3시간 전' },
];

const englishActivities: ActivityItem[] = [
  { id: 1, type: 'user', message: 'New user registered: admin@company-a.com', time: '5 min ago' },
  { id: 2, type: 'error', message: 'API rate limit exceeded - Company B', time: '12 min ago' },
  { id: 3, type: 'system', message: 'Declaration template update completed', time: '1 hour ago' },
  { id: 4, type: 'user', message: 'Document processed: Import Declaration #2024-001', time: '2 hours ago' },
  { id: 5, type: 'error', message: 'LLM API response delay detected', time: '3 hours ago' },
];

export default function ActivityLog() {
  const { t, language } = useLanguage();
  const activityData = language === 'ko' ? activities : englishActivities;

  const getIconAndColor = (type: string) => {
    switch (type) {
      case 'user':
        return { icon: User, color: 'text-green-600 bg-green-50' };
      case 'error':
        return { icon: AlertTriangle, color: 'text-red-600 bg-red-50' };
      case 'system':
        return { icon: Settings, color: 'text-blue-600 bg-blue-50' };
      default:
        return { icon: Info, color: 'text-slate-600 bg-slate-50' };
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <h3 className="text-lg font-semibold text-slate-800 mb-6">
        {t('admin.recentActivity')}
      </h3>
      <div className="space-y-4">
        {activityData.map((activity) => {
          const { icon: Icon, color } = getIconAndColor(activity.type);
          return (
            <div key={activity.id} className="flex items-start space-x-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${color}`}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-800">{activity.message}</p>
                <p className="text-xs text-slate-500 mt-1">{activity.time}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}