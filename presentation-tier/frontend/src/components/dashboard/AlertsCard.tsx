'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Info, CheckCircle, Clock } from 'lucide-react';

interface Alert {
  id: string;
  type: 'warning' | 'info' | 'success' | 'urgent';
  title: string;
  message: string;
  timestamp: string;
}

export function AlertsCard() {
  // 실제로는 API에서 가져올 데이터
  const alerts: Alert[] = [
    {
      id: '1',
      type: 'warning',
      title: '서류 보완 필요',
      message: '신고서 DEC-2024-001의 원산지증명서가 누락되었습니다.',
      timestamp: '10분 전',
    },
    {
      id: '2',
      type: 'urgent',
      title: '긴급 심사 요청',
      message: '고위험 화물에 대한 추가 검사가 필요합니다.',
      timestamp: '6시간 전',
    },
    {
      id: '3',
      type: 'success',
      title: '통관 완료',
      message: '신고서 DEC-2024-002가 성공적으로 통관되었습니다.',
      timestamp: '4시간 전',
    },
    {
      id: '4',
      type: 'info',
      title: '관세율 변경 안내',
      message: '2024년 3월부터 전자제품 관세율이 변경됩니다.',
      timestamp: '2시간 전',
    },
  ];

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'urgent':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getAlertVariant = (type: Alert['type']) => {
    switch (type) {
      case 'warning':
        return 'secondary';
      case 'info':
        return 'secondary';
      case 'success':
        return 'secondary';
      case 'urgent':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const getBadgeText = (type: Alert['type']) => {
    switch (type) {
      case 'warning':
        return '주의';
      case 'info':
        return '정보';
      case 'success':
        return '완료';
      case 'urgent':
        return '긴급';
      default:
        return '알림';
    }
  };

  return (
    <Card className="p-6 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="h-5 w-5 text-orange-500" />
        <h2 className="text-lg font-semibold">알림 센터</h2>
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-6 flex-1 flex items-center justify-center">
          <div>
            <div className="text-2xl mb-2">🔔</div>
            <p className="text-muted-foreground">새로운 알림이 없습니다</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col">
          <div className="space-y-4 flex-1">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border transition-colors hover:bg-accent/50 ${
                  alert.type === 'urgent' ? 'border-red-200 bg-red-50/50' : 'border-border'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {getAlertIcon(alert.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-sm truncate">
                        {alert.title}
                      </h3>
                      <Badge variant={getAlertVariant(alert.type)} className="text-xs">
                        {getBadgeText(alert.type)}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {alert.message}
                    </p>
                    <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {alert.timestamp}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* 하단 고정 영역 */}
          <div className="mt-auto">
            <div className="mt-3 pt-3 border-t">
              <button className="text-sm text-blue-600 hover:text-blue-800 font-medium w-full text-left">
                모든 알림 보기 →
              </button>
              
              {/* 추가 정보 영역 */}
              <div className="mt-2 p-2 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between text-xs text-gray-600">
                  <span>총 {alerts.length}개 알림</span>
                  <span>마지막 업데이트: 방금 전</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="text-xs text-gray-600">긴급 {alerts.filter(a => a.type === 'urgent').length}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span className="text-xs text-gray-600">주의 {alerts.filter(a => a.type === 'warning').length}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-xs text-gray-600">정보 {alerts.filter(a => a.type === 'info').length}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-gray-600">완료 {alerts.filter(a => a.type === 'success').length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}