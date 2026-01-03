import operator
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import NotRequired, TypedDict
from enum import Enum
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


def overwrite_active(_: Optional[str], new_value: Optional[str]) -> Optional[str]:
    return new_value

class AgentState(MessagesState):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    active_agent: Annotated[Optional[str], overwrite_active]
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
  

class gatheredSymptomInfo(BaseModel):
    """Schema for gathered symptom information from the user."""

    chief_complaint: Optional[str] = Field(
        default=None,
        description="The main symptom or complaint reported by the user.",
    )
    duration: Optional[str] = Field(
        default=None,
        description="The duration or onset of the symptoms.",
    )
    severity: Optional[str] = Field(
        default=None,
        description="The severity or location of the symptoms.",
    )
    age_group: Optional[str] = Field(
        default=None,
        description="The age group or any chronic conditions of the user.",
    )
    location: Optional[str] = Field(
        default=None,
        description="The location of the symptoms.",
    )
    other_symptoms: Optional[List[str]] = Field(
        default=None,
        description="Any other symptoms reported by the user.",
    )


class NextAgent(str, Enum):
    """Strictly enforce valid agent names"""
    TRIAGE = "triage"
    MEDICAL_INFO = "medical_info"

class SupervisorInfo(BaseModel):
    reasoning: str = Field(
        description="Brief 1-sentence explanation of routing decision (e.g., 'Patient reports current fever symptom')",        
    )
    confidence: float = Field(
        description="Routing certainty (0.0=low, 1.0=high). 1.0 for obvious keywords, 0.7+ for semantic decisions."
    )
    next_agent: NextAgent = Field(description="Target agent")