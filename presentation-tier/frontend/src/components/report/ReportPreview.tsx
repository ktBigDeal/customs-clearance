'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Edit, 
  Save, 
  Download, 
  FileText, 
  Calendar, 
  Building, 
  Package,
  DollarSign,
  Hash,
  X,
  Check
} from 'lucide-react';

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
  extractedData?: {
    companyInfo?: {
      name: string;
      address: string;
      businessNumber: string;
    };
    goods?: Array<{
      description: string;
      quantity: number;
      unitPrice: number;
      hsCode: string;
    }>;
    invoice?: {
      invoiceNumber: string;
      date: string;
      amount: number;
    };
  };
}

interface ReportPreviewProps {
  report: Report;
  onReportUpdate: (updatedReport: Report) => void;
  getStatusBadge: (status: Report['status']) => JSX.Element;
  getTypeLabel: (type: Report['declarationType']) => string;
}

export default function ReportPreview({ 
  report, 
  onReportUpdate, 
  getStatusBadge, 
  getTypeLabel 
}: ReportPreviewProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedReport, setEditedReport] = useState<Report>(report);
  const [isSaving, setIsSaving] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // 실제 구현시 API 호출
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const updatedReport = {
        ...editedReport,
        updatedAt: new Date().toISOString()
      };
      
      onReportUpdate(updatedReport);
      setIsEditing(false);
    } catch (error) {
      console.error('저장 실패:', error);
      alert('저장 중 오류가 발생했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedReport(report);
    setIsEditing(false);
  };

  const handleInputChange = (field: keyof Report, value: any) => {
    setEditedReport(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNestedInputChange = (
    section: 'companyInfo' | 'invoice',
    field: string,
    value: any
  ) => {
    setEditedReport(prev => ({
      ...prev,
      extractedData: {
        ...prev.extractedData,
        [section]: {
          ...prev.extractedData?.[section],
          [field]: value
        }
      }
    }));
  };

  const downloadReport = () => {
    // 실제 구현시 PDF 다운로드 API 호출
    alert('PDF 다운로드 기능은 추후 구현됩니다.');
  };

  const currentReport = isEditing ? editedReport : report;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 헤더 */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">{currentReport.declarationNumber}</h1>
              <p className="text-gray-600">
                {getTypeLabel(currentReport.declarationType)} • {getStatusBadge(currentReport.status)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {!isEditing ? (
              <>
                <Button
                  variant="outline"
                  onClick={downloadReport}
                  className="flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  PDF 다운로드
                </Button>
                <Button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2"
                >
                  <Edit className="w-4 h-4" />
                  편집하기
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  className="flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  취소
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2"
                >
                  {isSaving ? (
                    <>저장 중...</>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      저장
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </div>

        {/* 메타 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="w-4 h-4" />
            <span>생성일: {formatDate(currentReport.createdAt)}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="w-4 h-4" />
            <span>수정일: {formatDate(currentReport.updatedAt)}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Hash className="w-4 h-4" />
            <span>ID: {currentReport.id}</span>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 기본 정보 */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Building className="w-5 h-5" />
            기본 정보
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">신고번호</label>
              {isEditing ? (
                <input
                  type="text"
                  value={currentReport.declarationNumber}
                  onChange={(e) => handleInputChange('declarationNumber', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 py-2">{currentReport.declarationNumber}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">수입업체명</label>
              {isEditing ? (
                <input
                  type="text"
                  value={currentReport.importerName}
                  onChange={(e) => handleInputChange('importerName', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <p className="text-gray-900 py-2">{currentReport.importerName}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">신고 구분</label>
              {isEditing ? (
                <select
                  value={currentReport.declarationType}
                  onChange={(e) => handleInputChange('declarationType', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="IMPORT">수입</option>
                  <option value="EXPORT">수출</option>
                </select>
              ) : (
                <p className="text-gray-900 py-2">{getTypeLabel(currentReport.declarationType)}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
              {isEditing ? (
                <select
                  value={currentReport.status}
                  onChange={(e) => handleInputChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="DRAFT">초안</option>
                  <option value="SUBMITTED">제출됨</option>
                  <option value="APPROVED">승인됨</option>
                  <option value="REJECTED">반려됨</option>
                </select>
              ) : (
                <div className="py-2">{getStatusBadge(currentReport.status)}</div>
              )}
            </div>
          </div>
        </Card>

        {/* 상품 정보 */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Package className="w-5 h-5" />
            상품 정보
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">HS코드</label>
              {isEditing ? (
                <input
                  type="text"
                  value={currentReport.hsCode || ''}
                  onChange={(e) => handleInputChange('hsCode', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="HS코드를 입력하세요"
                />
              ) : (
                <p className="text-gray-900 py-2">{currentReport.hsCode || '미입력'}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">총 금액 (USD)</label>
              {isEditing ? (
                <input
                  type="number"
                  value={currentReport.totalAmount || ''}
                  onChange={(e) => handleInputChange('totalAmount', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="금액을 입력하세요"
                />
              ) : (
                <p className="text-gray-900 py-2 flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  {currentReport.totalAmount?.toLocaleString() || '미입력'}
                </p>
              )}
            </div>
            
            {currentReport.extractedData?.goods && currentReport.extractedData.goods.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">상품 목록</label>
                <div className="space-y-2">
                  {currentReport.extractedData.goods.map((good, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg text-sm">
                      <p className="font-medium">{good.description}</p>
                      <p className="text-gray-600">
                        수량: {good.quantity.toLocaleString()}개 • 
                        단가: ${good.unitPrice.toLocaleString()} • 
                        HS: {good.hsCode}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* 추출된 데이터 */}
      {currentReport.extractedData && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">추출된 문서 정보</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 업체 정보 */}
            {currentReport.extractedData.companyInfo && (
              <div>
                <h3 className="text-md font-medium mb-3">업체 정보</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">사업자번호</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={currentReport.extractedData.companyInfo.businessNumber}
                        onChange={(e) => handleNestedInputChange('companyInfo', 'businessNumber', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                    ) : (
                      <p className="text-sm text-gray-900">{currentReport.extractedData.companyInfo.businessNumber}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">주소</label>
                    {isEditing ? (
                      <textarea
                        value={currentReport.extractedData.companyInfo.address}
                        onChange={(e) => handleNestedInputChange('companyInfo', 'address', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        rows={2}
                      />
                    ) : (
                      <p className="text-sm text-gray-900">{currentReport.extractedData.companyInfo.address}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 송장 정보 */}
            {currentReport.extractedData.invoice && (
              <div>
                <h3 className="text-md font-medium mb-3">송장 정보</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">송장번호</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={currentReport.extractedData.invoice.invoiceNumber}
                        onChange={(e) => handleNestedInputChange('invoice', 'invoiceNumber', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                    ) : (
                      <p className="text-sm text-gray-900">{currentReport.extractedData.invoice.invoiceNumber}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">송장일자</label>
                    {isEditing ? (
                      <input
                        type="date"
                        value={currentReport.extractedData.invoice.date}
                        onChange={(e) => handleNestedInputChange('invoice', 'date', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                    ) : (
                      <p className="text-sm text-gray-900">{currentReport.extractedData.invoice.date}</p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">송장금액</label>
                    <p className="text-sm text-gray-900 flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      {currentReport.extractedData.invoice.amount.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* 작업 이력 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">작업 이력</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
            <div>
              <p className="text-sm font-medium">보고서 생성됨</p>
              <p className="text-xs text-gray-600">{formatDate(currentReport.createdAt)}</p>
            </div>
          </div>
          
          {currentReport.updatedAt !== currentReport.createdAt && (
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
              <div>
                <p className="text-sm font-medium">보고서 수정됨</p>
                <p className="text-xs text-gray-600">{formatDate(currentReport.updatedAt)}</p>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}