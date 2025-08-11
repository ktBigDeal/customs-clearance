'use client';

import { useState, useRef, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { declarationsApi } from '@/lib/declarations-api';
import { createDeclaration, performOcrAnalysis, type DeclarationCreateRequest } from '@/lib/api';

interface ReportGenerationProps {
  onReportGenerated: (report: any) => void;
}

interface UploadedFile {
  file: File;
  type: 'invoice' | 'packing_list' | 'bill_of_lading' | 'certificate_of_origin';
  preview: string;
}

export default function ReportGeneration({ onReportGenerated }: ReportGenerationProps) {
  const [step, setStep] = useState<'upload' | 'processing' | 'preview' | 'complete'>('upload');
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [processingStatus, setProcessingStatus] = useState<string>('');
  const [generatedReport, setGeneratedReport] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 파일 업로드 처리
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = () => {
        const newFile: UploadedFile = {
          file,
          type: 'invoice', // 기본값, 사용자가 선택 가능
          preview: reader.result as string
        };
        setUploadedFiles(prev => [...prev, newFile]);
      };
      reader.readAsDataURL(file);
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  // 파일 제거
  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // 파일 타입 변경
  const updateFileType = (index: number, type: UploadedFile['type']) => {
    setUploadedFiles(prev => prev.map((file, i) => 
      i === index ? { ...file, type } : file
    ));
  };

  // OCR 및 AI 분석 처리
  const processFiles = async () => {
    if (uploadedFiles.length === 0) {
      setError('최소 1개의 파일을 업로드해주세요.');
      return;
    }

    setStep('processing');
    setIsLoading(true);
    setError(null);

    try {
      // 1. OCR 처리
      setProcessingStatus('문서를 스캔하고 텍스트를 추출하는 중...');
      const ocrResult = await performOcrAnalysis({
        files: uploadedFiles.map(f => f.file),
        analysisType: uploadedFiles[0]?.type || 'invoice'
      });

      // 2. AI 분석
      setProcessingStatus('AI가 문서 내용을 분석하는 중...');
      const analysisResult = ocrResult;

      // 3. 신고서 생성
      setProcessingStatus('수출입 신고서를 생성하는 중...');
      
      // 분석 결과를 바탕으로 신고서 데이터 구성
      const declarationData: DeclarationCreateRequest = {
        declarationNumber: `IMP${Date.now().toString().slice(-6)}`,
        declarationType: 'IMPORT',
        status: 'DRAFT',
        importerName: analysisResult.structuredData?.companyInfo?.name || '추출된 업체명',
        hsCode: analysisResult.structuredData?.goods?.[0]?.hsCode || '',
        totalAmount: analysisResult.structuredData?.invoice?.amount || 0,
        declarationDetails: JSON.stringify({
          extractedData: analysisResult.structuredData,
          ocrConfidence: analysisResult.confidence,
          processedFiles: uploadedFiles.map(f => ({
            name: f.file.name,
            type: f.type,
            size: f.file.size
          }))
        })
      };

      // 백엔드 API를 통해 신고서 생성
      const createdDeclaration = await createDeclaration(
        declarationData,
        {
          invoiceFile: uploadedFiles.find(f => f.type === 'invoice')?.file,
          packingListFile: uploadedFiles.find(f => f.type === 'packing_list')?.file,
          billOfLadingFile: uploadedFiles.find(f => f.type === 'bill_of_lading')?.file,
          certificateOfOriginFile: uploadedFiles.find(f => f.type === 'certificate_of_origin')?.file,
        }
      );

      // 생성된 신고서에 추출된 데이터 추가
      const reportWithExtractedData = {
        ...createdDeclaration,
        extractedData: analysisResult.structuredData
      };

      setGeneratedReport(reportWithExtractedData);
      setStep('preview');
      
    } catch (err: any) {
      console.error('문서 처리 오류:', err);
      setError(err.message || '문서 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
      setStep('upload');
    } finally {
      setIsLoading(false);
      setProcessingStatus('');
    }
  };

  // 보고서 저장
  const saveReport = async () => {
    if (!generatedReport) return;

    setIsLoading(true);
    try {
      // 백엔드 API 호출 (실제 구현시)
      // const response = await fetch('/api/declarations', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(generatedReport)
      // });

      // 임시로 2초 대기
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      onReportGenerated(generatedReport);
      setStep('complete');
    } catch (err) {
      setError('보고서 저장 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 새로 시작
  const resetProcess = () => {
    setStep('upload');
    setUploadedFiles([]);
    setGeneratedReport(null);
    setError(null);
    setProcessingStatus('');
    setIsLoading(false);
  };

  const fileTypeOptions = [
    { value: 'invoice', label: '상업송장 (Commercial Invoice)' },
    { value: 'packing_list', label: '포장명세서 (Packing List)' },
    { value: 'bill_of_lading', label: '선하증권 (Bill of Lading)' },
    { value: 'certificate_of_origin', label: '원산지증명서 (Certificate of Origin)' }
  ];

  // 업로드 단계
  if (step === 'upload') {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">1단계: 문서 업로드</h2>
          
          {/* 드래그 앤 드롭 영역 */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
              ${isDragActive 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            {isDragActive ? (
              <p className="text-lg text-blue-600">파일을 여기에 놓아주세요...</p>
            ) : (
              <>
                <p className="text-lg text-gray-600 mb-2">클릭하거나 파일을 드래그하여 업로드</p>
                <p className="text-sm text-gray-500">
                  지원 형식: PDF, 이미지 (PNG, JPG), Word 문서 (최대 10MB)
                </p>
              </>
            )}
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}
        </Card>

        {/* 업로드된 파일 목록 */}
        {uploadedFiles.length > 0 && (
          <Card className="p-6">
            <h3 className="text-lg font-medium mb-4">업로드된 파일 ({uploadedFiles.length}개)</h3>
            <div className="space-y-4">
              {uploadedFiles.map((fileData, index) => (
                <div key={index} className="flex items-center gap-4 p-4 border rounded-lg">
                  <FileText className="w-8 h-8 text-blue-600" />
                  <div className="flex-1">
                    <p className="font-medium">{fileData.file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <select
                    value={fileData.type}
                    onChange={(e) => updateFileType(index, e.target.value as UploadedFile['type'])}
                    className="px-3 py-2 border rounded-md text-sm"
                  >
                    {fileTypeOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
            
            <div className="mt-6 flex justify-end">
              <Button onClick={processFiles} className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                보고서 생성 시작
              </Button>
            </div>
          </Card>
        )}
      </div>
    );
  }

  // 처리 중 단계
  if (step === 'processing') {
    return (
      <div className="max-w-2xl mx-auto">
        <Card className="p-8 text-center">
          <div className="mb-6">
            <Loader2 className="w-16 h-16 text-blue-600 mx-auto animate-spin mb-4" />
            <h2 className="text-xl font-semibold mb-2">보고서를 생성하고 있습니다</h2>
            <p className="text-gray-600">{processingStatus}</p>
          </div>
          
          <div className="bg-gray-200 rounded-full h-2 mb-4">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-1000"
              style={{ width: '75%' }}
            />
          </div>
          
          <p className="text-sm text-gray-500">
            잠시만 기다려주세요. 문서 분석에는 수 분이 소요될 수 있습니다.
          </p>
        </Card>
      </div>
    );
  }

  // 미리보기 단계
  if (step === 'preview' && generatedReport) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">생성된 신고서 미리보기</h2>
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-medium">생성 완료</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium mb-3">기본 정보</h3>
              <div className="space-y-2 text-sm">
                <div><strong>신고번호:</strong> {generatedReport.declarationNumber}</div>
                <div><strong>신고 구분:</strong> {generatedReport.declarationType === 'IMPORT' ? '수입' : '수출'}</div>
                <div><strong>수입업체:</strong> {generatedReport.importerName}</div>
                <div><strong>HS코드:</strong> {generatedReport.hsCode}</div>
                <div><strong>총 금액:</strong> ${generatedReport.totalAmount?.toLocaleString()}</div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-3">추출된 데이터</h3>
              <div className="space-y-2 text-sm">
                <div><strong>사업자번호:</strong> {generatedReport.extractedData?.companyInfo?.businessNumber}</div>
                <div><strong>주소:</strong> {generatedReport.extractedData?.companyInfo?.address}</div>
                <div><strong>송장번호:</strong> {generatedReport.extractedData?.invoice?.invoiceNumber}</div>
                <div><strong>송장일자:</strong> {generatedReport.extractedData?.invoice?.date}</div>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-amber-800">검토 필요</p>
                <p className="text-amber-700 mt-1">
                  AI가 추출한 정보를 검토하고 필요시 수정해주세요. 
                  저장 전 모든 정보가 정확한지 확인하시기 바랍니다.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-between">
            <Button variant="outline" onClick={resetProcess}>
              새로 시작하기
            </Button>
            <div className="flex gap-3">
              <Button variant="outline">수정하기</Button>
              <Button onClick={saveReport} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    저장 중...
                  </>
                ) : (
                  '저장하기'
                )}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  // 완료 단계
  if (step === 'complete') {
    return (
      <div className="max-w-2xl mx-auto">
        <Card className="p-8 text-center">
          <CheckCircle2 className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">보고서가 성공적으로 생성되었습니다!</h2>
          <p className="text-gray-600 mb-6">
            신고서가 저장되었으며, 보고서 목록에서 확인할 수 있습니다.
          </p>
          
          <div className="flex justify-center gap-3">
            <Button variant="outline" onClick={resetProcess}>
              새 보고서 생성
            </Button>
            <Button onClick={() => window.location.reload()}>
              목록으로 이동
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return null;
}