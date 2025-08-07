"""
Document Loader Module

한국 관세법 JSON 데이터를 조/항 단위로 청킹하는 로더 클래스입니다.
구글 콜랩 환경에서 개발된 CustomsLawLoader를 로컬 환경에 맞게 최적화했습니다.

Classes:
    CustomsLawLoader: 관세법 문서 처리 및 청킹을 담당하는 메인 클래스
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomsLawLoader:
    """관세법 JSON 데이터를 조/항 단위로 청킹하는 로더
    
    이 클래스는 한국 관세법 API에서 가져온 JSON 데이터를 분석하여
    조문 단위 또는 항 단위로 지능적으로 청킩합니다.
    
    Attributes:
        json_data (Dict): 처리할 법령 JSON 데이터
        documents (List[Dict]): 처리된 문서 청크들의 리스트
    """

    def __init__(self, json_data: Dict):
        """
        Args:
            json_data (Dict): 관세법 JSON 데이터
        """
        self.json_data = json_data
        self.documents = []
        logger.info(f"CustomsLawLoader initialized with data for: {self.get_law_info()[0]}")

    def clean_hierarchy_text(self, text: str) -> str:
        """계층 텍스트에서 개정 일자 제거
        
        Args:
            text (str): 원본 계층 텍스트 (예: "제1장 총칙 <개정 2010.12.30>")
            
        Returns:
            str: 정리된 텍스트 (예: "제1장 총칙")
        """
        if not text:
            return text
            
        # 개정 일자 패턴 제거: <개정 YYYY.MM.DD>, <신설 YYYY.MM.DD>, <개정 YYYY.MM.DD, YYYY.MM.DD> 등
        # 정규식으로 < > 안의 개정/신설 관련 내용을 모두 제거
        cleaned_text = re.sub(r'\s*<[^>]*(?:개정|신설)[^>]*>', '', text)
        
        return cleaned_text.strip()

    def normalize_paragraph_number(self, paragraph_number: str) -> str:
        """항 번호를 숫자로 정규화 (①②③ → 1,2,3)
        
        Args:
            paragraph_number (str): 원본 항 번호 (①, ②, ③ 등)
            
        Returns:
            str: 정규화된 항 번호 (1, 2, 3 등)
        """
        paragraph_map = {
            '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
            '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10',
            '⑪': '11', '⑫': '12', '⑬': '13', '⑭': '14', '⑮': '15',
            '⑯': '16', '⑰': '17', '⑱': '18', '⑲': '19', '⑳': '20'
        }
        return paragraph_map.get(paragraph_number, paragraph_number)

    def get_law_info(self) -> Tuple[str, str]:
        """법령 정보 추출 (법령명, 법령 단계)
        
        Returns:
            Tuple[str, str]: (법령명, 법령단계)
        """
        basic_info = self.json_data["법령"]["기본정보"]
        law_name = basic_info.get("법령명_한글", "")
        law_type = basic_info.get("법종구분", {}).get("content", "")
        
        # 법령 단계 결정
        if law_type == "법률":
            law_level = "법률"
        elif law_type == "대통령령":
            law_level = "시행령"
        elif law_type == "기획재정부령":
            law_level = "시행규칙"
        else:
            law_level = law_type
            
        return law_name, law_level

    def extract_hierarchy_context(self, current_index: int, articles: List[Dict]) -> Dict[str, Optional[str]]:
        """현재 조문의 상위 계층 정보 추출
        
        법령 계층 구조: 편(doc) - 장(chapter) - 절(section) - 관(subsection) - 조 - 항 - 호 - 목
        정규식 패턴을 사용하여 정확한 계층 식별을 수행합니다.
        
        Args:
            current_index (int): 현재 조문의 인덱스
            articles (List[Dict]): 전체 조문 리스트
            
        Returns:
            Dict[str, Optional[str]]: 계층 정보 (편, 장, 절, 관)
        """
        context = {"doc": None, "chapter": None, "section": None, "subsection": None}
        
        # 정규식 패턴 정의 (더 정확한 매칭을 위해)
        patterns = {
            "doc": re.compile(r'제\s*\d+\s*편'),          # 편: 제1편, 제 2 편 등
            "chapter": re.compile(r'제\s*\d+\s*장'),      # 장: 제1장, 제 2 장 등  
            "section": re.compile(r'제\s*\d+\s*절'),      # 절: 제1절, 제 2 절 등
            "subsection": re.compile(r'제\s*\d+\s*관')    # 관: 제1관, 제 2 관 등
        }

        # 역순으로 검색하여 가장 최근 계층 찾기
        for i in range(current_index - 1, -1, -1):
            article = articles[i]
            if article["조문여부"] == "전문":
                content = article["조문내용"].strip()
                
                # 각 계층별로 패턴 매칭 (아직 찾지 못한 계층만)
                for hierarchy_key, pattern in patterns.items():
                    if context[hierarchy_key] is None and pattern.search(content):
                        context[hierarchy_key] = self.clean_hierarchy_text(content)
                        break  # 하나의 전문은 하나의 계층만 나타냄
                
                # 모든 계층을 찾았으면 더 이상 검색하지 않음 (성능 최적화)
                if all(context.values()):
                    break

        return context

    def count_paragraphs(self, article: Dict) -> int:
        """조문의 항 개수 계산
        
        Args:
            article (Dict): 조문 데이터
            
        Returns:
            int: 항의 개수
        """
        if "항" in article and isinstance(article["항"], list):
            return len(article["항"])
        return 0

    def determine_chunking_strategy(self, article: Dict) -> str:
        """청킹 전략 결정: 조 vs 항 단위
        
        Args:
            article (Dict): 조문 데이터
            
        Returns:
            str: 청킹 전략 ("article_level" 또는 "paragraph_level")
        """
        paragraph_count = self.count_paragraphs(article)

        # 항이 3개 이상인 경우 항 단위로 분할
        if paragraph_count >= 3:
            return "paragraph_level"
        else:
            return "article_level"

    def clean_content(self, content: Any) -> str:
        """내용을 문자열로 변환하고 정리
        
        Args:
            content (Any): 정리할 내용
            
        Returns:
            str: 정리된 문자열
        """
        def to_string(item):
            """모든 타입을 문자열로 변환"""
            if isinstance(item, list):
                return "\n".join([to_string(sub_item) for sub_item in item])
            elif isinstance(item, dict):
                return "\n".join([to_string(value) for value in item.values()])
            elif item is None:
                return ""
            else:
                return str(item)

        # 문자열로 변환
        content_str = to_string(content)

        if not content_str.strip():
            return ""

        # 정규식 적용
        content_str = re.sub(r'제\d+조\([^)]+\)\s*', '', content_str)
        content_str = re.sub(r'^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*', '', content_str, flags=re.MULTILINE)

        return content_str.strip()

    def extract_article_number(self, article_number: str) -> str:
        """조문 번호 추출 (제137조의2 같은 특수 케이스 처리)
        
        Args:
            article_number (str): 원본 조문 번호
            
        Returns:
            str: 정제된 조문 번호
        """
        # 조문 번호에 "의" 가 포함된 경우 (예: 137의2)
        if "의" in article_number:
            return f"제{article_number}조"
        else:
            return f"제{article_number}조"

    def resolve_law_reference(self, reference: str, law_name: str, target_law_level: str) -> str:
        """법령 참조를 명확한 형태로 변환
        
        Args:
            reference (str): 원본 참조 (예: "법 제88조", "대통령령")
            law_name (str): 현재 법령명 (예: "관세법")
            target_law_level (str): 대상 법령 단계 ("법률", "시행령", "시행규칙")
            
        Returns:
            str: 명확한 참조 (예: "관세법 제88조", "관세법 시행령")
        """
        # 기본 법령명 처리 - 더 정확한 추출
        if "시행령" in law_name:
            base_law_name = law_name.replace(" 시행령", "").strip()
        elif "시행규칙" in law_name:
            base_law_name = law_name.replace(" 시행규칙", "").strip()
        else:
            base_law_name = law_name.replace("법", "").strip() + "법"
        
        # 참조 패턴에 따른 명확한 변환
        if reference.startswith("법 제"):
            # "법 제88조" → "관세법 제88조"
            article_part = reference.replace("법 ", "")
            return f"{base_law_name} {article_part}"
        elif reference.startswith("영 제"):
            # "영 제15조" → "관세법 시행령 제15조"
            article_part = reference.replace("영 ", "")
            return f"{base_law_name} 시행령 {article_part}"
        elif reference == "대통령령":
            # "대통령령" → "관세법 시행령"
            return f"{base_law_name} 시행령"
        elif reference == "기획재정부령":
            # "기획재정부령" → "관세법 시행규칙"
            return f"{base_law_name} 시행규칙"
        else:
            # 기타 경우는 원본 반환
            return reference

    def extract_internal_law_references(self, content: str, law_level: str, law_name: str) -> Dict[str, List[str]]:
        """내부 법령 참조 패턴 추출 (일반화된 버전)
        
        Args:
            content (str): 분석할 내용
            law_level (str): 법령 단계
            law_name (str): 법령명
            
        Returns:
            Dict[str, List[str]]: 참조 패턴 딕셔너리
        """
        references = {
            "refers_to_main_law": [],
            "refers_to_enforcement_decree": [],
            "refers_to_enforcement_rules": []
        }
        
        # 법 참조 패턴 - 명확한 법령명으로 변환
        law_pattern = r'법 제(\d+조(?:의\d+)?(?:제\d+항)?(?:제\d+호)?(?:제\d+목)?)'
        law_matches = re.findall(law_pattern, content)
        references["refers_to_main_law"] = [self.resolve_law_reference(f"법 제{match}", law_name, "법률") for match in law_matches]
        
        # 영 참조 패턴 - 명확한 법령명으로 변환
        decree_pattern = r'영 제(\d+조(?:의\d+)?(?:제\d+항)?(?:제\d+호)?(?:제\d+목)?)'
        decree_matches = re.findall(decree_pattern, content) 
        references["refers_to_enforcement_decree"] = [self.resolve_law_reference(f"영 제{match}", law_name, "시행령") for match in decree_matches]
        
        # 대통령령/기획재정부령 지시 패턴 - 명확한 법령명으로 변환
        if "대통령령" in content:
            references["refers_to_enforcement_decree"].append(self.resolve_law_reference("대통령령", law_name, "시행령"))
        if "기획재정부령" in content:
            references["refers_to_enforcement_rules"].append(self.resolve_law_reference("기획재정부령", law_name, "시행규칙"))
            
        return references

    def extract_external_law_references(self, content: str) -> List[str]:
        """외부 법령 참조 추출
        
        Args:
            content (str): 분석할 내용
            
        Returns:
            List[str]: 외부 법령 목록
        """
        # 「법령명」 패턴 추출
        external_law_pattern = r'「([^」]+)」'
        matches = re.findall(external_law_pattern, content)
        
        # 관세법 관련이 아닌 외부 법령만 필터링
        customs_related = ["관세법", "관세법 시행령", "관세법 시행규칙"]
        external_laws = [law for law in matches if law not in customs_related]
        
        return list(set(external_laws))  # 중복 제거

    def process_article_level(self, article: Dict, context: Dict, law_name: str, law_level: str) -> Optional[Dict]:
        """조 단위 청킹 처리
        
        Args:
            article (Dict): 조문 데이터
            context (Dict): 계층 정보
            law_name (str): 법령명
            law_level (str): 법령 단계
            
        Returns:
            Optional[Dict]: 처리된 문서 청크 (없으면 None)
        """
        if article["조문여부"] != "조문":
            return None

        # 전체 조문 내용 구성
        content_parts = []

        # 조문 기본 내용 (조번호와 제목 제거)
        base_content = self.clean_content(article["조문내용"])
        if base_content:  # 빈 내용이 아닌 경우에만 추가
            content_parts.append(base_content)

        # 항이 있는 경우 모든 항 추가
        if "항" in article and isinstance(article["항"], list):
            for para in article["항"]:
                clean_para_content = self.clean_content(para["항내용"])
                content_parts.append(clean_para_content)

        # 호가 조문에 직접 있는 경우 (제2조 정의 조문)
        elif "호" in article:
            for item in article["호"]:
                content_parts.append(item["호내용"])
                # 목이 있는 경우도 포함
                if "목" in item:
                    for mok_item in item["목"]:
                        content_parts.append(mok_item["목내용"])

        full_content = "\n".join(content_parts)
        
        # 조문 번호 처리
        article_index = self.extract_article_number(article['조문번호'])
        
        # 참조 패턴 추출
        internal_references = self.extract_internal_law_references(full_content, law_level, law_name)
        external_references = self.extract_external_law_references(full_content)

        return {
            "index": article_index,
            "subtitle": article.get("조문제목", ""),
            "content": full_content,
            "metadata": {
                "law_name": law_name,
                "law_level": law_level,
                **context,
                "effective_date": article["조문시행일자"],
                "reference": article.get("조문참고자료", ""),
                "hierarchy_path": self.build_hierarchy_path(context, article_index),
                "chunk_type": "article_level",
                "internal_law_references": internal_references,
                "external_law_references": external_references,
                "total_paragraphs": self.count_paragraphs(article)
            }
        }

    def process_paragraph_level(self, article: Dict, context: Dict, law_name: str, law_level: str) -> List[Dict]:
        """항 단위 청킹 처리
        
        Args:
            article (Dict): 조문 데이터
            context (Dict): 계층 정보
            law_name (str): 법령명
            law_level (str): 법령 단계
            
        Returns:
            List[Dict]: 처리된 문서 청크 리스트
        """
        documents = []

        if "항" not in article or not isinstance(article["항"], list):
            return []

        for para in article["항"]:
            # 각 항을 별도 청크로 생성
            clean_para_content = self.clean_content(para["항내용"])
            
            # 항 번호 정규화
            normalized_para_num = self.normalize_paragraph_number(para["항번호"])
            
            # 올바른 인덱스 형식: 제5조제1항
            article_number = article['조문번호']
            index = f"제{article_number}조제{normalized_para_num}항"
            
            # 참조 패턴 추출
            internal_references = self.extract_internal_law_references(clean_para_content, law_level, law_name)
            external_references = self.extract_external_law_references(clean_para_content)

            documents.append({
                "index": index,
                "subtitle": article.get("조문제목", ""),
                "content": clean_para_content,
                "metadata": {
                    "law_name": law_name,
                    "law_level": law_level,
                    **context,
                    "effective_date": article["조문시행일자"],
                    "reference": article.get("조문참고자료", ""),
                    "hierarchy_path": self.build_hierarchy_path(context, index),
                    "chunk_type": "paragraph_level",
                    "internal_law_references": internal_references,
                    "external_law_references": external_references,
                    "total_paragraphs": self.count_paragraphs(article)
                }
            })

        return documents

    def build_hierarchy_path(self, context: Dict, index: str) -> str:
        """계층 경로 구성
        
        법령 계층 구조에 따라 편-장-절-관-조(항) 순서로 경로를 구성합니다.
        
        Args:
            context (Dict): 계층 정보
            index (str): 조문 인덱스
            
        Returns:
            str: 계층 경로 문자열 (예: "제1장 총칙>제1절 통칙>제1조")
        """
        path_parts = []
        
        # 계층 순서대로 추가 (존재하는 것만)
        hierarchy_order = ["doc", "chapter", "section", "subsection"]
        
        for hierarchy_key in hierarchy_order:
            if context.get(hierarchy_key):
                path_parts.append(context[hierarchy_key])
        
        # 마지막에 조문/항 인덱스 추가
        path_parts.append(index)
        
        # 빈 문자열 제거 후 조인
        filtered_parts = [part for part in path_parts if part and part.strip()]
        
        return ">".join(filtered_parts)

    def load(self) -> List[Dict]:
        """전체 로딩 프로세스
        
        Returns:
            List[Dict]: 처리된 문서 청크들
        """
        articles = self.json_data["법령"]["조문"]["조문단위"]
        law_name, law_level = self.get_law_info()
        
        logger.info(f"Processing {len(articles)} articles from {law_name}")

        for i, article in enumerate(articles):
            # 계층 정보 추출
            context = self.extract_hierarchy_context(i, articles)

            # 조문만 처리 (전문 제외)
            if article["조문여부"] == "조문":
                # 청킹 전략 결정
                strategy = self.determine_chunking_strategy(article)

                if strategy == "paragraph_level":
                    docs = self.process_paragraph_level(article, context, law_name, law_level)
                    self.documents.extend(docs)
                else:
                    doc = self.process_article_level(article, context, law_name, law_level)
                    if doc:
                        self.documents.append(doc)

        logger.info(f"Processing completed. Generated {len(self.documents)} chunks.")
        return self.documents