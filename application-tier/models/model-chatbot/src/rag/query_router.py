"""
Query Router Module

사용자 질의를 분석하여 적절한 에이전트(TradeRegulationAgent vs ConsultationCaseAgent)로 라우팅
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """질의 유형 분류"""
    REGULATION = "regulation"  # 규제/법령 정보 질의
    CONSULTATION = "consultation"  # 실무/절차 상담 질의
    MIXED = "mixed"  # 혼합형 질의


class QueryRouter:
    """질의 라우터 - 사용자 질의를 분석하여 적절한 에이전트로 라우팅"""
    
    def __init__(self):
        """초기화"""
        self.regulation_keywords = self._load_regulation_keywords()
        self.consultation_keywords = self._load_consultation_keywords()
        self.animal_plant_products = self._load_animal_plant_products()
        
        logger.info("QueryRouter initialized")
    
    def route_query(self, user_query: str) -> Tuple[QueryType, float, Dict[str, Any]]:
        """
        사용자 질의를 분석하여 라우팅 결정
        
        Args:
            user_query (str): 사용자 질의
            
        Returns:
            Tuple[QueryType, float, Dict[str, Any]]: (질의 유형, 신뢰도, 라우팅 정보)
        """
        try:
            # 1. 질의 전처리
            normalized_query = self._normalize_query(user_query)
            
            # 2. 동식물 수입 질의 감지 (최우선)
            animal_plant_score = self._detect_animal_plant_import_query(normalized_query)
            if animal_plant_score > 0.8:
                return QueryType.REGULATION, animal_plant_score, {
                    "reason": "animal_plant_import_query",
                    "detected_products": self._extract_animal_plant_products(normalized_query),
                    "routing_priority": "high"
                }
            
            # 3. 규제/법령 질의 점수 계산
            regulation_score = self._calculate_regulation_score(normalized_query)
            
            # 4. 상담/절차 질의 점수 계산
            consultation_score = self._calculate_consultation_score(normalized_query)
            
            # 5. 라우팅 결정
            routing_decision = self._make_routing_decision(
                regulation_score, consultation_score, normalized_query
            )
            
            return routing_decision
            
        except Exception as e:
            logger.error(f"질의 라우팅 실패: {e}")
            # 기본값으로 상담 에이전트 사용
            return QueryType.CONSULTATION, 0.5, {"reason": "error_fallback"}
    
    def _normalize_query(self, query: str) -> str:
        """질의 정규화"""
        # 소문자 변환 및 불필요한 공백 제거
        normalized = query.lower().strip()
        # 특수문자 공백으로 치환
        normalized = re.sub(r'[^\w\s가-힣]', ' ', normalized)
        # 연속된 공백 제거
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
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
            r'hs.*코드', r'관세.*법', r'검역.*요구'
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
    
    def _make_routing_decision(self, regulation_score: float, consultation_score: float, 
                             query: str) -> Tuple[QueryType, float, Dict[str, Any]]:
        """라우팅 결정 로직"""
        
        # 점수 차이 계산
        score_diff = abs(regulation_score - consultation_score)
        
        # 결정 로직
        if regulation_score > consultation_score:
            if score_diff > 0.3:  # 명확한 규제 질의
                return QueryType.REGULATION, regulation_score, {
                    "reason": "clear_regulation_query",
                    "regulation_score": regulation_score,
                    "consultation_score": consultation_score,
                    "routing_priority": "high" if regulation_score > 0.7 else "medium"
                }
            elif score_diff > 0.1:  # 약간 규제 쪽
                return QueryType.REGULATION, regulation_score, {
                    "reason": "slight_regulation_preference",
                    "regulation_score": regulation_score,
                    "consultation_score": consultation_score,
                    "routing_priority": "medium"
                }
            else:  # 애매한 경우 - 혼합형
                return QueryType.MIXED, max(regulation_score, consultation_score), {
                    "reason": "ambiguous_query",
                    "regulation_score": regulation_score,
                    "consultation_score": consultation_score,
                    "routing_priority": "low"
                }
        
        elif consultation_score > regulation_score:
            if score_diff > 0.3:  # 명확한 상담 질의
                return QueryType.CONSULTATION, consultation_score, {
                    "reason": "clear_consultation_query",
                    "regulation_score": regulation_score,
                    "consultation_score": consultation_score,
                    "routing_priority": "high" if consultation_score > 0.7 else "medium"
                }
            elif score_diff > 0.1:  # 약간 상담 쪽
                return QueryType.CONSULTATION, consultation_score, {
                    "reason": "slight_consultation_preference",
                    "regulation_score": regulation_score,
                    "consultation_score": consultation_score,
                    "routing_priority": "medium"
                }
            else:  # 애매한 경우 - 혼합형
                return QueryType.MIXED, max(regulation_score, consultation_score), {
                    "reason": "ambiguous_query",
                    "regulation_score": regulation_score,
                    "consultation_score": consultation_score,
                    "routing_priority": "low"
                }
        
        else:  # 점수가 같은 경우
            # 기본값으로 상담 에이전트 사용 (더 포괄적)
            return QueryType.CONSULTATION, 0.5, {
                "reason": "equal_scores_default_consultation",
                "regulation_score": regulation_score,
                "consultation_score": consultation_score,
                "routing_priority": "low"
            }
    
    def _load_regulation_keywords(self) -> Dict[str, float]:
        """규제/법령 관련 키워드 로드"""
        return {
            # 핵심 규제 키워드 (높은 가중치)
            "규제": 0.8, "법령": 0.8, "금지": 0.7, "제한": 0.7,
            "허용": 0.6, "동식물": 0.8, "검역": 0.7,
            
            # 수입/수출 규제 관련
            "수입규제": 0.9, "수출규제": 0.9, "수입금지": 0.8, "수출금지": 0.8,
            "수입제한": 0.8, "수출제한": 0.8, "수입허용": 0.7, "수출허용": 0.7,
            
            # 관세 및 법령
            "관세법": 0.8, "관세율": 0.6, "hs코드": 0.7, "품목분류": 0.6,
            
            # 동식물 관련
            "검역요구": 0.8, "검역기준": 0.7, "수입허가": 0.7,
            "식물검역": 0.8, "동물검역": 0.8,
            
            # 일반 규제 용어
            "위반": 0.6, "처벌": 0.6, "벌금": 0.5, "위법": 0.6,
            "합법": 0.5, "적법": 0.5, "준수": 0.5
        }
    
    def _load_consultation_keywords(self) -> Dict[str, float]:
        """상담/절차 관련 키워드 로드"""
        return {
            # 절차 관련 키워드 (높은 가중치)
            "절차": 0.8, "방법": 0.7, "어떻게": 0.8, "해야": 0.6,
            "신청": 0.7, "신고": 0.8, "접수": 0.6,
            
            # 서류 관련
            "서류": 0.7, "문서": 0.6, "양식": 0.6, "작성": 0.6,
            "증명서": 0.7, "허가서": 0.7, "신고서": 0.8,
            
            # 통관 관련
            "통관": 0.9, "세관": 0.8, "신고": 0.8, "신고서": 0.8,
            "통관신고": 0.9, "수입신고": 0.8, "수출신고": 0.8,
            
            # 실무 관련
            "비용": 0.7, "수수료": 0.6, "기간": 0.7, "시간": 0.6,
            "소요": 0.5, "처리": 0.6, "완료": 0.5,
            
            # 문의 관련
            "문의": 0.6, "상담": 0.8, "도움": 0.6, "안내": 0.7,
            "가이드": 0.6, "설명": 0.6, "알려": 0.7,
            
            # FTA 관련
            "fta": 0.7, "원산지": 0.7, "특혜관세": 0.7, "원산지증명": 0.8,
            
            # 기타 실무
            "면세": 0.6, "감면": 0.6, "환급": 0.6, "정정": 0.6,
            "수정": 0.6, "변경": 0.6, "취소": 0.6
        }
    
    def _load_animal_plant_products(self) -> List[str]:
        """동식물 제품 목록 로드"""
        return [
            # 과일류
            '멜론', '아보카도', '바나나', '오렌지', '레몬', '라임', '파인애플', '망고', '키위',
            '사과', '배', '포도', '딸기', '체리', '복숭아', '자두', '살구', '감', '밤',
            '참외', '수박', '무화과', '석류', '감귤', '단감', '월귤', '두리안',
            
            # 곡물류
            '쌀', '밀', '옥수수', '콩', '팥', '녹두', '참깨', '들깨', '보리', '귀리',
            
            # 육류
            '돼지고기', '소고기', '닭고기', '오리고기', '양고기', '염소고기', '사슴고기',
            '가금육', '산양고기', '반추동물', '우제류동물',
            
            # 수산물
            '생선', '새우', '게', '조개', '굴', '전복', '해삼', '미역', '김',
            
            # 유제품
            '우유', '치즈', '버터', '요구르트', '유제품', '동물성유지',
            
            # 기타
            '계란', '꿀', '견과류', '호두', '아몬드', '피스타치오',
            
            # 채소류
            '감자', '고구마', '양파', '마늘', '생강', '당근', '무', '배추', '상추',
            '토마토', '고추', '가지', '오이', '호박', '브로콜리', '양배추'
        ]
    
    def get_routing_explanation(self, query: str) -> str:
        """라우팅 결정에 대한 설명 생성"""
        query_type, confidence, routing_info = self.route_query(query)
        
        explanation = f"질의 분석 결과:\\n"
        explanation += f"- 라우팅: {query_type.value} 에이전트\\n"
        explanation += f"- 신뢰도: {confidence:.2f}\\n"
        explanation += f"- 이유: {routing_info.get('reason', 'unknown')}\\n"
        
        if 'regulation_score' in routing_info:
            explanation += f"- 규제 점수: {routing_info['regulation_score']:.2f}\\n"
        if 'consultation_score' in routing_info:
            explanation += f"- 상담 점수: {routing_info['consultation_score']:.2f}\\n"
        
        if 'detected_products' in routing_info:
            products = routing_info['detected_products']
            if products:
                explanation += f"- 감지된 제품: {', '.join(products)}\\n"
        
        return explanation