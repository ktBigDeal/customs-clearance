'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Calendar, Hash, Download, Edit, Loader2 } from 'lucide-react';
import { declarationsApi } from '@/lib/declarations-api';

/* ====================== 타입 ====================== */
type Report = {
  id: number;
  declarationNumber: string;
  declarationType: 'IMPORT' | 'EXPORT';
  status: 'DRAFT' | 'UPDATED' | 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED';
  importerName?: string;
  hsCode?: string;
  totalAmount?: number;
  createdAt: string;
  updatedAt: string;
  declaration_details?: string | Record<string, any>;
  rawDetails?: Record<string, any>;
};

interface ReportPreviewProps {
  report: Report;
  getStatusBadge: (status: Report['status']) => JSX.Element;
  getTypeLabel: (type: Report['declarationType']) => string;
  isAdminView?: boolean; // 관리자 보기 모드 (수정 버튼 숨김)
}

/* ====================== 유틸: 파서/표시 ====================== */

// 숫자/문자 공통 포맷
const fmt = (v: any) =>
  v === null || v === undefined || v === ''
    ? '-'
    : typeof v === 'number'
    ? v.toLocaleString()
    : String(v);

// 상세(JSON) 파싱: rawDetails → declaration_details(JSON/string) → {}
const parseDetails = (src: any): Record<string, any> => {
  if (!src) return {};
  if (src.rawDetails && typeof src.rawDetails === 'object') return src.rawDetails;
  const payload = src.declaration_details ?? src.declarationDetails;
  if (!payload) return {};
  if (typeof payload === 'object') return payload;
  try {
    return JSON.parse(String(payload));
  } catch {
    return {};
  }
};

// 단순 객체 판정
function isPlainObject(x: any) {
  return x && typeof x === 'object' && !Array.isArray(x);
}

// 표 셀 안전 출력
function displayCell(v: any) {
  if (v === null || v === undefined || v === '') {
    return <span className="text-gray-400">-</span>;
  }
  if (typeof v === 'object') {
    return <code className="text-xs">{JSON.stringify(v)}</code>;
  }
  return <span>{String(v)}</span>;
}

