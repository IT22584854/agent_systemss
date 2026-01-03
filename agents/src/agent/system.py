"""Integrated Agent-Supervisor workflow that orchestrates triage and medical information sub-agents."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, List
from typing_extensions import Literal

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.src.graph.state import AgentState, AgentInputState  # noqa: E402
from agents.src.agent.supervisor import supervisor as supervisor_decision  # noqa: E402
from agents.src.agent.triage import graph as triage_graph  # noqa: E402
from agents.src.agent.medical_info import medical_info_graph  # noqa: E402

NODE_MAP: Dict[str, str] = {
    "triage": "triage_agent",
    "medical_info": "medical_info_agent",
}


def _copy_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    return list(messages) if messages else []


def route_supervisor(state: AgentState) -> Command[Literal["triage_agent", "medical_info_agent", "__end__"]]:
    """Resume an in-flight agent or ask the supervisor to pick the next specialist."""
    active_agent = state.get("active_agent")
    symptom_json = state.get("symptom_json")

    if active_agent == "triage" and not symptom_json:
        return Command(goto="triage_agent")

    if active_agent == "medical_info":
        return Command(goto="medical_info_agent")

    decision = supervisor_decision(state)
    target = decision.goto
    node_name = NODE_MAP[target]
    return Command(goto=node_name)


def triage_agent(state: AgentState) -> Command[Literal["medical_info_agent", "__end__"]]:
    """Run the triage sub-graph to gather immediate-care data."""
    result_state = triage_graph.invoke(state)
    updates = {
        key: result_state[key]
        for key in ("messages", "symptom_json")
        if key in result_state
    }
    updates["triage_turns"] = state.get("triage_turns", 0) + 1

    if result_state.get("symptom_json"):
        updates["active_agent"] = "medical_info"
        return Command(goto="medical_info_agent", update=updates)

    updates["active_agent"] = "triage"
    return Command(goto=END, update=updates)


def medical_info_agent(state: AgentState) -> Command[Literal["finalize_response"]]:
    """Invoke the retrieval-augmented medical information agent."""
    result_state = medical_info_graph.invoke(state)
    updates = {
        key: result_state[key]
        for key in ("messages", "symptom_json")
        if key in result_state
    }
    updates["active_agent"] = None
    return Command(goto="finalize_response", update=updates)


def finalize_response(state: AgentState):
    """Let the supervisor voice deliver the final answer with a safety reminder."""
    messages = _copy_messages(state.get("messages", []))
    if not messages:
        return {"messages": messages, "active_agent": None}

    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        reminder = (
            "\n\n⚠️ This guidance is informational only. Contact a healthcare professional "
            "or local emergency services if symptoms worsen or feel life-threatening."
        )
        if reminder not in last_message.content:
            messages[-1] = AIMessage(content=f"{last_message.content}{reminder}")

    return {"messages": messages, "active_agent": None}


workflow = StateGraph(AgentState, input_schema=AgentInputState)
workflow.add_node("route_supervisor", route_supervisor)
workflow.add_node("triage_agent", triage_agent)
workflow.add_node("medical_info_agent", medical_info_agent)
workflow.add_node("finalize_response", finalize_response)

workflow.add_edge(START, "route_supervisor")
workflow.add_edge("route_supervisor", "triage_agent")
workflow.add_edge("route_supervisor", "medical_info_agent")
workflow.add_edge("triage_agent", "medical_info_agent")
workflow.add_edge("triage_agent", END)
workflow.add_edge("medical_info_agent", "finalize_response")
workflow.add_edge("finalize_response", END)

agent_supervisor_graph = workflow.compile()

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    state = {
        "messages": [],
        "session_id": "demo-001",
        "symptom_json": {},
        "triage_turns": 0,
        "active_agent": None,
    }

    print("Agent-Supervisor workflow ready. Type 'quit' to exit.")

    while True:
        user = input("User: ").strip()
        if user.lower() in {"quit", "exit"}:
            break

        state["messages"].append(HumanMessage(content=user))
        result = agent_supervisor_graph.invoke(state)
        state.update(result)

        reply = state["messages"][-1].content
        print(f"Agent: {reply}")

        if state.get("symptom_json"):
            print("\nSymptom summary captured; handing off to medical-info agent...")
            break