'use client';

import { Users, FileText, Activity, AlertTriangle } from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import StatsCard from '@/components/admin/StatsCard';
import ChartSection from '@/components/admin/ChartSection';
import ActivityLog from '@/components/admin/ActivityLog';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function AdminDashboardPage() {
  const { t } = useLanguage();

  const stats = [
    {
      title: t('admin.activeUsers'),
      value: '1,234',
      change: '+12%',
      changeType: 'increase' as const,
      icon: Users,
    },
    {
      title: t('admin.processedDocs'),
      value: '8,567',
      change: '+8%',
      changeType: 'increase' as const,
      icon: FileText,
    },
    {
      title: t('admin.apiCallsToday'),
      value: '24,891',
      change: '+23%',
      changeType: 'increase' as const,
      icon: Activity,
    },
    {
      title: t('admin.errorCount'),
      value: '45',
      change: '-15%',
      changeType: 'decrease' as const,
      icon: AlertTriangle,
    },
  ];

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <DashboardLayout isAdmin={true}>
        <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-foreground">
            {t('admin.dashboard')}
          </h1>
          <p className="text-muted-foreground">
            시스템 전반적인 상태와 성능 지표를 모니터링하세요
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <StatsCard
              key={stat.title}
              title={stat.title}
              value={stat.value}
              icon={stat.icon}
              change={stat.change}
              changeType={stat.changeType}
            />
          ))}
        </div>

        {/* Charts and Activity */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Chart Section - Takes 2 columns */}
          <div className="lg:col-span-2">
            <ChartSection />
          </div>

          {/* Activity Log - Takes 1 column */}
          <div className="lg:col-span-1">
            <ActivityLog />
          </div>
        </div>
        </div>
      
      </DashboardLayout>
    </ProtectedRoute>
  );
}