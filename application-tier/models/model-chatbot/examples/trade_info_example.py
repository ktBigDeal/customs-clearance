#!/usr/bin/env python3
"""
무역 정보 일반 상담 에이전트 사용 예제

이 예제는 CSV 데이터를 기반으로 한 일반 무역 정보 상담 시스템의 사용법을 보여줍니다.
법률 자문이 아닌 실용적인 무역 정보와 가이드라인을 제공합니다.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from src.utils.config import load_config, get_csv_data_paths, get_trade_agent_config
    from src.data_processing.trade_info_csv_loader import CSVDocumentLoader
    from src.rag.embeddings import OpenAIEmbedder
    from src.rag.vector_store import ChromaVectorStore
    from src.rag.query_normalizer import TradeQueryNormalizer
    from src.rag.trade_info_retriever import TradeInfoRetriever
    from src.rag.trade_info_agent import GeneralInfoAgent
    from src.rag.law_data_processor import RAGDataProcessor
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("프로젝트 루트에서 실행했는지 확인해주세요.")
    sys.exit(1)


class TradeInfoSystem:
    """무역 정보 시스템 전체 래퍼 클래스"""
    
    def __init__(self):
        """시스템 초기화"""
        self.config = None
        self.embedder = None
        self.vector_store = None
        self.query_normalizer = None
        self.retriever = None
        self.agent = None
        self.data_processor = None
        
        print("🚀 무역 정보 시스템 초기화 중...")
        self._initialize_system()
    
    def _initialize_system(self):
        """시스템 컴포넌트 초기화"""
        try:
            # 1. 환경 설정 로드
            print("📋 환경 설정 로드 중...")
            self.config = load_config()
            trade_config = get_trade_agent_config()
            
            # 2. 임베딩 엔진 초기화
            print("🔧 임베딩 엔진 초기화 중...")
            self.embedder = OpenAIEmbedder()
            
            # 3. 벡터 저장소 초기화
            print("🗄️ 벡터 저장소 초기화 중...")
            self.vector_store = ChromaVectorStore(
                collection_name=trade_config["collection_name"]
            )
            
            # 4. 쿼리 정규화기 초기화
            print("🔍 쿼리 정규화기 초기화 중...")
            self.query_normalizer = TradeQueryNormalizer()
            
            # 5. 검색기 초기화
            print("📊 무역 정보 검색기 초기화 중...")
            self.retriever = TradeInfoRetriever(
                embedder=self.embedder,
                vector_store=self.vector_store,
                query_normalizer=self.query_normalizer,
                collection_name=trade_config["collection_name"]
            )
            
            # 6. 일반 정보 에이전트 초기화
            print("🤖 일반 정보 에이전트 초기화 중...")
            self.agent = GeneralInfoAgent(
                retriever=self.retriever,
                model_name=trade_config["model_name"],
                temperature=trade_config["temperature"],
                max_context_docs=trade_config["max_context_docs"],
                similarity_threshold=trade_config["similarity_threshold"]
            )
            
            # 7. 데이터 처리기 초기화 (선택적)
            print("📈 데이터 처리기 초기화 중...")
            self.data_processor = RAGDataProcessor(
                embedder=self.embedder,
                vector_store=self.vector_store
            )
            
            print("✅ 무역 정보 시스템 초기화 완료!")
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            raise
    
    def load_csv_data(self, force_reload: bool = False) -> bool:
        """CSV 데이터 로드 및 벡터 저장소에 추가"""
        try:
            # 기존 데이터 확인
            stats = self.vector_store.get_collection_stats()
            if stats.get("total_documents", 0) > 0 and not force_reload:
                print(f"ℹ️ 기존 데이터 발견: {stats['total_documents']}개 문서")
                print("기존 데이터를 사용합니다. 새로 로드하려면 force_reload=True를 사용하세요.")
                return True
            
            print("📁 CSV 데이터 로드 중...")
            csv_paths = get_csv_data_paths()
            all_documents = []
            
            for csv_name, csv_path in csv_paths.items():
                if not csv_path.exists():
                    print(f"⚠️ {csv_name} 파일 없음: {csv_path}")
                    continue
                
                print(f"📄 {csv_name} 처리 중...")
                try:
                    loader = CSVDocumentLoader(str(csv_path))
                    documents = loader.load()
                    
                    if documents:
                        # 임베딩 생성
                        print(f"🔧 {csv_name} 임베딩 생성 중... ({len(documents)}개 문서)")
                        documents_with_embeddings = self.data_processor.process_documents(documents)
                        all_documents.extend(documents_with_embeddings)
                        print(f"✅ {csv_name} 완료: {len(documents)}개 문서 처리")
                    else:
                        print(f"⚠️ {csv_name} 처리 결과 없음")
                        
                except Exception as e:
                    print(f"❌ {csv_name} 처리 실패: {e}")
                    continue
            
            if all_documents:
                # 벡터 저장소에 추가
                print(f"💾 벡터 저장소에 {len(all_documents)}개 문서 저장 중...")
                if force_reload:
                    self.vector_store.create_collection(reset=True)
                else:
                    self.vector_store.create_collection()
                
                self.vector_store.add_documents(all_documents)
                print("✅ 데이터 로드 완료!")
                return True
            else:
                print("❌ 처리된 문서가 없습니다.")
                return False
                
        except Exception as e:
            logger.error(f"CSV 데이터 로드 실패: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            retriever_stats = self.retriever.get_statistics()
            
            return {
                "system_initialized": all([
                    self.embedder, self.vector_store, self.retriever, self.agent
                ]),
                "vector_store": vector_stats,
                "retriever": retriever_stats,
                "agent_model": self.agent.model_name if self.agent else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, user_input: str, **kwargs) -> tuple:
        """사용자와 채팅"""
        return self.agent.chat(user_input, **kwargs)
    
    def search_info(self, query: str, **kwargs) -> List[Dict]:
        """정보 검색"""
        return self.retriever.search_trade_info(query, **kwargs)


def demonstrate_basic_usage():
    """기본 사용법 시연"""
    print("\n" + "="*60)
    print("🎯 기본 사용법 시연")
    print("="*60)
    
    try:
        # 시스템 초기화
        system = TradeInfoSystem()
        
        # 데이터 로드
        if not system.load_csv_data():
            print("❌ 데이터 로드 실패")
            return
        
        # 시스템 상태 확인
        status = system.get_system_status()
        print(f"\n📊 시스템 상태:")
        print(f"  - 총 문서 수: {status['vector_store'].get('total_documents', 0)}")
        print(f"  - 에이전트 모델: {status['agent_model']}")
        
        # 샘플 질문들
        sample_questions = [
            "철강 제품의 수출 규제 현황을 알려주세요",
            "HS코드 7208 관련 무역 규제가 있나요?",
            "미국으로 수출할 때 주의해야 할 품목들을 알려주세요",
            "플라스틱 제품의 수입 제한이 있는지 확인해주세요"
        ]
        
        print("\n💬 샘플 질문 처리:")
        for i, question in enumerate(sample_questions, 1):
            print(f"\n--- 질문 {i} ---")
            print(f"🙋 사용자: {question}")
            
            try:
                response, docs = system.chat(question)
                print(f"🤖 AI: {response[:200]}{'...' if len(response) > 200 else ''}")
                print(f"📑 참조 문서: {len(docs)}개")
                
                # 처음 질문에서만 상세 정보 표시
                if i == 1 and docs:
                    print("\n참조 문서 상세:")
                    for j, doc in enumerate(docs[:2], 1):
                        metadata = doc.get("metadata", {})
                        print(f"  {j}. {doc.get('index', 'N/A')}")
                        if metadata.get('hs_code'):
                            print(f"     HS코드: {metadata.get('hs_code')}")
                        if metadata.get('country'):
                            print(f"     국가: {metadata.get('country')}")
                        if metadata.get('regulation_type'):
                            print(f"     규제유형: {metadata.get('regulation_type')}")
                
            except Exception as e:
                print(f"❌ 처리 실패: {e}")
        
        print("\n✅ 기본 사용법 시연 완료")
        
    except Exception as e:
        print(f"❌ 시연 실패: {e}")


def demonstrate_advanced_search():
    """고급 검색 기능 시연"""
    print("\n" + "="*60)
    print("🔍 고급 검색 기능 시연")
    print("="*60)
    
    try:
        system = TradeInfoSystem()
        
        # 데이터가 없으면 로드
        status = system.get_system_status()
        if status['vector_store'].get('total_documents', 0) == 0:
            print("📁 데이터 로드 중...")
            if not system.load_csv_data():
                print("❌ 데이터 로드 실패")
                return
        
        # 1. 국가별 검색
        print("\n1️⃣ 국가별 검색:")
        results = system.retriever.search_by_country("미국", top_k=3)
        print(f"미국 관련 규제: {len(results)}개 발견")
        for result in results[:2]:
            metadata = result.get("metadata", {})
            print(f"  - {result.get('index', 'N/A')}: {metadata.get('regulation_type', 'N/A')}")
        
        # 2. 제품 카테고리별 검색
        print("\n2️⃣ 제품 카테고리별 검색:")
        results = system.retriever.search_by_product_category("철강", top_k=3)
        print(f"철강 제품 관련: {len(results)}개 발견")
        for result in results[:2]:
            metadata = result.get("metadata", {})
            print(f"  - {result.get('index', 'N/A')}: {metadata.get('country', 'N/A')}")
        
        # 3. 필터링된 검색
        print("\n3️⃣ 필터링된 검색:")
        filters = {"country": "중국", "regulation_type": "반덤핑"}
        results = system.retriever.search_trade_info(
            "철강 제품",
            top_k=3,
            filter_by=filters
        )
        print(f"중국 반덤핑 규제: {len(results)}개 발견")
        
        # 4. HS코드 검색
        print("\n4️⃣ HS코드 검색:")
        results = system.search_info("7208 철강")
        print(f"HS코드 7208 관련: {len(results)}개 발견")
        
        print("\n✅ 고급 검색 기능 시연 완료")
        
    except Exception as e:
        print(f"❌ 고급 검색 시연 실패: {e}")


def demonstrate_conversation():
    """대화형 기능 시연"""
    print("\n" + "="*60)
    print("💬 대화형 기능 시연")
    print("="*60)
    
    try:
        system = TradeInfoSystem()
        
        # 데이터가 없으면 로드
        status = system.get_system_status()
        if status['vector_store'].get('total_documents', 0) == 0:
            print("📁 데이터 로드 중...")
            if not system.load_csv_data():
                print("❌ 데이터 로드 실패")
                return
        
        # 대화 시나리오
        conversation = [
            "철강 제품 수출시 주의사항을 알려주세요",
            "특히 미국 수출시에는 어떤 규제가 있나요?",
            "반덤핑 규제는 언제부터 시작되었나요?",
            "이런 규제를 피할 수 있는 방법이 있을까요?"
        ]
        
        print("📝 대화 시나리오:")
        for i, message in enumerate(conversation, 1):
            print(f"\n{i}. 🙋 사용자: {message}")
            
            try:
                response, docs = system.chat(message)
                print(f"   🤖 AI: {response[:300]}{'...' if len(response) > 300 else ''}")
                print(f"   📊 참조 문서: {len(docs)}개")
            except Exception as e:
                print(f"   ❌ 응답 실패: {e}")
        
        # 대화 요약
        print(f"\n📋 대화 요약:")
        try:
            summary = system.agent.get_conversation_summary()
            print(summary)
        except Exception as e:
            print(f"❌ 요약 생성 실패: {e}")
        
        print("\n✅ 대화형 기능 시연 완료")
        
    except Exception as e:
        print(f"❌ 대화형 시연 실패: {e}")


def main():
    """메인 함수"""
    print("🌟 무역 정보 일반 상담 에이전트 사용 예제")
    print("=" * 60)
    
    try:
        # 환경 확인
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            print("   .env 파일을 생성하고 API 키를 설정해주세요.")
            return
        
        # 예제 실행
        demonstrate_basic_usage()
        demonstrate_advanced_search()
        demonstrate_conversation()
        
        print("\n" + "="*60)
        print("🎉 모든 예제 시연 완료!")
        print("\n💡 사용 팁:")
        print("- CSV 데이터는 한 번 로드되면 벡터 저장소에 저장됩니다")
        print("- force_reload=True로 데이터를 새로 로드할 수 있습니다")
        print("- 다양한 검색 필터를 활용해보세요")
        print("- 대화 기능으로 연속적인 질문이 가능합니다")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"예제 실행 실패: {e}")
        print(f"❌ 예제 실행 실패: {e}")


if __name__ == "__main__":
    main()