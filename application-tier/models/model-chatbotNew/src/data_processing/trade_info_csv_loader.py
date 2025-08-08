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

    # CSV 파일 유형별 스키마 정의 (단순화된 구조)
    CSV_SCHEMAS = {
        "수입규제DB_전체": {
            "type": "export_destination_restrictions",
            "columns": ["관리번호", "규제국", "품목명", "규제유형", "조사개시일", "규제상태", "최근갱신일"]
        },
        "수출제한품목": {
            "type": "export_restrictions",
            "columns": ["HS코드", "품목", "수출요령"]
        },
        "수입제한품목": {
            "type": "import_restrictions", 
            "columns": ["HS코드", "품목", "수입요령"]
        },
        "수출금지품목": {
            "type": "export_prohibitions",
            "columns": ["HS코드", "상세품목", "수출 금지 품목"]
        },
        "동식물허용금지지역": {
            "type": "import_restrictions",
            "columns": ["품목", "허용국가", "금지국가", "품목분류", "비고"]
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
        
        # 특별한 경우들을 먼저 확인
        if "동식물" in filename and ("허용" in filename or "금지" in filename):
            return "동식물허용금지지역"
        
        # 기존 패턴 매칭
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
        """행 데이터를 RAG 검색에 최적화된 컨텐츠로 포맷팅
        
        Args:
            row (pd.Series): CSV 행 데이터
            schema (Dict): CSV 스키마 정보
            
        Returns:
            str: 검색 최적화된 컨텐츠
        """
        if schema["type"] == "export_prohibitions":
            hs_code = self._clean_text(str(row.get("HS코드", "")))
            clean_hs_code = hs_code.replace(".0", "")
            if len(clean_hs_code) < 10:
                clean_hs_code = clean_hs_code.ljust(10, '0')
            
            product_name = self._clean_text(str(row.get("상세품목", "")))
            prohibition_reason = self._clean_text(str(row.get("수출 금지 품목", "")))
            product_category = self._extract_product_category(clean_hs_code)
            
            return f"[수출금지] HS코드 {clean_hs_code} - {prohibition_reason}\n품목: {product_name}\n금지사유: {prohibition_reason}\n분류: {product_category}\n관련키워드: 수출금지, 금지품목, {product_category}"
        
        elif schema["type"] in ["export_restrictions", "import_restrictions"]:
            # 동식물 허용/금지 지역 데이터 특별 처리
            if self.csv_type == "동식물허용금지지역":
                return self._format_animal_plant_content(row)
            
            # 기존 수출입 제한품목 처리
            hs_code = self._clean_text(str(row.get("HS코드", ""))).replace(".0", "")
            product_name = self._clean_text(str(row.get("품목", "")))
            
            # 올바른 컬럼 매핑 사용
            column_mapping = {
                "export_restrictions": "수출요령",
                "import_restrictions": "수입요령"
            }
            requirements_column = column_mapping.get(schema["type"], "")
            requirements = self._clean_text(str(row.get(requirements_column, "")))
            product_category = self._extract_product_category(hs_code)
            
            restriction_type = "수출제한" if schema["type"] == "export_restrictions" else "수입제한"
            
            return f"[{restriction_type}] HS코드 {hs_code}\n품목: {product_name}\n제한요령: {requirements}\n분류: {product_category}\n관련키워드: {restriction_type}, 제한품목, {product_category}"
        
        elif schema["type"] == "export_destination_restrictions":
            management_no = self._clean_text(str(row.get("관리번호", "")))
            country = self._clean_text(str(row.get("규제국", "")))
            product_name = self._clean_text(str(row.get("품목명", "")))
            regulation_type = self._clean_text(str(row.get("규제유형", "")))
            status = self._clean_text(str(row.get("규제상태", "")))
            start_date = self._clean_text(str(row.get("조사개시일", "")))
            updated_date = self._clean_text(str(row.get("최근갱신일", "")))
            
            return f"[{country}이 한국 제품에 거는 규제] {product_name} {regulation_type} 규제\n상태: {status}\n개시일: {start_date}\n최근갱신: {updated_date}\n관리번호: {management_no}\n관련키워드: {country}, {regulation_type}, 해외수출규제, 수출장벽, {status}"
        
        # 기본 방식 (fallback)
        content_parts = []
        for column in schema["content_columns"]:
            if column in row.index and row[column]:
                value = self._clean_text(str(row[column]))
                if value:
                    if column == "HS코드":
                        value = value.replace(".0", "")
                    content_parts.append(f"{column}: {value}")
        
        return "\n".join(content_parts)
    
    def _format_animal_plant_content(self, row: pd.Series) -> str:
        """동식물 허용/금지 지역 데이터 전용 포맷팅
        
        Args:
            row (pd.Series): CSV 행 데이터
            
        Returns:
            str: 동식물 검색 최적화된 컨텐츠
        """
        product_name = self._clean_text(str(row.get("품목", "")))
        allowed_countries = self._clean_text(str(row.get("허용국가", "")))
        prohibited_countries = self._clean_text(str(row.get("금지국가", "")))
        product_category = self._clean_text(str(row.get("품목분류", "")))
        notes = self._clean_text(str(row.get("비고", "")))
        
        # 허용국가 리스트 처리
        allowed_list = []
        if allowed_countries and allowed_countries != "nan":
            allowed_list = [country.strip() for country in allowed_countries.split("|") if country.strip()]
        
        # 금지국가 처리
        prohibition_info = prohibited_countries if prohibited_countries and prohibited_countries != "nan" else "허용국가외전체"
        
        # 특별조건 유무
        special_conditions = ""
        if notes and notes != "nan" and notes.strip():
            special_conditions = f"\n특별조건: {notes}"
        
        # 동식물 타입 확인
        animal_plant_type = "동물" if product_category in ["동물", "육류(식육)", "해산물가공품"] else "식물" if product_category == "식물" else "가공품"
        
        # 허용국가 목록 포맷팅
        allowed_countries_text = ", ".join(allowed_list) if allowed_list else "없음"
        
        content = f"[동식물수입규제] {product_name}\n"
        content += f"허용국가: {allowed_countries_text}\n"
        content += f"금지/제한: {prohibition_info}\n"
        content += f"품목분류: {product_category} ({animal_plant_type})\n"
        content += f"검역요구: 동식물검역, 수입허가{special_conditions}\n"
        content += f"관련키워드: 동식물, 수입규제, {animal_plant_type}, 검역, {product_category}"
        
        return content

    def _extract_metadata(self, row: pd.Series, schema: Dict, index: int) -> Dict[str, Any]:
        """행에서 통일된 메타데이터 추출
        
        Args:
            row (pd.Series): CSV 행 데이터
            schema (Dict): CSV 스키마 정보
            index (int): 행 인덱스
            
        Returns:
            Dict[str, Any]: 통일된 메타데이터
        """
        from datetime import datetime
        
        # 기본 메타데이터 구조
        metadata = {
            "data_type": "trade_regulation",
            "data_source": self.csv_type,
            "regulation_type": schema["type"],
            "chunk_type": "csv_record",
            "row_index": index,
            "updated_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # 규제 유형별 특화 메타데이터
        if self.csv_type == "동식물허용금지지역":
            # 동식물 허용/금지 지역 데이터 특별 처리
            product_name = self._clean_text(str(row.get("품목", "")))
            allowed_countries = self._clean_text(str(row.get("허용국가", "")))
            prohibited_countries = self._clean_text(str(row.get("금지국가", "")))
            product_category = self._clean_text(str(row.get("품목분류", "")))
            notes = self._clean_text(str(row.get("비고", "")))
            
            # 허용국가 리스트 처리
            allowed_list = []
            if allowed_countries and allowed_countries != "nan":
                allowed_list = [country.strip() for country in allowed_countries.split("|") if country.strip()]
            
            # 금지국가 처리
            prohibited_list = []
            if prohibited_countries and prohibited_countries != "nan" and prohibited_countries != "허용국가외전체":
                prohibited_list = [country.strip() for country in prohibited_countries.split("|") if country.strip()]
            
            # 동식물 구분
            animal_plant_type = "동물" if product_category in ["동물", "육류(식육)", "해산물가공품"] else "식물" if product_category == "식물" else "가공품"
            
            # 특별 조건 확인
            has_special_conditions = bool(notes and notes != "nan" and notes.strip())
            
            # 규제 강도 결정
            if prohibited_countries == "허용국가외전체":
                regulation_intensity = "high"  # 허용국가 외 전체 금지
                priority = 2
            elif prohibited_list:
                regulation_intensity = "medium"  # 일부 국가 금지
                priority = 1
            else:
                regulation_intensity = "low"  # 특별 금지 없음
                priority = 1
            
            metadata.update({
                "regulation_type": "import_regulations",  # 사용자 요구사항에 따라
                "product_name": product_name,
                "product_category": product_category,
                "animal_plant_type": animal_plant_type,
                "allowed_countries": allowed_list,
                "prohibited_countries": prohibited_list,
                "has_global_prohibition": prohibited_countries == "허용국가외전체",
                "special_conditions": notes if has_special_conditions else "",
                "has_special_conditions": has_special_conditions,
                "regulation_intensity": regulation_intensity,
                "priority": priority,
                "is_active": True,
                "total_allowed_countries": len(allowed_list),
                "total_prohibited_countries": len(prohibited_list)
            })
            
        elif schema["type"] == "export_destination_restrictions":
            regulating_country = self._clean_text(str(row.get("규제국", "")))
            regulation_type = self._clean_text(str(row.get("규제유형", "")))
            status = self._clean_text(str(row.get("규제상태", "")))
            
            # priority 및 is_active 로직 개선
            if status == "규제중":
                priority = 2  # 실제 적용 중인 해외 규제
                is_active = True
            elif status == "조사중":
                priority = 1  # 조사 단계 해외 규제
                is_active = False
            else:
                priority = 0  # 종료된 규제
                is_active = False
            
            metadata.update({
                "regulating_country": regulating_country,
                "affected_country": "한국",
                "direction": f"한국 수출 시 {regulating_country} 규제",
                "regulation_subtype": regulation_type,
                "status": status,
                "is_active": is_active,
                "priority": priority,
                "management_number": self._clean_text(str(row.get("관리번호", ""))),
                "product_name": self._clean_text(str(row.get("품목명", "")))
            })
            
        elif schema["type"] in ["export_restrictions", "import_restrictions", "export_prohibitions"]:
            hs_code = self._clean_text(str(row.get("HS코드", ""))).replace(".0", "")
            
            # export_prohibitions의 경우 10자리로 정규화
            if schema["type"] == "export_prohibitions" and len(hs_code) < 10:
                hs_code = hs_code.ljust(10, '0')
            
            product_category = self._extract_product_category(hs_code)
            
            metadata.update({
                "hs_code": hs_code,
                "product_category": product_category,
                "is_active": True  # 제한/금지 품목은 항상 활성
            })
            
            # 각 유형별 특수 필드
            if schema["type"] == "export_prohibitions":
                prohibition_reason = self._clean_text(str(row.get("수출 금지 품목", "")))
                metadata.update({
                    "prohibition_reason": prohibition_reason,
                    "priority": 3,  # 금지품목 최고 우선순위 (절대 금지)
                    "product_name": self._clean_text(str(row.get("상세품목", "")))
                })
            else:
                # 제한품목의 경우 - 올바른 컬럼 매핑 사용
                column_mapping = {
                    "export_restrictions": "수출요령",
                    "import_restrictions": "수입요령"
                }
                requirements_column = column_mapping.get(schema["type"], "")
                metadata.update({
                    "priority": 2,  # 제한품목 높은 우선순위 (실제 적용 중인 규제)
                    "product_name": self._clean_text(str(row.get("품목", ""))),
                    "requirements": self._clean_text(str(row.get(requirements_column, "")))
                })
        
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
            "01": "동물", "02": "육류", "03": "수산물", "04": "낙농품",
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
                # 컨텐츠 포맷팅 (RAG 최적화)
                content = self._format_content(row, schema)
                
                # 메타데이터 추출 (통일된 구조)
                metadata = self._extract_metadata(row, schema, index)
                
                # 빈 컨텐츠 스킵
                if not content.strip():
                    logger.warning(f"Skipping empty content for row {index}")
                    continue
                
                # 새로운 단순화된 문서 구조
                document = {
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