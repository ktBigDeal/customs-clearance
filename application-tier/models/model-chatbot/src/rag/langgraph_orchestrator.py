"""
LangGraph Intelligent Orchestrator Module

LangGraph를 활용한 지능형 멀티 에이전트 오케스트레이션 시스템
기존 QueryRouter를 대체하여 LLM 기반 라우팅과 복합 워크플로우 지원
"""

import logging
from typing import Literal, List, Dict, Any, Optional, TypedDict, Annotated
import operator
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command, Send
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentSelection(BaseModel):
    """
    AI가 어떤 에이전트를 선택할지 결정할 때 사용하는 데이터 모델
    
    Pydantic BaseModel을 상속받아 데이터 검증과 타입 안전성을 보장합니다.
    
    신입 개발자를 위한 설명:
    - 이 클래스는 AI Supervisor가 사용자 질문을 분석한 결과를 담는 "상자"입니다
    - Field()를 사용해서 각 필드에 대한 설명과 제약조건을 정의
    - Literal 타입으로 선택 가능한 에이전트를 제한
    - ge, le로 숫자 범위 검증 (greater equal, less equal)
    
    예시: 사용자가 "딸기 수입이 가능한가요?"라고 물으면
    → next_agent: "regulation_agent" (무역 규제 전문가)
    → reasoning: "동식물 수입 관련 질의로 규제 에이전트가 적합"
    → complexity: 0.3 (단순한 정보 조회)
    → requires_multiple_agents: False (한 명으로 충분)
    """
    next_agent: Literal["conversation_agent", "regulation_agent", "consultation_agent", "__end__"] = Field(
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
    """
    LangGraph에서 사용하는 대화 상태를 관리하는 데이터 구조
    
    TypedDict란?
    - 파이썬 딕셔너리에 타입 정보를 추가한 것
    - 런타임에는 일반 dict처럼 동작하지만, IDE와 타입 체커가 오류를 잡아줌
    - 예: state["messages"]는 List[BaseMessage] 타입임을 보장
    
    신입 개발자를 위한 각 필드 설명:
    - messages: 사용자와 AI의 대화 내역 (채팅 로그)
    - active_agents: 현재 활성화된 AI 에이전트 목록
    - query_complexity: 질문의 복잡도 (0.0=단순, 1.0=매우 복잡)
    - agent_responses: 각 에이전트의 응답 결과 저장소
    - routing_history: 어떤 에이전트가 언제 선택되었는지 기록
    - current_step: 현재 처리 단계 번호
    
    왜 이런 복잡한 상태가 필요한가?
    - 여러 AI가 협업할 때 정보를 공유하기 위해
    - 대화 맥락을 유지하여 일관된 응답 제공
    - 디버깅과 모니터링을 위한 상세한 로그 기록
    """
    messages: Annotated[List[BaseMessage], operator.add]
    active_agents: List[str]  # 현재 활성 에이전트들
    query_complexity: float   # 질의 복잡도
    agent_responses: Dict[str, Any]  # 에이전트별 응답 저장
    routing_history: List[Dict[str, Any]]  # 라우팅 히스토리
    current_step: int  # 현재 단계


class LangGraphOrchestrator:
    """
    LangGraph 기반 지능형 에이전트 오케스트레이터
    
    이 클래스가 하는 일을 쉽게 설명하면:
    "여러 명의 AI 전문가 중에서 질문에 가장 적합한 전문가를 자동으로 선택해주는 똑똑한 비서"
    
    오케스트레이터(Orchestrator)란?
    - 오케스트라 지휘자처럼 여러 AI 에이전트들을 조율하는 역할
    - 사용자 질문을 분석해서 어떤 전문가에게 보낼지 결정
    - 각 전문가의 답변을 취합해서 최종 결과 제공
    
    LangGraph란?
    - LangChain에서 만든 워크플로우 프레임워크
    - AI 에이전트들 사이의 복잡한 상호작용을 그래프로 관리
    - StateGraph: 상태를 유지하면서 노드 간 이동하는 그래프
    
    신입 개발자를 위한 핵심 개념:
    1. Supervisor: 질문을 분석해서 적절한 에이전트 선택
    2. Agent Nodes: 각각의 전문 AI (관세법, 규제, 상담)
    3. State Management: 대화 상태와 결과를 계속 추적
    4.Command Pattern: 다음에 어떤 노드로 갈지 명령으로 제어
    
    작동 흐름:
    사용자 질문 → Supervisor 분석 → 적절한 Agent 선택 → Agent 응답 → 결과 반환
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4.1-mini",
                 temperature: float = 0.1):
        """
        초기화
        
        Args:
            model_name: 사용할 언어 모델
            temperature: 모델 온도 설정
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # 구조화된 출력을 위한 LLM 초기화
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        
        # 구조화된 출력 LLM
        self.structured_llm = self.llm.with_structured_output(AgentSelection)
        
        # 에이전트 참조 저장 (나중에 설정)
        self.conversation_agent = None
        self.regulation_agent = None
        self.consultation_agent = None
        
        # StateGraph 초기화
        self.graph = None
        
        logger.info(f"LangGraphOrchestrator initialized with model: {model_name}")
    
    def set_agents(self, 
                   conversation_agent=None,
                   regulation_agent=None, 
                   consultation_agent=None):
        """에이전트 참조 설정"""
        self.conversation_agent = conversation_agent
        self.regulation_agent = regulation_agent
        self.consultation_agent = consultation_agent
        
        # StateGraph 구성
        self._build_graph()
        
        logger.info("Agents set and StateGraph built successfully")
    
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
            
            # 🔧 무한루프 방지: AIMessage인 경우 대화 종료
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
                goto="consultation_agent",
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

1. **conversation_agent** (관세법 RAG 전문가)
   - 관세법, 관세법시행령, 관세법시행규칙 조문 해석
   - 법률 조항별 정확한 정보 제공
   - 키워드: 관세법, 법령, 조문, 법률, 규정

2. **regulation_agent** (무역 규제 전문가) 
   - 동식물 수입 허용/금지 국가 정보
   - 수입/수출 규제 및 제한 사항  
   - 반덤핑, 세이프가드, 통상규제 정보
   - 외국이 한국에 거는 규제 정보
   - HS코드별 규제 정보
   - 키워드: 딸기, 과일, 동식물, 수입 허용, 금지, 규제, HS코드, 반덤핑, 세이프가드, 외국 규제

3. **consultation_agent** (실무 상담 전문가)
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
   - "딸기 수입 절차와 비용은?" → regulation + consultation
   - "관세법 조문과 실제 사례는?" → conversation + consultation

3. **특별 처리:**
   - 동식물 관련 질의 → regulation_agent 우선
   - 법령 조문 질의 → conversation_agent 우선
   - 실무 절차 질의 → consultation_agent 우선

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
    
    def conversation_agent_node(self, state: EnhancedState) -> Command:
        """관세법 RAG 에이전트 노드"""
        try:
            if not self.conversation_agent:
                raise ValueError("ConversationAgent not configured")
            
            last_message = state["messages"][-1]
            logger.info(f"🏛️ ConversationAgent processing: {last_message.content[:50]}...")
            
            # 기존 ConversationAgent 호출
            response, docs = self.conversation_agent.chat(last_message.content)
            
            # 응답 메시지 생성
            ai_response = AIMessage(content=response)
            
            # 메타데이터 추가
            metadata = {
                "agent": "conversation_agent",
                "docs_count": len(docs) if docs else 0,
                "doc_references": [doc.get("index", "") for doc in docs[:3]] if docs else []
            }
            
            return Command(
                goto="__end__",
                update={
                    "messages": [ai_response],
                    "agent_responses": {
                        **state.get("agent_responses", {}),
                        "conversation_agent": {
                            "response": response,
                            "docs": docs,
                            "metadata": metadata
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"ConversationAgent node failed: {e}")
            error_response = AIMessage(content=f"관세법 정보 검색 중 오류가 발생했습니다: {str(e)}")
            return Command(
                goto="__end__",
                update={"messages": [error_response]}
            )
    
    def regulation_agent_node(self, state: EnhancedState) -> Command:
        """무역 규제 전문 에이전트 노드"""
        try:
            if not self.regulation_agent:
                raise ValueError("TradeRegulationAgent not configured")
            
            last_message = state["messages"][-1]
            logger.info(f"⚖️ RegulationAgent processing: {last_message.content[:50]}...")
            
            # 기존 TradeRegulationAgent 호출
            response, docs = self.regulation_agent.query_regulation(last_message.content)
            
            # 응답 메시지 생성
            ai_response = AIMessage(content=response)
            
            # 메타데이터 추가
            metadata = {
                "agent": "regulation_agent",
                "docs_count": len(docs) if docs else 0,
                "boosted_docs": len([d for d in docs if d.get("boosted", False)]) if docs else 0
            }
            
            return Command(
                goto="__end__",
                update={
                    "messages": [ai_response],
                    "agent_responses": {
                        **state.get("agent_responses", {}),
                        "regulation_agent": {
                            "response": response,
                            "docs": docs,
                            "metadata": metadata
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"RegulationAgent node failed: {e}")
            error_response = AIMessage(content=f"무역 규제 정보 검색 중 오류가 발생했습니다: {str(e)}")
            return Command(
                goto="__end__",
                update={"messages": [error_response]}
            )
    
    def consultation_agent_node(self, state: EnhancedState) -> Command:
        """상담 사례 전문 에이전트 노드"""
        try:
            if not self.consultation_agent:
                raise ValueError("ConsultationCaseAgent not configured")
            
            last_message = state["messages"][-1]
            logger.info(f"💼 ConsultationAgent processing: {last_message.content[:50]}...")
            
            # 기존 ConsultationCaseAgent 호출
            response, docs = self.consultation_agent.query_consultation(last_message.content)
            
            # 응답 메시지 생성
            ai_response = AIMessage(content=response)
            
            # 메타데이터 추가
            metadata = {
                "agent": "consultation_agent",
                "docs_count": len(docs) if docs else 0,
                "case_types": list(set([doc.get("metadata", {}).get("category", "") for doc in docs])) if docs else []
            }
            
            return Command(
                goto="__end__",
                update={
                    "messages": [ai_response],
                    "agent_responses": {
                        **state.get("agent_responses", {}),
                        "consultation_agent": {
                            "response": response,
                            "docs": docs,
                            "metadata": metadata
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"ConsultationAgent node failed: {e}")
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
            builder.add_node("conversation_agent", self.conversation_agent_node)
            builder.add_node("regulation_agent", self.regulation_agent_node)
            builder.add_node("consultation_agent", self.consultation_agent_node)
            
            # 엣지 설정
            builder.add_edge(START, "supervisor")
            
            # supervisor에서 각 에이전트로의 조건부 엣지는 Command.goto로 처리됨
            # 각 에이전트에서 supervisor로 돌아가는 엣지는 Command.goto로 처리됨
            
            # 그래프 컴파일
            self.graph = builder.compile()
            
            logger.info("StateGraph built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build StateGraph: {e}")
            raise
    
    def invoke(self, user_input: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        오케스트레이터 실행
        
        Args:
            user_input: 사용자 입력
            config: 실행 설정
            
        Returns:
            실행 결과
        """
        try:
            if not self.graph:
                raise ValueError("StateGraph not built. Call set_agents() first.")
            
            # 초기 상태 구성
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "active_agents": [],
                "query_complexity": 0.0,
                "agent_responses": {},
                "routing_history": [],
                "current_step": 0
            }
            
            logger.info(f"🚀 LangGraph orchestration started: {user_input[:50]}...")
            
            # 그래프 실행
            result = self.graph.invoke(initial_state, config=config)
            
            logger.info(f"✅ LangGraph orchestration completed")
            
            return result
            
        except Exception as e:
            logger.error(f"LangGraph orchestration failed: {e}")
            return {
                "messages": [AIMessage(content=f"오케스트레이션 실행 중 오류가 발생했습니다: {str(e)}")],
                "error": str(e)
            }
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계 반환"""
        return {
            "orchestrator_type": "LangGraph",
            "model": self.model_name,
            "temperature": self.temperature,
            "available_agents": ["conversation_agent", "regulation_agent", "consultation_agent"]
        }