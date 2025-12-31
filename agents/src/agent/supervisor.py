from datetime import datetime
from pathlib import Path
import sys
from typing_extensions import Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from agents.src.graph.state import SupervisorInfo
from agents.src.prompts.supervisor import SUPERVISOR_PROMPT


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AGENTS_ROOT = Path(__file__).resolve().parents[2]
if str(AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTS_ROOT))

from dotenv import load_dotenv
load_dotenv()
from src.graph.state import AgentState, AgentInputState

response_model = init_chat_model("gpt-4o", temperature=0)

def supervisor(state: AgentState) -> Command[Literal["medical_info","triage"]]:
    """ clarify user query into relevent agent"""
    
    structured_output_model = response_model.with_structured_output(SupervisorInfo)

    user_question = state["messages"][0].content

    response = structured_output_model.invoke([
        HumanMessage(content=SUPERVISOR_PROMPT.format(
            query=user_question
        ))
    ])
    print(f"next agent :{response.next_agent}")
    return response.next_agent

