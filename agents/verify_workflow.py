
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup environment
from dotenv import load_dotenv
load_dotenv()

from src.agent.system import agent_supervisor_graph
from langchain_core.messages import HumanMessage

def test_workflow():
    print("🚀 Starting End-to-End Workflow Test")
    print("-" * 50)
    
    # Test input that should trigger triage -> medical info flow
    user_input = "I have a severe headache and fever for 2 days"
    print(f"👤 User: {user_input}")
    
    state = {
        "messages": [HumanMessage(content=user_input)],
        "session_id": "test-verify-001",
        "symptom_json": {},
        "rag_query": None,
        "triage_turns": 0,
        "active_agent": "triage",
        "new_message": True
    }
    
    config = {"run_name": "verify_workflow", "metadata": {"session_id": "test-verify-001"}}
    
    print("\n🔄 Invoking agent graph...")
    try:
        result = agent_supervisor_graph.invoke(state, config=config)
        
        print("\n✅ Execution Complete")
        print("-" * 50)
        
        # Print flow of messages
        for msg in result.get("messages", []):
            type_name = msg.type
            content = msg.content
            print(f"[{type_name.upper()}]: {content[:100]}..." if len(content) > 100 else f"[{type_name.upper()}]: {content}")
            
    except Exception as e:
        print(f"\n❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow()
