'use client';

import { useEffect, useState } from 'react';
import {
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  RefreshCw,
  Shield,
  Users,
  Activity,
  Server,
  AlertTriangle,
  Database,
  Cpu,
  HardDrive,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useLanguage } from '@/contexts/LanguageContext';

// 사용자 대시보드와 동일한 컴포넌트들 재사용
import { StatsCard } from '@/components/dashboard/StatsCard';
import { LineChart } from '@/components/dashboard/LineChart';
import { DonutChart } from '@/components/dashboard/DonutChart';
import { AlertsCard } from '@/components/dashboard/AlertsCard';

// API 연동 (향후 관리자 전용 API 추가 예정)
import { 
  declarationsApi, 
  type DeclarationStats, 
  type ChartData 
} from '@/lib/declarations-api';
import { adminService, SystemLog } from '@/services/admin.service';

export default function AdminDashboardPage() {
  const { t } = useLanguage();
  
  // 상태 관리
  const [stats, setStats] = useState<DeclarationStats | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [recentLogs, setRecentLogs] = useState<SystemLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // 실시간 시계
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // 데이터 로딩 함수 (관리자는 전체 데이터 조회)
  const loadDashboardData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // 병렬로 모든 데이터 로딩 (관리자는 전체 시스템 데이터)
      const [statsData, chartDataResult, logsData] = await Promise.all([
        declarationsApi.getStats(),
        declarationsApi.getChartData(),
        adminService.getLogs({
          keyword: '',
          level: 'all',
          source: 'all', 
          dateFilter: 'today',
          page: 0,
          size: 5
        }),
      ]);

      setStats(statsData);
      setChartData(chartDataResult);
      setRecentLogs(logsData.logs || []);
    } catch (err: any) {
      console.error('Failed to load admin dashboard data:', err);
      setError(err.message || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadDashboardData(true);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(date);
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    }).format(date);
  };

  // 관리자용 통계 카드 데이터 생성
  const adminStatsCards = stats ? [
    {
      title: t('dashboard.totalDeclarations'),
      value: stats.totalDeclarations,
      change: '+12%',
      trend: 'up' as const,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: t('dashboard.inProgress'),
      value: stats.pendingDeclarations + stats.underReviewDeclarations,
      change: '+5%',
      trend: 'up' as const,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: t('dashboard.completed'),
      value: stats.approvedDeclarations + stats.clearedDeclarations,
      change: '+8%',
      trend: 'up' as const,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: t('dashboard.rejected'),
      value: stats.rejectedDeclarations,
      change: '-3%',
      trend: 'down' as const,
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
  ] : [];

  if (loading) {
    return (
      <ProtectedRoute requiredRole="ADMIN">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="animate-pulse">
            <div className="h-48 bg-gray-200 rounded-lg mb-6"></div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
            <div className="grid gap-6 lg:grid-cols-2 mb-6">
              <div className="h-80 bg-gray-200 rounded-lg"></div>
              <div className="h-80 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (error) {
    return (
      <ProtectedRoute requiredRole="ADMIN">
        <div className="max-w-7xl mx-auto space-y-6">
          <Card className="p-8 text-center">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold mb-2">{t('common.dataLoadFailed')}</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => loadDashboardData()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {t('common.retry')}
            </Button>
          </Card>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 🎯 1. 관리자 히어로 섹션 */}
        <div className="relative overflow-hidden bg-gradient-to-r from-purple-600 via-purple-700 to-purple-800 text-white p-8 rounded-lg shadow-lg">
          {/* 배경 패턴 */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 left-0 w-full h-full bg-repeat opacity-20"
                 style={{
                   backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Ccircle cx='7' cy='7' r='7'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
                 }}
            />
          </div>

          <div className="relative z-10">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              {/* 왼쪽: 메인 텍스트 */}
              <div className="space-y-4">
                <div>
                  <h1 className="text-3xl lg:text-4xl font-bold mb-2">
                    {t('admin.dashboard')}
                  </h1>
                  <p className="text-purple-100 text-lg">
                    {t('admin.systemOverview')}
                  </p>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-purple-200" />
                    <div>
                      <div className="text-sm text-purple-200">{t('common.currentTime')}</div>
                      <div className="font-mono text-lg font-bold">
                        {formatTime(currentTime)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-purple-200" />
                    <div>
                      <div className="text-sm text-purple-200">{t('admin.permission')}</div>
                      <div className="font-bold">{t('admin.fullAccess')}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 오른쪽: 시스템 상태 */}
              <div className="text-center lg:text-right">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
                  <div className="flex items-center justify-center lg:justify-end gap-2 mb-2">
                    <TrendingUp className="h-6 w-6 text-purple-300" />
                    <span className="text-sm text-purple-100">{t('dashboard.totalDeclarations')}</span>
                  </div>
                  <div className="text-4xl lg:text-5xl font-bold mb-1">
                    {stats?.totalDeclarations?.toLocaleString() || 0}
                  </div>
                  <div className="text-lg text-purple-100">{t('common.count')}</div>
                </div>
              </div>
            </div>

            {/* 하단: 날짜 및 상태 */}
            <div className="mt-6 pt-6 border-t border-white/20">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="text-purple-100">
                  {formatDate(currentTime)}
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-purple-100">{t('admin.systemOperational')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 📊 2. 통합 통계 및 차트 섹션 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">{t('admin.systemStatistics')}</h2>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {t('common.refresh')}
            </Button>
          </div>
          
          {/* 통계 카드들 */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
            {adminStatsCards.map((stat, index) => (
              <StatsCard key={index} {...stat} />
            ))}
          </div>

          {/* 차트 섹션 */}
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('dashboard.monthlyProcessing')}</h3>
              {chartData?.monthlyData ? (
                <LineChart data={chartData.monthlyData} />
              ) : (
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  {t('common.loadingChartData')}
                </div>
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('dashboard.statusDistribution')}</h3>
              {chartData?.statusData ? (
                <DonutChart data={chartData.statusData} />
              ) : (
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  {t('common.loadingChartData')}
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* 🔄 3. 시스템 모니터링 통합 섹션 */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-6">
            <Server className="h-5 w-5 text-blue-600" />
            <h2 className="text-xl font-semibold">{t('admin.systemHealth')}</h2>
          </div>
          
          <div className="grid gap-6 lg:grid-cols-3">
            {/* 시스템 헬스 지표 */}
            <div className="lg:col-span-2">
              {/* 주요 지표 */}
              <div className="grid gap-4 md:grid-cols-3 mb-6">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600 mb-1">99.9%</div>
                  <div className="text-sm text-green-700">{t('admin.uptime')}</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 mb-1">
                    {stats ? Math.round((stats.approvedDeclarations / stats.totalDeclarations) * 100) : 0}%
                  </div>
                  <div className="text-sm text-blue-700">{t('admin.successRate')}</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600 mb-1">2.3s</div>
                  <div className="text-sm text-purple-700">{t('admin.avgResponseTime')}</div>
                </div>
              </div>
              
              {/* 시스템 리소스 */}
              <div className="border-t pt-4 mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">{t('admin.systemResources')}</h4>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <Cpu className="h-4 w-4 text-orange-500" />
                    <div>
                      <div className="text-sm font-medium">CPU</div>
                      <div className="text-xs text-gray-600">45%</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <Database className="h-4 w-4 text-green-500" />
                    <div>
                      <div className="text-sm font-medium">{t('admin.memory')}</div>
                      <div className="text-xs text-gray-600">62%</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <HardDrive className="h-4 w-4 text-blue-500" />
                    <div>
                      <div className="text-sm font-medium">{t('admin.storage')}</div>
                      <div className="text-xs text-gray-600">78%</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 최근 시스템 활동 */}
              <div className="border-t pt-4">
                <div className="flex items-center gap-2 mb-4">
                  <Activity className="h-5 w-5 text-green-600" />
                  <h4 className="text-lg font-medium">{t('admin.recentActivity')}</h4>
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full ml-auto">
                    {t('admin.live')}
                  </span>
                </div>
                <div className="space-y-2">
                  {recentLogs.length > 0 ? (
                    recentLogs.map((log) => {
                      const getLogIcon = (level: string, source: string) => {
                        if (level === 'ERROR') return { icon: AlertTriangle, color: 'border-red-400 bg-red-50', iconColor: 'text-red-600' };
                        if (level === 'WARN') return { icon: AlertTriangle, color: 'border-orange-400 bg-orange-50', iconColor: 'text-orange-600' };
                        if (source === 'AUTH') return { icon: CheckCircle, color: 'border-green-400 bg-green-50', iconColor: 'text-green-600' };
                        if (source === 'SYSTEM') return { icon: Database, color: 'border-blue-400 bg-blue-50', iconColor: 'text-blue-600' };
                        return { icon: Activity, color: 'border-gray-400 bg-gray-50', iconColor: 'text-gray-600' };
                      };
                      
                      const { icon: LogIcon, color, iconColor } = getLogIcon(log.level, log.source);
                      const timeAgo = new Date(log.timestamp).toLocaleString('ko-KR', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      });
                      
                      return (
                        <div key={log.id} className={`flex items-start gap-3 p-2 border-l-4 ${color} rounded-r`}>
                          <LogIcon className={`h-4 w-4 ${iconColor} mt-0.5`} />
                          <div className="flex-1">
                            <div className="text-sm font-medium">{log.message}</div>
                            <div className="text-xs text-gray-600">
                              {log.userName ? `${log.userName} • ` : ''}{timeAgo}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-center py-4 text-gray-500 text-sm">
                      오늘 로그가 없습니다
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* 알림 센터 */}
            <div>
              <AlertsCard />
            </div>
          </div>
        </Card>
      </div>
    </ProtectedRoute>
  );
}