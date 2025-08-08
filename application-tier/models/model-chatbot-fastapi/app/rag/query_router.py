"""
FastAPI용 Query Router Module
사용자 질의를 분석하여 적절한 에이전트로 라우팅하는 비동기 모듈
기존 model-chatbot의 QueryRouter를 FastAPI 환경에 맞게 포팅
"""

import asyncio
import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """질의 유형 분류"""
    REGULATION = "regulation"      # 규제/법령 정보 질의  
    CONSULTATION = "consultation"  # 실무/절차 상담 질의
    MIXED = "mixed"               # 혼합형 질의


class AsyncQueryRouter:
    """
    FastAPI용 비동기 질의 라우터
    
    사용자 질의를 분석하여 적절한 에이전트로 라우팅:
    - TradeRegulationAgent: 규제/법령 정보 질의
    - ConsultationCaseAgent: 실무/절차 상담 질의
    - LawAgent: 관세법 조문 질의
    
    기존 QueryRouter의 모든 기능을 비동기로 구현
    """
    
    def __init__(self):
        """비동기 질의 라우터 초기화"""
        self.regulation_keywords = self._load_regulation_keywords()
        self.consultation_keywords = self._load_consultation_keywords()
        self.animal_plant_products = self._load_animal_plant_products()
        self.law_keywords = self._load_law_keywords()
        
        logger.info("AsyncQueryRouter initialized")
    
    async def route_query(self, user_query: str) -> Tuple[QueryType, float, Dict[str, Any]]:
        """
        사용자 질의를 분석하여 라우팅 결정 (비동기)
        
        Args:
            user_query: 사용자 질의
            
        Returns:
            Tuple[QueryType, float, Dict[str, Any]]: (질의 유형, 신뢰도, 라우팅 정보)
        """
        try:
            # CPU-bound 작업을 executor에서 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._analyze_query_sync, 
                user_query
            )
            
            return result
            
        except Exception as e:
            logger.error(f"질의 라우팅 실패: {e}")
            # 기본값으로 상담 에이전트 사용
            return QueryType.CONSULTATION, 0.5, {"reason": "error_fallback"}
    
    def _analyze_query_sync(self, user_query: str) -> Tuple[QueryType, float, Dict[str, Any]]:
        """동기적 질의 분석 (executor에서 실행됨)"""
        # 1. 질의 전처리
        normalized_query = self._normalize_query(user_query)
        
        # 2. 관세법 조문 질의 감지 (최우선)
        law_score = self._calculate_law_score(normalized_query)
        if law_score > 0.7:
            return QueryType.REGULATION, law_score, {
                "reason": "customs_law_query",
                "agent_preference": "law_agent",
                "routing_priority": "highest"
            }
        
        # 3. 동식물 수입 질의 감지 (높은 우선순위)
        animal_plant_score = self._detect_animal_plant_import_query(normalized_query)
        if animal_plant_score > 0.8:
            return QueryType.REGULATION, animal_plant_score, {
                "reason": "animal_plant_import_query",
                "detected_products": self._extract_animal_plant_products(normalized_query),
                "routing_priority": "high"
            }
        
        # 4. 규제/법령 질의 점수 계산
        regulation_score = self._calculate_regulation_score(normalized_query)
        
        # 5. 상담/절차 질의 점수 계산
        consultation_score = self._calculate_consultation_score(normalized_query)
        
        # 6. 라우팅 결정
        return self._make_routing_decision(
            regulation_score, consultation_score, normalized_query
        )
    
    def _normalize_query(self, query: str) -> str:
        """질의 정규화"""
        # 소문자 변환 및 불필요한 공백 제거
        normalized = query.lower().strip()
        # 특수문자 공백으로 치환
        normalized = re.sub(r'[^\w\s가-힣]', ' ', normalized)
        # 연속된 공백 제거
        normalized = re.sub(r'\s+', ' ', normalized)
        # 최종 공백 제거
        return normalized.strip()
    
    def _calculate_law_score(self, query: str) -> float:
        """관세법 조문 질의 점수 계산"""
        score = 0.0
        
        # 관세법 관련 키워드 매칭
        for keyword, weight in self.law_keywords.items():
            if keyword in query:
                score += weight
        
        # 관세법 특화 패턴 매칭
        law_patterns = [
            r'관세법.*제.*조', r'관세법.*규정', r'관세법.*조문',
            r'관세.*법령', r'관세.*법률', r'법령.*내용',
            r'조문.*해석', r'법률.*근거', r'관세.*규정'
        ]
        
        for pattern in law_patterns:
            if re.search(pattern, query):
                score += 0.4
        
        return min(score, 1.0)
    
    def _detect_animal_plant_import_query(self, query: str) -> float:
        """동식물 수입 허용국가 질의 감지"""
        # 수입 관련 패턴
        import_patterns = [
            r'어디서.*수입', r'수입.*어디', r'어느.*나라.*수입',
            r'수입.*가능.*국가', r'허용.*국가', r'수입.*국가',
            r'수입.*해야', r'수입.*할.*수.*있'
        ]
        
        import_score = 0.0
        for pattern in import_patterns:
            if re.search(pattern, query):
                import_score += 0.4
        
        # 동식물 제품 언급 확인
        animal_plant_score = 0.0
        for product in self.animal_plant_products:
            if product in query:
                animal_plant_score += 0.6
                break
        
        return min(import_score + animal_plant_score, 1.0)
    
    def _extract_animal_plant_products(self, query: str) -> List[str]:
        """질의에서 동식물 제품 추출"""
        detected = []
        for product in self.animal_plant_products:
            if product in query:
                detected.append(product)
        return detected
    
    def _calculate_regulation_score(self, query: str) -> float:
        """규제/법령 질의 점수 계산"""
        score = 0.0
        
        # 규제 관련 키워드 매칭
        for keyword, weight in self.regulation_keywords.items():
            if keyword in query:
                score += weight
        
        # 규제 관련 패턴 매칭
        regulation_patterns = [
            r'규제.*어떻게', r'법령.*내용', r'금지.*품목',
            r'허용.*국가', r'수입.*제한', r'수출.*금지',
            r'hs.*코드', r'검역.*요구'
        ]
        
        for pattern in regulation_patterns:
            if re.search(pattern, query):
                score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_consultation_score(self, query: str) -> float:
        """상담/절차 질의 점수 계산"""
        score = 0.0
        
        # 상담 관련 키워드 매칭
        for keyword, weight in self.consultation_keywords.items():
            if keyword in query:
                score += weight
        
        # 절차 관련 패턴 매칭
        consultation_patterns = [
            r'어떻게.*해야', r'절차.*알려', r'방법.*가르쳐',
            r'신고.*방법', r'서류.*무엇', r'어디서.*신청',
            r'비용.*얼마', r'시간.*얼마', r'처리.*기간'
        ]
        
        for pattern in consultation_patterns:
            if re.search(pattern, query):
                score += 0.3
        
        return min(score, 1.0)
    
    def _make_routing_decision(self, 
                              regulation_score: float, 
                              consultation_score: float, 
                              query: str) -> Tuple[QueryType, float, Dict[str, Any]]:
        """라우팅 결정"""
        routing_info = {
            "regulation_score": regulation_score,
            "consultation_score": consultation_score,
            "analysis_method": "keyword_pattern_matching"
        }
        
        # 점수 차이가 클 때
        score_diff = abs(regulation_score - consultation_score)
        
        if score_diff > 0.3:
            if regulation_score > consultation_score:
                return QueryType.REGULATION, regulation_score, {
                    **routing_info,
                    "reason": "high_regulation_score",
                    "confidence": "high"
                }
            else:
                return QueryType.CONSULTATION, consultation_score, {
                    **routing_info,
                    "reason": "high_consultation_score", 
                    "confidence": "high"
                }
        
        # 점수가 비슷할 때
        elif regulation_score > 0.4 and consultation_score > 0.4:
            return QueryType.MIXED, max(regulation_score, consultation_score), {
                **routing_info,
                "reason": "mixed_query_type",
                "confidence": "medium"
            }
        
        # 둘 다 낮은 점수일 때
        elif regulation_score < 0.3 and consultation_score < 0.3:
            return QueryType.CONSULTATION, 0.5, {
                **routing_info,
                "reason": "low_confidence_default",
                "confidence": "low"
            }
        
        # 기본: 더 높은 점수쪽으로
        else:
            if regulation_score >= consultation_score:
                return QueryType.REGULATION, regulation_score, {
                    **routing_info,
                    "reason": "regulation_preference",
                    "confidence": "medium"
                }
            else:
                return QueryType.CONSULTATION, consultation_score, {
                    **routing_info,
                    "reason": "consultation_preference",
                    "confidence": "medium"
                }
    
    def _load_regulation_keywords(self) -> Dict[str, float]:
        """규제 관련 키워드 및 가중치"""
        return {
            # 규제 관련
            "규제": 0.4, "제한": 0.4, "금지": 0.5, "허용": 0.3,
            "수입규제": 0.6, "수출규제": 0.6, "수입제한": 0.6, "수출제한": 0.6,
            "금지품목": 0.7, "제한품목": 0.6,
            
            # 국가 및 지역
            "국가": 0.2, "지역": 0.2, "허용국가": 0.5, "금지국가": 0.5,
            
            # 검역 및 인증
            "검역": 0.4, "인증": 0.3, "허가": 0.3, "승인": 0.3,
            "검사": 0.3, "검증": 0.3,
            
            # 동식물
            "동물": 0.3, "식물": 0.3, "축산물": 0.4, "농산물": 0.4,
            "육류": 0.4, "과일": 0.3, "채소": 0.3,
            
            # HS코드 관련
            "hs코드": 0.5, "hs": 0.3, "품목분류": 0.4, "통계부호": 0.4
        }
    
    def _load_consultation_keywords(self) -> Dict[str, float]:
        """상담 관련 키워드 및 가중치"""
        return {
            # 절차 관련
            "절차": 0.5, "방법": 0.4, "과정": 0.3, "순서": 0.3,
            "신청": 0.4, "신고": 0.5, "접수": 0.3, "제출": 0.3,
            
            # 서류 관련  
            "서류": 0.4, "문서": 0.3, "양식": 0.4, "신청서": 0.5,
            "증명서": 0.4, "허가서": 0.4, "인증서": 0.4,
            
            # 비용 및 시간
            "비용": 0.4, "수수료": 0.4, "요금": 0.3, "가격": 0.2,
            "시간": 0.3, "기간": 0.4, "소요": 0.3, "처리": 0.3,
            
            # 질문 표현
            "어떻게": 0.3, "어디서": 0.3, "무엇": 0.2, "어떤": 0.2,
            "언제": 0.2, "얼마": 0.3, "몇": 0.2,
            
            # 도움 요청
            "도움": 0.2, "알려": 0.3, "가르쳐": 0.3, "설명": 0.3,
            "문의": 0.4, "상담": 0.5, "질문": 0.3,
            
            # 실무 관련
            "실무": 0.4, "업무": 0.3, "처리": 0.3, "담당": 0.2,
            "경험": 0.2, "사례": 0.4, "예시": 0.3
        }
    
    def _load_law_keywords(self) -> Dict[str, float]:
        """관세법 관련 키워드 및 가중치"""
        return {
            # 관세법 직접 언급
            "관세법": 0.8, "관세법령": 0.7, "관세규정": 0.6,
            "관세법시행령": 0.7, "관세법시행규칙": 0.7,
            
            # 법령 관련
            "법령": 0.5, "법률": 0.5, "조문": 0.6, "조항": 0.5,
            "규정": 0.4, "기준": 0.3, "원칙": 0.3,
            
            # 조 단위
            "제": 0.3, "조": 0.4, "항": 0.3, "호": 0.2,
            "관세법제": 0.6,
            
            # 관세 관련
            "관세": 0.4, "관세율": 0.5, "세율": 0.4, "부가세": 0.3,
            "과세": 0.4, "세금": 0.3, "납세": 0.4,
            
            # 법적 근거
            "근거": 0.4, "기준": 0.3, "원칙": 0.3, "규칙": 0.4,
            "해석": 0.4, "적용": 0.3, "판단": 0.3
        }
    
    def _load_animal_plant_products(self) -> List[str]:
        """동식물 제품 키워드 목록"""
        return [
            # 축산물
            "소고기", "돼지고기", "닭고기", "양고기", "육류", "고기",
            "우유", "치즈", "버터", "유제품",
            "계란", "달걀",
            
            # 수산물
            "생선", "어류", "연어", "참치", "고등어", "명태",
            "새우", "게", "조개", "굴", "전복", "수산물",
            
            # 농산물 - 과일
            "사과", "배", "귤", "오렌지", "바나나", "포도",
            "딸기", "복숭아", "자두", "감", "과일",
            "체리", "키위", "망고", "파인애플",
            
            # 농산물 - 채소
            "배추", "무", "당근", "양파", "마늘", "생강",
            "고추", "파프리카", "토마토", "오이", "호박",
            "콩", "옥수수", "감자", "고구마", "채소",
            
            # 곡물
            "쌀", "밀", "보리", "콩", "옥수수", "곡물", "곡류",
            
            # 견과류
            "땅콩", "아몬드", "호두", "잣", "견과류",
            
            # 식물 관련
            "식물", "꽃", "나무", "씨앗", "구근", "묘목",
            "화훼", "원예", "농작물",
            
            # 가공품
            "건조과일", "냉동식품", "통조림", "가공식품"
        ]


# 싱글톤 인스턴스 관리
_query_router_instance: Optional[AsyncQueryRouter] = None


async def get_query_router() -> AsyncQueryRouter:
    """
    AsyncQueryRouter 싱글톤 인스턴스 반환
    FastAPI dependency injection용
    """
    global _query_router_instance
    
    if _query_router_instance is None:
        _query_router_instance = AsyncQueryRouter()
    
    return _query_router_instance