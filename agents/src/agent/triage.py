from datetime import datetime
from pathlib import Path
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
    now = datetime.now()
    return f"{now.strftime('%a %b')} {now.day}, {now.year}"

# ===== CONFIGURATION =====
from dotenv import load_dotenv
load_dotenv()
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
            goto="create_symptom_report", 
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

triage_graph.add_edge(START, "clarify_with_user")
triage_graph.add_node(clarify_with_user)
triage_graph.add_node(create_symptom_report)

graph = triage_graph.compile()

output_path = Path("triage_graph.png")
graph.get_graph().draw_mermaid_png(output_file_path=output_path)
print(f"Graph exported to {output_path.resolve()}")

if __name__ == "__main__":
    print("Starting Triage Agent (type 'quit' to exit)...")
    messages = []
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        
        messages.append(HumanMessage(content=user_input))
        state = {"messages": messages}
        
        # Run the graph
        result = graph.invoke(state)
        
        # Update messages with the result
        messages = result["messages"]
        
        # Print the last message from the agent
        last_message = messages[-1]
        if isinstance(last_message, AIMessage):
            print(f"Agent: {last_message.content}")
            
        # Check if we are done (symptom report created)
        if "symptom_json" in result and result["symptom_json"]:
             print("\nSymptom Report Created:")
             print(result["symptom_json"])
             break