// 어떤 값이 와도 안전하게 렌더
function renderValue(val: any) {
  if (val === null || val === undefined) {
    return <span className="text-gray-400">-</span>;
  }

  // 배열
  if (Array.isArray(val)) {
    if (val.length === 0) return <span>[]</span>;

    const everyObj = val.every(isPlainObject);
    if (everyObj) {
      const headerKeys = Array.from(new Set(val.flatMap((o) => Object.keys(o ?? {}))));
      return (
        <div className="overflow-x-auto border rounded">
          <table className="min-w-full text-xs">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-2 py-1 text-left">#</th>
                {headerKeys.map((h) => (
                  <th key={`h-${h}`} className="px-2 py-1 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {val.map((row: any, idx: number) => (
                <tr key={`row-${idx}`} className="border-t">
                  <td className="px-2 py-1">{idx + 1}</td>
                  {headerKeys.map((h) => (
                    <td key={`c-${idx}-${h}`} className="px-2 py-1 whitespace-pre-wrap break-words">
                      {displayCell(row?.[h])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    // 혼합/원시 타입 배열
    return (
      <ul className="list-disc pl-5 space-y-1">
        {val.map((v, i) => (
          <li key={`arr-${i}`}>{isPlainObject(v) ? <code className="text-xs">{JSON.stringify(v)}</code> : String(v)}</li>
        ))}
      </ul>
    );
  }

  // 객체는 펼침
  if (isPlainObject(val)) {
    return (
      <details>
        <summary className="cursor-pointer text-blue-600 hover:underline">객체 열기</summary>
        <pre className="mt-2 p-2 bg-gray-50 border rounded text-xs overflow-auto">{JSON.stringify(val, null, 2)}</pre>
      </details>
    );
  }

  // 숫자/문자
  return <span>{String(val)}</span>;
}

/* 특정 키 후보 중 첫 유효값 선택 */
type FieldDef = { label: string; keys: string[] };
const pickFields = (
  detail: Record<string, any>,
  defs: FieldDef[]
): { label: string; key: string; value: any }[] =>
  defs
    .map((d) => {
      const key = d.keys.find((k) => detail[k] !== undefined && detail[k] !== null && detail[k] !== '');
      return key ? { label: d.label, key, value: detail[key] } : null;
    })
    .filter(Boolean) as { label: string; key: string; value: any }[];

/* ====================== 컴포넌트 ====================== */

export default function ReportPreview({ report, getStatusBadge, getTypeLabel, isAdminView = false }: ReportPreviewProps) {
  const router = useRouter();

  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<Record<string, any>>(() => parseDetails(report));

  // 상세 재조회(서버 우선 동기화)
  useEffect(() => {
    let alive = true;
    (async () => {
      setDetailError(null);
      setDetailLoading(true);
      try {
        const res = await declarationsApi.getById(report.id);
        const parsed = parseDetails(res ?? {});
        if (alive) setDetailData(parsed);
      } catch (e: any) {
        if (alive) setDetailError(e?.message || '상세 조회 중 오류가 발생했습니다.');
      } finally {
        if (alive) setDetailLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [report.id]);

  // 상단 메타
  const createdAtLabel = useMemo(
    () =>
      new Date(report.createdAt).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }),
    [report.createdAt]
  );
  const updatedAtLabel = useMemo(
    () =>
      new Date(report.updatedAt).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }),
    [report.updatedAt]
  );

  // XML 다운로드
  const [downloading, setDownloading] = useState(false);
  const handleDownloadXml = async () => {
    try {
      setDownloading(true);
      const docType: 'import' | 'export' = report.declarationType === 'EXPORT' ? 'export' : 'import';
      await declarationsApi.downloadXml(report.id, { docType });
    } catch (e: any) {
      alert(e?.message || 'XML 다운로드 중 오류가 발생했습니다.');
    } finally {
      setDownloading(false);
    }
  };

  // 수정 페이지로 이동
  const handleGoEdit = () => {
    //router.push(`/declaration/${report.id}/edit`);
  };

  /* 신고구분별 필드/품목 정의 */
  const isImport = report.declarationType === 'IMPORT';

  // 상단 주요 필드 (라벨/동의어 키)
  const importFieldDefs: FieldDef[] = [
    { label: '신고구분', keys: ['신고구분'] },
    { label: '거래구분', keys: ['거래구분'] },
    { label: '종류', keys: ['종류'] },
    { label: '원산지', keys: ['원산지'] },
    { label: 'BL/AWB 번호', keys: ['BL_AWB_번호', 'B/L(AWB)번호'] },
    { label: 'Master BL 번호', keys: ['Master_BL_번호', 'Master B/L 번호'] },
    { label: '국내도착항', keys: ['국내도착항'] },
    { label: '선기명', keys: ['선기명', '선박명'] },
    { label: '수입자', keys: ['수입자'] },
    { label: '납세의무자', keys: ['납세의무자'] },
    { label: '해외공급자', keys: ['해외공급자'] },
    { label: '적출국', keys: ['적출국'] },
    { label: '결제금액', keys: ['결제금액'] },
    { label: '총포장갯수', keys: ['총포장갯수'] },
    { label: '송품장부호', keys: ['송품장부호', '송품장부 호'] },
  ];

  const exportFieldDefs: FieldDef[] = [
    { label: '수출대행자', keys: ['수출대행자'] },
    { label: '제조자', keys: ['제조자'] },
    { label: '구매자', keys: ['구매자'] },
    { label: '신고구분', keys: ['신고구분'] },
    { label: '거래구분', keys: ['거래구분'] },
    { label: '종류', keys: ['종류'] },
    { label: '목적국', keys: ['목적국'] },
    { label: '선박명/편명', keys: ['선박명', '선박명(또는 항공편명)', '선기명'] },
    { label: '운송형태', keys: ['운송형태'] },
    { label: '송품장부호', keys: ['송품장부호', '송품장부 호'] },
    { label: '원산지', keys: ['원산지'] },
    { label: '순중량', keys: ['순중량'] },
    { label: '총중량', keys: ['총중량'] },
    { label: '총포장개수', keys: ['총포장개수'] },
    { label: '결제금액', keys: ['결제금액'] },
  ];

  const visiblePairs = pickFields(detailData, isImport ? importFieldDefs : exportFieldDefs);

  // 품목 테이블 정의
  type ColDef = { label: string; keys: string[] };
  const importItemCols: ColDef[] = [
    { label: '거래품명', keys: ['거래품명'] },
    { label: '세번번호', keys: ['세번번호'] },
    { label: '모델규격', keys: ['모델규격', '모델·규격'] },
    { label: '수량', keys: ['수량'] },
    { label: '단가', keys: ['단가'] },
    { label: '순중량', keys: ['순중량'] },
    { label: '총중량', keys: ['총중량'] },
    { label: '금액', keys: ['금액'] },
    { label: '총포장갯수', keys: ['총포장갯수'] },
  ];

  const exportItemCols: ColDef[] = [
    { label: '물품상태', keys: ['물품상태'] },
    { label: '품명', keys: ['품명'] },
    { label: '거래품명', keys: ['거래품명'] },
    { label: '상표명', keys: ['상표명'] },
    { label: '모델및규격', keys: ['모델및규격', '모델규격', '모델·규격'] },
    { label: '수량', keys: ['수량'] },
    { label: '단가', keys: ['단가'] },
    { label: '금액', keys: ['금액'] },
    { label: '세번부호', keys: ['세번부호', '세번번호'] },
    { label: '순중량', keys: ['순중량'] },
    { label: '총중량', keys: ['총중량'] },
    { label: '포장개수', keys: ['포장개수', '총포장갯수'] },
  ];

  const itemCols = isImport ? importItemCols : exportItemCols;

  // 품목 배열: 백엔드가 '_' 또는 ' ' 두 케이스로 줄 수 있어 둘 다 대응
  const items: any[] = Array.isArray(detailData?.['품목별_결과'])
    ? detailData['품목별_결과']
    : Array.isArray(detailData?.['품목별 결과'])
    ? detailData['품목별 결과']
    : [];

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
              <h1 className="text-2xl font-bold">{report.declarationNumber}</h1>
              <p className="text-gray-600 flex items-center gap-2">
                {getTypeLabel(report.declarationType)} • {getStatusBadge(report.status)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={handleDownloadXml}
              disabled={downloading}
              className="flex items-center gap-2"
            >
              {downloading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> XML 다운로드 중…
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  XML 다운로드
                </>
              )}
            </Button>

            {!isAdminView && (
              <Button onClick={handleGoEdit} className="flex items-center gap-2">
                <Edit className="w-4 h-4" />
                수정
              </Button>
            )}
          </div>
        </div>

        {/* 메타 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="w-4 h-4" />
            <span>생성일: {createdAtLabel}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="w-4 h-4" />
            <span>수정일: {updatedAtLabel}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Hash className="w-4 h-4" />
            <span>ID: {report.id}</span>
          </div>
        </div>
      </Card>

      {/* 상세 정보 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">상세 정보</h2>

        {detailLoading && (
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            불러오는 중…
          </div>
        )}
        {detailError && <p className="text-sm text-red-600 mb-2">에러: {detailError}</p>}

        {/* 주요 Key/Value */}
        {visiblePairs.length > 0 ? (
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
            {visiblePairs.map(({ label, value }) => (
              <div key={label} className="flex flex-col">
                <dt className="text-xs font-medium text-gray-500">{label}</dt>
                <dd className="text-sm text-gray-900 whitespace-pre-wrap break-words">{renderValue(value)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          !detailLoading && <p className="text-sm text-gray-500">표시할 상세 데이터가 없습니다.</p>
        )}

        {/* 품목 테이블 */}
        {items.length > 0 && (
          <div className="mt-6">
            <h3 className="text-base font-semibold mb-2">품목별 결과</h3>
            <div className="overflow-x-auto border rounded">
              <table className="min-w-full text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-2 py-1 text-left">#</th>
                    {itemCols.map((c) => (
                      <th key={c.label} className="px-2 py-1 text-left">
                        {c.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((row, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-2 py-1">{idx + 1}</td>
                      {itemCols.map((col) => {
                        const keyInRow = col.keys.find(
                          (k) => row?.[k] !== undefined && row?.[k] !== null && row?.[k] !== ''
                        );
                        return (
                          <td key={col.label} className="px-2 py-1 whitespace-pre-wrap break-words">
                            {fmt(keyInRow ? row[keyInRow] : '')}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      {/* 원본 JSON 확인용 */}
      <Card className="p-6">
        <details>
          <summary className="cursor-pointer text-blue-600 hover:underline">원본 JSON(declaration_details) 보기</summary>
          <pre className="mt-3 p-3 bg-gray-50 border rounded text-xs overflow-auto">
            {JSON.stringify(detailData ?? {}, null, 2)}
          </pre>
        </details>
      </Card>
    </div>
  );
}
