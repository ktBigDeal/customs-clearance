/**
 * 관세 신고서 API 클라이언트
 * 
 * 이 파일은 신고서 관련 모든 API 호출을 담당하는 클래스를 정의합니다.
 * CRUD 작업, 파일 업로드, 상태 관리, 승인/거부 등의 기능을 제공합니다.
 * 
 * @file declarations-api.ts
 * @description 신고서 API 클라이언트 및 관련 유틸리티
 * @since 2024-01-01
 * @author Frontend Team

 * 관세 신고서 API 클라이언트 — 백엔드 DeclarationController와 1:1 매핑
 *
 * Base Path: /api/v1/declaration
 *
 * 엔드포인트 매핑(Controller 기준)
 * - POST   /declaration                                  : 신고서 생성 (multipart)
 * - GET    /declaration/{declarationId}                  : 신고서 상세(Map<String,Object>)
 * - PUT    /declaration/{declarationId}                  : 신고서 수정(Map 기반 부분 업데이트)
 * - DELETE /declaration/{declarationId}                  : 신고서 삭제(boolean)
 * - GET    /declaration/user/{userId}                    : 사용자 신고서 목록
 * - GET    /declaration/user/{userId}/{status}           : 사용자 신고서 목록(상태 필터)
 * - GET    /declaration/admin                            : 관리자 전체 목록
 * - GET    /declaration/admin/{status}                   : 관리자 목록(상태 필터)
 * - GET    /declaration/attachment/{declarationId}       : 특정 신고서 첨부 목록
 * - GET    /declaration/attachment/user/{userId}         : 사용자 첨부 목록
 * - GET    /declaration/attachment/admin                 : 관리자 첨부 목록
 * - GET    /declaration/{declarationId}/xml?docType=...  : KCS XML 다운로드(import|export)
 */

import { apiClient } from './api';
import {
  Attachment,
  Declaration,
  DeclarationRequestDto,
  DeclarationResponseDto,
  DeclarationDetailResponse,
  DeclarationStatus,
  XmlDocType,
  DeclarationCreateFiles,
} from '@/types/declaration';

// 대시보드용 인터페이스
export interface DeclarationStats {
  totalDeclarations: number;
  pendingDeclarations: number;
  underReviewDeclarations: number;
  approvedDeclarations: number;
  rejectedDeclarations: number;
  clearedDeclarations: number;
}

export interface ChartData {
  monthlyData: Array<{
    month: string;
    count: number;
  }>;
  statusData: Array<{
    status: string;
    count: number;
    label: string;
  }>;
}

export interface ProcessingTimeStats {
  thisMonth: number;
  lastMonth: number;
  improvement: number;
  trend: 'up' | 'down';
}

const BASE = '/declaration';

/**
 * 관세 신고서 API 클라이언트 클래스
 * 
 * 신고서 관련 모든 API 작업을 담당하는 클래스입니다.
 * 생성, 조회, 수정, 삭제, 승인/거부, 파일 업로드 등의 기능을 제공합니다.
 * 
 * @class DeclarationsApi
 */
export class DeclarationsApi {

