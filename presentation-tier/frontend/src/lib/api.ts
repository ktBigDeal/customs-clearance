/**
 * HTTP API 클라이언트 라이브러리 (백엔드 통신의 중앙 관리소)
 * 
 * 🌐 **주요 역할**: 프론트엔드와 백엔드 간의 모든 HTTP 통신을 안전하고 효율적으로 관리
 * 
 * **신입 개발자를 위한 설명**:
 * - 이 파일은 서버와 데이터를 주고받는 모든 작업을 담당합니다
 * - GET(조회), POST(생성), PUT(전체수정), PATCH(부분수정), DELETE(삭제) 메소드 제공
 * - 자동으로 인증 토큰을 모든 요청에 붙여서 보냅니다
 * - 에러가 발생하면 사용자 친화적인 메시지로 변환해줍니다
 * - 파일 업로드/다운로드 기능도 포함되어 있습니다
 * 
 * **사용된 주요 기술**:
 * - Axios: HTTP 클라이언트 라이브러리 (fetch API보다 편리함)
 * - TypeScript 제네릭: 타입 안전한 API 호출
 * - Interceptors: 모든 요청/응답을 가로채서 공통 처리
 * - Singleton 패턴: 앱 전체에서 하나의 인스턴스만 사용
 * 
 * **보안 기능**:
 * - JWT 토큰 자동 관리 (localStorage에서 읽어서 헤더에 추가)
 * - 401 Unauthorized 발생 시 자동 로그아웃 처리
 * - HTTPS 환경에서만 사용 권장
 * - 요청 타임아웃 설정으로 무한 대기 방지
 * 
 * **에러 처리 전략**:
 * - 네트워크 에러: "네트워크 연결 확인" 메시지
 * - 서버 에러: 상태 코드별 적절한 한국어 메시지
 * - 개발 환경: 상세한 에러 로그, 운영 환경: 간단한 사용자 메시지
 * 
 * @file src/lib/api.ts
 * @description 백엔드 API 통신을 위한 중앙화된 HTTP 클라이언트
 * @since 2024-01-01
 * @author Frontend Team
 * @category API 통신
 * @tutorial Axios 사용법: https://axios-http.com/docs/intro
 * @tutorial HTTP 메소드 이해하기: https://developer.mozilla.org/ko/docs/Web/HTTP/Methods
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, ApiError } from '@/types/api';

/**
 * HTTP API 클라이언트 클래스
 * 
 * 백엔드 API와의 모든 통신을 담당하는 중앙화된 클라이언트입니다.
 * 인증 토큰 관리, 오류 처리, 요청/응답 로깅 등의 기능을 제공합니다.
 * 
 * @class ApiClient
 * @example
 * ```typescript
 * // 싱글톤 인스턴스 사용
 * import { apiClient } from '@/lib/api';
 * 
 * // GET 요청
 * const users = await apiClient.get<User[]>('/users');
 * 
 * // POST 요청
 * const newUser = await apiClient.post<User>('/users', userData);
 * ```
 */

export type DeclarationType = 'IMPORT' | 'EXPORT';
export type DeclarationStatus = 'DRAFT' | 'UPDATED' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'CLEARED';

class ApiClient {
  /** Axios 인스턴스 */
  private client: AxiosInstance;

