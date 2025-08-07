"""
Trade Regulation Agent Module

trade_regulation 데이터에 특화된 전용 에이전트
동식물 수입 규제, 일반 무역 규제 데이터만을 처리하여 정확한 규제 정보 제공
"""

import logging
import openai
from typing import List, Dict, Any, Optional, Tuple
import json
import os
from datetime import datetime
from .trade_info_retriever import TradeInfoRetriever

logger = logging.getLogger(__name__)


class TradeRegulationMemory:
    """무역 규제 전용 대화 기록 관리 클래스"""
    
    def __init__(self, max_history: int = 8):
        """
        초기화
        
        Args:
            max_history (int): 최대 대화 기록 수 (규제 정보는 간결하게)
        """
        self.max_history = max_history
        self.messages = []
        self.regulation_context = []  # 참조된 규제 정보들
        self.search_history = []  # 규제 검색 기록
        
    def add_user_message(self, message: str, search_context: Optional[Dict] = None) -> None:
        """사용자 메시지 추가"""
        message_data = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if search_context:
            message_data["search_context"] = search_context
            self.search_history.append(search_context)
        
        self.messages.append(message_data)
        self._trim_history()
    
    def add_assistant_message(self, message: str, source_regulations: List[Dict] = None) -> None:
        """어시스턴트 메시지 추가"""
        self.messages.append({
            "role": "assistant", 
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "source_regulations": source_regulations or []
        })
        
        # 참조된 규제 정보들을 컨텍스트에 추가
        if source_regulations:
            for regulation in source_regulations:
                if regulation not in self.regulation_context:
                    self.regulation_context.append(regulation)
        
        self._trim_history()
    
    def get_conversation_history(self, include_timestamps: bool = False) -> List[Dict]:
        """대화 기록 조회"""
        if include_timestamps:
            return self.messages.copy()
        else:
            return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def get_recent_context(self, num_turns: int = 2) -> List[Dict]:
        """최근 대화 컨텍스트 조회 (규제 정보는 간결하게)"""
        recent_messages = self.messages[-num_turns*2:] if self.messages else []
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    
    def clear_history(self) -> None:
        """대화 기록 초기화"""
        self.messages.clear()
        self.regulation_context.clear()
        self.search_history.clear()
    
    def _trim_history(self) -> None:
        """대화 기록 크기 제한"""
        if len(self.messages) > self.max_history:
            # 시스템 메시지는 유지하고 오래된 대화만 제거
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            
            # 최근 대화만 유지
            trimmed_other = other_messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + trimmed_other