  /**
   * Create a new declaration with file uploads
   */
  async createDeclaration(
    data: DeclarationRequestDto,
    files?: DeclarationCreateFiles
  ): Promise<DeclarationResponseDto> {
    const formData = new FormData();

    // DTO → FormData (null/undefined 제외)
    Object.entries(data || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null) formData.append(k, String(v));
    });

    if (files) {
      if (files.invoiceFile) formData.append('invoiceFile', files.invoiceFile);
      if (files.packingListFile) formData.append('packingListFile', files.packingListFile);
      if (files.billOfLadingFile) formData.append('billOfLadingFile', files.billOfLadingFile);
      if (files.certificateOfOriginFile)
        formData.append('certificateOfOriginFile', files.certificateOfOriginFile);
    }

    return apiClient.post<DeclarationResponseDto>(`${BASE}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  // Update existing declaration
  async update(
    declarationId: number,
    update: Record<string, any>
  ): Promise<DeclarationDetailResponse> {
    return apiClient.put<DeclarationDetailResponse>(`${BASE}/${declarationId}`, update);
  }

  // Delete declaration
  async remove(declarationId: number): Promise<boolean> {
    return apiClient.delete<boolean>(`${BASE}/${declarationId}`);
  }

  async getById(declarationId: number): Promise<DeclarationDetailResponse> {
    return apiClient.get<DeclarationDetailResponse>(`${BASE}/${declarationId}`);
  }

  /**사용자 신고서 목록 */
  async listByUser(): Promise<DeclarationResponseDto[]> {
    // 현재 로그인한 사용자의 ID를 localStorage에서 가져오기
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;
    const userId = user?.id || 1; // 기본값 1 (테스트용)
    
    return apiClient.get<DeclarationResponseDto[]>(`${BASE}/user/${userId}`);
  }

  /** 사용자 신고서 목록(상태 필터) */
  async listByUserAndStatus(status: DeclarationStatus): Promise<DeclarationResponseDto[]> {
    return apiClient.get<DeclarationResponseDto[]>(`${BASE}/user/${status}`);
  }

  /** 관리자 전체 목록 */
  async listAdmin(): Promise<DeclarationResponseDto[]> {
    return apiClient.get<DeclarationResponseDto[]>(`${BASE}/admin`);
  }

  /** 관리자 전체 목록 (listAdmin과 동일, 별칭) */
  async listAll(): Promise<DeclarationResponseDto[]> {
    return this.listAdmin();
  }

  /** 관리자 목록(상태 필터) */
  async listAdminByStatus(status: DeclarationStatus): Promise<DeclarationResponseDto[]> {
    return apiClient.get<DeclarationResponseDto[]>(`${BASE}/admin/${status}`);
  }

  /** 특정 신고서 첨부 목록 */
  async listAttachmentsByDeclaration(declarationId: number): Promise<Attachment[]> {
    return apiClient.get<Attachment[]>(`${BASE}/attachment/${declarationId}`);
  }

  /** 사용자 첨부 목록 */
  async listAttachmentsByUser(userId: number): Promise<Attachment[]> {
    return apiClient.get<Attachment[]>(`${BASE}/attachment/user/${userId}`);
  }

  /** 관리자 첨부 목록 */
  async listAttachmentsAdmin(): Promise<Attachment[]> {
    return apiClient.get<Attachment[]>(`${BASE}/attachment/admin`);
  }

  /** KCS XML 다운로드(import/export) */
  async downloadXml(
    declarationId: number,
    options?: { docType?: XmlDocType }
  ): Promise<void> {
    const query = options?.docType ? `?docType=${options.docType}` : '';
    const url = `${BASE}/${declarationId}/xml${query}`;
    const filename = `declaration-${declarationId}${options?.docType ? '-' + options.docType : ''}.xml`;
    return apiClient.downloadFile(url, filename);
  }

  // ========== 대시보드용 API 메서드들 ==========

  /**
   * 대시보드 통계 데이터 조회
   */
  async getStats(): Promise<DeclarationStats> {
    return apiClient.get<DeclarationStats>(`${BASE}/stats`);
  }

  /**
   * 최근 신고서 목록 조회
   */
  async getRecent(limit: number = 5): Promise<DeclarationResponseDto[]> {
    return apiClient.get<DeclarationResponseDto[]>(`${BASE}/recent?limit=${limit}`);
  }

  /**
   * 차트용 데이터 조회
   */
  async getChartData(): Promise<ChartData> {
    return apiClient.get<ChartData>(`${BASE}/chart-data`);
  }

  /**
   * 처리 시간 통계 조회
   */
  async getProcessingTimeStats(): Promise<ProcessingTimeStats> {
    return apiClient.get<ProcessingTimeStats>(`${BASE}/processing-time`);
  }
}

// Create singleton instance
export const declarationsApi = new DeclarationsApi();

// ========== 유틸리티 함수들 ==========

/**
 * 신고서 상태를 한국어로 변환
 */
export const getStatusKorean = (status: string): string => {
  switch (status) {
    case 'DRAFT':
      return '초안';
    case 'UPDATED':
      return '수정됨';
    case 'SUBMITTED':
      return '제출됨';
    case 'UNDER_REVIEW':
      return '심사 중';
    case 'APPROVED':
      return '승인';
    case 'REJECTED':
      return '반려';
    default:
      return status;
  }
};

/**
 * 신고서 타입을 한국어로 변환
 */
export const getTypeKorean = (type: string): string => {
  switch (type) {
    case 'IMPORT':
      return '수입';
    case 'EXPORT':
      return '수출';
    default:
      return type;
  }
};

/**
 * 상태별 색상 클래스 반환
 */
export const getStatusColorClass = (status: string): string => {
  switch (status) {
    case 'APPROVED':
      return 'bg-green-100 text-green-800';
    case 'SUBMITTED':
      return 'bg-blue-100 text-blue-800';
    case 'UNDER_REVIEW':
      return 'bg-purple-100 text-purple-800';
    case 'DRAFT':
    case 'UPDATED':
      return 'bg-orange-100 text-orange-800';
    case 'REJECTED':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

/**
 * 숫자를 한국 원화 형식으로 포맷
 */
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
  }).format(value);
};

/**
 * 날짜를 한국 형식으로 포맷
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
};