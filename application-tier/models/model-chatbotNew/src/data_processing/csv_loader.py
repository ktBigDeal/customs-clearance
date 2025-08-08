"""
CSV Document Loader Module

CSV 파일을 처리하여 일반 정보용 RAG 시스템을 위한 청킹된 문서로 변환하는 로더 클래스입니다.
무역 규제, 수출입 제한 품목 등의 CSV 데이터를 처리합니다.

Classes:
    CSVDocumentLoader: CSV 데이터 처리 및 청킹을 담당하는 메인 클래스
"""

import pandas as pd
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chardet

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVDocumentLoader:
    """CSV 데이터를 일반 정보 RAG용 문서로 청킹하는 로더
    
    이 클래스는 무역 관련 CSV 데이터를 분석하여 검색 가능한 문서 청크로 변환합니다.
    다양한 CSV 스키마를 지원하며 인코딩 문제를 자동으로 처리합니다.
    
    Attributes:
        csv_data (pd.DataFrame): 처리할 CSV 데이터
        csv_type (str): CSV 파일 유형 (regulations, restrictions, prohibitions)
        documents (List[Dict]): 처리된 문서 청크들의 리스트
    """

    # CSV 파일 유형별 스키마 정의
    CSV_SCHEMAS = {
        "수입규제DB_전체": {
            "type": "import_regulations",
            "columns": ["관리번호", "규제국", "품목명", "규제유형", "조사개시일", "규제상태", "최근갱신일"],
            "id_column": "관리번호",
            "title_column": "품목명",
            "content_columns": ["규제국", "품목명", "규제유형", "규제상태"]
        },
        "수출제한품목": {
            "type": "export_restrictions",
            "columns": ["HS코드", "품목", "수출요령"],
            "id_column": "HS코드",
            "title_column": "품목",
            "content_columns": ["HS코드", "품목", "수출요령"]
        },
        "수입제한품목": {
            "type": "import_restrictions", 
            "columns": ["HS코드", "품목", "수입요령"],
            "id_column": "HS코드",
            "title_column": "품목",
            "content_columns": ["HS코드", "품목", "수입요령"]
        },
        "수출금지품목": {
            "type": "export_prohibitions",
            "columns": ["HS코드", "상세품목", "수출 금지 품목"],
            "id_column": "HS코드", 
            "title_column": "상세품목",
            "content_columns": ["HS코드", "상세품목", "수출 금지 품목"]
        }
    }

    def __init__(self, csv_path: str, csv_type: Optional[str] = None):
        """
        Args:
            csv_path (str): 처리할 CSV 파일 경로
            csv_type (Optional[str]): CSV 파일 유형 (자동 감지 가능)
        """
        self.csv_path = Path(csv_path)
        self.csv_type = csv_type or self._detect_csv_type()
        self.csv_data = None
        self.documents = []
        
        # CSV 데이터 로드
        self._load_csv_data()
        
        logger.info(f"CSVDocumentLoader initialized for: {self.csv_type} ({len(self.csv_data)} rows)")

    def _detect_encoding(self, file_path: Path) -> str:
        """파일 인코딩 자동 감지
        
        Args:
            file_path (Path): 파일 경로
            
        Returns:
            str: 감지된 인코딩
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # 첫 10KB만 읽어서 감지
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                
                logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                
                # 신뢰도가 낮으면 UTF-8을 기본으로 사용
                if confidence < 0.7:
                    logger.warning(f"Low confidence encoding detection, using UTF-8")
                    return 'utf-8'
                    
                return encoding
        except Exception as e:
            logger.warning(f"Encoding detection failed: {e}, using UTF-8")
            return 'utf-8'

    def _detect_csv_type(self) -> str:
        """파일명을 기반으로 CSV 유형 자동 감지
        
        Returns:
            str: 감지된 CSV 유형
        """
        filename = self.csv_path.stem
        
        for csv_type in self.CSV_SCHEMAS.keys():
            if csv_type in filename:
                return csv_type
        
        # 기본값
        return "수입규제DB_전체"

    def _load_csv_data(self) -> None:
        """CSV 데이터 로드 및 전처리"""
        try:
            # 인코딩 감지 및 데이터 로드
            encoding = self._detect_encoding(self.csv_path)
            
            # 여러 인코딩으로 시도
            encodings_to_try = [encoding, 'utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
            
            for enc in encodings_to_try:
                try:
                    self.csv_data = pd.read_csv(self.csv_path, encoding=enc)
                    logger.info(f"Successfully loaded CSV with encoding: {enc}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if self.csv_data is None:
                raise ValueError("Failed to load CSV with any encoding")
            
            # 데이터 정리
            self.csv_data = self.csv_data.dropna(how='all')  # 완전히 빈 행 제거
            self.csv_data = self.csv_data.fillna('')  # NaN을 빈 문자열로 변경
            
            logger.info(f"Loaded {len(self.csv_data)} rows after preprocessing")
            
        except Exception as e:
            logger.error(f"Failed to load CSV data: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """텍스트 정리 및 정규화
        
        Args:
            text (str): 정리할 텍스트
            
        Returns:
            str: 정리된 텍스트
        """
        if not isinstance(text, str):
            text = str(text)
        
        # 기본 정리
        text = text.strip()
        
        # 여러 공백을 하나로 통합
        text = re.sub(r'\s+', ' ', text)
        
        # 특수 문자 정리 (필요시)
        # text = re.sub(r'[^\w\s가-힣()]', ' ', text)
        
        return text

    def _format_content(self, row: pd.Series, schema: Dict) -> str:
        """행 데이터를 검색 가능한 컨텐츠로 포맷팅
        
        Args:
            row (pd.Series): CSV 행 데이터
            schema (Dict): CSV 스키마 정보
            
        Returns:
            str: 포맷팅된 컨텐츠
        """
        # export_prohibitions의 경우 특별한 형식 사용
        if schema["type"] == "export_prohibitions":
            hs_code = self._clean_text(str(row.get("HS코드", "")))
            # HS코드 10자리로 정규화
            clean_hs_code = hs_code.replace(".0", "")
            if len(clean_hs_code) < 10:
                clean_hs_code = clean_hs_code.ljust(10, '0')
            
            product_name = self._clean_text(str(row.get("상세품목", "")))
            prohibition_item = self._clean_text(str(row.get("수출 금지 품목", "")))
            
            return f"HS코드: {clean_hs_code}\n품목: {product_name}\n수출금지품목: {prohibition_item}"
        
        # 다른 타입들은 기존 방식 사용
        content_parts = []
        
        for column in schema["content_columns"]:
            if column in row.index and row[column]:
                value = self._clean_text(str(row[column]))
                if value:
                    # HS코드의 경우 소수점 제거
                    if column == "HS코드":
                        value = value.replace(".0", "")
                    content_parts.append(f"{column}: {value}")
        
        return "\n".join(content_parts)

    def _extract_metadata(self, row: pd.Series, schema: Dict, index: int) -> Dict[str, Any]:
        """행에서 메타데이터 추출
        
        Args:
            row (pd.Series): CSV 행 데이터
            schema (Dict): CSV 스키마 정보
            index (int): 행 인덱스
            
        Returns:
            Dict[str, Any]: 메타데이터
        """
        metadata = {
            "data_source": self.csv_type,
            "category": schema["type"],
            "chunk_type": "csv_record",
            "row_index": index
        }
        
        # 스키마별 특수 메타데이터 추출
        if schema["type"] == "import_regulations":
            metadata.update({
                "country": self._clean_text(str(row.get("규제국", ""))),
                "regulation_type": self._clean_text(str(row.get("규제유형", ""))),
                "status": self._clean_text(str(row.get("규제상태", ""))),
                "management_number": self._clean_text(str(row.get("관리번호", "")))
            })
        elif schema["type"] in ["export_restrictions", "import_restrictions", "export_prohibitions"]:
            hs_code = self._clean_text(str(row.get("HS코드", "")))
            # 소수점 제거
            clean_hs_code = hs_code.replace(".0", "")
            
            # export_prohibitions의 경우 10자리로 정규화
            if schema["type"] == "export_prohibitions" and len(clean_hs_code) < 10:
                clean_hs_code = clean_hs_code.ljust(10, '0')
            
            metadata.update({
                "hs_code": clean_hs_code,
                "product_category": self._extract_product_category(clean_hs_code)
            })
            
            # export_prohibitions의 경우 prohibition_reason 추가
            if schema["type"] == "export_prohibitions":
                prohibition_reason = self._clean_text(str(row.get("수출 금지 품목", "")))
                metadata["prohibition_reason"] = prohibition_reason
        
        return metadata

    def _extract_product_category(self, hs_code: str) -> str:
        """HS코드에서 제품 카테고리 추출
        
        Args:
            hs_code (str): HS코드
            
        Returns:
            str: 제품 카테고리
        """
        if not hs_code or len(hs_code) < 2:
            return "기타"
        
        # HS코드 첫 2자리로 대분류 결정
        chapter = hs_code[:2]
        
        category_map = {
            "01": "살아있는동물", "02": "육류", "03": "수산물", "04": "낙농품",
            "05": "동물성제품", "06": "식물", "07": "채소", "08": "과실",
            "09": "커피차향신료", "10": "곡물", "11": "제분제품", "12": "유지종자",
            "13": "식물성수지", "14": "식물성편조물", "15": "동식물유지",
            "16": "육어류조제품", "17": "당류", "18": "코코아", "19": "곡물조제품",
            "20": "채소과실조제품", "21": "기타식료품", "22": "음료", "23": "식품공업잔재물",
            "24": "담배", "25": "광물", "26": "광석", "27": "연료",
            "28": "무기화학품", "29": "유기화학품", "30": "의약품", "31": "비료",
            "32": "염료", "33": "정유", "34": "비누", "35": "단백질계물질",
            "36": "화약", "37": "사진용품", "38": "기타화학품", "39": "플라스틱",
            "40": "고무", "41": "원피", "42": "가죽제품", "43": "모피",
            "44": "목재", "45": "코르크", "46": "짚세공품", "47": "펄프",
            "48": "지류", "49": "인쇄물", "50": "견", "51": "양모",
            "52": "면", "53": "기타식물성섬유", "54": "화학섬유장섬유",
            "55": "화학섬유단섬유", "56": "부직포", "57": "양탄자",
            "58": "특수직물", "59": "침투직물", "60": "메리야스편물",
            "61": "의류편물", "62": "의류직물", "63": "기타섬유제품",
            "64": "신발", "65": "모자", "66": "산우산", "67": "깃털제품",
            "68": "석제품", "69": "도자제품", "70": "유리", "71": "귀금속",
            "72": "철강", "73": "철강제품", "74": "동", "75": "니켈",
            "76": "알루미늄", "78": "납", "79": "아연", "80": "주석",
            "81": "기타금속", "82": "공구", "83": "기타금속제품",
            "84": "기계", "85": "전기기기", "86": "철도", "87": "자동차",
            "88": "항공기", "89": "선박", "90": "광학기기", "91": "시계",
            "92": "악기", "93": "무기", "94": "가구", "95": "완구",
            "96": "기타제품", "97": "예술품"
        }
        
        return category_map.get(chapter, "기타")

    def _generate_document_id(self, row: pd.Series, schema: Dict, index: int) -> str:
        """문서 ID 생성
        
        Args:
            row (pd.Series): CSV 행 데이터
            schema (Dict): CSV 스키마 정보
            index (int): 행 인덱스
            
        Returns:
            str: 생성된 문서 ID
        """
        id_column = schema["id_column"]
        
        if id_column in row.index and row[id_column]:
            id_value = self._clean_text(str(row[id_column]))
            
            # 타입별로 ID 형식 결정
            if schema["type"] == "import_regulations":
                # regulation_ 제거
                return id_value
            elif schema["type"] == "export_prohibitions":
                # HS코드를 10자리로 정규화 (소수점 제거하고 10자리 맞춤)
                hs_code = id_value.replace(".0", "")
                if len(hs_code) < 10:
                    hs_code = hs_code.ljust(10, '0')
                return hs_code
            else:
                # export_restrictions, import_restrictions: hs_ 제거, 소수점 제거
                return id_value.replace(".0", "")
        
        # ID가 없는 경우 인덱스 사용
        return f"{schema['type']}_{index}"

    def load(self) -> List[Dict]:
        """전체 로딩 프로세스
        
        Returns:
            List[Dict]: 처리된 문서 청크들
        """
        if self.csv_type not in self.CSV_SCHEMAS:
            raise ValueError(f"Unsupported CSV type: {self.csv_type}")
        
        schema = self.CSV_SCHEMAS[self.csv_type]
        
        logger.info(f"Processing {len(self.csv_data)} rows from {self.csv_type}")
        
        for index, row in self.csv_data.iterrows():
            try:
                # 문서 ID 생성
                doc_id = self._generate_document_id(row, schema, index)
                
                # 제목 추출
                title_column = schema["title_column"]
                title = self._clean_text(str(row.get(title_column, "")))
                
                # 컨텐츠 포맷팅
                content = self._format_content(row, schema)
                
                # 메타데이터 추출
                metadata = self._extract_metadata(row, schema, index)
                
                # 빈 컨텐츠 스킵
                if not content.strip():
                    logger.warning(f"Skipping empty content for row {index}")
                    continue
                
                document = {
                    "index": doc_id,
                    "title": title,
                    "content": content,
                    "metadata": metadata
                }
                
                self.documents.append(document)
                
            except Exception as e:
                logger.error(f"Failed to process row {index}: {e}")
                continue
        
        logger.info(f"Processing completed. Generated {len(self.documents)} chunks.")
        return self.documents

    def get_statistics(self) -> Dict[str, Any]:
        """처리 통계 반환
        
        Returns:
            Dict[str, Any]: 처리 통계
        """
        if not self.documents:
            return {"error": "No documents processed"}
        
        stats = {
            "total_documents": len(self.documents),
            "csv_type": self.csv_type,
            "source_file": str(self.csv_path),
            "average_content_length": sum(len(doc["content"]) for doc in self.documents) / len(self.documents)
        }
        
        # 카테고리별 분포
        categories = {}
        for doc in self.documents:
            category = doc["metadata"].get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        stats["category_distribution"] = categories
        
        return stats