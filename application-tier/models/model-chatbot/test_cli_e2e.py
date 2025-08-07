#!/usr/bin/env python3
"""
End-to-End CLI Test
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def test_cli_e2e():
    """Test CLI end-to-end functionality"""
    try:
        print("🧪 End-to-End CLI Test")
        print("=" * 30)
        
        # Start the CLI process
        process = subprocess.Popen(
            [sys.executable, "-m", "src.rag.unified_cli"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/Users/boradino/Desktop/AIVLE/빅 프로젝트/코드/AI"
        )
        
        # Send commands to simulate user interaction
        commands = [
            "3",  # Select LangGraph orchestration
            "관세법이란 무엇인가요?",  # Ask a question
            "q"   # Quit
        ]
        
        # Send all commands
        input_text = "\n".join(commands) + "\n"
        
        try:
            stdout, stderr = process.communicate(input=input_text, timeout=60)
            
            print("📄 CLI Output:")
            print(stdout[-1000:])  # Show last 1000 chars
            
            if "무한루프" in stderr or "timed out" in stderr.lower():
                print("❌ CLI still has infinite loop issues")
                return False
            
            if "AI 전문가:" in stdout:
                print("✅ CLI completed successfully with response")
                return True
            else:
                print("⚠️ CLI ran but no response found")
                return False
                
        except subprocess.TimeoutExpired:
            process.kill()
            print("❌ CLI test timed out - likely infinite loop")
            return False
            
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_cli_e2e()
    sys.exit(0 if success else 1)