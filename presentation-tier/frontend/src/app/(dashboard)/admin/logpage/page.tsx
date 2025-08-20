'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, Download, RefreshCw, Calendar, User, Activity, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { adminService, SystemLog, LogStats } from '@/services/admin.service';

export default function LogsPage() {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [stats, setStats] = useState<LogStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [selectedSource, setSelectedSource] = useState('all');
  const [dateFilter, setDateFilter] = useState('today');
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(20);

  // 삭제 모달 상태
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteType, setDeleteType] = useState<'all' | 'old'>('all');
  const [deleteDays, setDeleteDays] = useState(30);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadLogs = async () => {
    try {
      setIsLoading(true);
      const response = await adminService.getLogs({
        keyword: searchTerm,
        level: selectedLevel,
        source: selectedSource,
        dateFilter,
        page: currentPage,
        size: pageSize
      });
      setLogs(response.logs);
      setTotalCount(response.totalCount || 0);
      setTotalPages(response.totalPages || 0);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await adminService.getLogStats(dateFilter);
      setStats(statsData);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    setCurrentPage(0); // 검색 조건 변경시 첫 페이지로
  }, [searchTerm, selectedLevel, selectedSource, dateFilter]);

  useEffect(() => {
    loadLogs();
    loadStats();
  }, [searchTerm, selectedLevel, selectedSource, dateFilter, currentPage]);

  const handleExportLogs = () => {
    adminService.exportLogsToCSV(logs);
  };

  const handleDeleteAllLogs = () => {
    setDeleteType('all');
    setShowDeleteModal(true);
  };

  const handleDeleteOldLogs = () => {
    setDeleteType('old');
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    try {
      setIsDeleting(true);
      let result;
      
      if (deleteType === 'all') {
        result = await adminService.deleteAllLogs();
      } else {
        result = await adminService.deleteOldLogs(deleteDays);
      }
      
      alert(`${result.deletedCount}개의 로그가 삭제되었습니다.`);
      setCurrentPage(0); // 첫 페이지로 이동
      await loadLogs(); // 목록 새로고침
      await loadStats(); // 통계 새로고침
      setShowDeleteModal(false);
    } catch (error) {
      console.error(error);
      alert('로그 삭제 중 오류가 발생했습니다.');
    } finally {
      setIsDeleting(false);
    }
  };

  const getLevelColor = (level: string) => adminService.getLevelColorClass(level);

  const levels = ['all', 'ERROR', 'WARN', 'INFO', 'DEBUG'];
  const sources = ['all', 'AUTH', 'SYSTEM', 'API', 'DOCUMENT', 'CHAT'];

  return (
    <ProtectedRoute requiredRole="ADMIN">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold">시스템 로그 조회</h1>
            <p className="text-muted-foreground">시스템 활동 및 오류 로그를 조회하고 분석하세요</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadLogs} disabled={isLoading} className="gap-2">
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
            <Button onClick={handleExportLogs} className="gap-2">
              <Download className="w-4 h-4" />
              로그 내보내기
            </Button>
            <Button variant="outline" onClick={handleDeleteOldLogs} className="gap-2" disabled={isLoading}>
              <Trash2 className="w-4 h-4" />
              오래된 로그 삭제
            </Button>
            <Button variant="destructive" onClick={handleDeleteAllLogs} className="gap-2" disabled={isLoading}>
              <Trash2 className="w-4 h-4" />
              전체 로그 삭제
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-5 gap-4">
            <div className="relative xl:col-span-2">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="메시지, 사용자명, 소스로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <select value={selectedLevel} onChange={(e) => setSelectedLevel(e.target.value)} className="px-3 py-2 border rounded-lg">
              {levels.map(level => (
                <option key={level} value={level}>{level === 'all' ? '모든 레벨' : level}</option>
              ))}
            </select>

            <select value={selectedSource} onChange={(e) => setSelectedSource(e.target.value)} className="px-3 py-2 border rounded-lg">
              {sources.map(source => (
                <option key={source} value={source}>{source === 'all' ? '모든 소스' : source}</option>
              ))}
            </select>

            <select value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="px-3 py-2 border rounded-lg">
              <option value="today">오늘</option>
              <option value="week">이번 주</option>
              <option value="month">이번 달</option>
              <option value="all">전체 기간</option>
            </select>
          </div>
        </Card>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4"><p>전체 로그: {stats.totalLogs}</p></Card>
            <Card className="p-4"><p>에러: {stats.errorCount}</p></Card>
            <Card className="p-4"><p>경고: {stats.warnCount}</p></Card>
            <Card className="p-4"><p>정보: {stats.infoCount}</p></Card>
          </div>
        )}

        {/* Logs Table */}
        <Card className="overflow-hidden">
          <div className="p-4 border-b">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">
                시스템 로그 ({totalCount.toLocaleString()}개)
              </h3>
              <div className="text-sm text-gray-500">
                페이지 {currentPage + 1} / {totalPages} ({pageSize}개씩 표시)
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            {isLoading ? (
              <div className="flex justify-center py-12">로딩 중...</div>
            ) : logs.length > 0 ? (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">시간</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">레벨</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">소스</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">메시지</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">사용자</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">IP 주소</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td className="px-6 py-4 text-sm">{new Date(log.timestamp).toLocaleString('ko-KR')}</td>
                      <td className="px-6 py-4"><span className={`px-2 py-1 rounded-full text-xs ${getLevelColor(log.level)}`}>{log.level}</span></td>
                      <td className="px-6 py-4 text-sm">{log.source}</td>
                      <td className="px-6 py-4 text-sm">{log.message}</td>
                      <td className="px-6 py-4 text-sm">{log.userName || '-'}</td>
                      <td className="px-6 py-4 text-sm">{log.ipAddress || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-12">로그가 없습니다</div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="p-4 border-t bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  전체 {totalCount.toLocaleString()}개 중 {(currentPage * pageSize) + 1}-{Math.min((currentPage + 1) * pageSize, totalCount)}번째 표시
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(0)}
                    disabled={currentPage === 0}
                  >
                    처음
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 0}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    이전
                  </Button>
                  
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;
                      if (totalPages <= 5) {
                        pageNum = i;
                      } else if (currentPage <= 2) {
                        pageNum = i;
                      } else if (currentPage >= totalPages - 3) {
                        pageNum = totalPages - 5 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      
                      return (
                        <Button
                          key={pageNum}
                          variant={currentPage === pageNum ? "default" : "outline"}
                          size="sm"
                          onClick={() => setCurrentPage(pageNum)}
                          className="w-8 h-8 p-0"
                        >
                          {pageNum + 1}
                        </Button>
                      );
                    })}
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage >= totalPages - 1}
                  >
                    다음
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(totalPages - 1)}
                    disabled={currentPage >= totalPages - 1}
                  >
                    마지막
                  </Button>
                </div>
              </div>
            </div>
          )}
        </Card>

        {/* 삭제 확인 모달 */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-semibold mb-4">
                {deleteType === 'all' ? '전체 로그 삭제' : '오래된 로그 삭제'}
              </h3>
              
              <div className="mb-6">
                {deleteType === 'all' ? (
                  <div>
                    <p className="text-sm text-gray-600 mb-2">
                      정말로 모든 시스템 로그를 삭제하시겠습니까?
                    </p>
                    <div className="bg-red-50 border border-red-200 rounded-md p-3">
                      <p className="text-red-700 text-sm font-medium">
                        ⚠️ 주의: 이 작업은 되돌릴 수 없습니다.
                      </p>
                      <p className="text-red-600 text-xs mt-1">
                        전체 {totalCount.toLocaleString()}개의 로그가 영구적으로 삭제됩니다.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      삭제할 로그 기간 (일)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={deleteDays}
                      onChange={(e) => setDeleteDays(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="30"
                    />
                    <p className="text-sm text-gray-600 mt-2">
                      {deleteDays}일 이전의 로그가 삭제됩니다.
                    </p>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mt-3">
                      <p className="text-yellow-700 text-sm font-medium">
                        ⚠️ 주의: 이 작업은 되돌릴 수 없습니다.
                      </p>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowDeleteModal(false)}
                  disabled={isDeleting}
                >
                  취소
                </Button>
                <Button
                  variant="destructive"
                  onClick={confirmDelete}
                  disabled={isDeleting}
                  className="gap-2"
                >
                  {isDeleting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      삭제 중...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      {deleteType === 'all' ? '전체 삭제' : '오래된 로그 삭제'}
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
