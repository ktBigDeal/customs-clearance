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
 */

import { apiClient } from './api';
import {
  Declaration,
  DeclarationRequestDto,
  DeclarationResponseDto,
  DeclarationStatsDto,
  DeclarationListParams,
  DeclarationListResponse,
} from '@/types/declaration';
import { UploadResponse } from '@/types/api';

/**
 * 관세 신고서 API 클라이언트 클래스
 * 
 * 신고서 관련 모든 API 작업을 담당하는 클래스입니다.
 * 생성, 조회, 수정, 삭제, 승인/거부, 파일 업로드 등의 기능을 제공합니다.
 * 
 * @class DeclarationsApi
 * @example
 * ```typescript
 * import { declarationsApi } from '@/lib/declarations-api';
 * 
 * // 신고서 목록 조회
 * const declarations = await declarationsApi.getDeclarations({
 *   page: 1,
 *   size: 10,
 *   status: 'PENDING'
 * });
 * 
 * // 새 신고서 생성
 * const newDeclaration = await declarationsApi.createDeclaration({
 *   declarationType: 'IMPORT',
 *   importer: { name: 'ABC Company' }
 * });
 * ```
 */
export class DeclarationsApi {
  /**
   * 신고서 목록 조회 (페이지네이션 및 필터링 지원)
   * 
   * 조건에 따라 신고서 목록을 페이지 단위로 조회합니다.
   * 상태, 날짜 범위, 검색어 등으로 필터링이 가능합니다.
   * 
   * @param {DeclarationListParams} [params] - 조회 조건 (페이지, 필터 등)
   * @returns {Promise<DeclarationListResponse>} 신고서 목록과 페이지 정보
   * 
   * @example
   * ```typescript
   * // 기본 조회 (첫 페이지)
   * const result = await declarationsApi.getDeclarations();
   * 
   * // 필터링된 조회
   * const filtered = await declarationsApi.getDeclarations({
   *   page: 1,
   *   size: 20,
   *   status: 'PENDING',
   *   startDate: '2024-01-01',
   *   endDate: '2024-01-31',
   *   search: 'ABC Company'
   * });
   * ```
   */
  async getDeclarations(params?: DeclarationListParams): Promise<DeclarationListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const url = `/declarations${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get<DeclarationListResponse>(url);
  }

  /**
   * 단일 신고서 조회
   * 
   * ID를 사용하여 특정 신고서의 상세 정보를 조회합니다.
   * 
   * @param {number} id - 신고서 ID
   * @returns {Promise<DeclarationResponseDto>} 신고서 상세 정보
   * 
   * @example
   * ```typescript
   * const declaration = await declarationsApi.getDeclaration(123);
   * console.log(declaration.declarationNumber); // "IMP-2024-00123"
   * ```
   * 
   * @throws {ApiError} 신고서를 찾을 수 없는 경우 404 오류
   */
  async getDeclaration(id: number): Promise<DeclarationResponseDto> {
    return apiClient.get<DeclarationResponseDto>(`/declarations/${id}`);
  }

  /**
   * 새 신고서 생성
   * 
   * 신규 신고서를 생성합니다. 생성 후 추가 편집이 가능합니다.
   * 
   * @param {DeclarationRequestDto} declaration - 생성할 신고서 데이터
   * @returns {Promise<DeclarationResponseDto>} 생성된 신고서 정보
   * 
   * @example
   * ```typescript
   * const newDeclaration = await declarationsApi.createDeclaration({
   *   declarationType: 'IMPORT',
   *   importer: {
   *     name: 'ABC무역상사',
   *     businessNumber: '123-45-67890'
   *   },
   *   items: [
   *     {
   *       hsCode: '8471.30.1000',
   *       productName: '노트북 컴퓨터',
   *       quantity: 10,
   *       unitPrice: 1000
   *     }
   *   ]
   * });
   * ```
   * 
   * @throws {ApiError} 유효성 검증 실패 시 400 오류
   */
  async createDeclaration(declaration: DeclarationRequestDto): Promise<DeclarationResponseDto> {
    return apiClient.post<DeclarationResponseDto, DeclarationRequestDto>(
      '/declarations',
      declaration
    );
  }

  // Update existing declaration
  async updateDeclaration(
    id: number,
    declaration: Partial<DeclarationRequestDto>
  ): Promise<DeclarationResponseDto> {
    return apiClient.put<DeclarationResponseDto, Partial<DeclarationRequestDto>>(
      `/declarations/${id}`,
      declaration
    );
  }

  // Delete declaration
  async deleteDeclaration(id: number): Promise<void> {
    return apiClient.delete<void>(`/declarations/${id}`);
  }

  // Submit declaration for processing
  async submitDeclaration(id: number): Promise<DeclarationResponseDto> {
    return apiClient.post<DeclarationResponseDto>(`/declarations/${id}/submit`);
  }

  // Approve declaration (admin only)
  async approveDeclaration(id: number, notes?: string): Promise<DeclarationResponseDto> {
    return apiClient.post<DeclarationResponseDto>(
      `/declarations/${id}/approve`,
      { notes }
    );
  }

  // Reject declaration (admin only)
  async rejectDeclaration(id: number, reason: string): Promise<DeclarationResponseDto> {
    return apiClient.post<DeclarationResponseDto>(
      `/declarations/${id}/reject`,
      { reason }
    );
  }

  // Cancel declaration
  async cancelDeclaration(id: number): Promise<DeclarationResponseDto> {
    return apiClient.post<DeclarationResponseDto>(`/declarations/${id}/cancel`);
  }

  // Get declaration statistics
  async getDeclarationStats(): Promise<DeclarationStatsDto> {
    return apiClient.get<DeclarationStatsDto>('/declarations/stats');
  }

  // Upload attachment to declaration
  async uploadAttachment(
    declarationId: number,
    file: File,
    onUploadProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    return apiClient.uploadFile<UploadResponse>(
      `/declarations/${declarationId}/attachments`,
      file,
      onUploadProgress
    );
  }

  // Delete attachment from declaration
  async deleteAttachment(declarationId: number, attachmentId: number): Promise<void> {
    return apiClient.delete<void>(`/declarations/${declarationId}/attachments/${attachmentId}`);
  }

  // Download attachment
  async downloadAttachment(declarationId: number, attachmentId: number, filename: string): Promise<void> {
    return apiClient.downloadFile(
      `/declarations/${declarationId}/attachments/${attachmentId}/download`,
      filename
    );
  }

  // Export declarations to Excel
  async exportDeclarations(params?: DeclarationListParams): Promise<void> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const url = `/declarations/export${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    const filename = `declarations_${new Date().toISOString().split('T')[0]}.xlsx`;
    
    return apiClient.downloadFile(url, filename);
  }

