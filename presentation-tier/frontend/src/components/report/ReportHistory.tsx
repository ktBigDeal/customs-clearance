'use client';

import { useState, useEffect, useMemo } from 'react';
import { declarationsApi } from '@/lib/declarations-api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Search, 
  Filter, 
  Eye, 
  Edit, 
  Trash2, 
  Download, 
  MoreHorizontal,
  Calendar,
  FileText,
  DollarSign
} from 'lucide-react';
interface Report {
  id: number;
  declarationNumber: string;
  declarationType: 'IMPORT' | 'EXPORT';
  status: 'DRAFT' | 'UPDATED' | 'SUBMITTED' | 'APPROVED' | 'REJECTED';
  importerName: string;
  totalAmount?: number;
  createdAt: string;
  updatedAt: string;
}

interface ReportHistoryProps {
  reports: Report[];
  onReportSelect: (report: Report) => void;
  onReportDelete: (reportId: number) => void;
  getStatusBadge: (status: Report['status']) => JSX.Element;
  getTypeLabel: (type: Report['declarationType']) => string;
}

export default function ReportHistory({ 
  reports, 
  onReportSelect, 
  onReportDelete, 
  getStatusBadge, 
  getTypeLabel 
}: ReportHistoryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<Report['status'] | 'ALL'>('ALL');
  const [typeFilter, setTypeFilter] = useState<Report['declarationType'] | 'ALL'>('ALL');
  const [sortBy, setSortBy] = useState<'createdAt' | 'updatedAt' | 'declarationNumber'>('createdAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiReports, setApiReports] = useState<Report[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Load reports from API
  useEffect(() => {
    load()}, []);

  function toReportForListFromBackend(src: any) {
    // details 파싱 (문자열 JSON or 이미 파싱된 객체 대응)
    let details: any = {};
    try {
      if (typeof src?.declaration_details === 'string') {
        details = JSON.parse(src.declaration_details);
      } else if (src?.rawDetails && typeof src.rawDetails === 'object') {
        details = src.rawDetails;
      }
    } catch { /* ignore */ }

    const typeVal = src.declarationType ?? src.declaration_type;
    const declarationNumber =
      src.declarationNumber ??
      src.declaration_number ??
      details['신고번호'] ??
      details['송품장부 호'] ??
      `${typeVal === 'EXPORT' ? 'EXP' : 'IMP'}${String(src.id ?? Date.now()).padStart(6, '0')}`;

    return {
      id: src.id ?? Date.now(),
      declarationNumber,
      declarationType: typeVal ?? 'IMPORT',
      status: src.status ?? 'DRAFT',
      createdAt: src.createdAt ?? src.created_at ?? new Date().toISOString(),
      updatedAt: src.updatedAt ?? src.updated_at ?? new Date().toISOString(),
      totalAmount: 0,
      importerName: '',
    };
  }
  const load = async () => {

    try {
      setLoading(true);
      setLoadError(null);

      // 1) 서버 호출
      const raw = await declarationsApi.listByUser();
      // 2) 어떤 형태로 와도 배열만 안전하게 추출
      const arr: any[] = Array.isArray(raw)
        ? raw
        : Array.isArray((raw as any)?.data)
        ? (raw as any).data
        : Array.isArray((raw as any)?.content)
        ? (raw as any).content
        : [];

      // 3) 최소 정규화 후 상태 반영
      const mapped = arr.map(toReportForListFromBackend);
      setApiReports(mapped);

      // (선택) 디버그
      console.log('[History] fetched:', { raw, count: arr.length });
    } catch (e: any) {
      setLoadError(e?.message || '목록 조회에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 필터링 및 정렬된 보고서 목록 (API 데이터 또는 prop 데이터 사용)
// API가 오면 API 우선, 없으면 props.reports 사용 (참조를 useMemo로 고정)
  const currentReports = useMemo<Report[]>(
    () => (Array.isArray(apiReports) && apiReports.length ? apiReports : (reports ?? [])),
    [apiReports, reports]
  );  
  const filteredAndSortedReports = useMemo(() => {
    const input = Array.isArray(currentReports) ? currentReports : [];

    // 보이지 않는 공백 때문에 전체 필터링되는 걸 방지
    const term = (searchTerm ?? '').trim().toLowerCase();

    const filtered = input.filter((r) => {
      const dn = (r?.declarationNumber ?? '').toLowerCase();
      const im = (r?.importerName ?? '').toLowerCase();

      const matchesSearch = term === '' || dn.includes(term) || im.includes(term);
      const matchesStatus = statusFilter === 'ALL' || r?.status === statusFilter;
      const matchesType = typeFilter === 'ALL' || r?.declarationType === typeFilter;

      return matchesSearch && matchesStatus && matchesType;
    });

    const sorted = [...filtered].sort((a, b) => {
      const pick = (x: Report) =>
        sortBy === 'declarationNumber' ? (x?.declarationNumber ?? '')
        : sortBy === 'updatedAt' ? (x?.updatedAt ?? '')
        : (x?.createdAt ?? '');

      const av = pick(a), bv = pick(b);
      return sortOrder === 'asc' ? (av > bv ? 1 : av < bv ? -1 : 0) : (av < bv ? 1 : av > bv ? -1 : 0);
    });

    // 디버그 원하면 잠깐 켜두기
    // console.log('[History] lens:', { input: input.length, filtered: filtered.length, sorted: sorted.length });
    return sorted;
  }, [currentReports, searchTerm, statusFilter, typeFilter, sortBy, sortOrder]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDelete = (reportId: number, reportNumber: string) => {
    if (window.confirm(`신고서 ${reportNumber}을(를) 정말 삭제하시겠습니까?`)) {
      onReportDelete(reportId);
    }
  };

  // 통계 데이터 계산
  const stats = {
    total: currentReports.length,
    draft: currentReports.filter(r => r.status === 'DRAFT').length,
    submitted: currentReports.filter(r => r.status === 'SUBMITTED').length,
    approved: currentReports.filter(r => r.status === 'APPROVED').length,
    rejected: currentReports.filter(r => r.status === 'REJECTED').length,
    import: currentReports.filter(r => r.declarationType === 'IMPORT').length,
    export: currentReports.filter(r => r.declarationType === 'EXPORT').length,
    totalAmount: currentReports.reduce((sum, r) => sum + (r.totalAmount || 0), 0)
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">보고서를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">⚠️ 오류가 발생했습니다</div>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={() => window.location.reload()}>새로고침</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">전체 신고서</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
            <FileText className="w-8 h-8 text-blue-600" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">승인 완료</p>
              <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
            </div>
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-green-600 font-bold">✓</span>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">수입 신고</p>
              <p className="text-2xl font-bold text-blue-600">{stats.import}</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 text-xs font-bold">IN</span>
            </div>
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">총 거래액</p>
              <p className="text-2xl font-bold">${stats.totalAmount.toLocaleString()}</p>
            </div>
            <DollarSign className="w-8 h-8 text-green-600" />
          </div>
        </Card>
      </div>

      {/* 검색 및 필터 */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="신고번호 또는 업체명으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              필터
            </Button>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="createdAt">생성일순</option>
              <option value="updatedAt">수정일순</option>
              <option value="declarationNumber">신고번호순</option>
            </select>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </Button>
          </div>
        </div>

        {/* 확장 필터 */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="ALL">전체</option>
                  <option value="DRAFT">초안</option>
                  <option value="SUBMITTED">제출됨</option>
                  <option value="APPROVED">승인됨</option>
                  <option value="REJECTED">반려됨</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">구분</label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as typeof typeFilter)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="ALL">전체</option>
                  <option value="IMPORT">수입신고서</option>
                  <option value="EXPORT">수출신고서</option>
                </select>
              </div>
              
              <div className="flex items-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('ALL');
                    setTypeFilter('ALL');
                  }}
                  className="w-full"
                >
                  초기화
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 보고서 목록 */}
      <Card>
        <div className="p-4 border-b">
          <h3 className="text-lg font-medium">
            보고서 목록 ({filteredAndSortedReports.length}개)
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  신고번호
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  구분
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  업체명
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  금액
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  생성일
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  작업
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedReports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {report.declarationNumber ?? ''}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      report.declarationType === 'IMPORT' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {getTypeLabel(report.declarationType)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{report.importerName}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(report.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {report.totalAmount ? `$${report.totalAmount.toLocaleString()}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>{formatDate(report.createdAt)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onReportSelect(report)}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-green-600 hover:text-green-700"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-600 hover:text-gray-700"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(report?.id, report?.declarationNumber ?? '')}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredAndSortedReports.length === 0 && (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">조건에 맞는 보고서가 없습니다.</p>
          </div>
        )}
      </Card>
    </div>
  );
}