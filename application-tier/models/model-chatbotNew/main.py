#!/usr/bin/env python3
"""
Main Entry Point for Korean Trade Information System

관세법 RAG 시스템과 일반 무역 정보 시스템을 통합한 멀티 에이전트 챗봇
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
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiAgentChatbot:
    """멀티 에이전트 챗봇 메인 클래스"""
    
    def __init__(self):
        """챗봇 초기화"""
        self.orchestrator = None
        self.orchestrator_factory = None
        
        # 개별 에이전트 참조 (직접 접근용)
        self.customs_law_agent = None
        self.regulations_agent = None
        self.complaints_agent = None
        
        # 공통 구성요소
        self.embedder = None
        self.law_vector_store = None
        self.trade_vector_store = None
        
        print("🚀 한국 무역 정보 멀티 에이전트 챗봇")
        print("=" * 60)
    
    def display_main_menu(self):
        """메인 메뉴 출력"""
        print("\n" + "="*60)
        print("🏠 멀티 에이전트 챗봇 메인 메뉴")
        print("="*60)
        print("1. 🤖 통합 멀티 에이전트 시스템 (지능형 라우팅)")
        print("2. 🏛️ 관세법 조문 전문가 (직접 접근)")
        print("3. ⚖️ 무역 규제 전문가 (직접 접근)")
        print("4. 💼 실무 상담 전문가 (직접 접근)")
        print("5. 🗄️ 데이터베이스 관리")
        print("6. 📊 시스템 상태 확인")
        print("7. ⚙️ 설정")
        print("0. 🚪 종료")
        print("-" * 60)
    
    def get_user_choice(self, prompt: str = "선택", valid_options: Optional[List[str]] = None) -> str:
        """사용자 입력 받기"""
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
    
    def initialize_orchestrated_system(self) -> bool:
        """통합 멀티 에이전트 시스템 초기화"""
        try:
            if self.orchestrator:
                return True
            
            print("🔧 통합 멀티 에이전트 시스템 초기화 중...")
            
            # 환경 변수 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                return False
            
            # 오케스트레이터 팩토리 임포트 및 초기화
            from src.orchestrator.orchestrator import get_orchestrator_factory, create_orchestrated_system
            from src.config.config import get_quality_thresholds
            thresholds = get_quality_thresholds()
            
            print("  - 오케스트레이터 팩토리 초기화...")
            self.orchestrator_factory = get_orchestrator_factory()
            
            print("  - 멀티 에이전트 오케스트레이션 시스템 구성...")
            self.orchestrator = create_orchestrated_system(
                model_name="gpt-4.1-mini",
                temperature=thresholds["model_temperature"],
                use_intelligent_routing=True
            )
            
            print("✅ 통합 멀티 에이전트 시스템 초기화 완료!")
            print("  🧠 지능형 라우팅: LangGraph 기반 자동 분석")
            print("  🏛️ 관세법 에이전트: 법령 조문 전문")
            print("  ⚖️ 규제 에이전트: 무역 규제 및 동식물 검역 전문")
            print("  💼 상담 에이전트: 실무 민원상담 사례 전문")
            print("  🤝 복합 워크플로우: 멀티 에이전트 협업")
            return True
            
        except Exception as e:
            print(f"❌ 멀티 에이전트 시스템 초기화 실패: {e}")
            logger.error(f"Multi-agent system initialization failed: {e}")
            return False
    
    def initialize_individual_agent(self, agent_type: str) -> bool:
        """개별 에이전트 초기화"""
        try:
            print(f"🔧 {agent_type} 에이전트 초기화 중...")
            
            # 환경 변수 확인
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                return False
            
            if agent_type == "customs_law":
                if not self.customs_law_agent:
                    from src.agents.customs_law_agent import CustomsLawAgent
                    from src.config.config import get_quality_thresholds
                    thresholds = get_quality_thresholds()
                    
                    self.customs_law_agent = CustomsLawAgent(
                        model_name="gpt-4.1-mini",
                        temperature=thresholds["model_temperature"],
                        max_context_docs=5,
                        similarity_threshold=thresholds["similarity_threshold"]
                    )
                    print("✅ 관세법 조문 전문가 초기화 완료!")
                
            elif agent_type == "regulations":
                if not self.regulations_agent:
                    from src.agents.regulations_agent import RegulationsAgent
                    from src.config.config import get_quality_thresholds
                    thresholds = get_quality_thresholds()
                    
                    self.regulations_agent = RegulationsAgent(
                        model_name="gpt-4.1-mini",
                        temperature=thresholds["regulation_temperature"],
                        max_context_docs=8,
                        similarity_threshold=thresholds["similarity_threshold"]
                    )
                    print("✅ 무역 규제 전문가 초기화 완료!")
                
            elif agent_type == "complaints":
                if not self.complaints_agent:
                    from src.agents.complaints_agent import ComplaintsAgent
                    from src.config.config import get_quality_thresholds
                    thresholds = get_quality_thresholds()
                    
                    self.complaints_agent = ComplaintsAgent(
                        model_name="gpt-4.1-mini",
                        temperature=thresholds["consultation_temperature"],
                        max_context_docs=8,
                        similarity_threshold=thresholds["similarity_threshold"]
                    )
                    print("✅ 실무 상담 전문가 초기화 완료!")
            
            return True
            
        except Exception as e:
            print(f"❌ {agent_type} 에이전트 초기화 실패: {e}")
            logger.error(f"{agent_type} agent initialization failed: {e}")
            return False
    
    def orchestrated_chat(self):
        """통합 멀티 에이전트 대화 모드"""
        if not self.initialize_orchestrated_system():
            return
        
        # 데이터베이스 상태 확인
        try:
            if not self.orchestrator_factory:
                print("⚠️ 오케스트레이터가 초기화되지 않았습니다.")
                print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
                return
                
            stats = self.orchestrator_factory.get_agent_stats()
            if not stats.get("orchestrator_available", False):
                print("⚠️ 오케스트레이터가 초기화되지 않았습니다.")
                print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
                return
                
        except Exception as e:
            print(f"⚠️ 시스템 상태 확인 실패: {e}")
            print("   데이터베이스 관리 메뉴에서 데이터를 먼저 로드해주세요.")
            return
        
        print("\n💬 멀티 에이전트 챗봇 시작! (지능형 라우팅)")
        print("🤖 시스템이 질의를 분석하여 최적의 전문 에이전트로 자동 연결합니다.")
        print("  🏛️ 관세법 에이전트: 정확한 법령 조문 정보")
        print("  ⚖️ 규제 에이전트: 무역 규제 및 동식물 검역 정보")
        print("  💼 상담 에이전트: 실용적 업무 가이드 및 민원상담 사례")
        print("\n종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.")
        print("대화 기록을 초기화하려면 'reset'을 입력하세요.")
        print("라우팅 통계를 보려면 'stats'를 입력하세요.")
        print("=" * 60)
        
        routing_statistics = {
            "total_queries": 0,
            "agent_usage": {"customs_law_agent": 0, "regulations_agent": 0, "complaints_agent": 0},
            "avg_complexity": 0.0,
            "complex_queries": 0
        }
        
        while True:
            try:
                # 사용자 입력
                user_input = input("\n❓ 무역 정보 질문: ").strip()
                
                # 종료 명령어 확인
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 멀티 에이전트 챗봇을 종료합니다.")
                    break
                
                # 초기화 명령어 확인
                if user_input.lower() == 'reset':
                    # 개별 에이전트들의 대화 기록 초기화
                    try:
                        if self.orchestrator and hasattr(self.orchestrator, 'customs_law_agent') and self.orchestrator.customs_law_agent:
                            self.orchestrator.customs_law_agent.reset_conversation()
                        if self.orchestrator and hasattr(self.orchestrator, 'regulations_agent') and self.orchestrator.regulations_agent:
                            self.orchestrator.regulations_agent.reset_conversation()
                        if self.orchestrator and hasattr(self.orchestrator, 'complaints_agent') and self.orchestrator.complaints_agent:
                            self.orchestrator.complaints_agent.reset_conversation()
                    except:
                        pass
                    
                    routing_statistics = {
                        "total_queries": 0,
                        "agent_usage": {"customs_law_agent": 0, "regulations_agent": 0, "complaints_agent": 0},
                        "avg_complexity": 0.0,
                        "complex_queries": 0
                    }
                    print("🔄 모든 에이전트의 대화 기록과 통계가 초기화되었습니다.")
                    continue
                
                # 통계 명령어 확인
                if user_input.lower() == 'stats':
                    self._display_routing_stats(routing_statistics)
                    continue
                
                # 빈 입력 무시
                if not user_input:
                    continue
                
                # 오케스트레이터 실행
                print("\n🧠 지능형 라우팅 분석 중...")
                if not self.orchestrator:
                    print("❌ 오케스트레이터가 초기화되지 않았습니다.")
                    continue
                    
                result = self.orchestrator.process_query(user_input)
                
                if result.get("error"):
                    print(f"❌ 오류 발생: {result['error']}")
                    continue
                
                # 라우팅 정보 표시
                agent_used = result.get("agent_used", "unknown")
                complexity = result.get("complexity", 0.0)
                
                # 에이전트 아이콘 매핑
                agent_icons = {
                    "customs_law_agent": "🏛️ 관세법 전문가",
                    "regulations_agent": "⚖️ 규제 전문가",
                    "complaints_agent": "💼 상담 전문가"
                }
                
                agent_display = agent_icons.get(agent_used, f"🤖 {agent_used}")
                if complexity > 0:
                    complexity_level = "복합" if complexity > 0.7 else "보통" if complexity > 0.4 else "단순"
                    print(f"🔍 {agent_display}로 연결 (복잡도: {complexity:.2f} - {complexity_level})")
                else:
                    print(f"🔍 {agent_display}로 연결")
                
                # 라우팅 정보 표시
                routing_info = result.get("routing_info", {})
                if isinstance(routing_info, list) and routing_info:
                    latest_routing = routing_info[-1]
                    reasoning = latest_routing.get("reasoning", "")
                    if reasoning:
                        print(f"📝 분석: {reasoning}")
                elif isinstance(routing_info, dict):
                    reason = routing_info.get("reason", "")
                    if reason:
                        print(f"📝 라우팅 이유: {reason}")
                
                # 통계 업데이트
                routing_statistics["total_queries"] += 1
                if agent_used in routing_statistics["agent_usage"]:
                    routing_statistics["agent_usage"][agent_used] += 1
                
                if complexity > 0:
                    # 평균 복잡도 계산
                    prev_avg = routing_statistics["avg_complexity"]
                    total = routing_statistics["total_queries"]
                    routing_statistics["avg_complexity"] = (prev_avg * (total - 1) + complexity) / total
                    
                    if complexity > 0.7:
                        routing_statistics["complex_queries"] += 1
                
                # 응답 출력
                response = result.get("response", "응답을 생성할 수 없습니다.")
                print(f"\n🤖 {agent_display}:")
                print("-" * 50)
                print(response)
                
                # 참조 문서 정보 출력
                docs = result.get("docs", [])
                if docs:
                    print(f"\n📚 참조 정보 ({len(docs)}개):")
                    for i, doc in enumerate(docs[:5], 1):  # 상위 5개만 표시
                        metadata = doc.get("metadata", {})
                        similarity = doc.get("similarity", 0)
                        
                        # 에이전트별 맞춤 정보 표시
                        if agent_used == "customs_law_agent":
                            index = doc.get("index", "")
                            subtitle = doc.get("subtitle", "")
                            law_name = metadata.get("law_name", "")
                            display_text = f"{index} {subtitle} - {law_name}" if index else subtitle or "조문 정보"
                        
                        elif agent_used == "regulations_agent":
                            if metadata.get("data_source") == "동식물허용금지지역":
                                product_name = metadata.get("product_name", "")
                                allowed_countries = metadata.get("allowed_countries", [])
                                if isinstance(allowed_countries, str):
                                    try:
                                        allowed_countries = json.loads(allowed_countries)
                                    except:
                                        allowed_countries = [allowed_countries]
                                allowed_text = f"허용: {', '.join(allowed_countries[:2])}" if allowed_countries else ""
                                display_text = f"{product_name} - {allowed_text} 🐕🌱"
                            else:
                                title = doc.get("title", "")
                                hs_code = metadata.get("hs_code", "")
                                display_text = f"{title} (HS: {hs_code})" if hs_code else title
                        
                        else:  # complaints_agent
                            title = metadata.get("sub_title", "") or doc.get("title", "")
                            category = metadata.get("category", "")
                            display_text = f"{title} - {category}" if category else title
                        
                        boost_info = " 🎯" if doc.get("boosted") or doc.get("importance_score", 0) > 0.5 else ""
                        print(f"  {i}. {display_text[:80]}{boost_info} - 유사도: {similarity:.3f}")
                
            except KeyboardInterrupt:
                print("\n\n👋 멀티 에이전트 챗봇을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                logger.error(f"Orchestrated chat error: {e}")
    
    def individual_agent_chat(self, agent_type: str):
        """개별 에이전트 대화 모드"""
        if not self.initialize_individual_agent(agent_type):
            return
        
        # 에이전트별 설정
        agent_configs = {
            "customs_law": {
                "agent": self.customs_law_agent,
                "name": "관세법 조문 전문가",
                "icon": "🏛️",
                "method": "query_law",
                "description": "정확한 법령 조문 정보"
            },
            "regulations": {
                "agent": self.regulations_agent,
                "name": "무역 규제 전문가", 
                "icon": "⚖️",
                "method": "query_regulation",
                "description": "무역 규제 및 동식물 검역 정보"
            },
            "complaints": {
                "agent": self.complaints_agent,
                "name": "실무 상담 전문가",
                "icon": "💼", 
                "method": "query_consultation",
                "description": "실무 민원상담 사례 기반 안내"
            }
        }
        
        config = agent_configs.get(agent_type)
        if not config:
            print(f"❌ 알 수 없는 에이전트 타입: {agent_type}")
            return
        
        agent = config["agent"]
        if not agent:
            print(f"❌ {config['name']} 초기화 실패")
            return
        
        print(f"\n💬 {config['icon']} {config['name']} 대화 시작!")
        print(f"📋 {config['description']}")
        print("종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.")
        print("대화 기록을 초기화하려면 'reset'을 입력하세요.")
        print("=" * 60)
        
        while True:
            try:
                # 사용자 입력
                user_input = input(f"\n❓ {config['name']} 질문: ").strip()
                
                # 종료 명령어 확인
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"👋 {config['name']} 상담을 종료합니다.")
                    break
                
                # 초기화 명령어 확인
                if user_input.lower() == 'reset':
                    if hasattr(agent, 'reset_conversation'):
                        agent.reset_conversation()
                    print("🔄 대화 기록이 초기화되었습니다.")
                    continue
                
                # 빈 입력 무시
                if not user_input:
                    continue
                
                # 응답 생성
                print("\n🤔 답변 생성 중...")
                method_name = config["method"]
                if hasattr(agent, method_name):
                    method = getattr(agent, method_name)
                    response, docs = method(user_input)
                else:
                    print(f"❌ {config['name']} 질의 처리 기능을 사용할 수 없습니다.")
                    continue
                
                # 응답 출력
                print(f"\n{config['icon']} {config['name']}:")
                print("-" * 50)
                print(response)
                
                # 참조 문서 정보 출력
                if docs:
                    print(f"\n📚 참조 정보 ({len(docs)}개):")
                    for i, doc in enumerate(docs[:5], 1):
                        metadata = doc.get("metadata", {})
                        similarity = doc.get("similarity", 0)
                        
                        # 에이전트별 정보 포맷팅
                        if agent_type == "customs_law":
                            index = doc.get("index", "")
                            subtitle = doc.get("subtitle", "")
                            law_name = metadata.get("law_name", "")
                            display_text = f"{index} {subtitle} - {law_name}" if index else subtitle or "조문 정보"
                        
                        elif agent_type == "regulations":
                            if metadata.get("data_source") == "동식물허용금지지역":
                                product_name = metadata.get("product_name", "")
                                display_text = f"{product_name} 동식물 검역 정보"
                            else:
                                title = doc.get("title", "")
                                hs_code = metadata.get("hs_code", "")
                                display_text = f"{title} (HS: {hs_code})" if hs_code else title
                        
                        else:  # complaints
                            title = metadata.get("sub_title", "") or doc.get("title", "")
                            category = metadata.get("category", "")
                            display_text = f"{title} - {category}" if category else title
                        
                        boost_info = " 🎯" if (doc.get("boosted") or doc.get("importance_score", 0) > 0.5) else ""
                        print(f"  {i}. {display_text[:80]}{boost_info} - 유사도: {similarity:.3f}")
                
            except KeyboardInterrupt:
                print(f"\n\n👋 {config['name']} 상담을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                logger.error(f"Individual agent chat error: {e}")
    
    def _display_routing_stats(self, stats):
        """라우팅 통계 표시"""
        print(f"\n📊 멀티 에이전트 라우팅 통계")
        print("-" * 40)
        print(f"총 질의 수: {stats['total_queries']}")
        if stats['total_queries'] > 0:
            print(f"평균 복잡도: {stats['avg_complexity']:.2f}")
            print(f"복합 질의: {stats['complex_queries']} ({stats['complex_queries']/stats['total_queries']*100:.1f}%)")
        
        print(f"\n에이전트 사용 빈도:")
        for agent, count in stats['agent_usage'].items():
            percentage = count / max(stats['total_queries'], 1) * 100
            agent_name = {
                "customs_law_agent": "🏛️ 관세법 에이전트",
                "regulations_agent": "⚖️ 규제 에이전트", 
                "complaints_agent": "💼 상담 에이전트"
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
            
            # 임베딩 및 벡터 저장소 초기화
            if not self.embedder:
                from src.utils.embeddings import LangChainEmbedder
                self.embedder = LangChainEmbedder()
            
            if not self.law_vector_store:
                from src.utils.db_connect import LangChainVectorStore
                self.law_vector_store = LangChainVectorStore(
                    collection_name="law_collection",
                    embedding_function=self.embedder.embeddings,
                    use_docker_chromadb=True,
                    chromadb_host="localhost",
                    chromadb_port=8011
                )
            
            # 데이터 처리기 임포트 및 초기화
            # Use the existing law agent's data processing capabilities
            from src.agents.customs_law_agent import CustomsLawAgent
            from src.config.config import get_quality_thresholds
            thresholds = get_quality_thresholds()
            
            # Initialize law agent for data processing
            law_agent = CustomsLawAgent(
                embedder=self.embedder,
                vector_store=self.law_vector_store,
                similarity_threshold=thresholds["similarity_threshold"]
            )
            
            # 기존 데이터 확인
            stats = self.law_vector_store.get_collection_stats()
            
            if stats.get("total_documents", 0) > 0:
                print(f"ℹ️ 기존 데이터 발견: {stats['total_documents']}개 문서")
                confirm = self.get_user_choice("기존 데이터를 재설정하시겠습니까? (y/N)", ["y", "Y", "n", "N", ""])
                
                if confirm.lower() != "y":
                    print("기존 데이터를 사용합니다.")
                    return
                
                # 기존 데이터 재설정
                print("🗑️ 기존 데이터 삭제 중...")
                self.law_vector_store.create_collection(reset=True)
            
            # 관세법 JSON 데이터 로드
            print("📄 관세법 JSON 데이터 읽는 중...")
            import json
            from src.config.config import get_chunked_data_paths
            
            data_paths = get_chunked_data_paths()
            total_docs = []
            
            for law_name, path in data_paths.items():
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        docs = json.load(f)
                    total_docs.extend(docs)
                    print(f"  ✅ {law_name}: {len(docs)}개 문서")
                else:
                    print(f"  ⚠️ {law_name}: 파일 없음 - {path}")
            
            if total_docs:
                print(f"📝 총 {len(total_docs)}개 관세법 문서 벡터화 중...")
                print("⚡ 배치 처리로 토큰 제한을 피하여 안전하게 로드합니다...")
                doc_ids = self.law_vector_store.add_documents(total_docs, batch_size=100)
                print(f"✅ {len(doc_ids)}개 관세법 문서 로드 완료!")
                
                # 최종 상태 확인
                final_stats = self.law_vector_store.get_collection_stats()
                print(f"📊 최종 상태: {final_stats['total_documents']}개 문서")
            else:
                print("❌ 로드할 관세법 데이터를 찾을 수 없습니다.")
            
            print("✅ 관세법 데이터 로드 완료!")
                
        except Exception as e:
            print(f"❌ 관세법 데이터 로드 중 오류: {e}")
            logger.error(f"Customs law data loading failed: {e}")
    
    def load_trade_info_data(self):
        """무역 정보 데이터 로드"""
        try:
            print("\n🌐 무역 정보 데이터 로드 시작...")
            
            # 임베딩 및 벡터 저장소 초기화
            if not self.embedder:
                from src.utils.embeddings import LangChainEmbedder
                self.embedder = LangChainEmbedder()
            
            if not self.trade_vector_store:
                from src.utils.db_connect import LangChainVectorStore
                self.trade_vector_store = LangChainVectorStore(
                    collection_name="trade_info_collection",
                    embedding_function=self.embedder.embeddings,
                    use_docker_chromadb=True,
                    chromadb_host="localhost",
                    chromadb_port=8011
                )
            
            # 기존 데이터 확인
            stats = self.trade_vector_store.get_collection_stats()
            
            if stats.get("total_documents", 0) > 0:
                print(f"ℹ️ 기존 데이터 발견: {stats['total_documents']}개 문서")
                confirm = self.get_user_choice("기존 데이터를 재로드하시겠습니까? (y/N)", ["y", "Y", "n", "N", ""])
                
                if confirm.lower() != "y":
                    print("기존 데이터를 사용합니다.")
                    return
                
                # 기존 데이터 재설정
                print("🗑️ 기존 데이터 삭제 중...")
                self.trade_vector_store.create_collection(reset=True)
            
            # 무역정보 JSON/CSV 데이터 로드
            print("📄 무역정보 데이터 읽는 중...")
            import json
            from src.config.config import get_csv_output_paths, get_consultation_case_paths
            
            total_docs = []
            
            # CSV 기반 무역 데이터
            csv_paths = get_csv_output_paths()
            for data_name, path in csv_paths.items():
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        docs = json.load(f)
                    total_docs.extend(docs)
                    print(f"  ✅ {data_name}: {len(docs)}개 문서")
                else:
                    print(f"  ⚠️ {data_name}: 파일 없음 - {path}")
            
            # 민원상담 사례집
            consultation_paths = get_consultation_case_paths()
            consultation_path = consultation_paths.get("output_json")
            if consultation_path and consultation_path.exists():
                with open(consultation_path, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                total_docs.extend(docs)
                print(f"  ✅ 민원상담사례집: {len(docs)}개 문서")
            else:
                print(f"  ⚠️ 민원상담사례집: 파일 없음 - {consultation_path}")
            
            if total_docs:
                print(f"📝 총 {len(total_docs)}개 무역정보 문서 벡터화 중...")
                print("⚡ 배치 처리로 토큰 제한을 피하여 안전하게 로드합니다...")
                doc_ids = self.trade_vector_store.add_documents(total_docs, batch_size=100)
                print(f"✅ {len(doc_ids)}개 무역정보 문서 로드 완료!")
                
                # 최종 상태 확인
                final_stats = self.trade_vector_store.get_collection_stats()
                print(f"📊 최종 상태: {final_stats['total_documents']}개 문서")
            else:
                print("❌ 로드할 무역정보 데이터를 찾을 수 없습니다.")
            
            print("✅ 무역정보 데이터 로드 완료!")
            
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
            if not self.law_vector_store:
                from src.utils.db_connect import LangChainVectorStore
                from src.utils.embeddings import LangChainEmbedder
                embedder = LangChainEmbedder()
                self.law_vector_store = LangChainVectorStore(
                    collection_name="law_collection",
                    embedding_function=embedder.embeddings,
                    use_docker_chromadb=True,
                    chromadb_host="localhost",
                    chromadb_port=8011
                )
            
            stats = self.law_vector_store.get_collection_stats()
            if "error" in stats:
                print("  ❌ 연결 실패 또는 데이터 없음")
                print(f"  🔧 Docker ChromaDB 상태를 확인해주세요 (localhost:8011)")
            else:
                print(f"  ✅ 총 문서 수: {stats.get('total_documents', 0):,}개")
                print(f"  📂 컬렉션명: {stats.get('collection_name', 'N/A')}")
                print(f"  🐳 Docker ChromaDB 연결: localhost:8011")
        except Exception as e:
            print(f"  ❌ 상태 확인 실패: {e}")
            print(f"  🔧 Docker ChromaDB 컨테이너가 실행 중인지 확인해주세요")
        
        # 무역 정보 데이터베이스 상태
        print("\n🌐 무역 정보 데이터베이스:")
        try:
            if not self.trade_vector_store:
                from src.utils.db_connect import LangChainVectorStore
                from src.utils.embeddings import LangChainEmbedder
                embedder = LangChainEmbedder()
                self.trade_vector_store = LangChainVectorStore(
                    collection_name="trade_info_collection",
                    embedding_function=embedder.embeddings,
                    use_docker_chromadb=True,
                    chromadb_host="localhost",
                    chromadb_port=8011
                )
            
            stats = self.trade_vector_store.get_collection_stats()
            if "error" in stats:
                print("  ❌ 연결 실패 또는 데이터 없음")
                print(f"  🔧 Docker ChromaDB 상태를 확인해주세요 (localhost:8011)")
            else:
                print(f"  ✅ 총 문서 수: {stats.get('total_documents', 0):,}개")
                print(f"  📂 컬렉션명: {stats.get('collection_name', 'N/A')}")
                print(f"  🐳 Docker ChromaDB 연결: localhost:8011")
        except Exception as e:
            print(f"  ❌ 상태 확인 실패: {e}")
            print(f"  🔧 Docker ChromaDB 컨테이너가 실행 중인지 확인해주세요")
        
        input("\n✅ 계속하려면 Enter를 누르세요...")
    
    def reset_databases(self):
        """데이터베이스 초기화"""
        print("\n⚠️ 데이터베이스 초기화")
        print("이 작업은 Docker ChromaDB의 모든 벡터 데이터를 삭제합니다!")
        
        confirm1 = self.get_user_choice("정말로 초기화하시겠습니까? (yes/no)", ["yes", "no"])
        if confirm1 != "yes":
            print("❌ 취소되었습니다.")
            return
        
        confirm2 = self.get_user_choice("마지막 확인: 'DELETE'를 입력해주세요")
        if confirm2 != "DELETE":
            print("❌ 취소되었습니다.")
            return
        
        try:
            # Docker ChromaDB 클라이언트로 직접 삭제
            import chromadb
            client = chromadb.HttpClient(host="localhost", port=8011)
            
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
            print("🐳 Docker ChromaDB (localhost:8011)에서 삭제됨")
            
            # 에이전트 상태 초기화
            self.orchestrator = None
            self.customs_law_agent = None
            self.regulations_agent = None
            self.complaints_agent = None
            self.law_vector_store = None
            self.trade_vector_store = None
            
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 실패: {e}")
            print("🔧 Docker ChromaDB 컨테이너가 실행 중인지 확인해주세요")
    
    def settings_menu(self):
        """설정 메뉴"""
        print("\n⚙️ 설정 메뉴는 향후 추가될 예정입니다.")
        input("✅ 계속하려면 Enter를 누르세요...")
    
    def run(self):
        """메인 실행 루프"""
        print("\n🎮 멀티 에이전트 챗봇에 오신 것을 환영합니다!")
        print("💡 관세법 법률 정보와 실용적 무역 정보를 모두 제공합니다.")
        
        # 환경 변수 확인
        if not os.getenv("OPENAI_API_KEY"):
            print("\n❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            print("   .env 파일을 확인하거나 환경 변수를 설정해주세요.")
            return
        
        while True:
            try:
                self.display_main_menu()
                choice = self.get_user_choice("메뉴 선택", ["0", "1", "2", "3", "4", "5", "6", "7"])
                
                if choice == "0":
                    print("\n👋 시스템을 종료합니다.")
                    break
                
                elif choice == "1":
                    self.orchestrated_chat()
                
                elif choice == "2":
                    self.individual_agent_chat("customs_law")
                
                elif choice == "3":
                    self.individual_agent_chat("regulations")
                
                elif choice == "4":
                    self.individual_agent_chat("complaints")
                
                elif choice == "5":
                    self.database_management_menu()
                
                elif choice == "6":
                    self.show_database_status()
                
                elif choice == "7":
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
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="한국 무역 정보 멀티 에이전트 챗봇",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py                              # 통합 시스템 시작
  python main.py --agent customs_law          # 관세법 에이전트 직접 시작
  python main.py --agent regulations          # 규제 에이전트 직접 시작
  python main.py --agent complaints           # 상담 에이전트 직접 시작
        """
    )
    
    parser.add_argument(
        "--agent",
        choices=["customs_law", "regulations", "complaints"],
        help="특정 에이전트로 바로 시작"
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
    
    # 챗봇 인스턴스 생성
    chatbot = MultiAgentChatbot()
    
    # 특정 에이전트로 바로 시작
    if args.agent:
        agent_names = {
            "customs_law": "관세법 조문 전문가",
            "regulations": "무역 규제 전문가",
            "complaints": "실무 상담 전문가"
        }
        print(f"🚀 {agent_names[args.agent]}로 바로 시작합니다...")
        chatbot.individual_agent_chat(args.agent)
    else:
        # 통합 메뉴 시작
        chatbot.run()


if __name__ == "__main__":
    main()