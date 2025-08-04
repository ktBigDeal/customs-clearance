
/**
 * 수입신고서 작성 폼 컴포넌트
 * 
 * 이 컴포넌트는 수입신고서 작성을 위한 완전한 폼 인터페이스를 제공합니다.
 * 문서 추출 데이터와 신고서 폼이 좌우로 나뉘어 표시되며,
 * 사용자가 추출된 데이터를 검토하고 수정할 수 있습니다.
 * 
 * @file ImportDeclarationForm.tsx
 * @description 수입신고서 작성 및 편집 컴포넌트
 * @since 2024-01-01
 * @author Frontend Team
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';

/**
 * 수입신고서 작성 폼 메인 컴포넌트
 * 
 * AI가 추출한 문서 데이터를 기반으로 수입신고서를 작성할 수 있는
 * 인터랙티브한 폼을 제공합니다. 좌측에는 추출된 문서 데이터가,
 * 우측에는 실제 신고서 폼이 표시됩니다.
 * 
 * 주요 기능:
 * - 문서 데이터 자동 추출 및 표시
 * - 신고서 자동 작성
 * - 편집 가능한 필드 하이라이팅
 * - 임시 저장 및 최종 제출
 * - 세금 자동 계산
 * 
 * @returns {JSX.Element} 수입신고서 작성 폼 컴포넌트
 * 
 * @example
 * ```tsx
 * // 페이지에서 사용
 * <ImportDeclarationForm />
 * ```
 */
