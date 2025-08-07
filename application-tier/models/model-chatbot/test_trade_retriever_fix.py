#!/usr/bin/env python3
"""
Test TradeInfoRetriever fix for str vs int comparison error
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

def test_trade_retriever_fix():
    """Test the fixed TradeInfoRetriever"""
    try:
        print("🧪 Testing TradeInfoRetriever Type Fix")
        print("=" * 40)
        
        # API key check
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set")
            return False
        
        # Import components
        from src.rag.embeddings import OpenAIEmbedder
        from src.rag.vector_store import ChromaVectorStore
        from src.rag.query_normalizer import LawQueryNormalizer
        from src.rag.trade_info_retriever import TradeInfoRetriever
        
        print("📦 Creating TradeInfoRetriever...")
        
        # Initialize components
        embedder = OpenAIEmbedder()
        vector_store = ChromaVectorStore(
            collection_name="trade_info_collection",
            db_path="data/chroma_db"
        )
        query_normalizer = LawQueryNormalizer()
        
        # Create retriever
        retriever = TradeInfoRetriever(
            embedder=embedder,
            vector_store=vector_store,
            query_normalizer=query_normalizer,
            collection_name="trade_info_collection"
        )
        
        print("✅ TradeInfoRetriever created")
        
        # Test query that would trigger the error
        test_query = "딸기를 어디서 수입할 수 있나요?"
        print(f"🔍 Testing query: {test_query}")
        
        # This should not raise the '>=' error anymore
        results = retriever.search_trade_info(test_query, top_k=3)
        
        print(f"✅ Search completed successfully")
        print(f"📄 Results: {len(results)} documents")
        
        # Check if any results have boosted flag
        boosted_count = len([r for r in results if r.get("boosted", False)])
        print(f"🎯 Boosted results: {boosted_count}")
        
        # Test with specific animal/plant query
        test_query2 = "멜론 수입 허용 국가"
        print(f"🔍 Testing query 2: {test_query2}")
        
        results2 = retriever.search_trade_info(test_query2, top_k=3)
        print(f"✅ Search 2 completed successfully")
        print(f"📄 Results 2: {len(results2)} documents")
        
        print("🎉 All tests passed - Type error fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trade_retriever_fix()
    sys.exit(0 if success else 1)