#!/usr/bin/env python3
"""
Fixed LangGraph Orchestrator Test
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv()

def test_fixed_orchestrator():
    """Test the fixed LangGraph orchestrator for infinite loop"""
    try:
        print("🧪 Testing Fixed LangGraph Orchestrator")
        print("=" * 50)
        
        # API key check
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set")
            return False
        
        # Import and create system
        from src.rag.langgraph_factory import create_orchestrated_system
        
        print("📦 Creating LangGraph system...")
        orchestrator = create_orchestrated_system(
            model_name="gpt-4o-mini",
            temperature=0.1
        )
        
        print("✅ LangGraph system created")
        
        # Test query
        test_query = "관세법 제1조는 무엇인가요?"
        print(f"🔍 Testing query: {test_query}")
        
        # Set timeout to catch infinite loops
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Test timed out - likely infinite loop")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        try:
            result = orchestrator.invoke(test_query)
            signal.alarm(0)  # Cancel alarm
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                return False
            
            messages = result.get("messages", [])
            if messages:
                response = messages[-1].content
                print(f"✅ Response received (length: {len(response)})")
                print(f"📄 Preview: {response[:100]}...")
            
            # Check routing
            routing_history = result.get("routing_history", [])
            if routing_history:
                latest = routing_history[-1]
                agent = latest.get("selected_agent", "unknown")
                complexity = latest.get("complexity", 0)
                print(f"🎯 Routed to: {agent} (complexity: {complexity:.2f})")
            
            print("🎉 Test completed successfully - No infinite loop!")
            return True
            
        except TimeoutError:
            signal.alarm(0)
            print("❌ Test timed out - Infinite loop still exists!")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fixed_orchestrator()
    sys.exit(0 if success else 1)