class TradeRegulationAgent:
    """무역 규제 전용 에이전트 - trade_regulation 데이터만 처리"""
    
    def __init__(self,
                 retriever: TradeInfoRetriever,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = 0.1,  # 규제 정보는 더 정확하게
                 max_context_docs: int = 12,  # 더 많은 규제 문서 참조
                 similarity_threshold: float = 0.0):
        """
        초기화
        
        Args:
            retriever (TradeInfoRetriever): 무역 정보 검색기
            model_name (str): 사용할 GPT 모델명
            temperature (float): 생성 온도 (규제 정보는 낮게)
            max_context_docs (int): 최대 컨텍스트 문서 수
            similarity_threshold (float): 유사도 임계값
        """
        self.retriever = retriever
        self.model_name = model_name
        self.temperature = temperature
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please check your .env file or set the environment variable directly."
            )
        
        self.client = openai.OpenAI(api_key=api_key)
        self.memory = TradeRegulationMemory()
        
        logger.info(f"TradeRegulationAgent initialized with model: {model_name}")
    
    def query_regulation(self, user_input: str, 
                        search_filters: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict]]:
        """
        무역 규제 질의 처리 (trade_regulation 데이터만)
        
        Args:
            user_input (str): 사용자 입력
            search_filters (Optional[Dict[str, Any]]): 검색 필터
            
        Returns:
            Tuple[str, List[Dict]]: (응답 텍스트, 참조 규제 문서 리스트)
        """
        try:
            # 1. 검색 컨텍스트 준비
            search_context = {
                "query": user_input,
                "filters": search_filters,
                "data_type": "trade_regulation",  # 규제 데이터만
                "timestamp": datetime.now().isoformat()
            }
            
            # 2. trade_regulation 데이터에서만 검색
            if not search_filters:
                search_filters = {}
            search_filters["data_type"] = "trade_regulation"  # 필터 강제 설정
            
            # 3. 동식물 수입 규제 질의 감지 및 검색 컨텍스트 생성
            search_context = self._create_regulation_search_context(user_input)
            
            retrieved_docs = self.retriever.search_trade_info(
                raw_query=user_input,
                top_k=self.max_context_docs,
                include_related=True,
                expand_with_synonyms=True,
                similarity_threshold=self.similarity_threshold,
                filter_by=search_filters,
                search_context=search_context
            )
            
            # 3. 대화 기록에 사용자 메시지 추가
            self.memory.add_user_message(user_input, search_context)
            
            # 4. 응답 생성
            response_text = self._generate_regulation_response(user_input, retrieved_docs)
            
            # 5. 대화 기록에 응답 추가
            self.memory.add_assistant_message(response_text, retrieved_docs)
            
            logger.info(f"무역 규제 응답 생성 완료 (참조 규제: {len(retrieved_docs)}개)")
            return response_text, retrieved_docs
            
        except Exception as e:
            logger.error(f"무역 규제 질의 처리 실패: {e}")
            error_response = "죄송합니다. 무역 규제 정보를 조회하는 중 오류가 발생했습니다. 다시 시도해 주세요."
            return error_response, []
    
    def get_animal_plant_regulation(self, product: str) -> str:
        """특정 동식물 제품의 수입 규제 정보 조회"""
        try:
            # 동식물 규제 데이터에서만 검색
            search_filters = {
                "data_type": "trade_regulation",
                "data_source": "동식물허용금지지역"
            }
            
            retrieved_docs = self.retriever.search_trade_info(
                raw_query=f"{product} 수입 허용 국가 규제",
                top_k=10,
                filter_by=search_filters
            )
            
            if not retrieved_docs:
                return f"{product}에 대한 동식물 수입 규제 정보를 찾을 수 없습니다."
            
            # 규제 정보 요약 생성
            context = self._format_regulation_documents(retrieved_docs)
            
            summary_prompt = f"""다음 동식물 수입 규제 정보를 바탕으로 {product}의 수입 허용국가 정보를 제공해주세요:

{context}

{product} 수입 규제 요약:"""
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"동식물 규제 정보 조회 실패: {e}")
            return f"{product} 규제 정보 조회 중 오류가 발생했습니다."
    
    def reset_conversation(self) -> None:
        """대화 초기화"""
        self.memory.clear_history()
        logger.info("무역 규제 대화 기록이 초기화되었습니다.")
    
    def _create_regulation_search_context(self, user_input: str) -> Dict[str, Any]:
        """무역 규제 전용 검색 컨텍스트 생성 (LLM 기반 지능적 필터링 활용)"""
        search_context = {
            "agent_type": "regulation_agent",
            "domain_hints": ["trade_regulation", "animal_plant_import", "허용국가", "수입규제"],
            "boost_keywords": ["허용국가", "수입", "수출", "금지", "제한", "규제", "동식물", "검역"],
            "priority_data_sources": ["동식물허용금지지역", "수입규제DB", "수입제한품목", "수출제한품목"]
        }
        
        # HS코드 관련 질의 추가 힌트 제공
        if any(char.isdigit() for char in user_input) and len([c for c in user_input if c.isdigit()]) >= 4:
            search_context["domain_hints"].extend(["hs_code", "품목분류"])
            search_context["boost_keywords"].extend(["HS코드", "품목", "분류", "관세"])
        
        logger.debug(f"🎯 무역규제 검색 컨텍스트: {search_context}")
        return search_context
    
    def _generate_regulation_response(self, user_input: str, retrieved_docs: List[Dict]) -> str:
        """
        규제 문서를 바탕으로 응답 생성
        
        Args:
            user_input (str): 사용자 입력
            retrieved_docs (List[Dict]): 검색된 규제 문서들
            
        Returns:
            str: 생성된 응답
        """
        try:
            # 시스템 프롬프트
            system_prompt = self._get_regulation_system_prompt()
            
            # 컨텍스트 문서 포맷팅
            context = self._format_regulation_documents(retrieved_docs)
            
            # 대화 기록
            chat_history = self._format_chat_history()
            
            # 사용자 프롬프트 구성
            user_prompt = f"""[대화 기록]
{chat_history}

[무역 규제 정보]
{context}

[현재 질문]
{user_input}

위의 무역 규제 정보를 근거로 정확하고 신뢰할 수 있는 답변을 제공해주세요."""
            
            # GPT 응답 생성
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=1200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"규제 응답 생성 실패: {e}")
            return "규제 응답 생성 중 오류가 발생했습니다."
    
    def _get_regulation_system_prompt(self) -> str:
        """무역 규제 전용 시스템 프롬프트 반환"""
        return """당신은 한국 무역 규제 전문 AI입니다. 다음 원칙을 엄격히 준수하여 답변하세요:

**핵심 원칙:**
1. **규제 정보 최우선**: 제공된 무역 규제 정보만을 근거로 답변하세요. 추측이나 일반 지식은 사용하지 마세요.
2. **동식물 규제 우선**: 동식물 제품 수입 질문의 경우, 동식물허용금지지역 데이터를 최우선으로 참조하세요.
3. **정확성**: 규제 정보는 법적 구속력이 있으므로 100% 정확해야 합니다.
4. **명확성**: 허용국가, 금지국가, 특별조건을 명확히 구분하여 제시하세요.
5. **최신성**: 제공된 규제 정보가 없으면 "정보 없음"을 명시하고 관련 기관 문의를 안내하세요.

**데이터 우선순위:**
1. **동식물허용금지지역**: 동식물 제품의 수입 허용/금지 국가 정보 (최우선)
2. **수입규제DB**: 일반 수입 규제 및 제한 정보
3. **수입/수출 제한품목**: 특정 품목의 제한 및 금지 정보

**동식물 제품 처리 방법:**
- 허용국가가 명시된 경우: "○○국에서만 수입 가능"
- "허용국가외전체" 금지: "허용국가 외 모든 국가에서 수입 금지"
- 특별조건 존재: 반드시 조건 명시 (예: "특정 주/지역 제외")
- 규제 데이터 없음: "공식 규제 정보를 찾을 수 없음" + 관련 기관 안내

**답변 구조:**
### 핵심 답변
- **허용국가**: 명확한 국가 목록
- **금지/제한**: 금지 국가 또는 제한 조건

### 관련 규제 및 제한 사항
- 특별조건, 검역 요구사항, 추가 제한사항

### 추가 확인이 필요한 사항
- 관련 기관 문의 정보 (농림축산검역본부, 관세청 등)

**중요 경고:**
- 동식물 수입 규제는 검역과 직결되어 매우 엄격합니다.
- 규제 정보가 없으면 추측하지 말고 "정확한 정보 없음"을 명시하세요.
- 모든 답변은 제공된 규제 데이터에 기반해야 합니다."""
    
    def _format_regulation_documents(self, documents: List[Dict]) -> str:
        """규제 문서들을 포맷팅"""
        if not documents:
            return "관련 무역 규제 정보가 없습니다."
        
        formatted_docs = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            
            # 기본 정보
            doc_info = f"[규제 정보 {i}]"
            
            # 데이터 소스
            data_source = metadata.get("data_source", "")
            if data_source:
                doc_info += f" ({data_source})"
            
            # 동식물 규제 데이터 특별 처리
            if data_source == "동식물허용금지지역":
                product_name = metadata.get("product_name", "")
                allowed_countries = metadata.get("allowed_countries", [])
                prohibited_countries = metadata.get("prohibited_countries", [])
                special_conditions = metadata.get("special_conditions", "")
                
                if product_name:
                    doc_info += f"\\n제품: {product_name}"
                
                if allowed_countries:
                    if isinstance(allowed_countries, list):
                        allowed_str = ", ".join(allowed_countries)
                    else:
                        allowed_str = str(allowed_countries)
                    doc_info += f"\\n허용국가: {allowed_str}"
                
                if prohibited_countries:
                    if isinstance(prohibited_countries, list):
                        prohibited_str = ", ".join(prohibited_countries)
                    else:
                        prohibited_str = str(prohibited_countries)
                    doc_info += f"\\n금지국가: {prohibited_str}"
                
                if special_conditions:
                    doc_info += f"\\n특별조건: {special_conditions}"
            
            else:
                # 일반 규제 데이터 처리
                regulation_type = metadata.get("regulation_type", "")
                if regulation_type:
                    doc_info += f"\\n규제유형: {regulation_type}"
                
                # HS코드 정보
                hs_code = metadata.get("hs_code", "")
                if hs_code:
                    doc_info += f"\\nHS코드: {hs_code}"
                
                # 국가 정보
                affected_country = metadata.get("affected_country", "") or metadata.get("regulating_country", "")
                if affected_country:
                    doc_info += f"\\n대상국가: {affected_country}"
            
            # 내용
            content = doc.get("content", "")[:500]  # 최대 500자
            if len(doc.get("content", "")) > 500:
                content += "..."
            
            # 특수 정보
            special_info = ""
            if doc.get("boosted"):
                special_info = f" [우선매칭: {doc.get('boost_reason', '')}]"
            elif doc.get("match_type") == "exact_hs_code":
                special_info = " [정확한 HS코드 매칭]"
            
            formatted_doc = f"{doc_info}{special_info}\\n{content}"
            formatted_docs.append(formatted_doc)
        
        return "\\n\\n".join(formatted_docs)
    
    def _format_chat_history(self) -> str:
        """대화 기록 포맷팅"""
        if not self.memory.messages:
            return "이전 대화 없음"
        
        # 최근 2턴의 대화만 포함 (규제 정보는 간결하게)
        recent_messages = self.memory.get_recent_context(num_turns=2)
        
        formatted_history = []
        for msg in recent_messages:
            role = "사용자" if msg["role"] == "user" else "AI"
            content = msg["content"][:150]  # 최대 150자로 제한
            if len(msg["content"]) > 150:
                content += "..."
            formatted_history.append(f"{role}: {content}")
        
        return "\\n".join(formatted_history) if formatted_history else "이전 대화 없음"