#!/usr/bin/env python3
"""
Quick LangGraph Integration Validation
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

def quick_validation():
    """Quick LangGraph orchestration validation"""
    try:
        print("🧪 Quick LangGraph Validation")
        print("=" * 40)
        
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
        
        # Quick test query
        test_query = "관세법이란 무엇인가요?"
        print(f"🔍 Testing query: {test_query}")
        
        result = orchestrator.invoke(test_query)
        
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
        
        print("🎉 LangGraph validation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_validation()
    sys.exit(0 if success else 1)