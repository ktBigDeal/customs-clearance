"""
Orchestrator Module

통합 멀티 에이전트 오케스트레이션 시스템
LangGraph 기반 지능형 라우팅과 전통적 키워드 라우팅 결합
"""

import logging
from typing import Literal, List, Dict, Any, Optional, TypedDict, Annotated, Tuple
import operator
import json
import re
import os
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command, Send
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """질의 유형 분류"""
    LAW = "law"  # 관세법 조문 질의
    REGULATION = "regulation"  # 무역 규제 질의
    CONSULTATION = "consultation"  # 실무 상담 질의
    MIXED = "mixed"  # 혼합형 질의


class AgentSelection(BaseModel):
    """에이전트 선택 응답 모델"""
    next_agent: Literal["customs_law_agent", "regulations_agent", "complaints_agent", "__end__"] = Field(
        description="다음에 호출할 에이전트 이름"
    )
    reasoning: str = Field(description="에이전트 선택 이유")
    complexity: float = Field(
        description="질의 복잡도 (0.0-1.0)", 
        ge=0.0, le=1.0
    )
    requires_multiple_agents: bool = Field(
        description="여러 에이전트가 필요한 복합 질의인지 여부"
    )


class EnhancedState(TypedDict):
    """강화된 상태 관리"""
    messages: Annotated[List[BaseMessage], operator.add]
    active_agents: List[str]  # 현재 활성 에이전트들
    query_complexity: float   # 질의 복잡도
    agent_responses: Dict[str, Any]  # 에이전트별 응답 저장
    routing_history: List[Dict[str, Any]]  # 라우팅 히스토리
    current_step: int  # 현재 단계


