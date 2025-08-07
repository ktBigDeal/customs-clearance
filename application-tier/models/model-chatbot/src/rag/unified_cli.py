#!/usr/bin/env python3
"""
Unified CLI Interface for Korean Trade Information System

관세법 RAG 시스템과 일반 무역 정보 시스템을 통합한 CLI 인터페이스
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드 (여러 위치에서 시도)
env_paths = [
    project_root / ".env",  # 프로젝트 루트의 .env
    Path.cwd() / ".env",    # 현재 작업 디렉토리의 .env
    Path(__file__).parent.parent.parent / ".env"  # 명시적 경로
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✅ 환경변수 로드: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("⚠️ .env 파일을 찾을 수 없습니다. 환경변수를 직접 설정해주세요.")
    print(f"찾는 위치: {[str(p) for p in env_paths]}")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedTradeInfoCLI:
    """
    통합 무역 정보 상담 시스템 CLI
    
    이 클래스는 한국의 관세법과 무역 정보를 처리하는 3가지 AI 시스템을 
    하나의 사용자 인터페이스로 통합한 메인 애플리케이션입니다.
    
    제공하는 AI 시스템:
    1. 관세법 RAG 에이전트: 관세법 조문을 정확히 해석해주는 AI
    2. 듀얼 에이전트 시스템: 무역 규제와 상담 사례를 처리하는 2개 AI
    3. LangGraph 오케스트레이션: 여러 AI가 협업하는 고급 시스템
    
    신입 개발자를 위한 주요 개념:
    - RAG (Retrieval-Augmented Generation): 문서 검색 + AI 생성을 결합한 기술
    - Vector Store: 문서를 숫자 벡터로 변환해서 저장하는 데이터베이스
    - Embedding: 텍스트를 AI가 이해할 수 있는 숫자 벡터로 변환하는 과정
    - Agent: 특정 업무를 전문적으로 처리하는 AI 모듈
    
    Attributes:
        conversation_agent: 관세법 전문 AI 에이전트
        regulation_agent: 무역 규제 전문 AI 에이전트  
        consultation_agent: 상담 사례 전문 AI 에이전트
        langgraph_orchestrator: 여러 AI를 조율하는 오케스트레이터
    """
    
    def __init__(self):
        """
        CLI 애플리케이션을 초기화합니다.
        
        초기화 과정에서 하는 일:
        1. 모든 AI 에이전트 변수를 None으로 설정 (나중에 필요할 때 생성)
        2. 벡터 저장소와 임베딩 모델 변수 초기화
        3. 환영 메시지 출력
        
        왜 모든 것을 None으로 시작하나요?
        - 메모리 절약: 사용하지 않는 AI 모델을 미리 로드하지 않음
        - 빠른 시작: 필요한 것만 나중에 로드해서 시작 시간 단축
        - 에러 방지: API 키가 없어도 프로그램이 시작되도록 함
        """
        self.current_agent = None
        self.agent_type = None
        
        # ConversationAgent 관련
        self.conversation_embedder = None
        self.conversation_vector_store = None
        self.conversation_retriever = None
        self.conversation_agent = None
        
        # Dual Agent Architecture 관련
        self.general_embedder = None
        self.general_vector_store = None
        self.general_retriever = None
        self.query_router = None
        self.regulation_agent = None
        self.consultation_agent = None
        
        # LangGraph Orchestration 관련
        self.langgraph_orchestrator = None
        self.langgraph_factory = None
        
        print("🚀 통합 무역 정보 상담 시스템")
        print("=" * 60)
    
    def display_main_menu(self):
        """메인 메뉴 출력"""
        print("\n" + "="*60)
        print("🏠 무역 정보 통합 상담 시스템 메인 메뉴")
        print("="*60)
        print("1. 📚 관세법 RAG 에이전트 (정확한 법률 정보)")
        print("2. 🌐 지능형 무역 정보 에이전트 (듀얼 AI 시스템)")
        print("3. 🤖 LangGraph 오케스트레이션 시스템 (고급 AI)")
        print("4. 🗄️ 데이터베이스 관리")
        print("5. 📊 시스템 상태 확인")
        print("6. ⚙️ 설정")
        print("0. 🚪 종료")
        print("-" * 60)
    
    def get_user_choice(self, prompt: str = "선택", valid_options: List[str] = None) -> str:
        """
        사용자로부터 안전하게 입력을 받는 헬퍼 함수
        
        이 함수가 필요한 이유:
        - 사용자가 잘못된 옵션을 입력하면 다시 입력받음
        - Ctrl+C (KeyboardInterrupt)를 누르면 프로그램을 안전하게 종료
        - 입력 스트림이 끝나면 (EOF) 자동으로 종료 옵션 반환
        
        Args:
            prompt (str): 사용자에게 보여줄 입력 안내 메시지 (기본값: "선택")
            valid_options (List[str], optional): 허용되는 입력값 리스트 
                                               (예: ["0", "1", "2", "3"])
                                               None이면 모든 입력 허용
        
        Returns:
            str: 사용자가 입력한 문자열 (공백 제거됨)
                 Ctrl+C나 EOF 발생시에는 "0" 반환 (종료 신호)
        
        신입 개발자 팁:
        - try-except를 사용해서 예외 상황을 안전하게 처리
        - while True로 올바른 입력이 들어올 때까지 반복
        - strip()으로 앞뒤 공백 제거하는 것은 좋은 사용자 경험
        """
        while True:
            try:
                user_input = input(f"{prompt}: ").strip()
                
                if valid_options and user_input not in valid_options:
                    print(f"❌ 올바른 옵션을 선택해주세요: {', '.join(valid_options)}")
                    continue
                
                return user_input
                
            except KeyboardInterrupt:
                print("\n⚠️ 사용자에 의해 중단되었습니다.")
                return "0"
            except EOFError:
                return "0"
    
    def initialize_conversation_agent(self) -> bool:
        """
        관세법 전문 RAG 에이전트를 초기화합니다.
        
        RAG (Retrieval-Augmented Generation)란?
        1. Retrieval: 관련 관세법 조문을 데이터베이스에서 검색
        2. Augmented: 검색된 조문을 GPT에게 추가 정보로 제공
        3. Generation: GPT가 조문을 바탕으로 정확한 답변 생성
        
        초기화 단계별 설명:
        1. 환경 변수에서 OpenAI API 키 확인
        2. OpenAIEmbedder: 텍스트를 벡터로 변환하는 모델 로드
        3. ChromaVectorStore: 벡터를 저장하고 검색하는 데이터베이스 초기화
        4. LawQueryNormalizer: 사용자 질문을 표준화하는 전처리기
        5. SimilarLawRetriever: 유사한 법령 조문을 찾는 검색 엔진
        6. ConversationAgent: 최종적으로 사용자와 대화하는 AI 에이전트
        
        Returns:
            bool: 초기화 성공시 True, 실패시 False
                  실패 원인: API 키 없음, 모듈 로드 실패, 데이터베이스 연결 실패
        
        신입 개발자 주의사항:
        - 이미 초기화되어 있으면 다시 하지 않음 (성능 최적화)
        - 각 단계에서 실패하면 전체 초기화가 실패함
        - 예외 처리로 오류 메시지를 사용자에게 친화적으로 표시
        """
        try:
            if self.conversation_agent:
                return True
            
            print("🔧 관세법 RAG 에이전트 초기화 중...")
            
            # 모듈 임포트
            from .embeddings import OpenAIEmbedder
            from .vector_store import LangChainVectorStore
            from .query_normalizer import LawQueryNormalizer
            from .law_retriever import SimilarLawRetriever
            from .law_agent import ConversationAgent
            from .law_data_processor import EnhancedDataProcessor
            
            # 환경 변수 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                return False
            
            # 1. 임베딩 모델 초기화
            print("  - OpenAI 임베딩 모델 로드...")
            self.conversation_embedder = OpenAIEmbedder()
            
            # 2. 벡터 저장소 초기화 (Docker 모드 지원)
            print("  - ChromaDB 벡터 저장소 초기화...")
            from ..utils.config import get_chromadb_config
            chromadb_config = get_chromadb_config()
            
            self.conversation_vector_store = LangChainVectorStore(
                collection_name="customs_law_collection",
                config=chromadb_config
            )
            
            # 3. 쿼리 정규화기 및 검색기 초기화
            print("  - 검색 시스템 초기화...")
            query_normalizer = LawQueryNormalizer()
            self.conversation_retriever = SimilarLawRetriever(
                embedder=self.conversation_embedder,
                vector_store=self.conversation_vector_store,
                query_normalizer=query_normalizer
            )
            
            # 4. 대화 에이전트 초기화
            print("  - 대화 에이전트 초기화...")
            self.conversation_agent = ConversationAgent(
                retriever=self.conversation_retriever,
                max_context_docs=5,
                similarity_threshold=0.0
            )
            
            print("✅ 관세법 RAG 에이전트 초기화 완료!")
            return True
            
        except Exception as e:
            print(f"❌ 관세법 RAG 에이전트 초기화 실패: {e}")
            logger.error(f"ConversationAgent initialization failed: {e}")
            return False
    
    def initialize_dual_agent_system(self) -> bool:
        """듀얼 에이전트 시스템 초기화 (TradeRegulationAgent + ConsultationCaseAgent)"""
        try:
            if self.regulation_agent and self.consultation_agent:
                return True
            
            print("🔧 지능형 듀얼 에이전트 시스템 초기화 중...")
            
            # 모듈 임포트
            from .embeddings import OpenAIEmbedder
            from .vector_store import LangChainVectorStore
            from .query_normalizer import LawQueryNormalizer
            from .trade_info_retriever import TradeInfoRetriever
            from .trade_regulation_agent import TradeRegulationAgent
            from .consultation_case_agent import ConsultationCaseAgent
            from .query_router import QueryRouter
            from ..utils.config import get_trade_agent_config
            
            # 환경 변수 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                return False
            
            # 설정 로드
            trade_config = get_trade_agent_config()
            
            # 1. 공통 구성요소 초기화
            print("  - OpenAI 임베딩 모델 로드...")
            self.general_embedder = OpenAIEmbedder()
            
            print("  - ChromaDB 벡터 저장소 초기화...")
            from ..utils.config import get_chromadb_config
            chromadb_config = get_chromadb_config()
            
            self.general_vector_store = LangChainVectorStore(
                collection_name=trade_config["collection_name"],
                config=chromadb_config
            )
            
            print("  - 무역 정보 검색 시스템 초기화...")
            query_normalizer = LawQueryNormalizer()
            self.general_retriever = TradeInfoRetriever(
                embedder=self.general_embedder,
                vector_store=self.general_vector_store,
                query_normalizer=query_normalizer,
                collection_name=trade_config["collection_name"]
            )
            
            # 2. 쿼리 라우터 초기화
            print("  - 지능형 쿼리 라우터 초기화...")
            self.query_router = QueryRouter()
            
            # 3. 무역 규제 전용 에이전트 초기화
            print("  - 무역 규제 전문 에이전트 초기화...")
            self.regulation_agent = TradeRegulationAgent(
                retriever=self.general_retriever,
                model_name=trade_config["model_name"],
                temperature=0.1,  # 규제 정보는 더 정확하게
                max_context_docs=12,  # 더 많은 규제 문서 참조
                similarity_threshold=trade_config["similarity_threshold"]
            )
            
            # 4. 상담 사례 전용 에이전트 초기화
            print("  - 상담 사례 전문 에이전트 초기화...")
            self.consultation_agent = ConsultationCaseAgent(
                retriever=self.general_retriever,
                model_name=trade_config["model_name"],
                temperature=0.4,  # 상담사례는 약간 더 유연하게
                max_context_docs=8,  # 적당한 수의 상담사례 참조
                similarity_threshold=trade_config["similarity_threshold"]
            )
            
            print("✅ 듀얼 에이전트 시스템 초기화 완료!")
            print("  🔍 지능형 라우터: 질의 의도 자동 분석")
            print("  ⚖️ 규제 에이전트: 정확한 법령 및 규제 정보")
            print("  💼 상담 에이전트: 실용적 업무 가이드")
            return True
            
        except Exception as e:
            print(f"❌ 듀얼 에이전트 시스템 초기화 실패: {e}")
            logger.error(f"Dual agent system initialization failed: {e}")
            return False
    
    def initialize_langgraph_orchestration(self) -> bool:
        """LangGraph 오케스트레이션 시스템 초기화"""
        try:
            if self.langgraph_orchestrator:
                return True
            
            print("🤖 LangGraph 오케스트레이션 시스템 초기화 중...")
            
            # 환경 변수 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                return False
            
            # LangGraph 팩토리 및 오케스트레이터 임포트
            from .langgraph_factory import get_langgraph_factory, create_orchestrated_system
            
            print("  - LangGraph 팩토리 초기화...")
            self.langgraph_factory = get_langgraph_factory()
            
            print("  - 멀티 에이전트 오케스트레이션 시스템 구성...")
            self.langgraph_orchestrator = create_orchestrated_system(
                model_name="gpt-4.1-mini",
                temperature=0.1
            )
            
            print("✅ LangGraph 오케스트레이션 시스템 초기화 완료!")
            print("  🧠 지능형 Supervisor: LLM 기반 라우팅")
            print("  🏛️ 관세법 에이전트: 법령 조문 전문")
            print("  ⚖️ 규제 에이전트: 무역 규제 전문")
            print("  💼 상담 에이전트: 실무 사례 전문")
            print("  🤝 복합 워크플로우: 멀티 에이전트 협업")
            return True
            
        except Exception as e:
            print(f"❌ LangGraph 오케스트레이션 시스템 초기화 실패: {e}")
            logger.error(f"LangGraph orchestration system initialization failed: {e}")
            return False
    
    def conversation_agent_chat(self):
        """관세법 RAG 에이전트 대화 모드"""
        if not self.initialize_conversation_agent():
            return
        
        # 벡터 저장소 상태 확인
        try:
            if self.conversation_vector_store.collection is None:
                print("  - 기존 컬렉션 연결 시도...")
                self.conversation_vector_store._auto_connect_collection()
            
            stats = self.conversation_vector_store.get_collection_stats()
            
            if "error" in stats or stats.get("total_documents", 0) == 0:
                print("⚠️ 관세법 데이터베이스가 비어있습니다.")
                print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
                return
                
        except Exception as e:
            print(f"⚠️ 벡터 데이터베이스에 연결할 수 없습니다: {e}")
            print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
            return
        
        print("\n💬 관세법 RAG 상담 시작!")
        print("종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.")
        print("대화 기록을 초기화하려면 'reset'을 입력하세요.")
        print("=" * 60)
        
        while True:
            try:
                # 사용자 입력
                user_input = input("\n❓ 관세법 질문: ").strip()
                
                # 종료 명령어 확인
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 관세법 상담을 종료합니다.")
                    break
                
                # 초기화 명령어 확인
                if user_input.lower() == 'reset':
                    self.conversation_agent.reset_conversation()
                    print("🔄 대화 기록이 초기화되었습니다.")
                    continue
                
                # 빈 입력 무시
                if not user_input:
                    continue
                
                # 응답 생성
                print("\n🤔 답변 생성 중...")
                response, docs = self.conversation_agent.chat(user_input)
                
                # 응답 출력
                print(f"\n🤖 관세법 전문가:")
                print("-" * 50)
                print(response)
                
                # 참조 문서 정보 출력
                if docs:
                    print(f"\n📚 참조된 법령 ({len(docs)}개):")
                    for i, doc in enumerate(docs, 1):
                        metadata = doc.get("metadata", {})
                        
                        index = (doc.get("index") or 
                                metadata.get("index") or 
                                "").strip()
                        subtitle = (doc.get("subtitle") or 
                                   metadata.get("subtitle") or 
                                   "").strip()
                        law_name = metadata.get("law_name", "N/A")
                        similarity = abs(doc.get("similarity", 0))
                        
                        article_info = ""
                        if index and index != "N/A":
                            article_info = index
                            if subtitle:
                                article_info += f" ({subtitle})"
                        elif subtitle:
                            article_info = subtitle
                        else:
                            article_info = "조문 정보 없음"
                        
                        print(f"  {i}. {article_info} - {law_name} - 유사도: {similarity:.3f}")
                
            except KeyboardInterrupt:
                print("\n\n👋 관세법 상담을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                logger.error(f"Conversation chat error: {e}")
    
    def dual_agent_chat(self):
        """듀얼 에이전트 시스템 대화 모드"""
        if not self.initialize_dual_agent_system():
            return
        
        # 벡터 저장소 상태 확인
        try:
            stats = self.general_vector_store.get_collection_stats()
            
            if "error" in stats or stats.get("total_documents", 0) == 0:
                print("⚠️ 무역 정보 데이터베이스가 비어있습니다.")
                print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
                return
                
        except Exception as e:
            print(f"⚠️ 벡터 데이터베이스에 연결할 수 없습니다: {e}")
            print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
            return
        
        print("\n💬 지능형 무역 정보 상담 시작! (듀얼 AI 시스템)")
        print("🔍 시스템이 질의를 분석하여 최적의 전문 에이전트로 연결합니다.")
        print("  ⚖️ 규제 에이전트: 정확한 법령 및 규제 정보")
        print("  💼 상담 에이전트: 실용적 업무 가이드")
        print("\n종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.")
        print("대화 기록을 초기화하려면 'reset'을 입력하세요.")
        print("=" * 60)
        
        while True:
            try:
                # 사용자 입력
                user_input = input("\n❓ 무역 정보 질문: ").strip()
                
                # 종료 명령어 확인
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 무역 정보 상담을 종료합니다.")
                    break
                
                # 초기화 명령어 확인
                if user_input.lower() == 'reset':
                    self.regulation_agent.reset_conversation()
                    self.consultation_agent.reset_conversation()
                    print("🔄 모든 에이전트의 대화 기록이 초기화되었습니다.")
                    continue
                
                # 빈 입력 무시
                if not user_input:
                    continue
                
                # 1. 쿼리 라우팅
                print("\n🧠 질의 분석 중...")
                from .query_router import QueryType
                query_type, confidence, routing_info = self.query_router.route_query(user_input)
                
                # 라우팅 결과 표시
                if query_type == QueryType.REGULATION:
                    print(f"🔍 ⚖️ 규제 전문 에이전트로 연결 (신뢰도: {confidence:.2f})")
                    if routing_info.get('reason') == 'animal_plant_import_query':
                        detected_products = routing_info.get('detected_products', [])
                        if detected_products:
                            print(f"  🐕🌱 감지된 제품: {', '.join(detected_products)}")
                elif query_type == QueryType.CONSULTATION:
                    print(f"🔍 💼 상담 전문 에이전트로 연결 (신뢰도: {confidence:.2f})")
                else:
                    print(f"🔍 🤝 혼합형 질의 - 상담 에이전트로 연결 (신뢰도: {confidence:.2f})")
                
                # 2. 적절한 에이전트로 질의 처리
                print("🤔 답변 생성 중...")
                if query_type == QueryType.REGULATION:
                    response, docs = self.regulation_agent.query_regulation(user_input)
                    agent_name = "⚖️ 규제 전문가"
                else:
                    # CONSULTATION 또는 MIXED의 경우 상담 에이전트 사용
                    response, docs = self.consultation_agent.query_consultation(user_input)
                    agent_name = "💼 상담 전문가"
                
                # 응답 출력
                print(f"\n🤖 {agent_name}:")
                print("-" * 50)
                print(response)
                
                # 참조 문서 정보 출력
                if docs:
                    data_type_indicator = "📊 참조 정보" if query_type == QueryType.REGULATION else "💼 참조 사례"
                    print(f"\n{data_type_indicator} ({len(docs)}개):")
                    for i, doc in enumerate(docs, 1):
                        metadata = doc.get("metadata", {})
                        data_type = metadata.get("data_type", "")
                        similarity = abs(doc.get("similarity", 0))
                        
                        info_parts = []
                        
                        if data_type == "consultation_case":
                            # 민원상담 사례 정보 표시
                            title = metadata.get("sub_title", "")
                            category = metadata.get("category", "")
                            sub_category = metadata.get("sub_category", "")
                            case_number = metadata.get("management_number", "") or metadata.get("index", "")
                            
                            if title:
                                info_parts.append(title[:50] + ("..." if len(title) > 50 else ""))
                            if category:
                                info_parts.append(f"분야: {category}")
                            if sub_category:
                                info_parts.append(f"세부: {sub_category}")
                            if case_number:
                                info_parts.append(f"사례: {case_number}")
                            
                            info_parts.append("📋 상담사례")
                                
                        else:
                            # 무역규제 데이터 처리 (trade_regulation)
                            data_source = metadata.get("data_source", "")
                            regulation_type = metadata.get("regulation_type", "")
                            
                            # 동식물 허용금지지역 데이터 특별 처리
                            if data_source == "동식물허용금지지역":
                                product_name = metadata.get("product_name", "")
                                allowed_countries = metadata.get("allowed_countries", [])
                                prohibited_countries = metadata.get("prohibited_countries", [])
                                has_global_prohibition = metadata.get("has_global_prohibition", False)
                                special_conditions = metadata.get("special_conditions", "")
                                
                                if product_name:
                                    info_parts.append(f"품목: {product_name}")
                                
                                # 허용국가 정보
                                if allowed_countries:
                                    if len(allowed_countries) <= 3:
                                        allowed_text = ", ".join(allowed_countries)
                                    else:
                                        allowed_text = f"{', '.join(allowed_countries[:3])} 외 {len(allowed_countries)-3}개국"
                                    info_parts.append(f"허용: {allowed_text}")
                                
                                # 금지/제한 정보
                                if has_global_prohibition:
                                    if prohibited_countries:
                                        if len(prohibited_countries) <= 2:
                                            prohibited_text = ", ".join(prohibited_countries)
                                        else:
                                            prohibited_text = f"{', '.join(prohibited_countries[:2])} 외 {len(prohibited_countries)-2}개국"
                                        info_parts.append(f"금지: {prohibited_text}")
                                    else:
                                        info_parts.append(f"금지: 허용국가외전체")
                                
                                # 특별조건
                                if special_conditions:
                                    info_parts.append(f"조건: {special_conditions[:30]}{'...' if len(special_conditions) > 30 else ''}")
                                
                                info_parts.append("🐕🌱 동식물규제")
                            
                            else:
                                # 기존 무역규제 데이터 처리
                                title = doc.get("title", "")
                                hs_code = metadata.get("hs_code", "")
                                country = metadata.get("country", "")
                                
                                if title:
                                    info_parts.append(title[:50] + ("..." if len(title) > 50 else ""))
                                if hs_code:
                                    info_parts.append(f"HS: {hs_code}")
                                if country:
                                    info_parts.append(f"국가: {country}")
                                if regulation_type:
                                    info_parts.append(f"유형: {regulation_type}")
                                
                                info_parts.append("⚖️ 무역규제")
                        
                        # 부스팅 정보 표시
                        boost_info = ""
                        if doc.get("boosted"):
                            boost_info = " 🎯"
                        
                        info_text = " | ".join(info_parts) if info_parts else "정보 없음"
                        print(f"  {i}. {info_text}{boost_info} - 유사도: {similarity:.3f}")
                
            except KeyboardInterrupt:
                print("\n\n👋 듀얼 에이전트 상담을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                logger.error(f"Dual agent chat error: {e}")
    
    def langgraph_orchestration_chat(self):
        """LangGraph 오케스트레이션 시스템 대화 모드"""
        if not self.initialize_langgraph_orchestration():
            return
        
        # 벡터 저장소 상태 확인 (팩토리를 통해 확인)
        try:
            stats = self.langgraph_factory.get_agent_stats()
            
            if not stats.get("orchestrator_available", False):
                print("⚠️ LangGraph 오케스트레이터가 초기화되지 않았습니다.")
                return
            
            if not all(stats.get("agents", {}).values()):
                print("⚠️ 일부 에이전트가 초기화되지 않았습니다.")
                print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
                return
                
        except Exception as e:
            print(f"⚠️ 시스템 상태 확인 실패: {e}")
            print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
            return
        
        print("\n💬 LangGraph 오케스트레이션 상담 시작! (고급 AI 시스템)")
        print("🤖 지능형 Supervisor가 질의를 분석하여 최적의 전문 에이전트로 연결합니다.")
        print("  🧠 LLM 기반 라우팅: 질의 복잡도와 의도 자동 분석")
        print("  🏛️ 관세법 에이전트: 정확한 법령 조문 정보")
        print("  ⚖️ 규제 에이전트: 무역 규제 및 동식물 수입 정보")
        print("  💼 상담 에이전트: 실용적 업무 가이드")
        print("  🤝 복합 워크플로우: 멀티 에이전트 협업 (추후 지원)")
        print("\n종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.")
        print("대화 기록을 초기화하려면 'reset'을 입력하세요.")
        print("라우팅 통계를 보려면 'stats'를 입력하세요.")
        print("=" * 60)
        
        conversation_history = []
        routing_statistics = {
            "total_queries": 0,
            "agent_usage": {"conversation_agent": 0, "regulation_agent": 0, "consultation_agent": 0},
            "avg_complexity": 0.0,
            "complex_queries": 0
        }
        
        while True:
            try:
                # 사용자 입력
                user_input = input("\n❓ 무역 정보 질문: ").strip()
                
                # 종료 명령어 확인
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 LangGraph 오케스트레이션 상담을 종료합니다.")
                    break
                
                # 초기화 명령어 확인
                if user_input.lower() == 'reset':
                    conversation_history = []
                    routing_statistics = {
                        "total_queries": 0,
                        "agent_usage": {"conversation_agent": 0, "regulation_agent": 0, "consultation_agent": 0},
                        "avg_complexity": 0.0,
                        "complex_queries": 0
                    }
                    print("🔄 대화 기록과 통계가 초기화되었습니다.")
                    continue
                
                # 통계 명령어 확인
                if user_input.lower() == 'stats':
                    self._display_routing_stats(routing_statistics)
                    continue
                
                # 빈 입력 무시
                if not user_input:
                    continue
                
                # 1. LangGraph 오케스트레이터 실행
                print("\n🧠 지능형 Supervisor 분석 중...")
                result = self.langgraph_orchestrator.invoke(user_input)
                
                # 2. 결과 처리
                if "error" in result:
                    print(f"❌ 오류 발생: {result['error']}")
                    continue
                
                messages = result.get("messages", [])
                if not messages:
                    print("⚠️ 응답을 생성할 수 없습니다.")
                    continue
                
                # 3. 라우팅 정보 분석 및 표시
                routing_history = result.get("routing_history", [])
                if routing_history:
                    latest_routing = routing_history[-1]
                    selected_agent = latest_routing.get("selected_agent", "unknown")
                    complexity = latest_routing.get("complexity", 0.0)
                    reasoning = latest_routing.get("reasoning", "")
                    
                    # 에이전트 아이콘 매핑
                    agent_icons = {
                        "conversation_agent": "🏛️ 관세법 전문가",
                        "regulation_agent": "⚖️ 규제 전문가",
                        "consultation_agent": "💼 상담 전문가",
                        "__end__": "🏁 완료"
                    }
                    
                    agent_display = agent_icons.get(selected_agent, f"🤖 {selected_agent}")
                    complexity_level = "복합" if complexity > 0.7 else "보통" if complexity > 0.4 else "단순"
                    
                    print(f"🔍 {agent_display}로 연결 (복잡도: {complexity:.2f} - {complexity_level})")
                    if reasoning:
                        print(f"📝 분석: {reasoning}")
                    
                    # 통계 업데이트
                    routing_statistics["total_queries"] += 1
                    if selected_agent in routing_statistics["agent_usage"]:
                        routing_statistics["agent_usage"][selected_agent] += 1
                    
                    # 평균 복잡도 계산
                    prev_avg = routing_statistics["avg_complexity"]
                    total = routing_statistics["total_queries"]
                    routing_statistics["avg_complexity"] = (prev_avg * (total - 1) + complexity) / total
                    
                    if complexity > 0.7:
                        routing_statistics["complex_queries"] += 1
                
                # 4. 최종 응답 출력
                final_response = messages[-1]
                print(f"\n🤖 AI 전문가:")
                print("-" * 50)
                print(final_response.content)
                
                # 5. 에이전트별 상세 정보 출력
                agent_responses = result.get("agent_responses", {})
                if agent_responses:
                    for agent_name, agent_data in agent_responses.items():
                        docs = agent_data.get("docs", [])
                        metadata = agent_data.get("metadata", {})
                        
                        if docs:
                            # 에이전트별 참조 정보 표시
                            agent_display_name = {
                                "conversation_agent": "🏛️ 관세법 참조",
                                "regulation_agent": "⚖️ 규제 정보",
                                "consultation_agent": "💼 상담 사례"
                            }.get(agent_name, f"📚 {agent_name} 참조")
                            
                            print(f"\n{agent_display_name} ({len(docs)}개):")
                            
                            for i, doc in enumerate(docs[:3], 1):  # 상위 3개만 표시
                                doc_metadata = doc.get("metadata", {})
                                similarity = doc.get("similarity", 0)
                                
                                # 에이전트별 맞춤 정보 표시
                                if agent_name == "conversation_agent":
                                    index = doc.get("index", "")
                                    subtitle = doc.get("subtitle", "")
                                    law_name = doc_metadata.get("law_name", "")
                                    display_text = f"{index} {subtitle} - {law_name}" if index else subtitle or "조문 정보"
                                
                                elif agent_name == "regulation_agent":
                                    if doc_metadata.get("data_source") == "동식물허용금지지역":
                                        product_name = doc_metadata.get("product_name", "")
                                        allowed_countries = doc_metadata.get("allowed_countries", [])
                                        allowed_text = f"허용: {', '.join(allowed_countries[:2])}" if allowed_countries else ""
                                        display_text = f"{product_name} - {allowed_text}"
                                    else:
                                        title = doc.get("title", "")
                                        hs_code = doc_metadata.get("hs_code", "")
                                        display_text = f"{title} (HS: {hs_code})" if hs_code else title
                                
                                else:  # consultation_agent
                                    title = doc_metadata.get("sub_title", "")
                                    category = doc_metadata.get("category", "")
                                    display_text = f"{title} - {category}" if category else title
                                
                                boost_info = " 🎯" if doc.get("boosted") else ""
                                print(f"  {i}. {display_text[:80]}{boost_info} - 유사도: {similarity:.3f}")
                
                # 대화 히스토리에 추가
                conversation_history.append({
                    "query": user_input,
                    "response": final_response.content,
                    "routing": latest_routing if routing_history else None
                })
                
            except KeyboardInterrupt:
                print("\n\n👋 LangGraph 오케스트레이션 상담을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                logger.error(f"LangGraph orchestration chat error: {e}")
    
    def _display_routing_stats(self, stats):
        """라우팅 통계 표시"""
        print(f"\n📊 LangGraph 라우팅 통계")
        print("-" * 40)
        print(f"총 질의 수: {stats['total_queries']}")
        print(f"평균 복잡도: {stats['avg_complexity']:.2f}")
        print(f"복합 질의: {stats['complex_queries']} ({stats['complex_queries']/max(stats['total_queries'], 1)*100:.1f}%)")
        
        print(f"\n에이전트 사용 빈도:")
        for agent, count in stats['agent_usage'].items():
            percentage = count / max(stats['total_queries'], 1) * 100
            agent_name = {
                "conversation_agent": "🏛️ 관세법 에이전트",
                "regulation_agent": "⚖️ 규제 에이전트", 
                "consultation_agent": "💼 상담 에이전트"
            }.get(agent, agent)
            print(f"  {agent_name}: {count}회 ({percentage:.1f}%)")
    
    def database_management_menu(self):
        """데이터베이스 관리 메뉴"""
        while True:
            print("\n" + "="*60)
            print("🗄️ 데이터베이스 관리 메뉴")
            print("="*60)
            print("1. 📚 관세법 데이터 로드/재로드")
            print("2. 🌐 무역 정보 데이터 로드/재로드")
            print("3. 📊 데이터베이스 상태 확인")
            print("4. 🗑️ 데이터베이스 초기화")
            print("0. ⬅️ 메인 메뉴로")
            print("-" * 60)
            
            choice = self.get_user_choice("선택", ["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.load_customs_law_data()
            elif choice == "2":
                self.load_trade_info_data()
            elif choice == "3":
                self.show_database_status()
            elif choice == "4":
                self.reset_databases()
    
    def load_customs_law_data(self):
        """관세법 데이터 로드"""
        try:
            print("\n📚 관세법 데이터 로드 시작...")
            
            if not self.initialize_conversation_agent():
                return
            
            from .law_data_processor import EnhancedDataProcessor
            
            # 데이터 처리기 초기화
            data_processor = EnhancedDataProcessor(
                embedder=self.conversation_embedder,
                vector_store=self.conversation_vector_store
            )
            
            # 데이터 로드 및 처리
            confirm = self.get_user_choice("기존 데이터를 재설정하시겠습니까? (y/N)", ["y", "Y", "n", "N", ""])
            reset_db = confirm.lower() == "y"
            
            print("⚠️ 이 작업은 시간이 오래 걸릴 수 있습니다...")
            result = data_processor.load_and_process_all_laws(reset_db=reset_db)
            
            if result["status"] == "success":
                print("✅ 관세법 데이터 로드 완료!")
                stats = result["statistics"]
                print(f"  - 총 문서 수: {stats['total_documents']:,}개")
                print(f"  - 내부 참조: {stats['internal_references']:,}건")
                print(f"  - 외부 참조: {stats['external_references']:,}건")
            else:
                print(f"❌ 관세법 데이터 로드 실패: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ 관세법 데이터 로드 중 오류: {e}")
            logger.error(f"Customs law data loading failed: {e}")
    
    def load_trade_info_data(self):
        """무역 정보 데이터 로드"""
        try:
            print("\n🌐 무역 정보 데이터 로드 시작...")
            
            if not self.initialize_dual_agent_system():
                return
            
            from ..utils.config import get_data_paths
            from ..data_processing.trade_info_csv_loader import CSVDocumentLoader
            from .law_data_processor import RAGDataProcessor
            from ..utils.file_utils import load_json_data
            
            # 데이터 처리기 초기화
            data_processor = RAGDataProcessor(
                embedder=self.general_embedder,
                vector_store=self.general_vector_store
            )
            
            # 기존 데이터 확인
            stats = self.general_vector_store.get_collection_stats()
            force_reload = False
            
            if stats.get("total_documents", 0) > 0:
                print(f"ℹ️ 기존 데이터 발견: {stats['total_documents']}개 문서")
                confirm = self.get_user_choice("기존 데이터를 재로드하시겠습니까? (y/N)", ["y", "Y", "n", "N", ""])
                force_reload = confirm.lower() == "y"
                
                if not force_reload:
                    print("기존 데이터를 사용합니다.")
                    return
            
            print("📁 무역 정보 데이터 로드 중...")
            data_paths = get_data_paths()
            all_documents = []
            
            for data_name, data_path in data_paths.items():
                if not data_path.exists():
                    print(f"⚠️ {data_name} 파일 없음: {data_path}")
                    continue
                
                print(f"📄 {data_name} 처리 중...")
                try:
                    # 파일 확장자로 처리 방식 결정
                    if data_path.suffix.lower() == '.csv':
                        # CSV 파일 처리
                        loader = CSVDocumentLoader(str(data_path))
                        documents = loader.load()
                    elif data_path.suffix.lower() == '.json':
                        # JSON 파일 처리 (consultation_cases.json)
                        json_data = load_json_data(str(data_path))
                        if json_data and isinstance(json_data, list):
                            documents = json_data
                        else:
                            print(f"⚠️ {data_name} JSON 형식 오류")
                            continue
                    else:
                        print(f"⚠️ {data_name} 지원하지 않는 파일 형식: {data_path.suffix}")
                        continue
                    
                    if documents:
                        # 임베딩 생성
                        print(f"🔧 {data_name} 임베딩 생성 중... ({len(documents)}개 문서)")
                        documents_with_embeddings = data_processor.process_documents(documents)
                        all_documents.extend(documents_with_embeddings)
                        print(f"✅ {data_name} 완료: {len(documents)}개 문서 처리")
                    else:
                        print(f"⚠️ {data_name} 처리 결과 없음")
                        
                except Exception as e:
                    print(f"❌ {data_name} 처리 실패: {e}")
                    continue
            
            if all_documents:
                # 벡터 저장소에 추가
                print(f"💾 벡터 저장소에 {len(all_documents)}개 문서 저장 중...")
                if force_reload:
                    self.general_vector_store.create_collection(reset=True)
                else:
                    self.general_vector_store.create_collection()
                
                self.general_vector_store.add_documents(all_documents)
                print("✅ 무역 정보 데이터 로드 완료!")
            else:
                print("❌ 처리된 문서가 없습니다.")
                
        except Exception as e:
            print(f"❌ 무역 정보 데이터 로드 중 오류: {e}")
            logger.error(f"Trade info data loading failed: {e}")
    
    def show_database_status(self):
        """데이터베이스 상태 확인"""
        print("\n📊 데이터베이스 상태")
        print("="*60)
        
        # 관세법 데이터베이스 상태
        print("📚 관세법 데이터베이스:")
        try:
            if not self.conversation_vector_store:
                from .vector_store import LangChainVectorStore
                from ..utils.config import get_chromadb_config
                chromadb_config = get_chromadb_config()
                
                self.conversation_vector_store = LangChainVectorStore(
                    collection_name="customs_law_collection",
                    config=chromadb_config
                )
            
            stats = self.conversation_vector_store.get_collection_stats()
            if "error" in stats:
                print("  ❌ 연결 실패 또는 데이터 없음")
            else:
                print(f"  ✅ 총 문서 수: {stats.get('total_documents', 0):,}개")
                print(f"  📂 컬렉션명: {stats.get('collection_name', 'N/A')}")
        except Exception as e:
            print(f"  ❌ 상태 확인 실패: {e}")
        
        # 무역 정보 데이터베이스 상태
        print("\n🌐 무역 정보 데이터베이스:")
        try:
            if not self.general_vector_store:
                from .vector_store import LangChainVectorStore
                from ..utils.config import get_trade_agent_config, get_chromadb_config
                trade_config = get_trade_agent_config()
                chromadb_config = get_chromadb_config()
                
                self.general_vector_store = LangChainVectorStore(
                    collection_name=trade_config["collection_name"],
                    config=chromadb_config
                )
            
            stats = self.general_vector_store.get_collection_stats()
            if "error" in stats:
                print("  ❌ 연결 실패 또는 데이터 없음")
            else:
                print(f"  ✅ 총 문서 수: {stats.get('total_documents', 0):,}개")
                print(f"  📂 컬렉션명: {stats.get('collection_name', 'N/A')}")
        except Exception as e:
            print(f"  ❌ 상태 확인 실패: {e}")
        
        input("\n✅ 계속하려면 Enter를 누르세요...")
    
    def reset_databases(self):
        """데이터베이스 초기화"""
        print("\n⚠️ 데이터베이스 초기화")
        print("이 작업은 모든 벡터 데이터를 삭제합니다!")
        
        confirm1 = self.get_user_choice("정말로 초기화하시겠습니까? (yes/no)", ["yes", "no"])
        if confirm1 != "yes":
            print("❌ 취소되었습니다.")
            return
        
        confirm2 = self.get_user_choice("마지막 확인: 'DELETE'를 입력해주세요")
        if confirm2 != "DELETE":
            print("❌ 취소되었습니다.")
            return
        
        try:
            # ChromaDB 클라이언트로 직접 삭제
            import chromadb
            client = chromadb.PersistentClient(path="data/chroma_db")
            
            collections = client.list_collections()
            deleted_count = 0
            
            for collection in collections:
                try:
                    client.delete_collection(name=collection.name)
                    print(f"  ✅ '{collection.name}' 삭제 완료")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ '{collection.name}' 삭제 실패: {e}")
            
            print(f"✅ 데이터베이스 초기화 완료! ({deleted_count}개 컬렉션 삭제)")
            
            # 에이전트 상태 초기화
            self.conversation_agent = None
            self.regulation_agent = None
            self.consultation_agent = None
            self.query_router = None
            self.conversation_vector_store = None
            self.general_vector_store = None
            
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 실패: {e}")
    
    def settings_menu(self):
        """설정 메뉴"""
        print("\n⚙️ 설정 메뉴는 향후 추가될 예정입니다.")
        input("✅ 계속하려면 Enter를 누르세요...")
    
    def run(self):
        """메인 실행 루프"""
        print("\n🎮 통합 무역 정보 상담 시스템에 오신 것을 환영합니다!")
        print("💡 관세법 법률 정보와 실용적 무역 정보를 모두 제공합니다.")
        
        # 환경 변수 확인
        if not os.getenv("OPENAI_API_KEY"):
            print("\n❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            print("   .env 파일을 확인하거나 환경 변수를 설정해주세요.")
            return
        
        while True:
            try:
                self.display_main_menu()
                choice = self.get_user_choice("메뉴 선택", ["0", "1", "2", "3", "4", "5", "6"])
                
                if choice == "0":
                    print("\n👋 시스템을 종료합니다.")
                    break
                
                elif choice == "1":
                    self.conversation_agent_chat()
                
                elif choice == "2":
                    self.dual_agent_chat()
                
                elif choice == "3":
                    self.langgraph_orchestration_chat()
                
                elif choice == "4":
                    self.database_management_menu()
                
                elif choice == "5":
                    self.show_database_status()
                
                elif choice == "6":
                    self.settings_menu()
                
            except KeyboardInterrupt:
                print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                logger.error(f"Main loop error: {e}")
                input("계속하려면 Enter를 누르세요...")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="통합 무역 정보 상담 시스템 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python -m src.rag.unified_cli                    # 통합 시스템 시작
  python -m src.rag.unified_cli --agent law        # 관세법 에이전트 직접 시작
  python -m src.rag.unified_cli --agent trade      # 듀얼 AI 시스템 직접 시작
        """
    )
    
    parser.add_argument(
        "--agent",
        choices=["law", "trade"],
        help="특정 에이전트로 바로 시작 (law: 관세법 RAG, trade: 듀얼 AI 시스템)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # CLI 인스턴스 생성
    cli = UnifiedTradeInfoCLI()
    
    # 특정 에이전트로 바로 시작
    if args.agent == "law":
        print("🚀 관세법 RAG 에이전트로 바로 시작합니다...")
        cli.conversation_agent_chat()
    elif args.agent == "trade":
        print("🚀 듀얼 에이전트 시스템으로 바로 시작합니다...")
        cli.dual_agent_chat()
    else:
        # 통합 메뉴 시작
        cli.run()


if __name__ == "__main__":
    main()