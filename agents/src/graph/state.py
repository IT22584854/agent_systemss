import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class AgentInputState(MessagesState):
    """Input state for the full agent - only contains messages from user input."""
    pass

class SymptomData(TypedDict, total=False):
    chief_complaint: str
    duration: str
    severity: str
    age_group: str
    location: str
    other_symptoms: List[str]

def merge_symptoms(existing: SymptomData, updates: SymptomData) -> SymptomData:
    #keeps old data and only updates/adds what the sub-agent just found
    return {**(existing or {}), **(updates or {})}

class AgentState(MessagesState):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    active_agent: NotRequired[str]
    symptom_json: Annotated[SymptomData, merge_symptoms]
    triage_turns: int


# ===== STRUCTURED OUTPUT SCHEMAS =====

class ClarifyWithUser(BaseModel):
    """Schema for user clarification decision and questions."""

    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the symptoms they are experiencing.",
    )
    verification: str = Field(
        description="Verify message that we will handover medical_information agent after the user has provided the necessary information.",
    )
