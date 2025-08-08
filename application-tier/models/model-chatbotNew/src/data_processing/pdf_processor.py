"""
PDF Document Processor Module

PDF 문서를 텍스트 추출, 청킹, 메타데이터 보강을 통해 벡터 DB에 저장할 수 있는 형태로 처리하는 모듈입니다.
법령과는 다른 특성을 가진 PDF 문서들(제한품목, 작성요령 등)을 효과적으로 처리합니다.

Classes:
    PDFDocumentProcessor: PDF 문서 처리 및 청킹을 담당하는 메인 클래스
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import traceback

# PDF 처리 라이브러리들
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    
try:
    import tabula
    HAS_TABULA = True
except ImportError:
    HAS_TABULA = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

from ..config.config import get_setting
from .file_utils import save_chunks_as_jsonl

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFDocumentProcessor:
    """PDF 문서를 청킹하여 벡터 DB용으로 처리하는 클래스
    
    이 클래스는 다양한 유형의 PDF 문서(제한품목, 작성요령 등)를 분석하여
    문서 특성에 맞는 청킹 전략을 적용하고 메타데이터를 보강합니다.
    
    Attributes:
        pdf_path (Path): 처리할 PDF 파일 경로
        document_type (str): 문서 유형 분류 결과
        documents (List[Dict]): 처리된 문서 청크들의 리스트
        extraction_method (str): 사용할 추출 방법
    """

    def __init__(self, pdf_path: Path, document_name: str = None):
        """
        Args:
            pdf_path (Path): PDF 파일 경로
            document_name (str): 문서명 (경로에서 자동 추출 가능)
        """
        self.pdf_path = pdf_path
        self.document_name = document_name or pdf_path.stem
        self.document_type = self.classify_document_type()
        self.documents = []
        self.extraction_method = get_setting("pdf_processing.extraction_method", "hybrid")
        
        # 의존성 확인
        self._check_dependencies()
        
        logger.info(f"PDFDocumentProcessor initialized for: {self.document_name}")

    def _check_dependencies(self) -> None:
        """필요한 라이브러리 의존성 확인"""
        missing_deps = []
        
        if not HAS_PYPDF2:
            missing_deps.append("PyPDF2")
        if not HAS_PDFPLUMBER:
            missing_deps.append("pdfplumber")
        if not HAS_TABULA:
            missing_deps.append("tabula-py")
            
        if missing_deps:
            logger.warning(f"Missing PDF processing dependencies: {', '.join(missing_deps)}")
            print(f"⚠️ 누락된 PDF 처리 라이브러리: {', '.join(missing_deps)}")
            print("pip install -r requirements.txt 로 설치해주세요.")

    def classify_document_type(self) -> str:
        """문서 유형 분류
        
        파일명과 초기 내용을 바탕으로 문서 유형을 분류합니다.
        
        Returns:
            str: 문서 유형 ("restriction_list", "guideline", "statistics", "consultation_case", "other")
        """
        filename = self.document_name.lower()
        
        # 파일명 기반 분류
        if any(keyword in filename for keyword in ["제한품목", "금지품목", "restricted", "prohibited"]):
            return "restriction_list"
        elif any(keyword in filename for keyword in ["작성요령", "신고서", "guide", "manual"]):
            return "guideline" 
        elif any(keyword in filename for keyword in ["통계부호", "statistics", "code"]):
            return "statistics"
        elif any(keyword in filename for keyword in ["민원상담", "상담사례", "consultation", "민원", "사례집"]):
            return "consultation_case"
        else:
            return "other"

    def extract_text_pypdf2(self) -> str:
        """PyPDF2를 사용한 기본 텍스트 추출
        
        Returns:
            str: 추출된 텍스트
        """
        if not HAS_PYPDF2:
            return ""
            
        try:
            text_content = ""
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content += f"\n--- 페이지 {page_num + 1} ---\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"페이지 {page_num + 1} 텍스트 추출 실패: {e}")
                        
            return text_content
        except Exception as e:
            logger.error(f"PyPDF2 텍스트 추출 실패: {e}")
            return ""

    def extract_text_pdfplumber(self) -> Tuple[str, List[Dict]]:
        """pdfplumber를 사용한 정교한 텍스트 및 테이블 추출
        
        Returns:
            Tuple[str, List[Dict]]: (텍스트 내용, 테이블 리스트)
        """
        if not HAS_PDFPLUMBER:
            return "", []
            
        try:
            text_content = ""
            tables = []
            
            with pdfplumber.open(self.pdf_path) as pdf:
                # 민원상담 사례집의 경우 페이지 43-1072만 처리
                if self.document_type == "consultation_case":
                    start_page = 42  # 0-based index (43 page)
                    end_page = min(1072, len(pdf.pages))  # 1072 page까지
                    pages_to_process = pdf.pages[start_page:end_page]
                    page_offset = start_page
                else:
                    pages_to_process = pdf.pages
                    page_offset = 0
                
                for page_idx, page in enumerate(pages_to_process):
                    page_num = page_idx + page_offset + 1  # 실제 페이지 번호
                    try:
                        # 텍스트 추출
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_content += f"\n--- 페이지 {page_num} ---\n{page_text}\n"
                        
                        # 테이블 추출
                        page_tables = page.extract_tables()
                        if page_tables:
                            for table_idx, table in enumerate(page_tables):
                                if table and len(table) >= get_setting("pdf_processing.table_extraction.min_rows", 2):
                                    tables.append({
                                        "page": page_num,
                                        "table_index": table_idx + 1,
                                        "data": table,
                                        "rows": len(table),
                                        "cols": len(table[0]) if table else 0
                                    })
                                    
                    except Exception as e:
                        logger.warning(f"페이지 {page_num} pdfplumber 추출 실패: {e}")
                        
            return text_content, tables
        except Exception as e:
            logger.error(f"pdfplumber 추출 실패: {e}")
            return "", []

    def extract_tables_tabula(self) -> List[Dict]:
        """tabula-py를 사용한 테이블 전용 추출
        
        Returns:
            List[Dict]: 추출된 테이블 리스트
        """
        if not HAS_TABULA:
            return []
            
        try:
            # 모든 페이지에서 테이블 추출
            dfs = tabula.read_pdf(str(self.pdf_path), pages='all', multiple_tables=True)
            
            tables = []
            for idx, df in enumerate(dfs):
                if not df.empty and len(df) >= get_setting("pdf_processing.table_extraction.min_rows", 2):
                    tables.append({
                        "table_index": idx + 1,
                        "data": df.values.tolist(),
                        "columns": df.columns.tolist(),
                        "rows": len(df),
                        "cols": len(df.columns),
                        "extraction_method": "tabula"
                    })
                    
            return tables
        except Exception as e:
            logger.error(f"tabula 테이블 추출 실패: {e}")
            return []

    def extract_content(self) -> Dict[str, Any]:
        """하이브리드 방식으로 PDF 내용 추출
        
        Returns:
            Dict[str, Any]: 추출된 내용 (텍스트, 테이블, 메타데이터)
        """
        content = {
            "text": "",
            "tables": [],
            "extraction_methods": [],
            "page_count": 0,
            "extraction_success": False
        }
        
        try:
            # 페이지 수 확인
            if HAS_PYPDF2:
                with open(self.pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    content["page_count"] = len(pdf_reader.pages)
            
            # 추출 방법에 따른 처리
            if self.extraction_method in ["text", "hybrid"]:
                # pdfplumber 우선 시도
                text, plumber_tables = self.extract_text_pdfplumber()
                if text.strip():
                    content["text"] = text
                    content["tables"].extend(plumber_tables)
                    content["extraction_methods"].append("pdfplumber")
                else:
                    # pdfplumber 실패시 PyPDF2 시도
                    text = self.extract_text_pypdf2()
                    if text.strip():
                        content["text"] = text
                        content["extraction_methods"].append("pypdf2")
            
            if self.extraction_method in ["table", "hybrid"]:
                # tabula로 테이블 추가 추출
                tabula_tables = self.extract_tables_tabula()
                content["tables"].extend(tabula_tables)
                if tabula_tables:
                    content["extraction_methods"].append("tabula")
            
            # OCR은 필요시에만 (텍스트 추출이 실패한 경우)
            if not content["text"].strip() and self.extraction_method in ["ocr", "hybrid"]:
                logger.info("텍스트 추출 실패, OCR 시도는 현재 구현되지 않음")
                # TODO: OCR 구현 필요시 추가
            
            content["extraction_success"] = bool(content["text"].strip() or content["tables"])
            
        except Exception as e:
            logger.error(f"PDF 내용 추출 실패: {e}")
            logger.error(traceback.format_exc())
        
        return content

    def clean_text(self, text: str) -> str:
        """텍스트 정제
        
        Args:
            text (str): 원본 텍스트
            
        Returns:
            str: 정제된 텍스트
        """
        if not text:
            return ""
        
        # 페이지 구분자 제거
        text = re.sub(r'\n--- 페이지 \d+ ---\n', '\n', text)
        
        # 과도한 공백 정리
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 양쪽 공백 제거
        text = text.strip()
        
        return text

    def extract_hs_codes(self, text: str) -> List[str]:
        """HS코드 패턴 추출
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            List[str]: 추출된 HS코드 리스트
        """
        # HS코드 패턴: 4-6자리.2자리.2자리 또는 4자리.2자리 형태
        hs_patterns = [
            r'\b\d{4}\.\d{2}\.\d{2}\b',  # 1234.56.78
            r'\b\d{4}\.\d{2}\b',         # 1234.56
            r'\b\d{6}\.\d{2}\b',         # 123456.78
            r'\b\d{8}\b'                 # 12345678 (점 없는 형태)
        ]
        
        hs_codes = set()
        for pattern in hs_patterns:
            matches = re.findall(pattern, text)
            hs_codes.update(matches)
        
        return list(hs_codes)

    def find_related_law_references(self, text: str) -> List[str]:
        """관련 법령 참조 추출
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            List[str]: 관련 법령 참조 리스트
        """
        # 관세법 관련 참조 패턴
        law_patterns = [
            r'관세법\s*제\d+조(?:의\d+)?(?:제\d+항)?',
            r'관세법\s*시행령\s*제\d+조(?:의\d+)?(?:제\d+항)?',
            r'관세법\s*시행규칙\s*제\d+조(?:의\d+)?(?:제\d+항)?',
            r'「[^」]+」\s*제\d+조(?:의\d+)?(?:제\d+항)?'
        ]
        
        references = set()
        for pattern in law_patterns:
            matches = re.findall(pattern, text)
            references.update(matches)
        
        return list(references)

    def chunk_restriction_items(self, content: Dict[str, Any]) -> List[Dict]:
        """제한품목 문서 청킹 (품목별)
        
        Args:
            content (Dict): 추출된 PDF 내용
            
        Returns:
            List[Dict]: 청킹된 문서 리스트
        """
        chunks = []
        text = content.get("text", "")
        tables = content.get("tables", [])
        
        # 테이블이 있는 경우 테이블 기반 청킹
        if tables:
            for table_idx, table in enumerate(tables):
                table_data = table.get("data", [])
                if not table_data:
                    continue
                
                # 테이블 행별로 청킹 (헤더 제외)
                headers = table_data[0] if table_data else []
                for row_idx, row in enumerate(table_data[1:], 1):
                    if not any(cell and str(cell).strip() for cell in row):
                        continue  # 빈 행 스킵
                    
                    # 행을 텍스트로 변환
                    row_text = ""
                    for col_idx, cell in enumerate(row):
                        if col_idx < len(headers) and headers[col_idx]:
                            row_text += f"{headers[col_idx]}: {cell}\n"
                        else:
                            row_text += f"{cell}\n"
                    
                    row_text = self.clean_text(row_text)
                    if len(row_text) < get_setting("pdf_processing.min_chunk_size", 50):
                        continue
                    
                    # HS코드 추출
                    hs_codes = self.extract_hs_codes(row_text)
                    law_refs = self.find_related_law_references(row_text)
                    
                    chunk = {
                        "index": f"table_{table_idx + 1}_row_{row_idx}",
                        "title": f"{self.document_name} - 테이블 {table_idx + 1} 항목 {row_idx}",
                        "content": row_text,
                        "metadata": {
                            "document_type": self.document_type,
                            "source_pdf": self.pdf_path.name,
                            "category": self._get_category_from_name(self.document_name),
                            "page_number": table.get("page", None),
                            "table_index": table_idx + 1,
                            "row_index": row_idx,
                            "extraction_method": "table",
                            "hs_codes": hs_codes,
                            "related_law_references": law_refs,
                            "chunk_type": "item_based"
                        }
                    }
                    chunks.append(chunk)
        
        # 텍스트 기반 청킹 (테이블이 없거나 추가 텍스트가 있는 경우)
        if text and text.strip():
            text_chunks = self._chunk_text_by_sections(text)
            for idx, chunk_text in enumerate(text_chunks):
                if len(chunk_text) < get_setting("pdf_processing.min_chunk_size", 50):
                    continue
                
                hs_codes = self.extract_hs_codes(chunk_text)
                law_refs = self.find_related_law_references(chunk_text)
                
                chunk = {
                    "index": f"text_section_{idx + 1}",
                    "title": f"{self.document_name} - 섹션 {idx + 1}",
                    "content": chunk_text,
                    "metadata": {
                        "document_type": self.document_type,
                        "source_pdf": self.pdf_path.name,
                        "category": self._get_category_from_name(self.document_name),
                        "extraction_method": "text",
                        "hs_codes": hs_codes,
                        "related_law_references": law_refs,
                        "chunk_type": "section_based"
                    }
                }
                chunks.append(chunk)
        
        return chunks

    def chunk_guideline(self, content: Dict[str, Any]) -> List[Dict]:
        """가이드라인 문서 청킹 (섹션별)
        
        Args:
            content (Dict): 추출된 PDF 내용
            
        Returns:
            List[Dict]: 청킹된 문서 리스트
        """
        chunks = []
        text = content.get("text", "")
        
        if not text.strip():
            return chunks
        
        # 섹션별 청킹 (제목 패턴 기반)
        sections = self._split_by_headings(text)
        
        for idx, (heading, section_text) in enumerate(sections):
            clean_text = self.clean_text(section_text)
            if len(clean_text) < get_setting("pdf_processing.min_chunk_size", 50):
                continue
            
            law_refs = self.find_related_law_references(clean_text)
            
            chunk = {
                "index": f"section_{idx + 1}",
                "title": heading or f"{self.document_name} - 섹션 {idx + 1}",
                "content": clean_text,
                "metadata": {
                    "document_type": self.document_type,
                    "source_pdf": self.pdf_path.name,
                    "category": self._get_category_from_name(self.document_name),
                    "extraction_method": "text",
                    "related_law_references": law_refs,
                    "chunk_type": "section_based",
                    "section_heading": heading
                }
            }
            chunks.append(chunk)
        
        return chunks

    def chunk_statistics(self, content: Dict[str, Any]) -> List[Dict]:
        """통계/코드 문서 청킹 (카테고리별)
        
        Args:
            content (Dict): 추출된 PDF 내용
            
        Returns:
            List[Dict]: 청킹된 문서 리스트
        """
        chunks = []
        text = content.get("text", "")
        tables = content.get("tables", [])
        
        # 테이블 우선 처리
        if tables:
            for table_idx, table in enumerate(tables):
                table_data = table.get("data", [])
                if not table_data:
                    continue
                
                # 테이블 전체를 하나의 청크로 처리 (너무 큰 경우 분할)
                table_text = self._table_to_text(table_data)
                table_chunks = self._split_large_chunk(table_text)
                
                for chunk_idx, chunk_text in enumerate(table_chunks):
                    if len(chunk_text) < get_setting("pdf_processing.min_chunk_size", 50):
                        continue
                    
                    chunk = {
                        "index": f"table_{table_idx + 1}_part_{chunk_idx + 1}",
                        "title": f"{self.document_name} - 테이블 {table_idx + 1}",
                        "content": chunk_text,
                        "metadata": {
                            "document_type": self.document_type,
                            "source_pdf": self.pdf_path.name,
                            "category": self._get_category_from_name(self.document_name),
                            "page_number": table.get("page", None),
                            "table_index": table_idx + 1,
                            "extraction_method": "table",
                            "chunk_type": "category_based"
                        }
                    }
                    chunks.append(chunk)
        
        # 텍스트 처리
        if text.strip():
            text_chunks = self._chunk_text_by_sections(text)
            for idx, chunk_text in enumerate(text_chunks):
                if len(chunk_text) < get_setting("pdf_processing.min_chunk_size", 50):
                    continue
                
                chunk = {
                    "index": f"text_category_{idx + 1}",
                    "title": f"{self.document_name} - 카테고리 {idx + 1}",
                    "content": chunk_text,
                    "metadata": {
                        "document_type": self.document_type,
                        "source_pdf": self.pdf_path.name,
                        "category": self._get_category_from_name(self.document_name),
                        "extraction_method": "text",
                        "chunk_type": "category_based"
                    }
                }
                chunks.append(chunk)
        
        return chunks

    def chunk_consultation_cases(self, content: Dict[str, Any]) -> List[Dict]:
        """민원상담 사례집 청킹 (사례별)
        
        Args:
            content (Dict): 추출된 PDF 내용
            
        Returns:
            List[Dict]: 청킹된 문서 리스트
        """
        chunks = []
        text = content.get("text", "")
        
        if not text.strip():
            return chunks
        
        # 민원상담 사례의 경우 페이지 마커가 필요하므로 원본 텍스트 사용
        # 상담 사례 경계 감지
        case_boundaries = self._detect_consultation_case_boundaries(text)
        if not case_boundaries:
            logger.warning("민원상담 사례를 찾을 수 없습니다")
            return chunks
        
        # 각 사례 처리
        case_number = 1
        for start_pos, end_pos, case_title, subtitle, page_num in case_boundaries:
            try:
                # 사례 텍스트 추출 및 정제
                raw_case_text = text[start_pos:end_pos].strip()
                case_text = self.clean_text(raw_case_text)
                
                if len(case_text) < 100:  # 너무 짧은 사례 스킵
                    logger.warning(f"사례가 너무 짧음: {case_title}")
                    continue
                
                # 사례 내용 파싱 (소제목 포함)
                case_data = self._parse_consultation_case_content(case_text, case_title, subtitle)
                
                # 질문이나 답변이 없으면 스킵
                if not case_data['question'] and not case_data['answer']:
                    logger.warning(f"질문이나 답변이 없는 사례: {case_title}")
                    continue
                
                # 카테고리 및 상담 유형 분류
                category, consultation_type = self._categorize_consultation_case(case_data)
                
                # 컨텐츠 포맷팅 (소제목 포함)
                formatted_content = self._format_consultation_content(case_data, category, case_number, subtitle)
                
                # 메타데이터 생성 (페이지 번호 포함)
                metadata = self._create_consultation_metadata(case_data, category, consultation_type, page_num)
                
                # 최종 청크 생성
                consultation_chunk = {
                    "content": formatted_content,
                    "metadata": metadata
                }
                
                chunks.append(consultation_chunk)
                case_number += 1
                
            except Exception as e:
                logger.error(f"사례 처리 실패: {case_title} - {e}")
                continue
        
        logger.info(f"민원상담 사례 처리 완료: {len(chunks)}개 사례 생성")
        return chunks

    def _detect_consultation_case_boundaries(self, text: str) -> List[Tuple[int, int, str, str, int]]:
        """민원상담 사례의 경계를 감지"""
        # 페이지별로 처리하여 페이지 번호 추출
        page_sections = re.split(r'\n--- 페이지 (\d+) ---\n', text)
        
        case_boundaries = []
        
        for i in range(1, len(page_sections), 2):  # 페이지 번호가 홀수 인덱스에 있음
            page_num = int(page_sections[i])
            page_text = page_sections[i + 1] if i + 1 < len(page_sections) else ""
            
            # 사례 번호 패턴들 (실제 PDF 구조에 맞게)
            case_number_patterns = [
                r'^\s*(\d+)\s*\n●\s*\n([^\n]+)',  # "74\n●\n제목" 형태 (실제 구조)
                r'^\s*(\d+)\s*\n●\s*([^\n]+)',   # "74\n● 제목" 형태
                r'^\s*(\d+)\s*\n([가-힣\s]+)',   # "74\n제목" 형태 (한국어만)
                r'^\s*(\d+)\s*\n([^\n]{5,})',    # "74\n제목" 형태 (최소 5글자)
            ]
            
            page_start_pos = text.find(f"--- 페이지 {page_num} ---")
            
            for pattern in case_number_patterns:
                matches = re.finditer(pattern, page_text, re.MULTILINE)
                for match in matches:
                    case_number = match.group(1).strip()
                    subtitle = match.group(2).strip()
                    
                    # 소제목이 유효한지 확인 (너무 짧거나 의미없는 경우 스킵)
                    if len(subtitle) < 5 or len(case_number) > 3:
                        continue
                    
                    # 전체 텍스트에서의 위치 계산
                    case_start_in_page = match.start()
                    absolute_start_pos = page_start_pos + len(f"--- 페이지 {page_num} ---\n") + case_start_in_page
                    
                    case_boundaries.append((absolute_start_pos, -1, f"사례 {case_number}", subtitle, page_num))
        
        # 중복 제거 및 정렬
        case_boundaries = list(set(case_boundaries))
        case_boundaries.sort(key=lambda x: x[0])
        
        # 각 사례의 끝 위치 계산
        for i in range(len(case_boundaries)):
            start_pos, _, case_title, subtitle, page_num = case_boundaries[i]
            
            if i + 1 < len(case_boundaries):
                end_pos = case_boundaries[i + 1][0]
            else:
                end_pos = len(text)
            
            case_boundaries[i] = (start_pos, end_pos, case_title, subtitle, page_num)
        
        logger.info(f"감지된 민원상담 사례 수: {len(case_boundaries)}")
        return case_boundaries

    def _parse_consultation_case_content(self, case_text: str, case_title: str, subtitle: str = "") -> Dict[str, str]:
        """개별 상담 사례에서 질문, 답변, 관련법령 추출"""
        case_data = {
            "title": case_title,
            "subtitle": subtitle,
            "question": "",
            "answer": "",
            "related_laws": "",
            "keywords": []
        }
        
        # 질문 부분 추출 패턴 (실제 PDF 구조 기반)
        question_patterns = [
            r'구매자?\s+[A-Z가-힣]\s*는?\s+(.*?)(?=관세법|세법|답변|관련법령|$)',  # "구매자 B는..." 패턴
            r'(?:질문|문의)\s*[:\-]?\s*(.*?)(?=관세법|세법|답변|관련법령|$)',
            r'^([^?]*\?[^?]*?)(?=관세법|세법|답변|관련법령|$)',  # 물음표로 끝나는 문장
            r'(.{20,}하는가\?|.{20,}되는가\?|.{20,}인가\?)',  # 한국어 의문 표현
        ]
        
        # 답변 부분 추출 패턴 (관세법으로 시작하는 답변)
        answer_patterns = [
            r'(관세법[^●]+?)(?=관련법령|●|$)',  # 관세법으로 시작하는 답변
            r'(세법[^●]+?)(?=관련법령|●|$)',    # 세법으로 시작하는 답변
            r'답변\s*[:\-]?\s*(.*?)(?=관련법령|●|$)',
            r'(따라서[^●]+?)(?=관련법령|●|$)',  # "따라서"로 시작하는 결론 부분
        ]
        
        # 관련법령 추출 패턴
        law_patterns = [
            r'관련\s*법령?\s*[:\-]?\s*(.*?)$',
            r'법령\s*[:\-]?\s*(.*?)$',
            r'참고\s*[:\-]?\s*(.*?)$',
            r'근거\s*[:\-]?\s*(.*?)$'
        ]
        
        # 질문 추출
        for pattern in question_patterns:
            match = re.search(pattern, case_text, re.DOTALL | re.IGNORECASE)
            if match and match.group(1).strip():
                case_data["question"] = match.group(1).strip()
                break
        
        # 답변 추출
        for pattern in answer_patterns:
            match = re.search(pattern, case_text, re.DOTALL | re.IGNORECASE)
            if match and match.group(1).strip():
                case_data["answer"] = match.group(1).strip()
                break
        
        # 관련법령 추출
        for pattern in law_patterns:
            match = re.search(pattern, case_text, re.DOTALL | re.IGNORECASE)
            if match and match.group(1).strip():
                case_data["related_laws"] = match.group(1).strip()
                break
        
        # 키워드 추출 (질문과 답변에서)
        combined_text = f"{case_data['question']} {case_data['answer']}"
        case_data["keywords"] = self._extract_consultation_keywords(combined_text)
        
        return case_data

    def _extract_consultation_keywords(self, text: str) -> List[str]:
        """텍스트에서 상담 관련 중요 키워드 추출"""
        if not text:
            return []
        
        # 관세행정 관련 주요 키워드들
        important_keywords = [
            # 통관 관련
            "통관", "수입신고", "수출신고", "관세", "관세율", "세율",
            # 품목 관련  
            "HS코드", "품목분류", "원산지", "FTA", "협정세율",
            # 절차 관련
            "신고서", "작성요령", "제출서류", "증명서", "허가", "승인",
            # 기관 관련
            "세관", "관세청", "검역", "검사", "심사",
            # 의료/식품 관련
            "의료기기", "의약품", "식품", "건강기능식품", "화장품",
            # 특수 품목
            "농산물", "수산물", "축산물", "공산품", "화학물질"
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in important_keywords:
            if keyword in text or keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        # HS코드 패턴 추출
        hs_codes = re.findall(r'\b\d{4}\.?\d{2}\.?\d{2}\.?\d{0,2}\b', text)
        found_keywords.extend([f"HS{code}" for code in hs_codes[:3]])  # 최대 3개
        
        # 법령 참조 추출
        law_refs = re.findall(r'관세법[^\s]*|시행령[^\s]*|시행규칙[^\s]*', text)
        found_keywords.extend(law_refs[:2])  # 최대 2개
        
        return list(set(found_keywords))  # 중복 제거

    def _categorize_consultation_case(self, case_data: Dict[str, str]) -> Tuple[str, str]:
        """상담 사례의 카테고리와 상담 유형 분류"""
        combined_text = f"{case_data['title']} {case_data['question']} {case_data['answer']}".lower()
        
        # 카테고리 분류
        category_keywords = {
            "통관": ["통관", "신고", "신고서", "세관", "검사", "심사", "수입신고", "수출신고"],
            "관세": ["관세", "세율", "관세율", "부과", "납부", "감면", "환급"],
            "원산지": ["원산지", "fta", "협정", "협정세율", "특혜", "증명서"],
            "품목분류": ["hs코드", "품목분류", "분류", "세번", "해석", "결정"],
            "기타": []
        }
        
        category = "기타"
        for cat, keywords in category_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                category = cat
                break
        
        # 상담 유형 분류
        consultation_type_keywords = {
            "의료기기": ["의료기기", "의료용품", "의료"],
            "식품": ["식품", "건강기능식품", "농산물", "수산물", "축산물"],
            "화학물질": ["화학", "화학물질", "화학제품", "화학품"],
            "일반수입": ["수입", "구매", "매입"],
            "일반수출": ["수출", "판매", "매출"],
            "기타": []
        }
        
        consultation_type = "기타"
        for c_type, keywords in consultation_type_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                consultation_type = c_type
                break
        
        return category, consultation_type

    def _format_consultation_content(self, case_data: Dict[str, str], category: str, case_number: int, subtitle: str = "") -> str:
        """상담 사례를 RAG 검색에 최적화된 컨텐츠로 포맷팅"""
        content_parts = []
        
        # 소제목 부분 (대괄호로 감싸기)
        if subtitle:
            content_parts.append(f"[{subtitle}]")
        
        # 사례 제목 부분  
        title = f"{case_data['title']}"
        content_parts.append(title)
        
        # 질문 부분
        if case_data['question']:
            content_parts.append(f"질문: {case_data['question']}")
        
        # 답변 부분
        if case_data['answer']:
            content_parts.append(f"답변: {case_data['answer']}")
        
        # 관련법령 부분
        if case_data['related_laws']:
            content_parts.append(f"관련법령: {case_data['related_laws']}")
        
        # 키워드 부분
        if case_data['keywords']:
            keywords_str = ", ".join(case_data['keywords'])
            content_parts.append(f"키워드: 민원상담, 사례집, {keywords_str}")
        else:
            content_parts.append("키워드: 민원상담, 사례집")
        
        return "\n".join(content_parts)

    def _create_consultation_metadata(self, case_data: Dict[str, str], category: str, consultation_type: str, page_number: int) -> Dict[str, Any]:
        """상담 사례의 메타데이터 생성"""
        # 관련 법령 리스트 추출
        related_laws = []
        if case_data['related_laws']:
            # 관세법, 시행령, 시행규칙 등 추출
            law_patterns = [
                r'관세법\s*제\d+조(?:의\d+)?(?:제\d+항)?',
                r'시행령\s*제\d+조(?:의\d+)?(?:제\d+항)?',
                r'시행규칙\s*제\d+조(?:의\d+)?(?:제\d+항)?'
            ]
            
            for pattern in law_patterns:
                matches = re.findall(pattern, case_data['related_laws'])
                related_laws.extend(matches)
        
        metadata = {
            "data_type": "consultation_case",
            "data_source": "관세행정_민원상담_사례집",
            "document_type": "consultation_case",
            "category": category,
            "consultation_type": consultation_type,
            "page_number": page_number,
            "keywords": case_data['keywords'],
            "related_law_references": related_laws,
            "content_structure": {
                "has_question": bool(case_data['question']),
                "has_answer": bool(case_data['answer']),
                "has_law_references": bool(case_data['related_laws'])
            }
        }
        
        return metadata

    def _get_category_from_name(self, name: str) -> str:
        """문서명에서 카테고리 추출"""
        name_lower = name.lower()
        if "수입제한" in name_lower:
            return "수입제한"
        elif "수출제한" in name_lower:
            return "수출제한"
        elif "수출금지" in name_lower:
            return "수출금지"
        elif "작성요령" in name_lower:
            return "작성요령"
        elif "통계" in name_lower:
            return "무역통계"
        elif any(keyword in name_lower for keyword in ["민원상담", "상담사례", "민원", "사례집"]):
            return "민원상담"
        else:
            return "기타"

    def _chunk_text_by_sections(self, text: str, max_size: int = None) -> List[str]:
        """텍스트를 섹션별로 청킹"""
        if max_size is None:
            max_size = get_setting("pdf_processing.max_chunk_size", 1500)
        
        # 단락별로 분할
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def _split_by_headings(self, text: str) -> List[Tuple[str, str]]:
        """제목 패턴으로 텍스트 분할"""
        # 제목 패턴들 (숫자. 형태, 가. 나. 형태 등)
        heading_patterns = [
            r'^(\d+\.\s+[^\n]+)',  # 1. 제목
            r'^([가-힣]\.\s+[^\n]+)',  # 가. 제목
            r'^([IVX]+\.\s+[^\n]+)',  # I. 제목 (로마숫자)
            r'^([A-Z]\.\s+[^\n]+)',  # A. 제목
        ]
        
        sections = []
        current_heading = ""
        current_content = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                current_content += '\n'
                continue
            
            # 제목 패턴 확인
            is_heading = False
            for pattern in heading_patterns:
                if re.match(pattern, line):
                    # 이전 섹션 저장
                    if current_content.strip():
                        sections.append((current_heading, current_content.strip()))
                    
                    # 새 섹션 시작
                    current_heading = line
                    current_content = ""
                    is_heading = True
                    break
            
            if not is_heading:
                current_content += line + '\n'
        
        # 마지막 섹션 저장
        if current_content.strip():
            sections.append((current_heading, current_content.strip()))
        
        return sections

    def _table_to_text(self, table_data: List[List]) -> str:
        """테이블 데이터를 텍스트로 변환"""
        if not table_data:
            return ""
        
        text_parts = []
        headers = table_data[0] if table_data else []
        
        for row in table_data:
            row_parts = []
            for col_idx, cell in enumerate(row):
                if cell and str(cell).strip():
                    if col_idx < len(headers) and headers[col_idx]:
                        row_parts.append(f"{headers[col_idx]}: {cell}")
                    else:
                        row_parts.append(str(cell))
            
            if row_parts:
                text_parts.append(" | ".join(row_parts))
        
        return "\n".join(text_parts)

    def _split_large_chunk(self, text: str, max_size: int = None) -> List[str]:
        """큰 청크를 작은 청크로 분할"""
        if max_size is None:
            max_size = get_setting("pdf_processing.max_chunk_size", 1500)
        
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        lines = text.split('\n')
        current_chunk = ""
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_size:
                current_chunk += line + '\n'
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def process(self) -> List[Dict]:
        """전체 PDF 처리 프로세스
        
        Returns:
            List[Dict]: 처리된 문서 청크들
        """
        if not self.pdf_path.exists():
            logger.error(f"PDF 파일이 존재하지 않습니다: {self.pdf_path}")
            return []
        
        logger.info(f"PDF 처리 시작: {self.pdf_path.name}")
        
        # 1. 문서 유형 분류
        self.document_type = self.classify_document_type()
        logger.info(f"문서 유형: {self.document_type}")
        
        # 2. 내용 추출
        content = self.extract_content()
        if not content["extraction_success"]:
            logger.error("PDF 내용 추출 실패")
            return []
        
        logger.info(f"추출 방법: {', '.join(content['extraction_methods'])}")
        logger.info(f"페이지 수: {content['page_count']}, 테이블 수: {len(content['tables'])}")
        
        # 3. 문서 유형별 청킹
        if self.document_type == "restriction_list":
            chunks = self.chunk_restriction_items(content)
        elif self.document_type == "guideline":
            chunks = self.chunk_guideline(content)
        elif self.document_type == "statistics":
            chunks = self.chunk_statistics(content)
        elif self.document_type == "consultation_case":
            chunks = self.chunk_consultation_cases(content)
        else:
            # 기본 텍스트 청킹
            chunks = self.chunk_guideline(content)  # 가이드라인 방식 사용
        
        self.documents = chunks
        logger.info(f"청킹 완료: {len(chunks)}개 청크 생성")
        
        return self.documents

    def save_to_jsonl(self, output_path: Path) -> bool:
        """처리된 청크들을 JSONL 파일로 저장
        
        Args:
            output_path (Path): 출력 파일 경로
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.documents:
            logger.warning("저장할 문서가 없습니다. process() 메서드를 먼저 실행해주세요.")
            return False
        
        success = save_chunks_as_jsonl(self.documents, str(output_path))
        if success:
            logger.info(f"PDF 청크들이 JSONL 형식으로 저장되었습니다: {output_path}")
        
        return success

    def process_and_save_jsonl(self, output_path: Path) -> Tuple[List[Dict], bool]:
        """PDF 처리 후 바로 JSONL로 저장
        
        Args:
            output_path (Path): 출력 파일 경로
            
        Returns:
            Tuple[List[Dict], bool]: (처리된 청크들, 저장 성공 여부)
        """
        chunks = self.process()
        if not chunks:
            return [], False
        
        save_success = self.save_to_jsonl(output_path)
        return chunks, save_success

    def save_to_json(self, output_path: Path) -> bool:
        """처리된 청크들을 JSON 파일로 저장 (RAG 시스템 호환용)
        
        Args:
            output_path (Path): 출력 파일 경로
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.documents:
            logger.warning("저장할 문서가 없습니다. process() 메서드를 먼저 실행해주세요.")
            return False
        
        from .file_utils import save_processed_documents
        success = save_processed_documents(self.documents, str(output_path))
        if success:
            logger.info(f"PDF 청크들이 JSON 형식으로 저장되었습니다: {output_path}")
        
        return success

    def process_and_save_json(self, output_path: Path) -> Tuple[List[Dict], bool]:
        """PDF 처리 후 바로 JSON으로 저장 (RAG 시스템 호환용)
        
        Args:
            output_path (Path): 출력 파일 경로
            
        Returns:
            Tuple[List[Dict], bool]: (처리된 청크들, 저장 성공 여부)
        """
        chunks = self.process()
        if not chunks:
            return [], False
        
        save_success = self.save_to_json(output_path)
        return chunks, save_success

    def get_processing_summary(self) -> Dict[str, Any]:
        """처리 결과 요약 정보 반환
        
        Returns:
            Dict[str, Any]: 처리 요약 정보
        """
        if not self.documents:
            return {"status": "not_processed"}
        
        # 청크 유형별 통계
        chunk_types = {}
        extraction_methods = {}
        categories = {}
        
        total_content_length = 0
        hs_codes_count = 0
        law_refs_count = 0
        
        for doc in self.documents:
            # 청크 유형
            chunk_type = doc["metadata"].get("chunk_type", "unknown")
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            # 추출 방법
            extraction_method = doc["metadata"].get("extraction_method", "unknown")
            extraction_methods[extraction_method] = extraction_methods.get(extraction_method, 0) + 1
            
            # 카테고리
            category = doc["metadata"].get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            # 통계
            total_content_length += len(doc.get("content", ""))
            hs_codes_count += len(doc["metadata"].get("hs_codes", []))
            law_refs_count += len(doc["metadata"].get("related_law_references", []))
        
        return {
            "status": "processed",
            "document_name": self.document_name,
            "document_type": self.document_type,
            "total_chunks": len(self.documents),
            "chunk_types": chunk_types,
            "extraction_methods": extraction_methods,
            "categories": categories,
            "total_content_length": total_content_length,
            "average_chunk_size": total_content_length // len(self.documents) if self.documents else 0,
            "hs_codes_found": hs_codes_count,
            "law_references_found": law_refs_count
        }