"""
Query Normalizer Module

GPT-4.1mini를 사용하여 사용자 질의를 도메인별 문서 검색에 최적화
범용 QueryNormalizer와 도메인 전용 클래스들을 제공합니다.
"""

import logging
import openai
from typing import Optional, Dict, Any, List
import os
import json

logger = logging.getLogger(__name__)


class UniversalQueryNormalizer:
    """사용자 질의를 도메인별 문서 검색에 최적화된 형태로 정규화하는 범용 클래스"""
    
    def __init__(self, 
                 model_name: str = "gpt-4.1-mini", 
                 temperature: float = 0.3,
                 domain_config: Optional[Dict[str, Any]] = None):
        """
        초기화
        
        Args:
            model_name (str): 사용할 GPT 모델명
            temperature (float): 생성 온도
            domain_config (Optional[Dict[str, Any]]): 도메인별 설정
        """
        self.model_name = model_name
        self.temperature = temperature
        self.domain_config = domain_config or self._get_default_config()
        
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please check your .env file or set the environment variable directly."
            )
        
        self.client = openai.OpenAI(api_key=api_key)
        
        logger.info(f"UniversalQueryNormalizer initialized with model: {model_name}, domain: {self.domain_config.get('domain_name', 'universal')}")
    
    def normalize(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        LLM을 사용하여 검색 최적화된 쿼리로 변환
        
        Args:
            query (str): 원본 사용자 질의
            context (Optional[Dict[str, Any]]): 추가 컨텍스트 정보
            
        Returns:
            str: 정규화된 검색 쿼리
        """
        try:
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(query, context)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=200
            )
            
            normalized_query = response.choices[0].message.content.strip()
            
            logger.debug(f"Query normalized: '{query}' -> '{normalized_query}'")
            return normalized_query
            
        except Exception as e:
            logger.error(f"Failed to normalize query: {e}")
            # 실패 시 원본 쿼리 반환
            return query
    
    def expand_query_with_synonyms(self, query: str) -> str:
        """
        도메인별 동의어를 포함하여 쿼리 확장
        
        Args:
            query (str): 원본 쿼리
            
        Returns:
            str: 동의어가 포함된 확장 쿼리
        """
        try:
            system_prompt = self.domain_config.get('synonym_expansion_prompt', self._get_default_synonym_prompt())

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 쿼리를 확장하세요: {query}"}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            expanded_query = response.choices[0].message.content.strip()
            
            logger.debug(f"Query expanded: '{query}' -> '{expanded_query}'")
            return expanded_query
            
        except Exception as e:
            logger.error(f"Failed to expand query: {e}")
            return query
    
    def extract_intent(self, query: str) -> Dict[str, Any]:
        """
        질의에서 도메인별 의도와 주요 개념 추출
        
        Args:
            query (str): 사용자 질의
            
        Returns:
            Dict[str, Any]: 추출된 의도 정보
        """
        try:
            system_prompt = self.domain_config.get('intent_extraction_prompt', self._get_default_intent_prompt())

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 질의를 분석하세요: {query}"}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            intent_json = response.choices[0].message.content.strip()
            intent_data = json.loads(intent_json)
            
            logger.debug(f"Extracted intent: {intent_data}")
            return intent_data
            
        except Exception as e:
            logger.error(f"Failed to extract intent: {e}")
            return self.domain_config.get('default_intent', {
                "intent_type": "정보조회",
                "key_concepts": [],
                "category": "일반",
                "urgency": "보통",
                "specificity": "일반적"
            })
    
    def _get_system_prompt(self) -> str:
        """도메인별 시스템 프롬프트 반환"""
        return self.domain_config.get('system_prompt', self._get_default_system_prompt())
    
    def _build_user_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """사용자 프롬프트 구성"""
        prompt = f"다음 질문을 문서 검색에 적합한 형태로 변환하세요:\n\n{query}"
        
        if context:
            prompt += f"\n\n추가 컨텍스트:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        return prompt
    
    def _get_default_config(self) -> Dict[str, Any]:
        """기본 도메인 설정 반환"""
        return {
            "domain_name": "universal",
            "system_prompt": self._get_default_system_prompt(),
            "synonym_expansion_prompt": self._get_default_synonym_prompt(),
            "intent_extraction_prompt": self._get_default_intent_prompt(),
            "default_intent": {
                "intent_type": "정보조회",
                "key_concepts": [],
                "category": "일반",
                "urgency": "보통",
                "specificity": "일반적"
            }
        }
    
    def _get_default_system_prompt(self) -> str:
        """기본 시스템 프롬프트"""
        return """당신은 문서 검색을 위한 질의 정규화 전문가입니다.

사용자의 자연어 질문을 다음과 같이 변환하세요:
1. 전문용어로 표준화
2. 검색에 효과적인 키워드 중심으로 재구성  
3. 불필요한 조사나 어미 제거
4. 관련 영역 명시

변환된 검색 쿼리만 간결하게 반환하세요."""
    
    def _get_default_synonym_prompt(self) -> str:
        """기본 동의어 확장 프롬프트"""
        return """당신은 전문 용어 전문가입니다. 
사용자의 질의를 분석하여 관련된 용어의 동의어나 유사한 표현을 추가해 검색 쿼리를 확장하세요.

확장된 쿼리만 반환하세요."""
    
    def _get_default_intent_prompt(self) -> str:
        """기본 의도 추출 프롬프트"""
        return """사용자의 질의를 분석하여 다음 정보를 JSON 형태로 추출하세요:

{
    "intent_type": "정보조회|절차안내|요건확인|기타",
    "key_concepts": ["핵심", "개념", "리스트"],
    "category": "일반",
    "urgency": "높음|보통|낮음",
    "specificity": "구체적|일반적"
}

JSON만 반환하세요."""


class LawQueryNormalizer(UniversalQueryNormalizer):
    """관세법 전용 쿼리 정규화 클래스"""
    
    def __init__(self, model_name: str = "gpt-4.1-mini", temperature: float = 0.3):
        law_config = {
            "domain_name": "customs_law",
            "system_prompt": self._get_law_system_prompt(),
            "synonym_expansion_prompt": self._get_law_synonym_prompt(),
            "intent_extraction_prompt": self._get_law_intent_prompt(),
            "default_intent": {
                "intent_type": "정보조회",
                "key_concepts": [],
                "law_area": "일반",
                "urgency": "보통",
                "specificity": "일반적"
            }
        }
        super().__init__(model_name, temperature, law_config)
    
    def _get_law_system_prompt(self) -> str:
        """관세법 전용 시스템 프롬프트"""
        return """당신은 관세법 문서 검색을 위한 질의 정규화 전문가입니다.

사용자의 자연어 질문을 다음과 같이 변환하세요:
1. 법률 전문용어로 표준화
2. 검색에 효과적인 키워드 중심으로 재구성  
3. 불필요한 조사나 어미 제거
4. 관련 법령 영역 명시

변환 예시:
"물품 검사는 언제 안 해도 돼?" → "물품 검사 면제 조건 및 기준"
"수입할 때 뭘 내야 해?" → "수입신고 필수 서류 및 제출 요건"
"관세 안 내도 되는 경우는?" → "관세 면제 대상 및 조건"

변환된 검색 쿼리만 간결하게 반환하세요."""
    
    def _get_law_synonym_prompt(self) -> str:
        """관세법 전용 동의어 확장 프롬프트"""
        return """당신은 한국 관세법 전문가입니다. 
사용자의 질의를 분석하여 관련된 법률 용어의 동의어나 유사한 표현을 추가해 검색 쿼리를 확장하세요.

예시:
입력: "수입신고"  
출력: "수입신고 반입신고 수입허가 통관신고"

입력: "관세면제"
출력: "관세면제 관세감면 무관세 면세"

확장된 쿼리만 반환하세요."""
    
    def _get_law_intent_prompt(self) -> str:
        """관세법 전용 의도 추출 프롬프트"""
        return """당신은 한국 관세법 전문가입니다.
사용자의 질의를 분석하여 다음 정보를 JSON 형태로 추출하세요:

{
    "intent_type": "정보조회|절차안내|요건확인|예외조건|처벌규정",
    "key_concepts": ["핵심", "개념", "리스트"],
    "law_area": "수입|수출|통관|관세|보세|검사|신고",
    "urgency": "높음|보통|낮음",
    "specificity": "구체적|일반적"
}

JSON만 반환하세요."""

    def extract_legal_intent(self, query: str) -> Dict[str, Any]:
        """하위 호환성을 위한 메서드 (기존 코드와의 호환성)"""
        return self.extract_intent(query)


class TradeQueryNormalizer(UniversalQueryNormalizer):
    """무역 정보 전용 쿼리 정규화 클래스"""
    
    def __init__(self, model_name: str = "gpt-4.1-mini", temperature: float = 0.3):
        trade_config = {
            "domain_name": "trade_information",
            "system_prompt": self._get_trade_system_prompt(),
            "synonym_expansion_prompt": self._get_trade_synonym_prompt(),
            "intent_extraction_prompt": self._get_trade_intent_prompt(),
            "default_intent": {
                "intent_type": "정보조회",
                "key_concepts": [],
                "trade_category": "일반",
                "urgency": "보통",
                "specificity": "일반적"
            }
        }
        super().__init__(model_name, temperature, trade_config)
    
    def _get_trade_system_prompt(self) -> str:
        """무역 정보 전용 시스템 프롬프트"""
        return """당신은 무역 규제 및 수출입 정보 검색을 위한 질의 정규화 전문가입니다.

사용자의 자연어 질문을 다음과 같이 변환하세요:
1. 무역 전문용어로 표준화
2. 검색에 효과적인 키워드 중심으로 재구성  
3. 불필요한 조사나 어미 제거
4. HS코드, 국가명, 규제유형, 동식물 품목 등 핵심 정보 식별

변환 예시:
"중국으로 전자제품 수출할 때 제한 있나?" → "중국 전자제품 수출 제한 규제"
"HS코드 8471 수입 금지 품목인가?" → "HS코드 8471 수입 금지 제한 여부"
"미국 반덤핑 규제 대상 품목은?" → "미국 반덤핑 규제 대상 품목 목록"
"아보카도는 어느 나라에서 수입해야해?" → "아보카도 수입 허용 국가 동식물 검역"
"바나나 수입 가능한 국가는?" → "바나나 수입 허용 국가 동식물 규제"

변환된 검색 쿼리만 간결하게 반환하세요."""
    
    def _get_trade_synonym_prompt(self) -> str:
        """무역 정보 전용 동의어 확장 프롬프트"""
        return """당신은 국제무역 전문가입니다. 
사용자의 질의를 분석하여 관련된 무역 용어의 동의어나 유사한 표현을 추가해 검색 쿼리를 확장하세요.

예시:
입력: "수출 제한"  
출력: "수출 제한 수출 금지 수출 규제 수출 통제"

입력: "반덤핑"
출력: "반덤핑 AD 덤핑방지 덤핑 관세"

입력: "아보카도 수입"
출력: "아보카도 수입 동식물 검역 과일 수입 농산물 수입 식물 수입"

입력: "동식물 검역"
출력: "동식물 검역 식물방역 동물검역 농산물 검역 방역 위생검사"

확장된 쿼리만 반환하세요."""
    
    def _get_trade_intent_prompt(self) -> str:
        """무역 정보 전용 의도 추출 프롬프트"""
        return """당신은 국제무역 전문가입니다.
사용자의 질의를 분석하여 다음 정보를 JSON 형태로 추출하세요:

{
    "intent_type": "정보조회|규제확인|품목검색|국가별규제|HS코드조회|동식물검역",
    "key_concepts": ["핵심", "개념", "리스트"],
    "trade_category": "수출제한|수입규제|수출금지|반덤핑|세이프가드|동식물수입규제",
    "urgency": "높음|보통|낮음",
    "specificity": "구체적|일반적"
}

JSON만 반환하세요."""


class AdvancedQueryProcessor:
    """고급 쿼리 처리 기능을 제공하는 클래스"""
    
    def __init__(self, normalizer: UniversalQueryNormalizer):
        """
        초기화
        
        Args:
            normalizer (UniversalQueryNormalizer): 기본 정규화기
        """
        self.normalizer = normalizer
        
        # 미리 정의된 용어 매핑 (도메인별로 확장 가능)
        self.domain_synonyms = self._get_domain_synonyms()
    
    def _get_domain_synonyms(self) -> Dict[str, List[str]]:
        """도메인별 동의어 매핑 반환"""
        domain_name = self.normalizer.domain_config.get('domain_name', 'universal')
        
        if domain_name == 'customs_law':
            return {
                "신고": ["신고서", "신청", "접수", "제출"],
                "검사": ["검사", "검증", "확인", "심사", "점검"],
                "면제": ["면제", "감면", "제외", "예외", "면제대상"],
                "과세": ["과세", "부과", "징수", "세금", "관세"],
                "수입": ["반입", "도입", "수입", "들여오기"],
                "수출": ["반출", "수출", "내보내기"],
                "통관": ["통관", "세관통과", "관세절차"],
                "보세": ["보세구역", "보세창고", "보세가공"],
                "원산지": ["원산지", "생산국", "제조국"],
                "운송": ["운송", "운반", "배송", "운송수단"]
            }
        elif domain_name == 'trade_information':
            return {
                "규제": ["규제", "제한", "통제", "금지"],
                "수출": ["수출", "반출", "해외판매", "외국판매"],
                "수입": ["수입", "반입", "국내반입", "외국구매"],
                "반덤핑": ["반덤핑", "AD", "덤핑방지", "덤핑관세"],
                "세이프가드": ["세이프가드", "긴급수입제한", "SG", "긴급관세"],
                "FTA": ["FTA", "자유무역협정", "특혜관세", "협정관세"],
                "동식물": ["동식물", "동물", "식물", "농산물", "축산물", "수산물", "가축", "농작물"],
                "검역": ["검역", "방역", "위생검사", "동식물검역", "식물방역", "동물검역"],
                "아보카도": ["아보카도", "열대과일", "과일", "식물", "농산물"],
                "허용": ["허용", "가능", "승인", "인정", "수입가능"],
                "금지": ["금지", "불가", "제한", "차단", "수입금지", "수입불가"],
                "국가": ["국가", "나라", "원산지", "생산국", "수출국"]
            }
        else:
            return {}
    
    def process_complex_query(self, query: str) -> Dict[str, Any]:
        """
        복합 질의 처리 및 분석
        
        Args:
            query (str): 복합 질의
            
        Returns:
            Dict[str, Any]: 처리된 질의 정보
        """
        # 1. 기본 정규화
        normalized = self.normalizer.normalize(query)
        
        # 2. 의도 추출
        intent = self.normalizer.extract_intent(query)
        
        # 3. 동의어 확장
        expanded = self.normalizer.expand_query_with_synonyms(normalized)
        
        # 4. 키워드 추출
        keywords = self._extract_keywords(query)
        
        # 5. 검색 전략 결정
        search_strategy = self._determine_search_strategy(intent, keywords)
        
        return {
            "original_query": query,
            "normalized_query": normalized,
            "expanded_query": expanded,
            "intent": intent,
            "keywords": keywords,
            "search_strategy": search_strategy
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        질의에서 핵심 키워드 추출
        
        Args:
            query (str): 질의
            
        Returns:
            List[str]: 추출된 키워드
        """
        keywords = []
        
        # 미리 정의된 용어 찾기
        for base_term, synonyms in self.domain_synonyms.items():
            if any(syn in query for syn in [base_term] + synonyms):
                keywords.append(base_term)
        
        return keywords
    
    def _determine_search_strategy(self, intent: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
        """
        검색 전략 결정
        
        Args:
            intent (Dict[str, Any]): 추출된 의도
            keywords (List[str]): 키워드 리스트
            
        Returns:
            Dict[str, Any]: 검색 전략
        """
        strategy = {
            "primary_search": "semantic",  # semantic, keyword, hybrid
            "filters": {},
            "boost_factors": {},
            "result_count": 5
        }
        
        # 의도에 따른 전략 조정
        if intent.get("specificity") == "구체적":
            strategy["result_count"] = 3
            strategy["primary_search"] = "hybrid"
        
        if intent.get("urgency") == "높음":
            strategy["boost_factors"]["recent"] = 1.2
        
        # 도메인별 카테고리에 따른 필터링
        domain_name = self.normalizer.domain_config.get('domain_name', 'universal')
        if domain_name == 'customs_law':
            law_area = intent.get("law_area")
            if law_area and law_area != "일반":
                strategy["filters"]["law_area"] = law_area
        elif domain_name == 'trade_information':
            trade_category = intent.get("trade_category")
            if trade_category and trade_category != "일반":
                strategy["filters"]["trade_category"] = trade_category
        
        return strategy


# 하위 호환성을 위한 alias
QueryNormalizer = LawQueryNormalizer