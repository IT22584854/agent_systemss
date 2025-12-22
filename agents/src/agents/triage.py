from datetime import datetime
from typing_extensions import Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from agents.src.graph.state import ClarifyWithUser, AgentState, gatheredSymptomInfo, AgentInputState
from agents.src.prompts.triage_prompt import clarify_with_user_instructions, create_symptom_report_instructions

# ===== UTILITY FUNCTIONS =====

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")

# ===== CONFIGURATION =====

# Initialize model
model = init_chat_model(model="openai:gpt-4.1", temperature=0.0)

# ===== WORKFLOW NODES =====
def clarify_with_user(state: AgentState) -> Command[Literal["create_symptom_report", "__end__"]]:
    """Node to clarify symptoms with the user."""

    # set up structured output model
    structured_output_model = model.with_structured_output(ClarifyWithUser)

    # Invoke the model with clarification instructions
    response = structured_output_model.invoke([
        HumanMessage(content=clarify_with_user_instructions.format(
            messages=get_buffer_string(messages=state["messages"]), 
            date=get_today_str()
        ))
    ])

    if response.need_clarification:
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        return Command(
            goto="write_research_brief", 
            update={"messages": [AIMessage(content=response.verification)]}
        )
    
def create_symptom_report(state: AgentState):
    """Node to create symptom report for handoff to medical_information agent."""
    
    #setup structured output model
    structured_output_model = model.with_structured_output(gatheredSymptomInfo)

    # Invoke the model to gather symptom information
    response = structured_output_model.invoke([
        HumanMessage(content=create_symptom_report_instructions.format(
            messages=get_buffer_string(messages=state["messages"]),
            date=get_today_str()
        ))
    ])


    return {
        "symptom_json": {
            "chief_complaint": response.chief_complaint,
            "duration": response.duration,
            "severity": response.severity,
            "age_group": response.age_group,
            "location": response.location,
            "other_symptoms": response.other_symptoms,
        }
    }

# ===== GRAPH CONSTRUCTION =====

triage_graph = StateGraph(AgentState, input_schema=AgentInputState)

triage_graph.add_node("clarify_with_user", clarify_with_user)
triage_graph.add_node("create_symptom_report", create_symptom_report)

triage_graph.add_edge(START, "clarify_with_user")
triage_graph.add_edge("clarify_with_user", "create_symptom_report", condition=lambda cmd: cmd.goto == "create_symptom_report")
triage_graph.add_edge("clarify_with_user", END, condition=lambda cmd: cmd.goto == END)
