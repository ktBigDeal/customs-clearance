'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { declarationsApi } from '@/lib/declarations-api';
import { DeclarationRequestDto, DeclarationType } from '@/types/declaration';



interface ReportGenerationProps {
  onReportGenerated: (report: any) => void;
}

interface UploadedFile {
  file: File;
  type: 'invoiceFile' | 'packingListFile' | 'billOfLadingFile' | 'certificateOfOriginFile';
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
          type: 'invoiceFile', // 기본값, 사용자가 선택 가능
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
      setProcessingStatus('신고서 생성 준비 중...');            
      // 1) (선택) 기본 신고서 데이터 구성
      const declarationData: DeclarationRequestDto = {
        declarationNumber: `IMP${Date.now().toString().slice(-6)}`,
        declarationType: DeclarationType.IMPORT,
        // 필요 시 추가 필드: status, remarks 등
        // status: 'DRAFT' as any,
      };

      // 2) 신고서 생성 API 호출 (파일 동봉)
    setProcessingStatus('신고서를 생성하는 중...');
    const created = await declarationsApi.createDeclaration(
      declarationData,
      {
        invoiceFile: uploadedFiles.find(f => f.type === 'invoiceFile')?.file,
        packingListFile: uploadedFiles.find(f => f.type === 'packingListFile')?.file,
        billOfLadingFile: uploadedFiles.find(f => f.type === 'billOfLadingFile')?.file,
        certificateOfOriginFile: uploadedFiles.find(f => f.type === 'certificateOfOriginFile')?.file,
      }
    );

    console.log('created', JSON.stringify(created));

    // 3) 결과 전달 (백엔드 응답 형태가 Declaration | { declaration: Declaration } 둘 다 대응)
    const reportPayload = (created && (created as any).declaration)
      ? (created as any).declaration
      : created;

    console.log(reportPayload);

    setProcessingStatus('신고서 생성 완료!');
    setGeneratedReport(reportPayload);
    setStep('preview');
  } catch (e: any) {
    console.error(e);
    setError(e?.message || '신고서 생성 중 오류가 발생했습니다.'); 
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
  useEffect(() => {
    console.log('[RG] mounted');
    return () => console.log('[RG] unmounted');
  }, []);

  useEffect(() => {
    console.log('[RG] step =', step);
  }, [step]);

  useEffect(() => {
    console.log('[RG] has generatedReport =', !!generatedReport);
  }, [generatedReport]);
  const fileTypeOptions = [
    { value: 'invoiceFile', label: '상업송장 (Commercial Invoice)' },
    { value: 'packingListFile', label: '포장명세서 (Packing List)' },
    { value: 'billOfLadingFile', label: '선하증권 (Bill of Lading)' },
    { value: 'certificateOfOriginFile', label: '원산지증명서 (Certificate of Origin)' }
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
    // details 소스: mapper가 넣은 rawDetails가 있으면 우선 사용,
    // 없으면 백엔드의 declaration_details(JSON 문자열)를 파싱
    console.log('생성된 신고서 미리보기');

    const details: any = (() => {
      const candidate = (generatedReport as any)?.rawDetails;
      if (candidate && typeof candidate === 'object') return candidate;
      try {
        const s = (generatedReport as any)?.declaration_details;
        return typeof s === 'string' ? JSON.parse(s) : {};
      } catch {
        return {};
      }
    })();

    const entries = Object.entries(details ?? {});

    // 값 렌더링(배열/객체도 안전하게 처리)
    const renderValue = (val: any) => {
      if (val == null) return <span className="text-gray-400">-</span>;
      if (Array.isArray(val)) {
        if (val.length === 0) return <span>[]</span>;
        const allObjects = val.every(v => v && typeof v === 'object' && !Array.isArray(v));
        if (allObjects) {
          // 배열의 모든 key를 합쳐 테이블 헤더 생성
          const headerKeys = Array.from(
            val.reduce<Set<string>>((set, row) => {
              Object.keys(row || {}).forEach(k => set.add(k));
              return set;
            }, new Set<string>())
          );

          return (
            <details className="group">
              <summary className="cursor-pointer text-blue-600 hover:underline">
                {val.length}개 항목 보기
              </summary>
              <div className="mt-2 overflow-x-auto border rounded">
                <table className="min-w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-2 py-1 text-left">#</th>
                      {headerKeys.map(h => (
                        <th key={h} className="px-2 py-1 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {val.map((row: any, idx: number) => (
                      <tr key={idx} className="border-t">
                        <td className="px-2 py-1">{idx + 1}</td>
                        {headerKeys.map(h => (
                          <td key={h} className="px-2 py-1 whitespace-pre-wrap break-words">
                            {formatPrimitive(row?.[h])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          );
        }
        // 배열이지만 원시/혼합 타입인 경우
        return <span>{JSON.stringify(val)}</span>;
      }
      if (typeof val === 'object') {
        return (
          <details className="group">
            <summary className="cursor-pointer text-blue-600 hover:underline">객체 열기</summary>
            <pre className="mt-2 p-2 bg-gray-50 border rounded text-xs overflow-auto">
              {JSON.stringify(val, null, 2)}
            </pre>
          </details>
        );
      }
      return formatPrimitive(val);
    };

  function formatPrimitive(v: any) {
    if (typeof v === 'number') return v.toLocaleString();
    return String(v);
  }

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

        {/* 상단 기본 메타 정보(프론트 공통 필드) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium mb-3">기본 정보</h3>
            <div className="space-y-2 text-sm">
              <div><strong>신고번호:</strong> {generatedReport.declarationNumber ?? ''}</div>
              <div><strong>신고 구분:</strong> {generatedReport.declarationType === 'IMPORT' ? '수입' : '수출'}</div>
              <div><strong>상태:</strong> {generatedReport.status ?? 'DRAFT'}</div>
              <div><strong>생성일:</strong> {generatedReport.createdAt ? new Date(generatedReport.createdAt).toLocaleString() : '-'}</div>
              <div><strong>수정일:</strong> {generatedReport.updatedAt ? new Date(generatedReport.updatedAt).toLocaleString() : '-'}</div>
            </div>
          </div>
        </div>

        {/* JSON Key/Value 전체 출력 */}
        <div className="mt-8">
          <h3 className="text-lg font-medium mb-3">상세 데이터 (JSON)</h3>
          {entries.length === 0 ? (
            <p className="text-sm text-gray-500">표시할 데이터가 없습니다.</p>
          ) : (
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
              {entries.map(([key, value]) => (
                <div key={key} className="flex flex-col">
                  <dt className="text-xs font-medium text-gray-500">{key}</dt>
                  <dd className="text-sm text-gray-900 whitespace-pre-wrap break-words">
                    {renderValue(value)}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </div>

        {/* 안내 메시지 */}
        <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-amber-800">검토 필요</p>
              <p className="text-amber-700 mt-1">
                JSON의 key/value를 그대로 표시했습니다. 저장 전에 필드들을 확인하고 필요 시 보정하세요.
              </p>
            </div>
          </div>
        </div>

        {/* 버튼들 */}
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