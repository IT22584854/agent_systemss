"""Linear triage -> medical information workflow with supervisor orchestration."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, List
from typing_extensions import Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langsmith import traceable

# Path setup
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.src.graph.state import AgentState, AgentInputState
from agents.src.agent.triage import graph as triage_graph
from agents.src.agent.medical_info import medical_info_graph
from agents.src.utils import setup_logger

# ===== LOGGING =====
logger = setup_logger("agent_supervisor")


def _copy_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    return list(messages) if messages else []


def _build_run_config(state: AgentState, run_name: str) -> Dict[str, Any]:
    """Create a LangSmith config block with consistent metadata."""
    session_id = state.get("session_id", "unknown-session")
    return {
        "run_name": f"{run_name}-{session_id}",
        "metadata": {
            "session_id": session_id,
            "active_agent": state.get("active_agent"),
            "triage_turns": state.get("triage_turns"),
            "has_rag_query": bool(state.get("rag_query")),
        },
    }


@traceable(name="triage_agent")
def triage_agent(state: AgentState):
    """Run the triage sub-graph to gather immediate-care data."""
    logger.info("Invoking triage sub-graph")
    
    try:
        result_state = triage_graph.invoke(state, config=_build_run_config(state, "triage_graph"))
        updates = {}
        _sentinel = object()
        
        for key in ("messages", "rag_query", "active_agent"):
            value = result_state.get(key, _sentinel)
            if value is not _sentinel:
                updates[key] = value
        updates["triage_turns"] = state.get("triage_turns", 0) + 1

        active_agent = result_state.get("active_agent")
        rag_query = result_state.get("rag_query")
        needs_follow_up = active_agent == "triage"

        if needs_follow_up:
            logger.info("Triage needs follow-up, returning to user")
            updates["new_message"] = True
            updates["rag_query"] = None
            return Command(goto="finalize_response", update=updates)

        if rag_query:
            logger.info(f"Triage complete, routing to medical info with query: {rag_query[:50]}...")
            return Command(goto="medical_info_agent", update=updates)

        # Fallback: end the run without advancing if no RAG query was produced
        logger.warning("No RAG query produced, finalizing response")
        updates["new_message"] = True
        return Command(goto="finalize_response", update=updates)
        
    except Exception as e:
        logger.error(f"Error in triage_agent: {e}")
        return Command(goto="finalize_response", update={"new_message": True})


@traceable(name="medical_info_agent")
def medical_info_agent(state: AgentState) -> Command[Literal["finalize_response"]]:
    """Invoke the retrieval-augmented medical information agent."""
    logger.info("Invoking medical info sub-graph")
    
    try:
        rag_query = state.get("rag_query")
        med_state = state

        if rag_query:
            synthetic_message = HumanMessage(
                content=rag_query,
                name="triage_summary",
                additional_kwargs={"source": "triage_rag"},
            )
            med_state = dict(state)
            med_messages = _copy_messages(state.get("messages", []))
            med_messages.append(synthetic_message)
            med_state["messages"] = med_messages
        
        result_state = medical_info_graph.invoke(med_state, config=_build_run_config(state, "medical_info_graph"))
        updates = {}
        _sentinel = object()
        
        for key in ("symptom_json",):
            value = result_state.get(key, _sentinel)
            if value is not _sentinel:
                updates[key] = value

        # Critical: Only propagate NEW messages to avoid duplication
        # The subgraph was initialized with: existing history + 1 synthetic message
        # So new messages start after len(existing_history) + 1
        start_idx = len(state.get("messages", []))
        all_subgraph_msgs = result_state.get("messages", [])
        
        new_messages = []
        if len(all_subgraph_msgs) > start_idx:
            # Check if the message at start_idx is the synthetic one we added
            potential_new = all_subgraph_msgs[start_idx:]
            
            for msg in potential_new:
                # Filter out the synthetic trigger message if it appears
                if (isinstance(msg, HumanMessage) and 
                    msg.additional_kwargs.get("source") == "triage_rag"):
                    continue
                new_messages.append(msg)
                
        if new_messages:
            updates["messages"] = new_messages
        updates["rag_query"] = None
        updates["active_agent"] = None
        
        logger.info("Medical info processing complete")
        return Command(goto="finalize_response", update=updates)
        
    except Exception as e:
        logger.error(f"Error in medical_info_agent: {e}")
        return Command(goto="finalize_response", update={"rag_query": None, "active_agent": None})


@traceable(name="finalize_response")
def finalize_response(state: AgentState):
    """Deliver the final answer along with any safety reminder."""
    logger.info("Finalizing response")
    messages = _copy_messages(state.get("messages", []))
    return {
        "messages": messages,
        "active_agent": None,
        "rag_query": None,
        "new_message": True
    }


# ===== BUILD WORKFLOW =====
workflow = StateGraph(AgentState, input_schema=AgentInputState)
workflow.add_node("triage_agent", triage_agent)
workflow.add_node("medical_info_agent", medical_info_agent)
workflow.add_node("finalize_response", finalize_response)

workflow.add_edge(START, "triage_agent")
from langgraph.checkpoint.memory import MemorySaver

# Initialize MemorySaver (In-Memory Persistence)
# This is stable and works with async/sync without complex context management
checkpointer = MemorySaver()

agent_supervisor_graph = workflow.compile(
    checkpointer=checkpointer
)

# Guard graph visualization - only run when script is executed directly
# Guard graph visualization - only run when script is executed directly
if __name__ == "__main__":
    output_path = Path("system.png")
    agent_supervisor_graph.get_graph().draw_mermaid_png(output_file_path=output_path)
    logger.info(f"Graph exported to {output_path.resolve()}")

    # Use a fixed session ID for the demo
    session_id = "demo-session"
    config = {"configurable": {"thread_id": session_id}}
    
    logger.info(f"Starting Session: {session_id}")
    logger.info("Triage/medical workflow ready. Type 'quit' to exit.")
    
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        
        graph_input = {"messages": [HumanMessage(content=user_input)]}

        # Use invoke for simple synchronous execution in CLI
        result = agent_supervisor_graph.invoke(graph_input, config=config)
        
        snapshot = agent_supervisor_graph.get_state(config)
        messages = snapshot.values.get("messages", [])
        
        reply_message = None
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                continue
            reply_message = message
            break

        if reply_message is None:
            logger.info("Agent: (no response)")
        else:
            logger.info(f"Agent: {reply_message.content}")