  /**
   * ApiClient 생성자
   * 
   * Axios 인스턴스를 생성하고 기본 설정을 적용합니다.
   * 베이스 URL, 타임아웃, 기본 헤더 등을 설정합니다.
   * 
   * @constructor
   */
  constructor() {
    this.client = axios.create({
      /** API 서버의 기본 URL (환경변수 또는 기본값 사용) */
      baseURL: process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : 'http://localhost:8080/api/v1',
      /** 요청 타임아웃 (100초) */
      timeout: 100000,
      /** 기본 HTTP 헤더 */
      headers: {
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * 요청/응답 인터셉터 설정
   * 
   * Axios 인터셉터를 설정하여 모든 요청에 인증 토큰을 추가하고,
   * 응답에 대한 공통 오류 처리 및 로깅을 수행합니다.
   * 
   * @private
   */
  private setupInterceptors() {
    /**
     * 요청 인터셉터
     * 모든 HTTP 요청에 대해 인증 토큰 추가 및 디버깅 정보를 설정합니다.
     */
    this.client.interceptors.request.use(
      (config) => {
        // 인증 토큰이 있으면 Authorization 헤더에 추가
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // 디버깅을 위한 요청 시작 시간 기록
        config.metadata = { requestStartedAt: Date.now() };
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response time in development
        if (process.env.NODE_ENV === 'development') {
          const duration = Date.now() - (response.config.metadata?.requestStartedAt || 0);
          console.log(`API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`);
        }
        
        return response;
      },
      (error) => {
        if (error.response) {
          // Server responded with error status
          const apiError: ApiError = {
            message: error.response.data?.message || '서버 오류가 발생했습니다.',
            code: error.response.data?.code || 'UNKNOWN_ERROR',
            timestamp: error.response.data?.timestamp || new Date().toISOString(),
            path: error.response.config?.url || '',
            details: error.response.data?.details,
          };

          // Handle specific error codes
          switch (error.response.status) {
            case 401:
              this.handleUnauthorized();
              break;
            case 403:
              apiError.message = '접근 권한이 없습니다.';
              break;
            case 404:
              apiError.message = '요청한 리소스를 찾을 수 없습니다.';
              break;
            case 500:
              apiError.message = '서버 내부 오류가 발생했습니다.';
              break;
          }

          return Promise.reject(apiError);
        } else if (error.request) {
          // Network error
          const networkError: ApiError = {
            message: '네트워크 연결을 확인해 주세요.',
            code: 'NETWORK_ERROR',
            timestamp: new Date().toISOString(),
            path: error.config?.url || '',
          };
          return Promise.reject(networkError);
        } else {
          // Request setup error
          const setupError: ApiError = {
            message: '요청 설정 중 오류가 발생했습니다.',
            code: 'REQUEST_SETUP_ERROR',
            timestamp: new Date().toISOString(),
            path: '',
          };
          return Promise.reject(setupError);
        }
      }
    );
  }

  private getAuthToken(): string | null {
    // In a real app, this would get the token from localStorage, cookies, or auth store
    if (typeof window !== 'undefined') {
      return localStorage.getItem('jwtToken');
    }
    return null;
  }

  private handleUnauthorized() {
    // Clear auth token and redirect to login
    if (typeof window !== 'undefined') {
      localStorage.removeItem('jwtToken');
      window.location.href = '/login';
    }
  }

  /**
   * HTTP GET 요청 수행
   * 
   * 지정된 URL로 GET 요청을 보내고 응답 데이터를 반환합니다.
   * 
   * @template T - 응답 데이터의 타입
   * @param {string} url - 요청할 API 엔드포인트 URL
   * @param {AxiosRequestConfig} [config] - 추가 Axios 설정 (선택적)
   * @returns {Promise<T>} 응답 데이터
   * 
   * @example
   * ```typescript
   * // 사용자 목록 조회
   * const users = await apiClient.get<User[]>('/users');
   * 
   * // 쿼리 파라미터와 함께 요청
   * const filteredUsers = await apiClient.get<User[]>('/users', {
   *   params: { role: 'admin', limit: 10 }
   * });
   * ```
   * 
   * @throws {ApiError} API 서버 오류 또는 네트워크 오류 발생 시
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return response.data as T;
  }

  /**
   * HTTP POST 요청 수행
   * 
   * 지정된 URL로 POST 요청을 보내고 응답 데이터를 반환합니다.
   * 새로운 리소스 생성 시 주로 사용됩니다.
   * 
   * @template T - 응답 데이터의 타입
   * @template D - 요청 본문 데이터의 타입
   * @param {string} url - 요청할 API 엔드포인트 URL
   * @param {D} [data] - 요청 본문에 포함할 데이터 (선택적)
   * @param {AxiosRequestConfig} [config] - 추가 Axios 설정 (선택적)
   * @returns {Promise<T>} 응답 데이터
   * 
   * @example
   * ```typescript
   * // 새 사용자 생성
   * const newUser = await apiClient.post<User, CreateUserRequest>('/users', {
   *   name: '홍길동',
   *   email: 'hong@example.com'
   * });
   * 
   * // 데이터 없이 POST 요청 (액션 트리거 등)
   * await apiClient.post('/users/123/activate');
   * ```
   * 
   * @throws {ApiError} API 서버 오류 또는 네트워크 오류 발생 시
   */
  async post<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return response.data as T;
  }

  /**
   * HTTP PUT 요청 수행
   * 
   * 지정된 URL로 PUT 요청을 보내고 응답 데이터를 반환합니다.
   * 기존 리소스의 전체 업데이트 시 주로 사용됩니다.
   * 
   * @template T - 응답 데이터의 타입
   * @template D - 요청 본문 데이터의 타입
   * @param {string} url - 요청할 API 엔드포인트 URL
   * @param {D} [data] - 요청 본문에 포함할 데이터 (선택적)
   * @param {AxiosRequestConfig} [config] - 추가 Axios 설정 (선택적)
   * @returns {Promise<T>} 응답 데이터
   * 
   * @example
   * ```typescript
   * // 사용자 정보 전체 업데이트
   * const updatedUser = await apiClient.put<User, UpdateUserRequest>('/users/123', {
   *   name: '김철수',
   *   email: 'kim@example.com',
   *   role: 'admin'
   * });
   * ```
   * 
   * @throws {ApiError} API 서버 오류 또는 네트워크 오류 발생 시
   */
  async put<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return response.data as T;
  }

  /**
   * HTTP PATCH 요청 수행
   * 
   * 지정된 URL로 PATCH 요청을 보내고 응답 데이터를 반환합니다.
   * 기존 리소스의 부분 업데이트 시 주로 사용됩니다.
   * 
   * @template T - 응답 데이터의 타입
   * @template D - 요청 본문 데이터의 타입
   * @param {string} url - 요청할 API 엔드포인트 URL
   * @param {D} [data] - 요청 본문에 포함할 데이터 (선택적)
   * @param {AxiosRequestConfig} [config] - 추가 Axios 설정 (선택적)
   * @returns {Promise<T>} 응답 데이터
   * 
   * @example
   * ```typescript
   * // 사용자 이름만 업데이트
   * const updatedUser = await apiClient.patch<User>('/users/123', {
   *   name: '이영희'
   * });
   * ```
   * 
   * @throws {ApiError} API 서버 오류 또는 네트워크 오류 발생 시
   */
  async patch<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config);
    return response.data as T;
  }

