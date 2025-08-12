/**
 * 통합 타입 정의 — backend 엔티티(Declaration, Attachment) 및 enum에 맞춤
 * 참고: Declaration.java의 내부 enum — DeclarationType{IMPORT,EXPORT}, DeclarationStatus{DRAFT,UPDATED,SUBMITTED,APPROVED,REJECTED}
 * 업로드된 엔티티 파일이 일부 생략(...)되어 있어 필드는 안전한 최소 필드 집합 + 선택 필드로 정의했습니다.
 * 실제 필드명이 다를 가능성이 있으므로 필요 시 후속 커밋에서 맞춤 보정하세요.
 */

export type ID = number;

/** 신고 유형 */
export enum DeclarationType {
  IMPORT = 'IMPORT',
  EXPORT = 'EXPORT',
}

/** 신고 상태 */
export enum DeclarationStatus {
  DRAFT = 'DRAFT',
  UPDATED = 'UPDATED',
  SUBMITTED = 'SUBMITTED',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}

/** XML 문서 타입 (Controller: /{id}/xml?docType=import|export) */
export type XmlDocType = 'import' | 'export';

/** 첨부 파일 엔티티 — Attachment.java 기반(일부 필드는 업로드본에서 생략되어 optional 처리) */
export interface Attachment {
  id: ID;
  declarationId: ID;
  filename: string;
  originalFilename?: string;
  filePath?: string;
  fileSize?: number;
  contentType?: string;
  uploadedBy?: ID;
  createdAt?: string; // ISO
  updatedAt?: string; // ISO
  /** 확장 필드 수용 */
  [key: string]: any;
}

/** 신고 엔티티 — Declaration.java 기반(필드 일부는 optional) */
export interface Declaration {
  id: ID;
  declarationNumber?: string;
  declarationType: DeclarationType;
  status: DeclarationStatus;
  // 추정/관례 필드 (업로드본에서 BaseEntity 언급) → optional로 안전 처리
  details?: Record<string, any> | null; // Map/JSON 등 상세정보 컨테이너
  remarks?: string | null;
  createdAt?: string; // ISO
  updatedAt?: string; // ISO
  createdBy?: string;
  updatedBy?: string;
  /** 확장 필드 수용 */
  [key: string]: any;
}

/** 생성/수정 요청 DTO — Map<String,Object> 기반으로 오는 케이스를 수용 */
export interface DeclarationRequestDto {
  declarationNumber?: string;
  declarationType: DeclarationType;
  status?: DeclarationStatus; // 기본 DRAFT 가정
  // 백엔드가 Map 기반으로 받는 값들을 유연 수용
  [key: string]: any;
}

/** 응답 DTO — Declaration + 확장 필드 */
export interface DeclarationResponseDto extends Declaration {}

/** 상세 조회 응답 — Controller가 Map<String,Object>로 내려줄 수 있어 유연하게 수용 */
export interface DeclarationDetailResponse {
  declaration?: Declaration;
  attachments?: Attachment[];
  [key: string]: any;
}

/** 생성 시 파일 페이로드 타입 */
export interface DeclarationCreateFiles {
  invoiceFile?: File;
  packingListFile?: File;
  billOfLadingFile?: File;
  certificateOfOriginFile?: File;
  [key: string]: File | undefined;
}
