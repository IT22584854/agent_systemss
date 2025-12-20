from typing import NotRequired, TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    active_agent: NotRequired[str]
    symptom_json: Optional[Dict[str, Any]]
    triage_turns: int
