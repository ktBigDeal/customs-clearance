'use client';

import { useEffect, useMemo, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Plus } from 'lucide-react';
import ReportGeneration from '@/components/report/ReportGeneration';
import ReportHistory from '@/components/report/ReportHistory';
import ReportPreview from '@/components/report/ReportPreview';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { declarationsApi } from '@/lib/declarations-api';
import { useAuth } from '@/contexts/AuthContext';

// ====== Types kept minimal to match components ======
export interface Report {
  id: number;
  declarationNumber: string;
  declarationType: 'IMPORT' | 'EXPORT';
  status: 'DRAFT' | 'UPDATED' | 'SUBMITTED' | 'APPROVED' | 'REJECTED';
  createdAt: string;
  updatedAt: string;
}

// Map backend DTO -> Report used by UI components
function mapDtoToReport(dto: any): Report {
  return {
    id: dto?.id ?? dto?.declarationId ?? 0,
    declarationNumber: dto?.declarationNumber ?? dto?.number ?? '-',
    declarationType: (dto?.declarationType ?? dto?.type ?? 'IMPORT') as Report['declarationType'],
    status: (dto?.status ?? 'DRAFT') as Report['status'],
    createdAt: dto?.createdAt ?? dto?.created_at ?? new Date().toISOString(),
    updatedAt: dto?.updatedAt ?? dto?.updated_at ?? dto?.createdAt ?? new Date().toISOString(),
  };
}

export default function ReportPage() {
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'generate' | 'history' | 'preview'>('generate');
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  // ====== Queries ======
  const {
    data: reports = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<Report[]>({
    queryKey: ['reports'],
    queryFn: async () => {
      const list = await declarationsApi.listByUser();
      return (list ?? []).map(mapDtoToReport);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (reportId: number) => declarationsApi.remove(reportId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });

  // Keep preview tab sane if current selection disappears
  useEffect(() => {
    if (activeTab === 'preview' && selectedReport) {
      const exists = reports.find((r) => r.id === selectedReport.id);
      if (!exists) {
        setSelectedReport(null);
        setActiveTab('history');
      }
    }
  }, [reports, activeTab, selectedReport]);

  // ====== Callbacks ======
  const handleReportGenerated = (newReport: Report) => {
    // After creation, refresh list and show preview of the new one
    queryClient.invalidateQueries({ queryKey: ['reports'] });
    setSelectedReport(newReport);
    setActiveTab('preview');
  };

  const handleReportSelect = (report: Report) => {
    setSelectedReport(report);
    setActiveTab('preview');
  };

  const handleReportDelete = (reportId: number) => {
    deleteMutation.mutate(reportId);
  };

  const handleReportUpdate = (updatedReport: Report) => {
    // Optimistically update cache item shape
    queryClient.setQueryData<Report[]>(['reports'], (old) =>
      (old ?? []).map((r) => (r.id === updatedReport.id ? { ...r, ...updatedReport } : r))
    );
    setSelectedReport(updatedReport);
  };

  const getStatusBadge = (status: Report['status']) => {
    const styles: Record<Report['status'], string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      UPDATED: 'bg-gray-100 text-gray-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
    };

    const labels: Record<Report['status'], string> = {
      DRAFT: '초안',
      UPDATED: '수정됨',
      SUBMITTED: '제출됨',
      APPROVED: '승인됨',
      REJECTED: '반려됨',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const getTypeLabel = (type: Report['declarationType']) => (type === 'IMPORT' ? '수입신고서' : '수출신고서');

  // ====== Render ======
  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">보고서 관리</h1>
          <p className="text-gray-600 mt-1">수출입 신고서를 생성하고 관리하세요</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant={activeTab === 'generate' ? 'default' : 'outline'}
            onClick={() => setActiveTab('generate')}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            신규 생성
          </Button>
          <Button
            variant={activeTab === 'history' ? 'default' : 'outline'}
            onClick={() => setActiveTab('history')}
            className="flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            목록 보기
          </Button>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('generate')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'generate'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            보고서 생성
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            보고서 목록 ({reports.length})
          </button>
          {selectedReport && (
            <button
              onClick={() => setActiveTab('preview')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'preview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              보고서 미리보기
            </button>
          )}
        </nav>
      </div>

      {/* 탭 내용 */}
      <div className="mt-6">
        {activeTab === 'generate' && <ReportGeneration onReportGenerated={handleReportGenerated} />}

        {activeTab === 'history' && (
          <ReportHistory
            reports={reports}
            onReportSelect={handleReportSelect}
            onReportDelete={handleReportDelete}
            getStatusBadge={getStatusBadge}
            getTypeLabel={getTypeLabel}
          />
        )}

        {activeTab === 'preview' && selectedReport && (
          <ReportPreview report={selectedReport} getStatusBadge={getStatusBadge} getTypeLabel={getTypeLabel} />)
        }
      </div>

      {/* 로딩/에러/빈 상태 */}
      {isLoading && (
        <Card className="p-8 text-center">
          <p className="text-gray-600">목록을 불러오는 중…</p>
        </Card>
      )}

      {isError && (
        <Card className="p-8 text-center">
          <p className="text-red-600">목록 조회 중 오류가 발생했습니다.</p>
          <Button className="mt-3" onClick={() => refetch()}>
            다시 시도
          </Button>
        </Card>
      )}

      {!isLoading && !isError && activeTab === 'history' && reports.length === 0 && (
        <Card className="p-8 text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">보고서가 없습니다</h3>
          <p className="text-gray-500 mb-4">첫 번째 보고서를 생성해보세요</p>
          <Button onClick={() => setActiveTab('generate')} className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            보고서 생성하기
          </Button>
        </Card>
      )}
    </div>
  );
}
