'use client';

import {
  BarChart3,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Plus,
  Eye,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function DashboardPage() {
  const { t } = useLanguage();
  
  // Mock data for dashboard
  const stats = [
    {
      title: t('dashboard.stats.totalDeclarations'),
      value: '1,234',
      change: '+12%',
      trend: 'up',
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: t('dashboard.stats.pendingDeclarations'),
      value: '23',
      change: '-5%',
      trend: 'down',
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: t('dashboard.stats.approvedDeclarations'),
      value: '1,156',
      change: '+8%',
      trend: 'up',
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: t('dashboard.stats.rejectedDeclarations'),
      value: '55',
      change: '+2%',
      trend: 'up',
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
  ];

  const recentDeclarations = [
    {
      id: 'DEC-2024-001',
      company: '(주)무역회사',
      type: 'IMPORT',
      status: 'UNDER_REVIEW',
      date: '2024-01-15',
      value: '₩125,000,000',
    },
    {
      id: 'DEC-2024-002',
      company: '글로벌 익스포트',
      type: 'EXPORT',
      status: 'APPROVED',
      date: '2024-01-14',
      value: '₩89,500,000',
    },
    {
      id: 'DEC-2024-003',
      company: '한국 트레이딩',
      type: 'IMPORT',
      status: 'PENDING_DOCUMENTS',
      date: '2024-01-14',
      value: '₩201,750,000',
    },
    {
      id: 'DEC-2024-004',
      company: '동서무역상사',
      type: 'EXPORT',
      status: 'CLEARED',
      date: '2024-01-13',
      value: '₩67,800,000',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
      case 'CLEARED':
        return 'bg-green-100 text-green-800';
      case 'UNDER_REVIEW':
        return 'bg-blue-100 text-blue-800';
      case 'PENDING_DOCUMENTS':
        return 'bg-orange-100 text-orange-800';
      case 'REJECTED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return t('dashboard.status.approved');
      case 'CLEARED':
        return t('dashboard.status.cleared');
      case 'UNDER_REVIEW':
        return t('dashboard.status.underReview');
      case 'PENDING_DOCUMENTS':
        return t('dashboard.status.pendingDocuments');
      case 'REJECTED':
        return t('dashboard.status.rejected');
      default:
        return status;
    }
  };

  const getTypeText = (type: string) => {
    switch (type) {
      case 'IMPORT':
        return t('dashboard.type.import');
      case 'EXPORT':
        return t('dashboard.type.export');
      default:
        return type;
    }
  };

  return (
    <ProtectedRoute requiredRole="USER">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-foreground">
            {t('dashboard.title')}
          </h1>
          <p className="text-muted-foreground">
            {t('dashboard.subtitle')}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.title} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      {stat.title}
                    </p>
                    <div className="flex items-center gap-2">
                      <p className="text-2xl font-bold">{stat.value}</p>
                      <span
                        className={`text-xs font-medium px-2 py-1 rounded-full ${
                          stat.trend === 'up'
                            ? 'bg-green-100 text-green-600'
                            : 'bg-red-100 text-red-600'
                        }`}
                      >
                        {stat.change}
                      </span>
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Recent Declarations */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  {t('dashboard.recentDeclarations')}
                </h2>
                <Button variant="outline" size="sm">
                  <Eye className="h-4 w-4 mr-2" />
                  {t('dashboard.viewAllDeclarations')}
                </Button>
              </div>
              <div className="space-y-4">
                {recentDeclarations.map((declaration) => (
                  <div
                    key={declaration.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm">
                          {declaration.id}
                        </p>
                        <span
                          className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusColor(
                            declaration.status
                          )}`}
                        >
                          {getStatusText(declaration.status)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {declaration.company}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {getTypeText(declaration.type)} •{' '}
                        {declaration.date}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-sm">
                        {declaration.value}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="space-y-6">
            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-4">
                {t('dashboard.quickActions')}
              </h2>
              <div className="space-y-3">
                <Button className="w-full justify-start" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  {t('dashboard.newDeclaration')}
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  {t('dashboard.viewDeclarations')}
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  {t('dashboard.monthlyReport')}
                </Button>
              </div>
            </Card>

            {/* Processing Time */}
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold">
                  {t('dashboard.avgProcessingTime')}
                </h2>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    {t('dashboard.thisMonth')}
                  </span>
                  <span className="font-semibold">2.3일</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    {t('dashboard.lastMonth')}
                  </span>
                  <span className="font-semibold text-muted-foreground">
                    2.8일
                  </span>
                </div>
                <div className="pt-2 border-t">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500"></div>
                    <span className="text-sm text-green-600 font-medium">
                      18% {t('dashboard.improvement')}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}