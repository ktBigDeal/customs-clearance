'use client';

import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { Search, Plus, Trash2, Download, Eye, Filter, Calendar, FileText, Archive, User, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { declarationsApi } from '@/lib/declarations-api';
import ReportPreview from '@/components/report/ReportPreview';

// Report 타입을 Document로 변경하여 관리자용으로 확장
export interface Document {
  id: number;
  declarationNumber: string;
  declarationType: 'IMPORT' | 'EXPORT';
  status: 'DRAFT' | 'UPDATED' | 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED';
  createdAt: string;
  updatedAt: string;
  // 관리자용 추가 필드
  userId?: number;
  userName?: string;
  userEmail?: string;
}

// 백엔드 DTO를 Document로 매핑
function mapDtoToDocument(dto: any): Document {
  return {
    id: dto?.id ?? dto?.declarationId ?? 0,
    declarationNumber: dto?.declarationNumber ?? dto?.number ?? '-',
    declarationType: (dto?.declarationType ?? dto?.type ?? 'IMPORT') as Document['declarationType'],
    status: (dto?.status ?? 'DRAFT') as Document['status'],
    createdAt: dto?.createdAt ?? dto?.created_at ?? new Date().toISOString(),
    updatedAt: dto?.updatedAt ?? dto?.updated_at ?? dto?.createdAt ?? new Date().toISOString(),
    // 사용자 정보 (백엔드에서 제공되는 경우)
    userId: dto?.userId ?? dto?.user_id,
    userName: dto?.userName ?? dto?.user_name ?? '익명',
    userEmail: dto?.userEmail ?? dto?.user_email ?? '',
  };
}

export default function DocumentsPage() {
  const { t } = useLanguage();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'all' | 'import' | 'export'>('all');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // 모든 사용자의 문서(신고서) 조회
  const {
    data: documents = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<Document[]>({
    queryKey: ['admin-documents'],
    queryFn: async () => {
      // 관리자용 API 엔드포인트 (모든 사용자 문서 조회)
      const list = await declarationsApi.listAll();
      // 예시 파일 3개 제거 (ID: 1, 2, 3)
      const filteredList = (list ?? []).filter(item => 
        item.id !== 1 && item.id !== 2 && item.id !== 3
      );
      return filteredList.map(mapDtoToDocument);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (documentId: number) => declarationsApi.remove(documentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin-documents'] });
    },
  });

  // 필터링된 문서 목록
  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => {
      const matchesSearch = 
        doc.declarationNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.userName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.userEmail?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesTab = activeTab === 'all' || doc.declarationType.toLowerCase() === activeTab;
      const matchesStatus = selectedStatus === 'all' || doc.status === selectedStatus;
      
      return matchesSearch && matchesTab && matchesStatus;
    });
  }, [documents, searchTerm, activeTab, selectedStatus]);

  // 상태별 색상 반환
  const getStatusBadge = (status: Document['status']) => {
    const styles: Record<Document['status'], string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      UPDATED: 'bg-blue-100 text-blue-800',
      SUBMITTED: 'bg-yellow-100 text-yellow-800',
      UNDER_REVIEW: 'bg-purple-100 text-purple-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
    };

    const labels: Record<Document['status'], string> = {
      DRAFT: '초안',
      UPDATED: '수정됨',
      SUBMITTED: '제출됨',
      UNDER_REVIEW: '검토중',
      APPROVED: '승인됨',
      REJECTED: '반려됨',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const getTypeLabel = (type: Document['declarationType']) => (type === 'IMPORT' ? '수입신고서' : '수출신고서');

  // 신고서 상세 보기
  const handleDocumentView = (document: Document) => {
    setSelectedDocument(document);
    setIsDetailModalOpen(true);
  };

  // 신고서 다운로드 (XML)
  const handleDocumentDownload = async (document: Document) => {
    try {
      await declarationsApi.downloadXml(document.id, {
        docType: document.declarationType.toLowerCase() as 'import' | 'export'
      });
    } catch (error) {
      console.error('신고서 다운로드 실패:', error);
      alert('신고서 다운로드에 실패했습니다.');
    }
  };

  // 신고서 삭제
  const handleDocumentDelete = (documentId: number) => {
    if (confirm('정말로 이 신고서를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      deleteMutation.mutate(documentId);
    }
  };

  // 모달 닫기
  const closeDetailModal = () => {
    setIsDetailModalOpen(false);
    setSelectedDocument(null);
  };

  const statuses = ['all', 'DRAFT', 'UPDATED', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED'];

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">문서 관리</h1>
            <p className="text-gray-600 mt-1">모든 사용자의 신고서 문서를 관리하세요</p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant={activeTab === 'all' ? 'default' : 'outline'}
              onClick={() => setActiveTab('all')}
              className="flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              전체 문서
            </Button>
            <Button
              variant={activeTab === 'import' ? 'default' : 'outline'}
              onClick={() => setActiveTab('import')}
            >
              수입신고서
            </Button>
            <Button
              variant={activeTab === 'export' ? 'default' : 'outline'}
              onClick={() => setActiveTab('export')}
            >
              수출신고서
            </Button>
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('all')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'all'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              전체 문서 ({documents.length})
            </button>
            <button
              onClick={() => setActiveTab('import')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'import'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              수입신고서 ({documents.filter(d => d.declarationType === 'IMPORT').length})
            </button>
            <button
              onClick={() => setActiveTab('export')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'export'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              수출신고서 ({documents.filter(d => d.declarationType === 'EXPORT').length})
            </button>
          </nav>
        </div>

        {/* 통계 */}
        {!isLoading && !isError && documents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">전체 문서</p>
                  <p className="text-2xl font-bold text-gray-900">{documents.length}</p>
                </div>
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">수입신고서</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {documents.filter(d => d.declarationType === 'IMPORT').length}
                  </p>
                </div>
                <span className="text-2xl">📥</span>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">수출신고서</p>
                  <p className="text-2xl font-bold text-green-600">
                    {documents.filter(d => d.declarationType === 'EXPORT').length}
                  </p>
                </div>
                <span className="text-2xl">📤</span>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">승인된 문서</p>
                  <p className="text-2xl font-bold text-green-600">
                    {documents.filter(d => d.status === 'APPROVED').length}
                  </p>
                </div>
                <span className="text-2xl">✅</span>
              </div>
            </Card>
          </div>
        )}

        {/* 검색 및 필터 */}
        <Card className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="신고서 번호, 사용자명, 이메일로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[120px]"
            >
              {statuses.map(status => (
                <option key={status} value={status}>
                  {status === 'all' ? '전체 상태' : 
                   status === 'DRAFT' ? '초안' :
                   status === 'UPDATED' ? '수정됨' :
                   status === 'SUBMITTED' ? '제출됨' :
                   status === 'UNDER_REVIEW' ? '검토중' :
                   status === 'APPROVED' ? '승인됨' : '반려됨'}
                </option>
              ))}
            </select>
          </div>
        </Card>

        {/* 문서 목록 */}
        <div className="mt-6">
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      신고서 정보
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      사용자 정보
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      생성일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      최종 수정일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredDocuments.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 text-2xl mr-3">
                            {doc.declarationType === 'IMPORT' ? '📥' : '📤'}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {doc.declarationNumber}
                            </div>
                            <div className="text-sm text-gray-500">
                              {getTypeLabel(doc.declarationType)}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 w-8 h-8 mr-3">
                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                              <User className="w-4 h-4 text-blue-600" />
                            </div>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {doc.userName || '익명'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {doc.userEmail || 'ID: ' + doc.userId}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          {new Date(doc.createdAt).toLocaleDateString('ko-KR', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(doc.createdAt).toLocaleTimeString('ko-KR', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          {new Date(doc.updatedAt).toLocaleDateString('ko-KR', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(doc.updatedAt).toLocaleTimeString('ko-KR', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(doc.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-blue-600 hover:text-blue-800"
                            onClick={() => handleDocumentView(doc)}
                            title="신고서 상세보기"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-green-600 hover:text-green-800"
                            onClick={() => handleDocumentDownload(doc)}
                            title="신고서 다운로드 (XML)"
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-red-600 hover:text-red-800"
                            onClick={() => handleDocumentDelete(doc.id)}
                            title="신고서 삭제"
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
          </Card>
        </div>

        {/* 로딩/에러/빈 상태 */}
        {isLoading && (
          <Card className="p-8 text-center">
            <p className="text-gray-600">문서 목록을 불러오는 중…</p>
          </Card>
        )}

        {isError && (
          <Card className="p-8 text-center">
            <p className="text-red-600">문서 목록 조회 중 오류가 발생했습니다.</p>
            <Button className="mt-3" onClick={() => refetch()}>
              다시 시도
            </Button>
          </Card>
        )}

        {!isLoading && !isError && filteredDocuments.length === 0 && (
          <Card className="p-8 text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">문서가 없습니다</h3>
            <p className="text-gray-500 mb-4">
              {searchTerm || selectedStatus !== 'all' 
                ? '검색 조건에 맞는 문서가 없습니다' 
                : '생성된 신고서 문서가 없습니다'
              }
            </p>
          </Card>
        )}

        {/* 신고서 상세보기 모달 - Portal을 사용하여 body에 직접 렌더링 */}
        {isDetailModalOpen && selectedDocument && typeof window !== 'undefined' &&
          createPortal(
            <div 
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4"
              onClick={closeDetailModal}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                margin: 0,
                zIndex: 9999
              }}
            >
              <div 
                className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[95vh] overflow-hidden mx-auto"
                onClick={(e) => e.stopPropagation()}
                style={{ margin: '0 auto' }}
              >
                {/* 모달 헤더 */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">
                      신고서 미리보기 - {selectedDocument.userName || '익명'}
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                      {selectedDocument.declarationNumber} • 관리자 보기
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={closeDetailModal}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </Button>
                </div>

                {/* 모달 내용 - ReportPreview 사용 */}
                <div className="overflow-y-auto max-h-[calc(95vh-80px)] p-4 bg-gray-50">
                  <ReportPreview
                    report={{
                      id: selectedDocument.id,
                      declarationNumber: selectedDocument.declarationNumber,
                      declarationType: selectedDocument.declarationType,
                      status: selectedDocument.status,
                      createdAt: selectedDocument.createdAt,
                      updatedAt: selectedDocument.updatedAt,
                    }}
                    getStatusBadge={getStatusBadge}
                    getTypeLabel={getTypeLabel}
                    isAdminView={true}
                  />
                </div>
              </div>
            </div>,
            document.body
          )
        }
        </div>
    </ProtectedRoute>
  );
}