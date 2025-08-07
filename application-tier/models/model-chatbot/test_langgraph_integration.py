#!/usr/bin/env python3
"""
LangGraph Integration Test

LangGraph 오케스트레이션 시스템의 기본 동작을 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_orchestration():
    """기본 LangGraph 오케스트레이션 테스트"""
    try:
        print("🧪 LangGraph Integration Test 시작")
        print("=" * 60)
        
        # API 키 확인
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            return False
        
        # LangGraph 팩토리 임포트
        from src.rag.langgraph_factory import create_orchestrated_system
        
        print("📦 LangGraph 오케스트레이션 시스템 생성 중...")
        
        # 오케스트레이션 시스템 생성
        orchestrator = create_orchestrated_system(
            model_name="gpt-4o-mini",
            temperature=0.1
        )
        
        print("✅ LangGraph 오케스트레이션 시스템 생성 완료")
        
        # 통계 정보 출력
        from src.rag.langgraph_factory import get_langgraph_factory
        factory = get_langgraph_factory()
        stats = factory.get_agent_stats()
        
        print(f"\n📊 시스템 상태:")
        print(f"  - 오케스트레이터: {'✅' if stats['orchestrator_available'] else '❌'}")
        print(f"  - 관세법 에이전트: {'✅' if stats['agents']['conversation_agent'] else '❌'}")
        print(f"  - 규제 에이전트: {'✅' if stats['agents']['regulation_agent'] else '❌'}")
        print(f"  - 상담 에이전트: {'✅' if stats['agents']['consultation_agent'] else '❌'}")
        
        # 테스트 질의들
        test_queries = [
            "관세법 제1조는 무엇인가요?",  # conversation_agent 예상
            "딸기는 어느 나라에서 수입해야 하나요?",  # regulation_agent 예상
            "수입신고는 어떻게 하나요?",  # consultation_agent 예상
        ]
        
        print(f"\n🔍 테스트 질의 실행:")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- 테스트 {i} ---")
            print(f"질의: {query}")
            
            try:
                # 오케스트레이터 실행
                result = orchestrator.invoke(query)
                
                # 결과 분석
                if "error" in result:
                    print(f"❌ 오류 발생: {result['error']}")
                    continue
                
                messages = result.get("messages", [])
                if messages:
                    last_response = messages[-1]
                    print(f"응답: {last_response.content[:100]}...")
                
                # 라우팅 히스토리 확인
                routing_history = result.get("routing_history", [])
                if routing_history:
                    latest_routing = routing_history[-1]
                    print(f"라우팅: {latest_routing.get('selected_agent', 'unknown')}")
                    print(f"복잡도: {latest_routing.get('complexity', 0):.2f}")
                    print(f"이유: {latest_routing.get('reasoning', 'N/A')}")
                
                print("✅ 테스트 성공")
                
            except Exception as e:
                print(f"❌ 테스트 실패: {e}")
                logger.error(f"Query {i} failed: {e}")
        
        print(f"\n🎉 LangGraph Integration Test 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        logger.error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_routing_accuracy():
    """라우팅 정확도 테스트"""
    try:
        print(f"\n🎯 라우팅 정확도 테스트")
        print("-" * 40)
        
        from src.rag.langgraph_factory import create_orchestrated_system
        
        orchestrator = create_orchestrated_system()
        
        # 라우팅 테스트 케이스
        routing_test_cases = [
            {
                "query": "관세법 제5조에 대해 알려주세요",
                "expected_agent": "conversation_agent",
                "category": "법령 조문"
            },
            {
                "query": "양벚딸기는 어떤 나라에서 수입 가능한가요?",
                "expected_agent": "regulation_agent", 
                "category": "동식물 수입 규제"
            },
            {
                "query": "통관신고서는 어떻게 작성하나요?",
                "expected_agent": "consultation_agent",
                "category": "실무 절차"
            },
            {
                "query": "HS코드 0810.10은 어떤 규제가 있나요?",
                "expected_agent": "regulation_agent",
                "category": "HS코드 규제"
            },
            {
                "query": "FTA 원산지증명서 발급 절차를 알려주세요",
                "expected_agent": "consultation_agent",
                "category": "원산지 절차"
            }
        ]
        
        correct_routes = 0
        total_tests = len(routing_test_cases)
        
        for i, test_case in enumerate(routing_test_cases, 1):
            query = test_case["query"]
            expected = test_case["expected_agent"]
            category = test_case["category"]
            
            print(f"\n{i}. [{category}] {query}")
            
            try:
                result = orchestrator.invoke(query)
                routing_history = result.get("routing_history", [])
                
                if routing_history:
                    actual = routing_history[-1].get("selected_agent", "unknown")
                    complexity = routing_history[-1].get("complexity", 0)
                    reasoning = routing_history[-1].get("reasoning", "")
                    
                    if actual == expected:
                        print(f"✅ 예상: {expected} | 실제: {actual} | 복잡도: {complexity:.2f}")
                        correct_routes += 1
                    else:
                        print(f"❌ 예상: {expected} | 실제: {actual} | 복잡도: {complexity:.2f}")
                        print(f"   이유: {reasoning}")
                else:
                    print(f"❌ 라우팅 정보 없음")
                    
            except Exception as e:
                print(f"❌ 테스트 실패: {e}")
        
        accuracy = (correct_routes / total_tests) * 100
        print(f"\n📈 라우팅 정확도: {correct_routes}/{total_tests} ({accuracy:.1f}%)")
        
        if accuracy >= 80:
            print("🎉 라우팅 정확도 우수!")
        elif accuracy >= 60:
            print("⚠️ 라우팅 정확도 보통 - 개선 필요")
        else:
            print("🚨 라우팅 정확도 낮음 - 즉시 개선 필요")
        
        return accuracy >= 60
        
    except Exception as e:
        print(f"❌ 라우팅 테스트 실패: {e}")
        return False


def test_error_handling():
    """오류 처리 테스트"""
    try:
        print(f"\n🛡️ 오류 처리 테스트")
        print("-" * 40)
        
        from src.rag.langgraph_factory import create_orchestrated_system
        
        orchestrator = create_orchestrated_system()
        
        # 오류 테스트 케이스
        error_test_cases = [
            "",  # 빈 질의
            "   ",  # 공백만
            "a" * 1000,  # 매우 긴 질의
            "🎵🎶🎵🎶",  # 이모지만
        ]
        
        for i, query in enumerate(error_test_cases, 1):
            print(f"\n{i}. 오류 케이스: {'빈 질의' if not query.strip() else f'{str(query)[:20]}...'}")
            
            try:
                result = orchestrator.invoke(query)
                
                if "error" in result:
                    print(f"✅ 오류 적절히 처리됨: {result['error'][:50]}...")
                else:
                    messages = result.get("messages", [])
                    if messages:
                        print(f"✅ 응답 생성됨: {messages[-1].content[:50]}...")
                    else:
                        print("⚠️ 응답 없음")
                        
            except Exception as e:
                print(f"⚠️ 예외 발생: {str(e)[:50]}...")
        
        print(f"✅ 오류 처리 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 오류 처리 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("🚀 LangGraph Integration Test Suite")
    print("=" * 60)
    
    # 환경 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return
    
    test_results = []
    
    # 1. 기본 통합 테스트
    result1 = test_basic_orchestration()
    test_results.append(("기본 통합", result1))
    
    # 2. 라우팅 정확도 테스트
    result2 = test_routing_accuracy()
    test_results.append(("라우팅 정확도", result2))
    
    # 3. 오류 처리 테스트
    result3 = test_error_handling()
    test_results.append(("오류 처리", result3))
    
    # 전체 결과
    print(f"\n📋 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total = len(test_results)
    print(f"\n전체: {passed}/{total} 통과 ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 모든 테스트 통과!")
    elif passed >= total * 0.7:
        print("⚠️ 대부분 테스트 통과 - 일부 개선 필요")
    else:
        print("🚨 테스트 실패 - 시스템 점검 필요")


if __name__ == "__main__":
    main()