export default function ImportDeclarationForm() {
  /** 현재 선택된 분석 문서 파일명 */
  const [selectedFile, setSelectedFile] = useState('invoice_ABC_240115.pdf');
  
  /** 수입신고서 폼 데이터 */
  const [formData, setFormData] = useState({
    declarationNumber: 'IMP-2024-00001',
    declarationType: '일반수입신고',
    declarationDate: '2024-01-15',
    importer: {
      name: 'ABC무역상사',
      businessNumber: '123-45-67890',
      address: '서울시 강남구 테헤란로 123',
      representative: '김철수'
    },
    exporter: {
      name: 'Global Trading Co.',
      address: '123 Main St, New York, USA',
      country: '미국'
    },
    items: [
      {
        id: 1,
        hsCode: '8471.30.1000',
        productName: '노트북 컴퓨터',
        specification: 'Dell Latitude 3520, 15.6인치',
        quantity: 50,
        unit: '대',
        unitPrice: 800,
        totalPrice: 40000,
        currency: 'USD',
        origin: '중국',
        editable: true
      },
      {
        id: 2,
        hsCode: '8528.72.1000',
        productName: '모니터',
        specification: '27인치 LED 모니터',
        quantity: 25,
        unit: '대',
        unitPrice: 200,
        totalPrice: 5000,
        currency: 'USD',
        origin: '한국',
        editable: false
      }
    ],
    transport: {
      method: '해상운송',
      vessel: 'KOREA EXPRESS',
      arrivalPort: '부산항',
      arrivalDate: '2024-01-10'
    },
    customs: {
      dutyRate: '8%',
      vatRate: '10%',
      totalDuty: 3600,
      totalVat: 4500,
      totalTax: 8100
    }
  });

  /** 현재 편집 중인 필드 ID (없으면 null) */
  const [editingField, setEditingField] = useState<string | null>(null);

  /** 
   * AI가 문서에서 추출한 원본 데이터
   * 실제 환경에서는 API 호출을 통해 받아오는 데이터입니다.
   */
  const extractedData = {
    invoice: {
      number: 'INV-2024-001',
      date: '2024-01-05',
      seller: 'Global Trading Co.',
      buyer: 'ABC무역상사',
      items: [
        { name: '노트북 컴퓨터', qty: 50, price: 800, total: 40000 },
        { name: '모니터', qty: 25, price: 200, total: 5000 }
      ],
      totalAmount: 45000,
      currency: 'USD'
    },
    packingList: {
      totalPackages: 10,
      grossWeight: '500kg',
      netWeight: '450kg',
      dimensions: '120x80x60cm'
    },
    bl: {
      number: 'BL-2024-001',
      vessel: 'KOREA EXPRESS',
      port: '부산항',
      eta: '2024-01-10'
    }
  };

  /**
   * 폼 필드 값 변경 핸들러
   * 
   * 중첩된 객체 필드를 점(.) 표기법으로 업데이트할 수 있습니다.
   * 예: 'importer.name', 'transport.vessel' 등
   * 
   * @param {string} field - 업데이트할 필드 경로 (점 표기법)
   * @param {any} value - 새로운 값
   * 
   * @example
   * ```typescript
   * // 단순 필드 업데이트
   * handleInputChange('declarationType', '긴급수입신고');
   * 
   * // 중첩 객체 필드 업데이트
   * handleInputChange('importer.name', 'ABC무역상사');
   * ```
   */
  const handleInputChange = (field: string, value: any) => {
    const keys = field.split('.');
    setFormData(prev => {
      const newData = { ...prev };
      let current = newData;

      // 중첩된 객체를 순회하며 최종 필드에 접근
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;

      return newData;
    });
  };

  /**
   * 품목 정보 변경 핸들러
   * 
   * 특정 품목의 필드를 업데이트합니다.
   * 
   * @param {number} itemId - 품목 ID
   * @param {string} field - 업데이트할 필드명
   * @param {any} value - 새로운 값
   * 
   * @example
   * ```typescript
   * // 품목 수량 변경
   * handleItemChange(1, 'quantity', 100);
   * 
   * // 품목 단가 변경
   * handleItemChange(1, 'unitPrice', 1000);
   * ```
   */
  const handleItemChange = (itemId: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.map(item =>
        item.id === itemId ? { ...item, [field]: value } : item
      )
    }));
  };

  /**
   * 자동 작성 버튼 클릭 핸들러
   * 
   * AI가 추출한 문서 데이터를 기반으로 신고서를 자동으로 채웁니다.
   * 실제 환경에서는 API 호출을 통해 자동 작성을 수행합니다.
   * 
   * @example
   * ```typescript
   * handleAutoFill(); // 자동 작성 실행
   * ```
   */
  const handleAutoFill = () => {
    // TODO: 실제 자동 작성 API 호출 구현
    alert('문서 데이터를 기반으로 신고서가 자동으로 채워졌습니다.');
  };

  /**
   * 임시 저장 버튼 클릭 핸들러
   * 
   * 현재 작성 중인 신고서를 임시 저장합니다.
   * 나중에 이어서 작성할 수 있도록 데이터를 보존합니다.
   * 
   * @example
   * ```typescript
   * handleTempSave(); // 임시 저장 실행
   * ```
   */
  const handleTempSave = () => {
    // TODO: 실제 임시 저장 API 호출 구현
    alert('임시저장이 완료되었습니다.');
  };

  /**
   * 최종 제출 버튼 클릭 핸들러
   * 
   * 작성된 신고서를 관세청에 최종 제출합니다.
   * 제출 전 필수 항목 검증을 수행합니다.
   * 
   * @example
   * ```typescript
   * handleFinalSubmit(); // 최종 제출 실행
   * ```
   */
  const handleFinalSubmit = () => {
    // TODO: 폼 검증 및 실제 제출 API 호출 구현
    alert('수입신고서가 최종 제출되었습니다.');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <Link href="/" className="text-2xl font-bold text-blue-600" style={{ fontFamily: 'var(--font-pacifico)' }}>
                TradeFlow
              </Link>
              <nav className="flex space-x-6">
                <Link href="/" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">대시보드</Link>
                <Link href="#" className="text-blue-600 font-medium cursor-pointer border-b-2 border-blue-600 pb-1">수입신고서 작성</Link>
                <Link href="#" className="text-gray-600 hover:text-blue-600 font-medium cursor-pointer">신고 내역</Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleAutoFill}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-purple-700 transition-colors whitespace-nowrap cursor-pointer flex items-center space-x-2"
              >
                <i className="ri-magic-line w-4 h-4"></i>
                <span>자동작성</span>
              </button>
              <button
                onClick={handleTempSave}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-700 transition-colors whitespace-nowrap cursor-pointer flex items-center space-x-2"
              >
                <i className="ri-save-line w-4 h-4"></i>
                <span>임시저장</span>
              </button>
              <button
                onClick={handleFinalSubmit}
                className="bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors whitespace-nowrap cursor-pointer flex items-center space-x-2"
              >
                <i className="ri-send-plane-line w-4 h-4"></i>
                <span>최종제출</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Panel - Extracted Data */}
        <div className="w-96 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">추출된 문서 데이터</h2>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>

            {/* File Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">분석 문서</label>
              <select
                value={selectedFile}
                onChange={(e) => setSelectedFile(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm pr-8"
              >
                <option value="invoice_ABC_240115.pdf">invoice_ABC_240115.pdf</option>
                <option value="packing_list_240115.pdf">packing_list_240115.pdf</option>
                <option value="bl_KOREA_240115.pdf">bl_KOREA_240115.pdf</option>
              </select>
            </div>

            {/* Commercial Invoice Data */}
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-3">
                <i className="ri-file-text-line w-4 h-4 text-blue-600"></i>
                <h3 className="font-medium text-gray-900">상업송장 (Commercial Invoice)</h3>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-600">송장번호:</span>
                    <div className="font-medium">{extractedData.invoice.number}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">발행일:</span>
                    <div className="font-medium">{extractedData.invoice.date}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">판매자:</span>
                    <div className="font-medium">{extractedData.invoice.seller}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">구매자:</span>
                    <div className="font-medium">{extractedData.invoice.buyer}</div>
                  </div>
                </div>

                <div className="border-t border-blue-200 pt-3">
                  <div className="text-sm text-gray-600 mb-2">품목 정보:</div>
                  {extractedData.invoice.items.map((item, index) => (
                    <div key={index} className="bg-white rounded p-2 mb-2 text-sm">
                      <div className="font-medium">{item.name}</div>
                      <div className="text-gray-600">
                        수량: {item.qty}개 × ${item.price} = ${item.total.toLocaleString()}
                      </div>
                    </div>
                  ))}
                  <div className="text-right font-medium text-blue-700">
                    총액: ${extractedData.invoice.totalAmount.toLocaleString()} USD
                  </div>
                </div>
              </div>
            </div>

            {/* Packing List Data */}
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-3">
                <i className="ri-package-line w-4 h-4 text-green-600"></i>
                <h3 className="font-medium text-gray-900">포장명세서 (Packing List)</h3>
              </div>
              <div className="bg-green-50 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">총 포장개수:</span>
                  <span className="font-medium">{extractedData.packingList.totalPackages}박스</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">총 중량:</span>
                  <span className="font-medium">{extractedData.packingList.grossWeight}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">순 중량:</span>
                  <span className="font-medium">{extractedData.packingList.netWeight}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">규격:</span>
                  <span className="font-medium">{extractedData.packingList.dimensions}</span>
                </div>
              </div>
            </div>

            {/* B/L Data */}
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-3">
                <i className="ri-ship-line w-4 h-4 text-purple-600"></i>
                <h3 className="font-medium text-gray-900">선하증권 (B/L)</h3>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">B/L 번호:</span>
                  <span className="font-medium">{extractedData.bl.number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">선박명:</span>
                  <span className="font-medium">{extractedData.bl.vessel}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">도착항:</span>
                  <span className="font-medium">{extractedData.bl.port}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">도착예정일:</span>
                  <span className="font-medium">{extractedData.bl.eta}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Import Declaration Form */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h1 className="text-2xl font-bold text-gray-900">수입신고서</h1>
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <i className="ri-shield-check-line w-4 h-4 text-green-600"></i>
                    <span>자동 검증 완료</span>
                  </div>
                </div>
              </div>

              <div className="p-6 space-y-8">
                {/* Basic Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">기본 정보</h3>
                  <div className="grid grid-cols-3 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">신고번호</label>
                      <input
                        type="text"
                        value={formData.declarationNumber}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">신고구분</label>
                      <select
                        value={formData.declarationType}
                        onChange={(e) => handleInputChange('declarationType', e.target.value)}
                        className="w-full px-3 py-2 border-2 border-yellow-300 bg-yellow-50 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm pr-8"
                      >
                        <option>일반수입신고</option>
                        <option>긴급수입신고</option>
                        <option>간이수입신고</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">신고일자</label>
                      <input
                        type="date"
                        value={formData.declarationDate}
                        onChange={(e) => handleInputChange('declarationDate', e.target.value)}
                        className="w-full px-3 py-2 border-2 border-yellow-300 bg-yellow-50 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Importer Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">수입자 정보</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">업체명</label>
                      <input
                        type="text"
                        value={formData.importer.name}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">사업자등록번호</label>
                      <input
                        type="text"
                        value={formData.importer.businessNumber}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">주소</label>
                      <input
                        type="text"
                        value={formData.importer.address}
                        onChange={(e) => handleInputChange('importer.address', e.target.value)}
                        className="w-full px-3 py-2 border-2 border-yellow-300 bg-yellow-50 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Exporter Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">수출자 정보</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">업체명</label>
                      <input
                        type="text"
                        value={formData.exporter.name}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">국가</label>
                      <input
                        type="text"
                        value={formData.exporter.country}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">주소</label>
                      <input
                        type="text"
                        value={formData.exporter.address}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                  </div>
                </div>

                {/* Items Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">품목 정보</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full border border-gray-200 rounded-lg">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">HS코드</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">품명</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">규격</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">수량</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">단가</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">총가격</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">원산지</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {formData.items.map((item, index) => (
                          <tr key={item.id} className={item.editable ? 'bg-yellow-50' : ''}>
                            <td className="px-4 py-3">
                              <input
                                type="text"
                                value={item.hsCode}
                                onChange={(e) => item.editable && handleItemChange(item.id, 'hsCode', e.target.value)}
                                className={`w-full px-2 py-1 text-sm rounded border ${
                                  item.editable
                                    ? 'border-yellow-300 bg-yellow-50'
                                    : 'border-gray-200 bg-gray-50'
                                }`}
                                readOnly={!item.editable}
                              />
                            </td>
                            <td className="px-4 py-3">
                              <input
                                type="text"
                                value={item.productName}
                                onChange={(e) => item.editable && handleItemChange(item.id, 'productName', e.target.value)}
                                className={`w-full px-2 py-1 text-sm rounded border ${
                                  item.editable
                                    ? 'border-yellow-300 bg-yellow-50'
                                    : 'border-gray-200 bg-gray-50'
                                }`}
                                readOnly={!item.editable}
                              />
                            </td>
                            <td className="px-4 py-3">
                              <input
                                type="text"
                                value={item.specification}
                                onChange={(e) => item.editable && handleItemChange(item.id, 'specification', e.target.value)}
                                className={`w-full px-2 py-1 text-sm rounded border ${
                                  item.editable
                                    ? 'border-yellow-300 bg-yellow-50'
                                    : 'border-gray-200 bg-gray-50'
                                }`}
                                readOnly={!item.editable}
                              />
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex">
                                <input
                                  type="number"
                                  value={item.quantity}
                                  onChange={(e) => item.editable && handleItemChange(item.id, 'quantity', parseInt(e.target.value))}
                                  className={`w-16 px-2 py-1 text-sm rounded-l border ${
                                    item.editable
                                      ? 'border-yellow-300 bg-yellow-50'
                                      : 'border-gray-200 bg-gray-50'
                                  }`}
                                  readOnly={!item.editable}
                                />
                                <span className="px-2 py-1 bg-gray-100 text-sm text-gray-600 rounded-r border-l-0 border border-gray-200">
                                  {item.unit}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <input
                                type="number"
                                value={item.unitPrice}
                                onChange={(e) => item.editable && handleItemChange(item.id, 'unitPrice', parseFloat(e.target.value))}
                                className={`w-20 px-2 py-1 text-sm rounded border ${
                                  item.editable
                                    ? 'border-yellow-300 bg-yellow-50'
                                    : 'border-gray-200 bg-gray-50'
                                }`}
                                readOnly={!item.editable}
                              />
                            </td>
                            <td className="px-4 py-3">
                              <span className="font-medium text-sm">
                                ${item.totalPrice.toLocaleString()}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <select
                                value={item.origin}
                                onChange={(e) => item.editable && handleItemChange(item.id, 'origin', e.target.value)}
                                className={`w-full px-2 py-1 text-sm rounded border pr-6 ${
                                  item.editable
                                    ? 'border-yellow-300 bg-yellow-50'
                                    : 'border-gray-200 bg-gray-50'
                                }`}
                                disabled={!item.editable}
                              >
                                <option>{item.origin}</option>
                                <option>한국</option>
                                <option>중국</option>
                                <option>일본</option>
                                <option>미국</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Transport Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">운송 정보</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">운송수단</label>
                      <input
                        type="text"
                        value={formData.transport.method}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">선박명</label>
                      <input
                        type="text"
                        value={formData.transport.vessel}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">도착항</label>
                      <input
                        type="text"
                        value={formData.transport.arrivalPort}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">도착일자</label>
                      <input
                        type="date"
                        value={formData.transport.arrivalDate}
                        onChange={(e) => handleInputChange('transport.arrivalDate', e.target.value)}
                        className="w-full px-3 py-2 border-2 border-yellow-300 bg-yellow-50 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Tax Calculation */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">세금 계산</h3>
                  <div className="bg-blue-50 rounded-lg p-6">
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">관세율</label>
                        <input
                          type="text"
                          value={formData.customs.dutyRate}
                          onChange={(e) => handleInputChange('customs.dutyRate', e.target.value)}
                          className="w-full px-3 py-2 border-2 border-yellow-300 bg-yellow-50 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">부가세율</label>
                        <input
                          type="text"
                          value={formData.customs.vatRate}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                          readOnly
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">관세액</label>
                        <input
                          type="text"
                          value={`₩${formData.customs.totalDuty.toLocaleString()}`}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm font-medium"
                          readOnly
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">부가세액</label>
                        <input
                          type="text"
                          value={`₩${formData.customs.totalVat.toLocaleString()}`}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm font-medium"
                          readOnly
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">총 세금</label>
                        <input
                          type="text"
                          value={`₩${formData.customs.totalTax.toLocaleString()}`}
                          className="w-full px-3 py-2 border border-blue-300 bg-blue-100 rounded-lg text-sm font-bold text-blue-800"
                          readOnly
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Legend */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <i className="ri-information-line w-4 h-4 text-yellow-600"></i>
                    <span className="text-sm font-medium text-yellow-800">수정 가능 필드 안내</span>
                  </div>
                  <p className="text-sm text-yellow-700">
                    노란색으로 하이라이트된 필드는 수정이 가능합니다. 문서에서 자동으로 추출된 데이터를 검토하고 필요시 수정해주세요.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
