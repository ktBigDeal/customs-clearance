'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Upload, Download, Eye, Edit, Trash2, Plus, Filter, Search } from 'lucide-react';

import ReportGeneration from '@/components/report/ReportGeneration';
import ReportHistory from '@/components/report/ReportHistory';
import ReportPreview from '@/components/report/ReportPreview';

interface Report {
  id: number;
  declarationNumber: string;
  declarationType: 'IMPORT' | 'EXPORT';
  status: 'DRAFT' | 'UPDATED' | 'SUBMITTED' | 'APPROVED' | 'REJECTED';
  importerName: string;
  hsCode?: string;
  totalAmount?: number;
  createdAt: string;
  updatedAt: string;
}

export default function ReportPage() {
  const [activeTab, setActiveTab] = useState<'generate' | 'history' | 'preview'>('generate');
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [reports, setReports] = useState<Report[]>([
    {
      id: 1,
      declarationNumber: 'IMP2024001',
      declarationType: 'IMPORT',
      status: 'APPROVED',
      importerName: '한국무역주식회사',
      hsCode: '1234567890',
      totalAmount: 50000,
      createdAt: '2024-01-15T09:30:00Z',
      updatedAt: '2024-01-15T14:20:00Z'
    },
    {
      id: 2,
      declarationNumber: 'EXP2024001',
      declarationType: 'EXPORT',
      status: 'SUBMITTED',
      importerName: 'ABC Trading Co.',
      hsCode: '0987654321',
      totalAmount: 75000,
      createdAt: '2024-01-14T11:15:00Z',
      updatedAt: '2024-01-14T16:45:00Z'
    }
  ]);

  const handleReportGenerated = (newReport: Report) => {
    setReports(prev => [newReport, ...prev]);
    setActiveTab('history');
  };

  const handleReportSelect = (report: Report) => {
    setSelectedReport(report);
    setActiveTab('preview');
  };

  const handleReportUpdate = (updatedReport: Report) => {
    setReports(prev => prev.map(r => r.id === updatedReport.id ? updatedReport : r));
    setSelectedReport(updatedReport);
  };

  const handleReportDelete = (reportId: number) => {
    setReports(prev => prev.filter(r => r.id !== reportId));
    if (selectedReport?.id === reportId) {
      setSelectedReport(null);
      setActiveTab('history');
    }
  };

  const getStatusBadge = (status: Report['status']) => {
    const styles = {
      DRAFT: 'bg-gray-100 text-gray-800',
      UPDATED: 'bg-gray-100 text-gray-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800'
    };

    const labels = {
      DRAFT: '초안',
      UPDATED: '수정됨',
      SUBMITTED: '제출됨',
      APPROVED: '승인됨',
      REJECTED: '반려됨'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const getTypeLabel = (type: Report['declarationType']) => {
    return type === 'IMPORT' ? '수입신고서' : '수출신고서';
  };

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
        {activeTab === 'generate' && (
          <ReportGeneration onReportGenerated={handleReportGenerated} />
        )}

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
          <ReportPreview
            report={selectedReport}
            onReportUpdate={handleReportUpdate}
            getStatusBadge={getStatusBadge}
            getTypeLabel={getTypeLabel}
          />
        )}
      </div>

      {/* 빈 상태 메시지 */}
      {activeTab === 'history' && reports.length === 0 && (
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