  /**
   * HTTP DELETE 요청 수행
   * 
   * 지정된 URL로 DELETE 요청을 보내고 응답 데이터를 반환합니다.
   * 리소스 삭제 시 주로 사용됩니다.
   * 
   * @template T - 응답 데이터의 타입
   * @param {string} url - 요청할 API 엔드포인트 URL
   * @param {AxiosRequestConfig} [config] - 추가 Axios 설정 (선택적)
   * @returns {Promise<T>} 응답 데이터
   * 
   * @example
   * ```typescript
   * // 사용자 삭제
   * await apiClient.delete('/users/123');
   * 
   * // 삭제된 리소스 정보 반환받기
   * const deletedUser = await apiClient.delete<User>('/users/123');
   * ```
   * 
   * @throws {ApiError} API 서버 오류 또는 네트워크 오류 발생 시
   */
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return response.data as T;
  }

  // File upload
  async uploadFile<T>(url: string, file: File, onUploadProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(progress);
        }
      },
    };

    const response = await this.client.post<ApiResponse<T>>(url, formData, config);
    return response.data as T;
  }

  // Download file
  async downloadFile(url: string, filename?: string): Promise<void> {
    const response = await this.client.get(url, {
      responseType: 'blob',
    });

    // Create download link
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Health check
  async healthCheck() {
    return this.get('/health');
  }

  /**
   * Cloud Run 프록시를 통한 API 호출 메서드들
   * 
   * Vercel의 API 프록시를 통해 Cloud Run 서비스들과 통신합니다.
   * 개발환경에서는 로컬 서비스로, 프로덕션에서는 실제 Cloud Run URL로 자동 라우팅됩니다.
   */

  /**
   * Cloud Run 서비스에 GET 요청
   * 
   * @param {string} path - API 경로 (예: 'chatbot/health', 'ocr/extract')
   * @param {AxiosRequestConfig} [config] - 추가 설정
   * @returns {Promise<T>} 응답 데이터
   */
  async cloudRunGet<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await fetch(`/api/cloud-run/${path}${config?.params ? `?${new URLSearchParams(config.params).toString()}` : ''}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
    });
    
    if (!response.ok) {
      throw new Error(`Cloud Run API 오류: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Cloud Run 서비스에 POST 요청
   * 
   * @param {string} path - API 경로
   * @param {D} [data] - 요청 본문 데이터
   * @returns {Promise<T>} 응답 데이터
   */
  async cloudRunPost<T, D = unknown>(path: string, data?: D): Promise<T> {
    const response = await fetch(`/api/cloud-run/${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`Cloud Run API 오류: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Cloud Run 서비스에 PUT 요청
   */
  async cloudRunPut<T, D = unknown>(path: string, data?: D): Promise<T> {
    const response = await fetch(`/api/cloud-run/${path}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`Cloud Run API 오류: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * Cloud Run 서비스에 DELETE 요청
   */
  async cloudRunDelete<T>(path: string): Promise<T> {
    const response = await fetch(`/api/cloud-run/${path}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
    });
    
    if (!response.ok) {
      throw new Error(`Cloud Run API 오류: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }

  /**
   * 인증 헤더 생성
   */
  private getAuthHeaders(): Record<string, string> {
    const token = this.getAuthToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

export interface OcrAnalysisRequest {
  files: File[];
  analysisType: 'invoice' | 'packing_list' | 'bill_of_lading' | 'certificate_of_origin';
}

export interface OcrAnalysisResult {
  extractedText: string;
  structuredData: any;
  confidence: number;
}

/**
 * Perform OCR analysis on uploaded files (mock implementation)
 */
export const performOcrAnalysis = async (
  request: OcrAnalysisRequest
): Promise<OcrAnalysisResult> => {
  // Mock implementation - in real app, this would call AI Gateway
  await new Promise(resolve => setTimeout(resolve, 3000)); // 3 second delay
  
  return {
    extractedText: 'Mock extracted text from documents...',
    structuredData: {
      companyInfo: {
        name: 'AI 추출된 업체명',
        address: '서울시 강남구 테헤란로 123',
        businessNumber: '123-45-67890'
      },
      goods: [
        {
          description: 'AI 추출된 상품명',
          quantity: 100,
          unitPrice: 50,
          hsCode: '1234567890'
        }
      ],
      invoice: {
        invoiceNumber: 'INV-2024-001',
        date: '2024-01-15',
        amount: 5000
      }
    },
    confidence: 0.92
  };
};

// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      requestStartedAt: number;
    };
  }
}
/**
 * HS Code 관련 API 함수들
 * Google Cloud Run 서비스와 직접 통신
 */

export interface HSCodeRecommendRequest {
  product_description: string;
  additional_info?: string;
}

export interface HSCodeRecommendResponse {
  recommended_codes: Array<{
    hs_code: string;
    description: string;
    confidence: number;
    category: string;
  }>;
  analysis_summary: string;
}

export interface USConvertRequest {
  korean_hs_code: string;
  product_description?: string;
}

export interface USConvertResponse {
  us_hs_code: string;
  korean_hs_code: string;
  description: string;
  tariff_rate?: string;
  notes?: string;
}

/**
 * HS Code 추천 API 호출
 * Google Cloud Run 서비스와 직접 통신
 */
export const recommendHSCode = async (
  request: HSCodeRecommendRequest
): Promise<HSCodeRecommendResponse> => {
  const RECOMMEND_URL = process.env.NEXT_PUBLIC_HSCODE_RECOMMEND_URL;
  
  if (!RECOMMEND_URL) {
    throw new Error('HS Code 추천 서비스 URL이 설정되지 않았습니다.');
  }

  const response = await fetch(`${RECOMMEND_URL}/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HS Code 추천 API 오류: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
};

/**
 * US HS Code 변환 API 호출
 * Google Cloud Run 서비스와 직접 통신
 */
export const convertToUSHSCode = async (
  request: USConvertRequest
): Promise<USConvertResponse> => {
  const CONVERT_URL = process.env.NEXT_PUBLIC_HSCODE_US_CONVERT_URL;
  
  if (!CONVERT_URL) {
    throw new Error('US HS Code 변환 서비스 URL이 설정되지 않았습니다.');
  }

  const response = await fetch(`${CONVERT_URL}/convert`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`US HS Code 변환 API 오류: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
};

/**
 * HS Code 서비스들의 헬스 체크
 */
export const checkHSCodeServices = async (): Promise<{
  recommend: { status: boolean; url: string };
  convert: { status: boolean; url: string };
}> => {
  const RECOMMEND_URL = process.env.NEXT_PUBLIC_HSCODE_RECOMMEND_URL;
  const CONVERT_URL = process.env.NEXT_PUBLIC_HSCODE_US_CONVERT_URL;

  const [recommendHealth, convertHealth] = await Promise.allSettled([
    fetch(`${RECOMMEND_URL}/health`).then(res => res.ok),
    fetch(`${CONVERT_URL}/health`).then(res => res.ok)
  ]);

  return {
    recommend: {
      status: recommendHealth.status === 'fulfilled' ? recommendHealth.value : false,
      url: RECOMMEND_URL || 'URL 미설정'
    },
    convert: {
      status: convertHealth.status === 'fulfilled' ? convertHealth.value : false,
      url: CONVERT_URL || 'URL 미설정'
    }
  };
};

/**
 * HS Code 서비스 API 문서 확인 (개발용)
 */
export const getHSCodeServiceDocs = (): {
  recommend: string;
  convert: string;
} => {
  const RECOMMEND_URL = process.env.NEXT_PUBLIC_HSCODE_RECOMMEND_URL;
  const CONVERT_URL = process.env.NEXT_PUBLIC_HSCODE_US_CONVERT_URL;

  return {
    recommend: `${RECOMMEND_URL}/docs`,
    convert: `${CONVERT_URL}/docs`
  };
};
