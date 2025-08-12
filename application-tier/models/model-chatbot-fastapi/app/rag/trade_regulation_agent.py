"""
FastAPI용 무역 규제 전문 에이전트
기존 model-chatbot의 TradeRegulationAgent를 비동기 버전으로 포팅
trade_regulation 데이터에 특화된 전용 에이전트
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

# OpenAI 클라이언트 import
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

# 로컬 모듈들 import
from .trade_info_retriever import TradeInfoRetriever

logger = logging.getLogger(__name__)


class AsyncTradeRegulationMemory:
    """
    무역 규제 전용 대화 기록 관리 클래스 (비동기 호환)
    
    무역 규제 상담에 특화된 메모리 관리:
    - 간결한 대화 기록 유지 (규제 정보는 복잡하므로)
    - 참조된 규제 정보 추적
    - 검색 기록 관리로 연속 질문 지원
    
    주요 특징:
    - 일반 대화보다 짧은 기록 유지 (기본 8턴)
    - 규제 특화 컨텍스트 관리
    - 검색 패턴 학습 지원
    """
    
    def __init__(self, max_history: int = 8):
        """
        무역 규제 전용 메모리 초기화
        
        Args:
            max_history: 최대 대화 기록 수 (규제 정보는 간결하게 관리)
        """
        self.max_history = max_history
        self.messages = []
        self.regulation_context = []  # 참조된 규제 정보들
        self.search_history = []  # 규제 검색 기록
        
    async def add_user_message(self, message: str, search_context: Optional[Dict] = None) -> None:
        """사용자 메시지 추가 (비동기)"""
        message_data = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if search_context:
            message_data["search_context"] = search_context
            self.search_history.append(search_context)
        
        self.messages.append(message_data)
        await self._trim_history()
    
    async def add_assistant_message(self, 
                                   message: str, 
                                   source_regulations: Optional[List[Dict]] = None) -> None:
        """어시스턴트 메시지 추가 (비동기)"""
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
        
        await self._trim_history()
    
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
    
    async def clear_history(self) -> None:
        """대화 기록 초기화 (비동기)"""
        self.messages.clear()
        self.regulation_context.clear()
        self.search_history.clear()
    
    async def _trim_history(self) -> None:
        """대화 기록 크기 제한 (비동기)"""
        if len(self.messages) > self.max_history:
            # 시스템 메시지는 유지하고 오래된 대화만 제거
            system_messages = [msg for msg in self.messages if msg["role"] == "system"]
            other_messages = [msg for msg in self.messages if msg["role"] != "system"]
            
            # 최근 대화만 유지
            trimmed_other = other_messages[-(self.max_history - len(system_messages)):]
            self.messages = system_messages + trimmed_other


class AsyncTradeRegulationAgent:
    """
    FastAPI용 비동기 무역 규제 전문 에이전트
    
    무역 규제 데이터(trade_regulation)에 특화된 RAG 에이전트:
    - 동식물 수입 허용국가 정보
    - 수입/수출 규제 및 제한 품목
    - HS코드 기반 품목별 규제 정보
    - 국가별 무역 규제 현황
    
    기존 TradeRegulationAgent의 모든 기능을 비동기로 구현하면서
    FastAPI 환경에 최적화
    """
    
    def __init__(self,
                 retriever: Optional['TradeInfoRetriever'] = None,
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = 0.1,  # 규제 정보는 더 정확하게
                 max_context_docs: int = 12,  # 더 많은 규제 문서 참조
                 similarity_threshold: float = 0.0,
                 openai_api_key: Optional[str] = None):
        """
        비동기 무역 규제 에이전트 초기화
        
        Args:
            retriever: 무역 정보 검색 엔진 (None이면 나중에 초기화)
            model_name: OpenAI 모델명
            temperature: 생성 온도 (규제 정보는 낮게 설정)
            max_context_docs: 최대 컨텍스트 문서 수
            similarity_threshold: 유사도 임계값
            openai_api_key: OpenAI API 키 (None이면 환경변수 사용)
        """
        self.retriever = retriever
        self.model_name = model_name
        self.temperature = temperature
        self.max_context_docs = max_context_docs
        self.similarity_threshold = similarity_threshold
        
        # OpenAI 비동기 클라이언트 초기화
        if AsyncOpenAI:
            self.client = AsyncOpenAI(api_key=openai_api_key)
        else:
            self.client = None
            logger.warning("AsyncOpenAI not available, using synchronous fallback")
        
        # 무역 규제 전용 메모리 초기화
        self.memory = AsyncTradeRegulationMemory()
        
        self.is_initialized = False
        logger.info("AsyncTradeRegulationAgent initialized")
    
    async def initialize(self) -> None:
        """에이전트 초기화 (retriever 생성 등)"""
        if self.is_initialized:
            return
            
        try:
            # retriever가 없으면 생성
            if not self.retriever:
                await self._create_retriever()
            
            self.is_initialized = True
            logger.info("✅ AsyncTradeRegulationAgent fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AsyncTradeRegulationAgent: {e}")
            raise
    
    async def _create_retriever(self) -> None:
        """무역 정보 검색 엔진 생성"""
        try:
            # 기존 model-chatbot 모듈을 사용하여 retriever 생성
            # 동기 방식이므로 executor에서 실행
            loop = asyncio.get_event_loop()
            self.retriever = await loop.run_in_executor(None, self._create_retriever_sync)
            
            logger.info("✅ Trade info retriever created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create trade info retriever: {e}")
            self.retriever = None
    
    def _create_retriever_sync(self) -> 'TradeInfoRetriever':
        """동기적 retriever 생성 (executor에서 실행)"""
        # 기존 model-chatbot의 설정을 사용
        from ..utils.config import get_trade_agent_config
        from .embeddings import LangChainEmbedder
        from .vector_store import LangChainVectorStore
        from .query_normalizer import TradeQueryNormalizer
        
        config = get_trade_agent_config()
        
        embedder = LangChainEmbedder()
        vector_store = LangChainVectorStore(
            collection_name=config["collection_name"]
        )
        query_normalizer = TradeQueryNormalizer()
        
        return TradeInfoRetriever(
            embedder=embedder,
            vector_store=vector_store,
            query_normalizer=query_normalizer
        )
    
    async def query_regulation(self, 
                              user_input: str, 
                              search_filters: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict]]:
        """
        무역 규제 질의 처리 (trade_regulation 데이터만)
        
        Args:
            user_input: 사용자 입력
            search_filters: 검색 필터
            
        Returns:
            Tuple[str, List[Dict]]: (응답 텍스트, 참조 규제 문서 리스트)
        """
        if not self.is_initialized:
            await self.initialize()
        
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
            
            # 3. 규제 전용 검색 컨텍스트 생성
            regulation_context = await self._create_regulation_search_context(user_input)
            
            # 4. 관련 문서 검색
            retrieved_docs = await self._search_regulation_documents(
                user_input, search_filters, regulation_context
            )
            
            # 5. 사용자 메시지를 메모리에 추가
            await self.memory.add_user_message(user_input, search_context)
            
            # 6. AI 응답 생성
            response_text = await self._generate_regulation_response(user_input, retrieved_docs)
            
            # 7. 응답을 메모리에 추가
            await self.memory.add_assistant_message(response_text, retrieved_docs)
            
            logger.info(f"✅ Trade regulation query completed: {user_input[:50]}...")
            
            return response_text, retrieved_docs
            
        except Exception as e:
            logger.error(f"❌ Trade regulation query failed: {e}")
            error_response = "죄송합니다. 무역 규제 정보를 조회하는 중 오류가 발생했습니다. 다시 시도해 주세요."
            return error_response, []
    
    async def get_animal_plant_regulation(self, product: str) -> str:
        """특정 동식물 제품의 수입 규제 정보 조회"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 동식물 규제 데이터에서만 검색
            search_filters = {
                "data_type": "trade_regulation",
                "data_source": "동식물허용금지지역"
            }
            
            retrieved_docs = await self._search_regulation_documents(
                f"{product} 수입 허용 국가 규제",
                search_filters
            )
            
            if not retrieved_docs:
                return f"{product}에 대한 동식물 수입 규제 정보를 찾을 수 없습니다."
            
            # 규제 정보 요약 생성
            context = self._format_regulation_documents(retrieved_docs)
            
            summary_prompt = f"""다음 동식물 수입 규제 정보를 바탕으로 {product}의 수입 허용국가 정보를 제공해주세요:

{context}

{product} 수입 규제 요약:"""
            
            if self.client:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Fallback for synchronous client
                import openai
                response = openai.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Animal plant regulation query failed: {e}")
            return f"{product} 규제 정보 조회 중 오류가 발생했습니다."
    
    async def reset_conversation(self) -> None:
        """대화 초기화"""
        await self.memory.clear_history()
        logger.info("Trade regulation conversation history reset")
    
    def get_conversation_history(self) -> List[Dict]:
        """현재 대화 기록 반환"""
        return self.memory.get_conversation_history(include_timestamps=True)
    
    async def _create_regulation_search_context(self, user_input: str) -> Dict[str, Any]:
        """무역 규제 전용 검색 컨텍스트 생성 (질의 의도 기반 동적 생성)"""
        
        # 기본 컨텍스트
        search_context = {
            "agent_type": "regulation_agent",
            "domain_hints": ["trade_regulation"],
            "boost_keywords": [],
            "priority_data_sources": []
        }
        
        # 질의 텍스트 소문자 변환
        query_lower = user_input.lower()
        
        # 1. 수출/수입 구분
        is_export_query = any(keyword in query_lower for keyword in 
                             ["수출", "export", "내보내", "해외판매", "외국판매"])
        is_import_query = any(keyword in query_lower for keyword in 
                             ["수입", "import", "들여오", "해외구매", "외국구매"])
        
        # 2. 제한/금지 구분
        is_restriction_query = any(keyword in query_lower for keyword in 
                                  ["제한", "restriction", "제한품목", "제한물품"])
        is_prohibition_query = any(keyword in query_lower for keyword in 
                                  ["금지", "prohibition", "금지품목", "금지물품"])
        
        # 3. 동식물 관련 구분
        animal_plant_keywords = ["동식물", "동물", "식물", "농산물", "축산물", "검역", "아보카도", 
                                "바나나", "딸기", "소고기", "돼지고기", "닭고기", "생선", "우유"]
        is_animal_plant_query = any(keyword in query_lower for keyword in animal_plant_keywords)
        
        # 4. 외국 규제 (한국 수출품에 대한 외국의 규제) - 키워드 확장
        foreign_restriction_patterns = [
            "외국", "해외", "상대국", "목적지", "destination",
            "베트남", "인도", "중국", "미국", "일본", "태국", "싱가포르", "필리핀", "말레이시아",
            "이 거는", "가 거는", "이 한국", "가 한국", "대한", "한국에", "한국 제품",
            "반덤핑", "세이프가드", "수입제한", "수입금지", "관세부과", "통상제재"
        ]
        is_foreign_restriction = any(keyword in query_lower for keyword in foreign_restriction_patterns)
        
        # 5. 질의 유형별 컨텍스트 설정 (우선순위 기반 분류)
        # 1순위: 외국 규제 (키워드만으로 판단, is_export_query 조건 제거)
        if is_foreign_restriction:
            # 외국이 한국 수출품에 거는 규제
            search_context.update({
                "domain_hints": ["trade_regulation", "destination_restrictions", "외국규제"],
                "boost_keywords": ["목적지국", "상대국규제", "해외규제", "수입규제DB"],
                "priority_data_sources": ["수입규제DB_전체"],
                "regulation_type_hint": "export_destination_restrictions"
            })
            
        # 2순위: 동식물 수입 규제  
        elif is_import_query and is_animal_plant_query:
            search_context.update({
                "domain_hints": ["trade_regulation", "animal_plant_import", "허용국가", "수입규제"],
                "boost_keywords": ["허용국가", "동식물", "검역", "수입허용", "수입금지", "검역규정"],
                "priority_data_sources": ["동식물허용금지지역"],
                "regulation_type_hint": "import_regulations"
            })
            
        # 3순위: 한국의 수출 금지 품목
        elif is_export_query and is_prohibition_query:
            search_context.update({
                "domain_hints": ["trade_regulation", "export_control", "수출금지", "수출규제"],
                "boost_keywords": ["수출금지", "수출금지품목", "수출규제", "수출통제"],
                "priority_data_sources": ["수출금지품목"],
                "regulation_type_hint": "export_prohibitions"
            })
            
        # 4순위: 한국의 수출 제한 품목
        elif is_export_query and is_restriction_query:
            search_context.update({
                "domain_hints": ["trade_regulation", "export_control", "수출제한", "수출규제"],
                "boost_keywords": ["수출제한", "수출제한품목", "수출규제", "수출통제", "수출관리법"],
                "priority_data_sources": ["수출제한품목"],
                "regulation_type_hint": "export_restrictions"
            })
            
        # 5순위: 한국의 일반 수입 제한 품목  
        elif is_import_query and is_restriction_query and not is_animal_plant_query:
            search_context.update({
                "domain_hints": ["trade_regulation", "import_control", "수입제한", "수입규제"],
                "boost_keywords": ["수입제한", "수입제한품목", "수입규제", "수입통제"],
                "priority_data_sources": ["수입제한품목"],
                "regulation_type_hint": "import_restrictions"
            })
            
        else:
            # 기본 경우: 모든 규제 데이터에서 검색
            search_context.update({
                "domain_hints": ["trade_regulation", "general_regulations"],
                "boost_keywords": ["규제", "제한", "금지", "허용", "수출", "수입"],
                "priority_data_sources": ["수출제한품목", "수입제한품목", "동식물허용금지지역", "수출금지품목", "수입규제DB_전체"]
            })
        
        # 6. HS코드 관련 질의 추가 힌트 제공
        if any(char.isdigit() for char in user_input) and len([c for c in user_input if c.isdigit()]) >= 4:
            search_context["domain_hints"].extend(["hs_code", "품목분류"])
            search_context["boost_keywords"].extend(["HS코드", "품목", "분류", "관세"])
        
        logger.info(f"🎯 동적 검색 컨텍스트 생성: {search_context}")
        return search_context
    
    async def _search_regulation_documents(self, 
                                          query: str, 
                                          search_filters: Optional[Dict[str, Any]] = None,
                                          search_context: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """규제 문서 검색 (비동기)"""
        if not self.retriever:
            logger.warning("Retriever not available, returning empty results")
            return []
        
        try:
            # 동기 retriever를 비동기로 실행
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: self.retriever.search_trade_info(
                    raw_query=query,
                    top_k=self.max_context_docs,
                    include_related=True,
                    expand_with_synonyms=True,
                    similarity_threshold=self.similarity_threshold,
                    filter_by=search_filters,
                    search_context=search_context
                )
            )
            
            logger.info(f"Retrieved {len(docs)} regulation documents")
            return docs
            
        except Exception as e:
            logger.error(f"Regulation document search failed: {e}")
            return []
    
    async def _generate_regulation_response(self, query: str, documents: List[Dict]) -> str:
        """규제 응답 생성 (비동기)"""
        try:
            # 시스템 프롬프트
            system_prompt = self._get_regulation_system_prompt()
            
            # 컨텍스트 문서 포맷팅
            context = self._format_regulation_documents(documents)
            
            # 대화 기록
            chat_history = self._format_chat_history()
            
            # 사용자 프롬프트 구성
            user_prompt = f"""[대화 기록]
{chat_history}

[무역 규제 정보]
{context}

[현재 질문]
{query}

위의 무역 규제 정보를 근거로 정확하고 신뢰할 수 있는 답변을 제공해주세요."""
            
            # OpenAI API 호출
            if self.client:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=1200
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Fallback for synchronous client
                import openai
                response = openai.chat.completions.create(
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
            logger.error(f"Regulation response generation failed: {e}")
            return f"규제 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
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
                    doc_info += f"\n제품: {product_name}"
                
                if allowed_countries:
                    if isinstance(allowed_countries, list):
                        allowed_str = ", ".join(allowed_countries)
                    else:
                        allowed_str = str(allowed_countries)
                    doc_info += f"\n허용국가: {allowed_str}"
                
                if prohibited_countries:
                    if isinstance(prohibited_countries, list):
                        prohibited_str = ", ".join(prohibited_countries)
                    else:
                        prohibited_str = str(prohibited_countries)
                    doc_info += f"\n금지국가: {prohibited_str}"
                
                if special_conditions:
                    doc_info += f"\n특별조건: {special_conditions}"
            
            else:
                # 일반 규제 데이터 처리
                regulation_type = metadata.get("regulation_type", "")
                if regulation_type:
                    doc_info += f"\n규제유형: {regulation_type}"
                
                # HS코드 정보
                hs_code = metadata.get("hs_code", "")
                if hs_code:
                    doc_info += f"\nHS코드: {hs_code}"
                
                # 국가 정보
                affected_country = metadata.get("affected_country", "") or metadata.get("regulating_country", "")
                if affected_country:
                    doc_info += f"\n대상국가: {affected_country}"
            
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
            
            formatted_doc = f"{doc_info}{special_info}\n{content}"
            formatted_docs.append(formatted_doc)
        
        return "\n\n".join(formatted_docs)
    
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
        
        return "\n".join(formatted_history) if formatted_history else "이전 대화 없음"


# 싱글톤 인스턴스 관리를 위한 전역 변수
_trade_regulation_agent_instance: Optional[AsyncTradeRegulationAgent] = None


async def get_trade_regulation_agent() -> AsyncTradeRegulationAgent:
    """
    무역 규제 에이전트 싱글톤 인스턴스 반환
    FastAPI dependency injection용
    """
    global _trade_regulation_agent_instance
    
    if _trade_regulation_agent_instance is None:
        _trade_regulation_agent_instance = AsyncTradeRegulationAgent()
        await _trade_regulation_agent_instance.initialize()
    
    return _trade_regulation_agent_instance


async def create_trade_regulation_agent(**kwargs) -> AsyncTradeRegulationAgent:
    """
    새로운 무역 규제 에이전트 인스턴스 생성
    
    Args:
        **kwargs: AsyncTradeRegulationAgent 생성자 파라미터
        
    Returns:
        초기화된 AsyncTradeRegulationAgent 인스턴스
    """
    agent = AsyncTradeRegulationAgent(**kwargs)
    await agent.initialize()
    return agent