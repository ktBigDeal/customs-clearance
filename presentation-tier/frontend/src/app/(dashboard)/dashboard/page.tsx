'use client';

import { useEffect, useState } from 'react';
import {
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// 새로운 컴포넌트들 import
import { CustomsHeroSection } from '@/components/dashboard/CustomsHeroSection';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { LineChart } from '@/components/dashboard/LineChart';
import { DonutChart } from '@/components/dashboard/DonutChart';
import { RealTimeDeclarationList } from '@/components/dashboard/RealTimeDeclarationList';
import { AlertsCard } from '@/components/dashboard/AlertsCard';

// API 연동
import { 
  declarationsApi, 
  type DeclarationStats, 
  type ChartData, 
  type ProcessingTimeStats 
} from '@/lib/declarations-api';

export default function DashboardPage() {
  const { t } = useLanguage();
  
  // 상태 관리
  const [stats, setStats] = useState<DeclarationStats | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [processingTime, setProcessingTime] = useState<ProcessingTimeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // 데이터 로딩 함수
  const loadDashboardData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // 병렬로 모든 데이터 로딩
      const [statsData, chartDataResult, processingTimeData] = await Promise.all([
        declarationsApi.getStats(),
        declarationsApi.getChartData(),
        declarationsApi.getProcessingTimeStats(),
      ]);

      setStats(statsData);
      setChartData(chartDataResult);
      setProcessingTime(processingTimeData);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
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

  // 통계 카드 데이터 생성
  const statsCards = stats ? [
    {
      title: '전체 신고서',
      value: stats.totalDeclarations,
      change: '+12%',
      trend: 'up' as const,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: '작성 중',
      value: stats.pendingDeclarations,
      change: '-5%',
      trend: 'down' as const,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: '승인',
      value: stats.approvedDeclarations,
      change: '+8%',
      trend: 'up' as const,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: '제출 완료',
      value: stats.clearedDeclarations,
      change: '+5%',
      trend: 'up' as const,
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
  ] : [];

  if (loading) {
    return (
      <ProtectedRoute requiredRole="USER">
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
      <ProtectedRoute requiredRole="USER">
        <div className="max-w-7xl mx-auto space-y-6">
          <Card className="p-8 text-center">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold mb-2">데이터 로딩 실패</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => loadDashboardData()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              다시 시도
            </Button>
          </Card>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute requiredRole="USER">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 🎯 1. 히어로 섹션 */}
        <CustomsHeroSection
          todayProcessed={stats?.clearedDeclarations || 0}
          totalDeclarations={stats?.totalDeclarations || 0}
          processingTime={processingTime?.thisMonth || 0}
        />

        {/* 📊 2. 통계 카드 섹션 */}
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">통계 현황</h2>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statsCards.map((stat, index) => (
            <StatsCard key={index} {...stat} />
          ))}
        </div>

        {/* 📈 3. 차트 섹션 */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">월별 처리 현황</h3>
            {chartData?.monthlyData ? (
              <LineChart data={chartData.monthlyData} />
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                차트 데이터 로딩 중...
              </div>
            )}
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">상태별 분포</h3>
            {chartData?.statusData ? (
              <DonutChart data={chartData.statusData} />
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                차트 데이터 로딩 중...
              </div>
            )}
          </Card>
        </div>

        {/* 🔄 4. 메인 콘텐츠 그리드 */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* 실시간 신고서 목록 */}
          <div className="lg:col-span-2">
            <RealTimeDeclarationList />
          </div>
          
          {/* 사이드 패널 */}
          <div className="space-y-6">
            {/* 알림 센터 */}
            <AlertsCard />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}