class MultiAgentOrchestrator:
    """통합 멀티 에이전트 오케스트레이션 시스템"""
    
    def __init__(self, 
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = 0.1,
                 use_intelligent_routing: bool = True):
        """
        초기화
        
        Args:
            model_name: 사용할 언어 모델
            temperature: 모델 온도 설정
            use_intelligent_routing: LangGraph 지능형 라우팅 사용 여부
        """
        self.model_name = model_name
        self.temperature = temperature
        self.use_intelligent_routing = use_intelligent_routing
        
        # 구조화된 출력을 위한 LLM 초기화
        if use_intelligent_routing:
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature
            )
            self.structured_llm = self.llm.with_structured_output(AgentSelection)
        
        # 에이전트 참조 저장
        self.customs_law_agent = None
        self.regulations_agent = None
        self.complaints_agent = None
        
        # LangGraph 구성요소
        self.graph = None
        
        # 전통적 라우팅을 위한 키워드 매핑
        self._initialize_routing_keywords()
        
        logger.info(f"MultiAgentOrchestrator initialized (intelligent_routing: {use_intelligent_routing})")
    
    def set_agents(self, 
                   customs_law_agent=None,
                   regulations_agent=None, 
                   complaints_agent=None):
        """에이전트 참조 설정"""
        self.customs_law_agent = customs_law_agent
        self.regulations_agent = regulations_agent
        self.complaints_agent = complaints_agent
        
        # LangGraph 사용시 그래프 구성
        if self.use_intelligent_routing:
            self._build_graph()
        
        logger.info("Agents set successfully")
    
    def process_query(self, user_query: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        사용자 질의 처리
        
        Args:
            user_query: 사용자 입력
            config: 실행 설정
            
        Returns:
            처리 결과
        """
        try:
            if self.use_intelligent_routing and self.graph:
                return self._process_with_langgraph(user_query, config)
            else:
                return self._process_with_traditional_routing(user_query)
                
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "response": f"질의 처리 중 오류가 발생했습니다: {str(e)}",
                "error": str(e),
                "agent_used": "error_handler"
            }
    
    def _process_with_langgraph(self, user_query: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """LangGraph 기반 지능형 처리"""
        try:
            # 초기 상태 구성
            initial_state = {
                "messages": [HumanMessage(content=user_query)],
                "active_agents": [],
                "query_complexity": 0.0,
                "agent_responses": {},
                "routing_history": [],
                "current_step": 0
            }
            
            logger.info(f"🚀 LangGraph orchestration started: {user_query[:50]}...")
            
            # 그래프 실행
            result = self.graph.invoke(initial_state, config=config)
            
            # 결과 포맷팅
            final_response = ""
            agent_used = "unknown"
            docs = []
            
            if result.get("messages"):
                final_response = result["messages"][-1].content
            
            if result.get("agent_responses"):
                # 마지막으로 실행된 에이전트 찾기
                for agent_name, agent_data in result["agent_responses"].items():
                    agent_used = agent_name
                    if agent_data.get("docs"):
                        docs = agent_data["docs"]
                    break
            
            logger.info(f"✅ LangGraph orchestration completed")
            
            return {
                "response": final_response,
                "agent_used": agent_used,
                "docs": docs,
                "routing_info": result.get("routing_history", []),
                "complexity": result.get("query_complexity", 0.0)
            }
            
        except Exception as e:
            logger.error(f"LangGraph processing failed: {e}")
            # Fallback to traditional routing
            return self._process_with_traditional_routing(user_query)
    
    def _process_with_traditional_routing(self, user_query: str) -> Dict[str, Any]:
        """전통적 키워드 기반 라우팅 처리"""
        try:
            # 라우팅 결정
            query_type, confidence, routing_info = self._route_query_traditional(user_query)
            
            # 에이전트 선택 및 실행
            if query_type == QueryType.LAW:
                agent = self.customs_law_agent
                agent_name = "customs_law_agent"
                response, docs = agent.query_law(user_query) if agent else ("에이전트가 설정되지 않았습니다.", [])
            elif query_type == QueryType.REGULATION:
                agent = self.regulations_agent
                agent_name = "regulations_agent"
                response, docs = agent.query_regulation(user_query) if agent else ("에이전트가 설정되지 않았습니다.", [])
            elif query_type == QueryType.CONSULTATION:
                agent = self.complaints_agent
                agent_name = "complaints_agent"
                response, docs = agent.query_consultation(user_query) if agent else ("에이전트가 설정되지 않았습니다.", [])
            else:  # MIXED
                # 기본값으로 상담 에이전트 사용
                agent = self.complaints_agent
                agent_name = "complaints_agent"
                response, docs = agent.query_consultation(user_query) if agent else ("에이전트가 설정되지 않았습니다.", [])
            
            return {
                "response": response,
                "agent_used": agent_name,
                "docs": docs,
                "routing_info": routing_info,
                "confidence": confidence,
                "query_type": query_type.value
            }
            
        except Exception as e:
            logger.error(f"Traditional routing failed: {e}")
            return {
                "response": f"전통적 라우팅 처리 중 오류가 발생했습니다: {str(e)}",
                "error": str(e),
                "agent_used": "error_handler"
            }
    
    def intelligent_supervisor(self, state: EnhancedState) -> Command:
        """
        LLM 기반 지능형 supervisor
        사용자 질의를 분석하여 최적의 에이전트 선택
        """
        try:
            # 현재 메시지 추출
            if not state["messages"]:
                return Command(goto="__end__")
            
            last_message = state["messages"][-1]
            
            # 무한루프 방지: AIMessage인 경우 대화 종료
            if isinstance(last_message, AIMessage):
                logger.info("🏁 Agent response received, ending conversation")
                return Command(goto="__end__")
            
            # HumanMessage인 경우에만 라우팅 수행
            if not isinstance(last_message, HumanMessage):
                logger.warning(f"Unexpected message type: {type(last_message)}")
                return Command(goto="__end__")
            
            # 라우팅 프롬프트 구성
            routing_prompt = self._create_routing_prompt(last_message.content, state)
            
            # 구조화된 출력으로 에이전트 선택
            response = self.structured_llm.invoke([
                SystemMessage(content=routing_prompt),
                HumanMessage(content=f"사용자 질의: {last_message.content}")
            ])
            
            # 라우팅 히스토리 업데이트
            routing_info = {
                "query": last_message.content,
                "selected_agent": response.next_agent,
                "reasoning": response.reasoning,
                "complexity": response.complexity,
                "requires_multiple": response.requires_multiple_agents,
                "step": state.get("current_step", 0) + 1
            }
            
            # 상태 업데이트
            updated_state = {
                "query_complexity": response.complexity,
                "routing_history": state.get("routing_history", []) + [routing_info],
                "current_step": state.get("current_step", 0) + 1
            }
            
            logger.info(f"🧠 Supervisor decision: {response.next_agent} (complexity: {response.complexity:.2f})")
            logger.info(f"📝 Reasoning: {response.reasoning}")
            
            # 복합 질의 처리
            if response.requires_multiple_agents and response.complexity > 0.7:
                return self._handle_complex_query(state, response)
            
            # 단일 에이전트 라우팅
            return Command(
                goto=response.next_agent,
                update=updated_state
            )
            
        except Exception as e:
            logger.error(f"Supervisor routing failed: {e}")
            # 기본값으로 상담 에이전트 사용
            return Command(
                goto="complaints_agent",
                update={"routing_history": state.get("routing_history", []) + [{"error": str(e)}]}
            )
    
    def _create_routing_prompt(self, user_query: str, state: EnhancedState) -> str:
        """라우팅을 위한 프롬프트 생성"""
        
        routing_history = state.get("routing_history", [])
        context = ""
        
        if routing_history:
            context = f"\n이전 라우팅 히스토리:\n"
            for i, hist in enumerate(routing_history[-3:], 1):  # 최근 3개만
                context += f"{i}. {hist.get('selected_agent', 'unknown')} - {hist.get('reasoning', '')}\n"
        
        return f"""
당신은 한국 무역 정보 시스템의 지능형 라우터입니다.
사용자 질의를 분석하여 가장 적절한 전문 에이전트를 선택해주세요.

{context}

## 사용 가능한 에이전트:

1. **customs_law_agent** (관세법 조문 전문가)
   - 관세법, 관세법시행령, 관세법시행규칙 조문 해석
   - 법률 조항별 정확한 정보 제공
   - 키워드: 관세법, 법령, 조문, 법률, 규정, 조

2. **regulations_agent** (무역 규제 전문가) 
   - 동식물 수입 허용/금지 국가 정보
   - 수입/수출 규제 및 제한 사항
   - HS코드별 규제 정보
   - 키워드: 딸기, 과일, 동식물, 수입 허용, 금지, 규제, HS코드

3. **complaints_agent** (실무 상담 전문가)
   - 실제 민원 상담 사례 기반 안내
   - 수입/수출 절차 및 실무 가이드
   - 비용, 기간, 방법 등 실용적 정보
   - 키워드: 절차, 방법, 비용, 신고, 서류, 어떻게

4. **__end__** (완료)
   - 대화 종료나 추가 도움이 불필요한 경우

## 분석 기준:

1. **질의 복잡도 평가:**
   - 단순 (0.0-0.3): 단일 정보 요청
   - 보통 (0.4-0.6): 여러 정보 연관
   - 복합 (0.7-1.0): 다중 에이전트 협업 필요

2. **복합 질의 예시:**
   - "딸기 수입 절차와 비용은?" → regulations + complaints
   - "관세법 조문과 실제 사례는?" → customs_law + complaints

3. **특별 처리:**
   - 동식물 관련 질의 → regulations_agent 우선
   - 법령 조문 질의 → customs_law_agent 우선
   - 실무 절차 질의 → complaints_agent 우선

응답 형식에 맞춰 next_agent, reasoning, complexity, requires_multiple_agents를 제공해주세요.
"""
    
    def _handle_complex_query(self, state: EnhancedState, response: AgentSelection) -> Command:
        """복합 질의 처리 (추후 구현)"""
        logger.info(f"🔄 Complex query detected (complexity: {response.complexity:.2f})")
        
        # 현재는 첫 번째 적절한 에이전트로 라우팅
        # 추후 Send API를 사용한 병렬 처리 구현 예정
        return Command(
            goto=response.next_agent,
            update={
                "query_complexity": response.complexity,
                "routing_history": state.get("routing_history", []) + [{
                    "type": "complex_query",
                    "selected_agent": response.next_agent,
                    "reasoning": response.reasoning
                }]
            }
        )
    
    def customs_law_agent_node(self, state: EnhancedState) -> Command:
        """관세법 조문 전문 에이전트 노드"""
        try:
            if not self.customs_law_agent:
                raise ValueError("CustomsLawAgent not configured")
            
            last_message = state["messages"][-1]
            logger.info(f"🏛️ CustomsLawAgent processing: {last_message.content[:50]}...")
            
            # 관세법 에이전트 호출
            response, docs = self.customs_law_agent.query_law(last_message.content)
            
            # 응답 메시지 생성
            ai_response = AIMessage(content=response)
            
            # 메타데이터 추가
            metadata = {
                "agent": "customs_law_agent",
                "docs_count": len(docs) if docs else 0,
                "doc_references": [doc.get("index", "") for doc in docs[:3]] if docs else []
            }
            
            return Command(
                goto="__end__",
                update={
                    "messages": [ai_response],
                    "agent_responses": {
                        **state.get("agent_responses", {}),
                        "customs_law_agent": {
                            "response": response,
                            "docs": docs,
                            "metadata": metadata
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"CustomsLawAgent node failed: {e}")
            error_response = AIMessage(content=f"관세법 정보 검색 중 오류가 발생했습니다: {str(e)}")
            return Command(
                goto="__end__",
                update={"messages": [error_response]}
            )
    
    def regulations_agent_node(self, state: EnhancedState) -> Command:
        """무역 규제 전문 에이전트 노드"""
        try:
            if not self.regulations_agent:
                raise ValueError("RegulationsAgent not configured")
            
            last_message = state["messages"][-1]
            logger.info(f"⚖️ RegulationsAgent processing: {last_message.content[:50]}...")
            
            # 규제 에이전트 호출
            response, docs = self.regulations_agent.query_regulation(last_message.content)
            
            # 응답 메시지 생성
            ai_response = AIMessage(content=response)
            
            # 메타데이터 추가
            metadata = {
                "agent": "regulations_agent",
                "docs_count": len(docs) if docs else 0,
                "boosted_docs": len([d for d in docs if d.get("boosted", False)]) if docs else 0
            }
            
            return Command(
                goto="__end__",
                update={
                    "messages": [ai_response],
                    "agent_responses": {
                        **state.get("agent_responses", {}),
                        "regulations_agent": {
                            "response": response,
                            "docs": docs,
                            "metadata": metadata
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"RegulationsAgent node failed: {e}")
            error_response = AIMessage(content=f"무역 규제 정보 검색 중 오류가 발생했습니다: {str(e)}")
            return Command(
                goto="__end__",
                update={"messages": [error_response]}
            )
    
    def complaints_agent_node(self, state: EnhancedState) -> Command:
        """상담 사례 전문 에이전트 노드"""
        try:
            if not self.complaints_agent:
                raise ValueError("ComplaintsAgent not configured")
            
            last_message = state["messages"][-1]
            logger.info(f"💼 ComplaintsAgent processing: {last_message.content[:50]}...")
            
            # 상담 에이전트 호출
            response, docs = self.complaints_agent.query_consultation(last_message.content)
            
            # 응답 메시지 생성
            ai_response = AIMessage(content=response)
            
            # 메타데이터 추가
            metadata = {
                "agent": "complaints_agent",
                "docs_count": len(docs) if docs else 0,
                "case_types": list(set([doc.get("metadata", {}).get("category", "") for doc in docs])) if docs else []
            }
            
            return Command(
                goto="__end__",
                update={
                    "messages": [ai_response],
                    "agent_responses": {
                        **state.get("agent_responses", {}),
                        "complaints_agent": {
                            "response": response,
                            "docs": docs,
                            "metadata": metadata
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"ComplaintsAgent node failed: {e}")
            error_response = AIMessage(content=f"상담 사례 검색 중 오류가 발생했습니다: {str(e)}")
            return Command(
                goto="__end__",
                update={"messages": [error_response]}
            )
    
    def _build_graph(self):
        """StateGraph 구성"""
        try:
            # StateGraph 생성
            builder = StateGraph(EnhancedState)
            
            # 노드 추가
            builder.add_node("supervisor", self.intelligent_supervisor)
            builder.add_node("customs_law_agent", self.customs_law_agent_node)
            builder.add_node("regulations_agent", self.regulations_agent_node)
            builder.add_node("complaints_agent", self.complaints_agent_node)
            
            # 엣지 설정
            builder.add_edge(START, "supervisor")
            
            # 그래프 컴파일
            self.graph = builder.compile()
            
            logger.info("StateGraph built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build StateGraph: {e}")
            raise
    
    def _route_query_traditional(self, user_query: str) -> Tuple[QueryType, float, Dict[str, Any]]:
        """전통적 키워드 기반 라우팅"""
        try:
            # 질의 전처리
            normalized_query = self._normalize_query(user_query)
            
            # 동식물 수입 질의 감지 (최우선)
            animal_plant_score = self._detect_animal_plant_import_query(normalized_query)
            from ..config.config import get_quality_thresholds
            thresholds = get_quality_thresholds()
            
            if animal_plant_score > thresholds["animal_plant_score_threshold"]:
                return QueryType.REGULATION, animal_plant_score, {
                    "reason": "animal_plant_import_query",
                    "detected_products": self._extract_animal_plant_products(normalized_query),
                    "routing_priority": "high"
                }
            
            # 관세법 조문 질의 점수 계산
            law_score = self._calculate_law_score(normalized_query)
            
            # 규제 질의 점수 계산
            regulation_score = self._calculate_regulation_score(normalized_query)
            
            # 상담/절차 질의 점수 계산
            consultation_score = self._calculate_consultation_score(normalized_query)
            
            # 라우팅 결정
            max_score = max(law_score, regulation_score, consultation_score)
            
            if law_score == max_score and max_score > 0.4:
                return QueryType.LAW, law_score, {
                    "reason": "law_query_detected",
                    "scores": {"law": law_score, "regulation": regulation_score, "consultation": consultation_score}
                }
            elif regulation_score == max_score and max_score > 0.4:
                return QueryType.REGULATION, regulation_score, {
                    "reason": "regulation_query_detected", 
                    "scores": {"law": law_score, "regulation": regulation_score, "consultation": consultation_score}
                }
            elif consultation_score == max_score and max_score > 0.4:
                return QueryType.CONSULTATION, consultation_score, {
                    "reason": "consultation_query_detected",
                    "scores": {"law": law_score, "regulation": regulation_score, "consultation": consultation_score}
                }
            else:
                # 기본값으로 상담 에이전트 사용
                return QueryType.CONSULTATION, 0.5, {
                    "reason": "default_fallback",
                    "scores": {"law": law_score, "regulation": regulation_score, "consultation": consultation_score}
                }
            
        except Exception as e:
            logger.error(f"Traditional routing failed: {e}")
            return QueryType.CONSULTATION, 0.3, {"reason": "error_fallback", "error": str(e)}
    
    def _normalize_query(self, query: str) -> str:
        """질의 정규화"""
        normalized = query.lower().strip()
        normalized = re.sub(r'[^\w\s가-힣]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
    def _detect_animal_plant_import_query(self, query: str) -> float:
        """동식물 수입 허용국가 질의 감지"""
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
    
    def _calculate_law_score(self, query: str) -> float:
        """관세법 조문 질의 점수 계산"""
        score = 0.0
        
        # 관세법 관련 키워드 매칭
        for keyword, weight in self.law_keywords.items():
            if keyword in query:
                score += weight
        
        # 법령 관련 패턴 매칭
        law_patterns = [
            r'관세법.*조', r'법령.*내용', r'조문.*무엇',
            r'법.*규정', r'시행령.*조', r'시행규칙.*조',
            r'제.*조', r'법률.*조항'
        ]
        
        for pattern in law_patterns:
            if re.search(pattern, query):
                score += 0.4
        
        return min(score, 1.0)
    
    def _calculate_regulation_score(self, query: str) -> float:
        """규제 질의 점수 계산"""
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
    
    def _initialize_routing_keywords(self):
        """라우팅을 위한 키워드 초기화"""
        # 관세법 조문 관련 키워드
        self.law_keywords = {
            "관세법": 0.9, "법령": 0.8, "조문": 0.8, "법률": 0.7,
            "시행령": 0.8, "시행규칙": 0.8, "규정": 0.6,
            "조": 0.7, "항": 0.6, "호": 0.5, "법조문": 0.9
        }
        
        # 규제 관련 키워드
        self.regulation_keywords = {
            "규제": 0.8, "금지": 0.7, "제한": 0.7, "허용": 0.6,
            "동식물": 0.8, "검역": 0.7, "수입규제": 0.9, "수출규제": 0.9,
            "수입금지": 0.8, "수출금지": 0.8, "수입제한": 0.8, "수출제한": 0.8,
            "수입허용": 0.7, "수출허용": 0.7, "관세율": 0.6, "hs코드": 0.7,
            "품목분류": 0.6, "검역요구": 0.8, "검역기준": 0.7, "수입허가": 0.7,
            "식물검역": 0.8, "동물검역": 0.8, "위반": 0.6, "처벌": 0.6
        }
        
        # 상담/절차 관련 키워드
        self.consultation_keywords = {
            "절차": 0.8, "방법": 0.7, "어떻게": 0.8, "해야": 0.6,
            "신청": 0.7, "신고": 0.8, "접수": 0.6, "서류": 0.7,
            "문서": 0.6, "양식": 0.6, "작성": 0.6, "증명서": 0.7,
            "허가서": 0.7, "신고서": 0.8, "통관": 0.9, "세관": 0.8,
            "통관신고": 0.9, "수입신고": 0.8, "수출신고": 0.8,
            "비용": 0.7, "수수료": 0.6, "기간": 0.7, "시간": 0.6,
            "소요": 0.5, "처리": 0.6, "완료": 0.5, "문의": 0.6,
            "상담": 0.8, "도움": 0.6, "안내": 0.7, "가이드": 0.6,
            "설명": 0.6, "알려": 0.7, "fta": 0.7, "원산지": 0.7,
            "특혜관세": 0.7, "원산지증명": 0.8, "면세": 0.6, "감면": 0.6,
            "환급": 0.6, "정정": 0.6, "수정": 0.6, "변경": 0.6, "취소": 0.6
        }
        
        # 동식물 제품 목록
        self.animal_plant_products = [
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
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계 반환"""
        return {
            "orchestrator_type": "MultiAgent",
            "model": self.model_name,
            "temperature": self.temperature,
            "intelligent_routing": self.use_intelligent_routing,
            "available_agents": ["customs_law_agent", "regulations_agent", "complaints_agent"]
        }
    
    def get_routing_explanation(self, query: str) -> str:
        """라우팅 결정에 대한 설명 생성"""
        if self.use_intelligent_routing:
            return f"LangGraph 지능형 라우팅을 사용하여 질의를 분석합니다: {query[:50]}..."
        else:
            query_type, confidence, routing_info = self._route_query_traditional(query)
            
            explanation = f"질의 분석 결과:\n"
            explanation += f"- 라우팅: {query_type.value} 에이전트\n"
            explanation += f"- 신뢰도: {confidence:.2f}\n"
            explanation += f"- 이유: {routing_info.get('reason', 'unknown')}\n"
            
            if 'scores' in routing_info:
                scores = routing_info['scores']
                explanation += f"- 점수: 법령({scores.get('law', 0):.2f}), 규제({scores.get('regulation', 0):.2f}), 상담({scores.get('consultation', 0):.2f})\n"
            
            if 'detected_products' in routing_info:
                products = routing_info['detected_products']
                if products:
                    explanation += f"- 감지된 제품: {', '.join(products)}\n"
            
            return explanation


class OrchestratorFactory:
    """오케스트레이터 팩토리 클래스"""
    
    def __init__(self):
        """팩토리 초기화"""
        self.orchestrator = None
        
        # 공통 구성요소
        self.embedder = None
        self.law_vector_store = None
        self.trade_vector_store = None
        self.query_normalizer = None
        
        logger.info("OrchestratorFactory initialized")
    
    def create_orchestrated_system(self, 
                                  model_name: str = "gpt-4.1-mini",
                                  temperature: float = 0.1,
                                  use_intelligent_routing: bool = True,
                                  force_rebuild: bool = False) -> MultiAgentOrchestrator:
        """
        완전한 멀티 에이전트 오케스트레이션 시스템 생성
        
        Args:
            model_name: 사용할 언어 모델
            temperature: 모델 온도 설정
            use_intelligent_routing: LangGraph 지능형 라우팅 사용 여부
            force_rebuild: 강제 재구성 여부
            
        Returns:
            설정된 MultiAgentOrchestrator
        """
        try:
            logger.info(f"🏗️ Building multi-agent orchestrated system...")
            
            # API 키 확인
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # 기존 오케스트레이터가 있고 재구성이 필요하지 않으면 반환
            if self.orchestrator and not force_rebuild:
                logger.info("Using existing orchestrator")
                return self.orchestrator
            
            # 1. 공통 구성요소 초기화
            self._initialize_common_components()
            
            # 2. 개별 에이전트 생성
            customs_law_agent = self._create_customs_law_agent()
            regulations_agent = self._create_regulations_agent(model_name, temperature)
            complaints_agent = self._create_complaints_agent(model_name, temperature)
            
            # 3. 오케스트레이터 생성
            self.orchestrator = MultiAgentOrchestrator(
                model_name=model_name,
                temperature=temperature,
                use_intelligent_routing=use_intelligent_routing
            )
            
            # 4. 에이전트들을 오케스트레이터에 연결
            self.orchestrator.set_agents(
                customs_law_agent=customs_law_agent,
                regulations_agent=regulations_agent,
                complaints_agent=complaints_agent
            )
            
            logger.info("✅ Multi-agent orchestrated system created successfully")
            return self.orchestrator
            
        except Exception as e:
            logger.error(f"Failed to create orchestrated system: {e}")
            raise
    
    def _initialize_common_components(self):
        """공통 구성요소 초기화"""
        try:
            logger.info("🔧 Initializing common components...")
            
            # 임베딩 모델
            if not self.embedder:
                from ..utils.embeddings import LangChainEmbedder
                self.embedder = LangChainEmbedder()
                logger.info("  - LangChain Embedder initialized")
            
            # Query normalizer functionality simplified  
            self.query_normalizer = None
            logger.info("  - Basic query processing enabled")
            
            # 벡터 저장소들
            if not self.law_vector_store:
                from ..utils.db_connect import LangChainVectorStore
                self.law_vector_store = LangChainVectorStore(
                    collection_name="law_collection",
                    embedding_function=self.embedder.embeddings
                )
                logger.info("  - LangChain Law Vector Store initialized")
            
            if not self.trade_vector_store:
                from ..utils.db_connect import LangChainVectorStore
                from ..config.config import get_quality_thresholds
                self.trade_vector_store = LangChainVectorStore(
                    collection_name="trade_info_collection",
                    embedding_function=self.embedder.embeddings
                )
                logger.info("  - LangChain Trade Vector Store initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize common components: {e}")
            raise
    
    def _create_customs_law_agent(self):
        """관세법 조문 전문 에이전트 생성"""
        try:
            logger.info("🏛️ Creating CustomsLawAgent...")
            
            from ..agents.customs_law_agent import CustomsLawAgent
            
            # 관세법 에이전트 생성
            agent = CustomsLawAgent(
                embedder=self.embedder,
                vector_store=self.law_vector_store,
                query_normalizer=self.query_normalizer,
                max_context_docs=5,
                similarity_threshold=0.0
            )
            
            logger.info("  ✅ CustomsLawAgent created")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create CustomsLawAgent: {e}")
            raise
    
    def _create_regulations_agent(self, model_name: str, temperature: float):
        """무역 규제 전문 에이전트 생성"""
        try:
            logger.info("⚖️ Creating RegulationsAgent...")
            
            from ..agents.regulations_agent import RegulationsAgent
            from ..config.config import get_quality_thresholds
            thresholds = get_quality_thresholds()
            
            # 규제 에이전트 생성
            agent = RegulationsAgent(
                retriever=None,  # 내부에서 자동 생성
                model_name=model_name,
                temperature=thresholds["regulation_temperature"],
                max_context_docs=8,
                similarity_threshold=thresholds["similarity_threshold"]
            )
            
            logger.info("  ✅ RegulationsAgent created")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create RegulationsAgent: {e}")
            raise
    
    def _create_complaints_agent(self, model_name: str, temperature: float):
        """상담 사례 전문 에이전트 생성"""
        try:
            logger.info("💼 Creating ComplaintsAgent...")
            
            from ..agents.complaints_agent import ComplaintsAgent
            from ..config.config import get_quality_thresholds
            thresholds = get_quality_thresholds()
            
            # 상담 에이전트 생성
            agent = ComplaintsAgent(
                retriever=None,  # 내부에서 자동 생성
                model_name=model_name,
                temperature=thresholds["consultation_temperature"],
                max_context_docs=8,
                similarity_threshold=thresholds["similarity_threshold"]
            )
            
            logger.info("  ✅ ComplaintsAgent created")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create ComplaintsAgent: {e}")
            raise
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """에이전트 통계 정보 반환"""
        stats = {
            "factory_type": "OrchestratorFactory",
            "orchestrator_available": self.orchestrator is not None
        }
        
        if self.orchestrator:
            try:
                stats["orchestrator_stats"] = self.orchestrator.get_routing_stats()
            except:
                pass
        
        return stats
    
    def reset(self):
        """팩토리 상태 초기화"""
        logger.info("🔄 Resetting OrchestratorFactory...")
        
        self.orchestrator = None
        
        # 공통 구성요소는 유지 (재사용 가능)
        
        logger.info("✅ Factory reset completed")


# 글로벌 팩토리 인스턴스 (싱글톤 패턴)
_factory_instance = None

def get_orchestrator_factory() -> OrchestratorFactory:
    """글로벌 오케스트레이터 팩토리 인스턴스 반환"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = OrchestratorFactory()
    return _factory_instance


def create_orchestrated_system(model_name: str = "gpt-4.1-mini", 
                              temperature: float = 0.1,
                              use_intelligent_routing: bool = True,
                              force_rebuild: bool = False) -> MultiAgentOrchestrator:
    """
    편의 함수: 완전한 멀티 에이전트 오케스트레이션 시스템 생성
    
    Args:
        model_name: 사용할 언어 모델
        temperature: 모델 온도 설정
        use_intelligent_routing: LangGraph 지능형 라우팅 사용 여부
        force_rebuild: 강제 재구성 여부
        
    Returns:
        설정된 MultiAgentOrchestrator
    """
    factory = get_orchestrator_factory()
    return factory.create_orchestrated_system(
        model_name=model_name,
        temperature=temperature,
        use_intelligent_routing=use_intelligent_routing,
        force_rebuild=force_rebuild
    )