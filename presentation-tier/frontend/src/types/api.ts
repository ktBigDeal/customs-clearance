export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
  first: boolean;
  last: boolean;
  numberOfElements: number;
}

export interface ApiError {
  message: string;
  code: string;
  timestamp: string;
  path: string;
  details?: Record<string, unknown>;
}

export interface UploadResponse {
  fileName: string;
  fileSize: number;
  fileType: string;
  url: string;
  uploadedAt: string;
}

export interface HealthResponse {
  status: 'UP' | 'DOWN';
  timestamp: string;
  version: string;
  environment: string;
  database: {
    status: 'UP' | 'DOWN';
    responseTime: number;
  };
  services: {
    aiGateway: 'UP' | 'DOWN';
    fileStorage: 'UP' | 'DOWN';
  };
}

export type SortDirection = 'ASC' | 'DESC';

export interface PaginationParams {
  page?: number;
  size?: number;
  sort?: string;
  direction?: SortDirection;
}

export interface SearchParams extends PaginationParams {
  search?: string;
  dateFrom?: string;
  dateTo?: string;
}