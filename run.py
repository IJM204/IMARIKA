#!/usr/bin/env python3
"""
Imarika Agricultural AI Assistant - Main Runner
Usage: python run.py [mode]
Modes: chat, test, build-kg
"""

import sys
import subprocess
from pathlib import Path

def run_chat():
    """Launch the Streamlit chat interface"""
    print("🌾 Starting Imarika Chat Interface...")
    subprocess.run([
        "streamlit", "run", "streamlit_openwebui_style.py",
        "--server.port", "8501",
        "--server.headless", "true"
    ])

def run_test():
    """Run system tests"""
    print("🧪 Running Imarika System Tests...")
    
    # Test knowledge graph
    print("\n1. Testing Knowledge Graph...")
    subprocess.run(["python", "knowledge_graph.py"])
    
    # Test LangGraph agent
    print("\n2. Testing LangGraph Agent...")
    subprocess.run(["python", "langgraph_imarika.py"])

def build_knowledge_graph():
    """Rebuild knowledge graph from CSV data"""
    print("📊 Building Knowledge Graph...")
    subprocess.run(["python", "knowledge_graph.py"])

def show_help():
    """Show usage information"""
    print("""
🌾 Imarika Agricultural AI Assistant

Usage: python run.py [mode]

Modes:
  chat     - Launch Streamlit chat interface (default)
  test     - Run system tests
  build-kg - Rebuild knowledge graph
  help     - Show this help message

Examples:
  python run.py           # Start chat interface
  python run.py chat      # Start chat interface
  python run.py test      # Run tests
  python run.py build-kg  # Rebuild knowledge graph
    """)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "chat"
    
    if mode == "chat":
        run_chat()
    elif mode == "test":
        run_test()
    elif mode == "build-kg":
        build_knowledge_graph()
    elif mode == "help":
        show_help()
    else:
        print(f"Unknown mode: {mode}")
        show_help()
        sys.exit(1)