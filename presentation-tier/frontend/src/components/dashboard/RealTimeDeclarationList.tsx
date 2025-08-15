'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Eye, RefreshCw } from 'lucide-react';
import { 
  declarationsApi, 
  getStatusKorean, 
  getTypeKorean, 
  getStatusColorClass,
  formatDate,
  formatCurrency 
} from '@/lib/declarations-api';
import type { DeclarationResponseDto } from '@/types/declaration';

export function RealTimeDeclarationList() {
  const [declarations, setDeclarations] = useState<DeclarationResponseDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDeclarations = async () => {
    try {
      setError(null);
      const data = await declarationsApi.getRecent(5);
      setDeclarations(data);
    } catch (err: any) {
      console.error('Failed to fetch declarations:', err);
      setError(err.message || '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDeclarations();
  };

  useEffect(() => {
    fetchDeclarations();

    // 30초마다 자동 새로고침
    const interval = setInterval(fetchDeclarations, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">최근 신고서</h2>
        </div>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                </div>
                <div className="h-4 bg-gray-200 rounded w-20"></div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">최근 신고서</h2>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            재시도
          </Button>
        </div>
        <div className="text-center py-8">
          <div className="text-red-500 mb-2">⚠️</div>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold">최근 신고서</h2>
          <p className="text-sm text-muted-foreground">실시간 업데이트</p>
        </div>
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

      {declarations.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-4xl mb-2">📋</div>
          <p className="text-muted-foreground">등록된 신고서가 없습니다</p>
          <p className="text-sm text-muted-foreground mt-1">
            새로운 신고서를 작성해보세요
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {declarations.map((declaration) => (
            <div
              key={declaration.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
            >
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-sm">
                    {declaration.declarationNumber || `DEC-${declaration.id}`}
                  </p>
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusColorClass(
                      declaration.status
                    )}`}
                  >
                    {getStatusKorean(declaration.status)}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {/* 회사명이 있다면 표시, 없으면 사용자 정보 */}
                  신고서 ID: {declaration.id}
                </p>
                <p className="text-xs text-muted-foreground">
                  {getTypeKorean(declaration.declarationType)} •{' '}
                  {formatDate(declaration.createdAt)}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-sm">
                  {declaration.totalValue ? formatCurrency(declaration.totalValue) : '-'}
                </p>
                <Button variant="ghost" size="sm" className="mt-1">
                  <Eye className="h-3 w-3 mr-1" />
                  보기
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}