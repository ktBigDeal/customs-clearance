export interface Declaration {
  id: number;
  declarationNumber: string;
  declarationType: DeclarationType;
  status: DeclarationStatus;
  companyName: string;
  declarantName: string;
  declarantEmail: string;
  declarantPhone: string;
  goodsDescription: string;
  totalValue: number;
  currency: string;
  weight: number;
  quantity: number;
  hsCode?: string;
  originCountry: string;
  destinationCountry: string;
  portOfEntry: string;
  expectedArrival?: Date;
  submittedAt: Date;
  processedAt?: Date;
  completedAt?: Date;
  notes?: string;
  attachments?: DeclarationAttachment[];
  fees?: DeclarationFee[];
  history?: DeclarationHistory[];
  createdAt: Date;
  updatedAt: Date;
}

export type DeclarationType = 'IMPORT' | 'EXPORT' | 'TRANSIT';

export type DeclarationStatus = 
  | 'DRAFT'
  | 'SUBMITTED' 
  | 'UNDER_REVIEW'
  | 'PENDING_DOCUMENTS'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'CLEARED';

export interface DeclarationAttachment {
  id: number;
  fileName: string;
  fileSize: number;
  fileType: string;
  uploadedAt: Date;
  url: string;
}

export interface DeclarationFee {
  id: number;
  feeType: string;
  amount: number;
  currency: string;
  status: 'PENDING' | 'PAID' | 'WAIVED';
  dueDate?: Date;
  paidAt?: Date;
}

export interface DeclarationHistory {
  id: number;
  action: string;
  description: string;
  performedBy: string;
  performedAt: Date;
  oldStatus?: DeclarationStatus;
  newStatus?: DeclarationStatus;
}

export interface DeclarationRequestDto {
  declarationType: DeclarationType;
  companyName: string;
  declarantName: string;
  declarantEmail: string;
  declarantPhone: string;
  goodsDescription: string;
  totalValue: number;
  currency: string;
  weight: number;
  quantity: number;
  hsCode?: string;
  originCountry: string;
  destinationCountry: string;
  portOfEntry: string;
  expectedArrival?: string;
  notes?: string;
}

export interface DeclarationResponseDto {
  id: number;
  declarationNumber: string;
  declarationType: DeclarationType;
  status: DeclarationStatus;
  companyName: string;
  declarantName: string;
  declarantEmail: string;
  declarantPhone: string;
  goodsDescription: string;
  totalValue: number;
  currency: string;
  weight: number;
  quantity: number;
  hsCode?: string;
  originCountry: string;
  destinationCountry: string;
  portOfEntry: string;
  expectedArrival?: string;
  submittedAt: string;
  processedAt?: string;
  completedAt?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface DeclarationStatsDto {
  totalDeclarations: number;
  pendingDeclarations: number;
  approvedDeclarations: number;
  rejectedDeclarations: number;
  totalValue: number;
  averageProcessingTime: number;
  statusDistribution: Record<DeclarationStatus, number>;
  monthlyTrends: MonthlyTrend[];
}

export interface MonthlyTrend {
  month: string;
  count: number;
  totalValue: number;
}

export interface DeclarationListParams {
  page?: number;
  size?: number;
  sort?: string;
  direction?: 'ASC' | 'DESC';
  status?: DeclarationStatus;
  declarationType?: DeclarationType;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
}

export interface DeclarationListResponse {
  content: DeclarationResponseDto[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
  first: boolean;
  last: boolean;
  numberOfElements: number;
}