  // Get declaration history
  async getDeclarationHistory(id: number) {
    return apiClient.get(`/declarations/${id}/history`);
  }

  // Add note to declaration
  async addNote(id: number, note: string): Promise<DeclarationResponseDto> {
    return apiClient.post<DeclarationResponseDto>(
      `/declarations/${id}/notes`,
      { note }
    );
  }

  // Search declarations
  async searchDeclarations(query: string, filters?: Partial<DeclarationListParams>): Promise<DeclarationListResponse> {
    const params = {
      search: query,
      ...filters,
    };
    return this.getDeclarations(params);
  }

  // Get recently updated declarations
  async getRecentDeclarations(limit: number = 10): Promise<DeclarationResponseDto[]> {
    return apiClient.get<DeclarationResponseDto[]>(
      `/declarations/recent?limit=${limit}`
    );
  }

  // Get declarations by status
  async getDeclarationsByStatus(status: string): Promise<DeclarationResponseDto[]> {
    return apiClient.get<DeclarationResponseDto[]>(
      `/declarations?status=${status}`
    );
  }

  // Bulk operations
  async bulkApprove(ids: number[]): Promise<void> {
    return apiClient.post<void>('/declarations/bulk/approve', { ids });
  }

  async bulkReject(ids: number[], reason: string): Promise<void> {
    return apiClient.post<void>('/declarations/bulk/reject', { ids, reason });
  }

  async bulkDelete(ids: number[]): Promise<void> {
    return apiClient.post<void>('/declarations/bulk/delete', { ids });
  }
}

// Create singleton instance
export const declarationsApi = new DeclarationsApi();