"""Intent classifier agent for user clarification and intent extraction."""
from datetime import datetime
from pathlib import Path
import sys

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langsmith import traceable

# Path setup for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.src.graph.state import ClarifyWithUser, AgentState, AgentInputState
from agents.src.prompts.triage_prompt import intent_classifier_prompt
from agents.src.config import LLM_MODEL, LLM_TEMPERATURE
from agents.src.utils import setup_logger, sanitize_input, retry_on_error, create_error_response

# ===== LOGGING =====
logger = setup_logger("intent_classifier_agent")

# ===== UTILITY FUNCTIONS ===== 

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    now = datetime.now()
    return f"{now.strftime('%a %b')} {now.day}, {now.year}"

# ===== CONFIGURATION =====
from dotenv import load_dotenv
load_dotenv()

# Initialize model with centralized config
model = init_chat_model(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

# ===== WORKFLOW NODES =====
@traceable(name="clarify_with_user")
def clarify_with_user(state: AgentState):
    """Clarify user intent and emit a RAG query when ready."""
    
    logger.info("Intent classifier agent processing request")
    
    try:
        # Sanitize the latest user message
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                sanitized_content = sanitize_input(last_msg.content)
                logger.debug(f"Sanitized input length: {len(sanitized_content)}")
        
        structured_output_model = model.with_structured_output(ClarifyWithUser)
        
        @retry_on_error(logger=logger)
        def invoke_model():
            return structured_output_model.invoke([
                HumanMessage(content=intent_classifier_prompt.format(
                    messages=get_buffer_string(messages=state["messages"]),
                    date=get_today_str()
                ))
            ])
         
        response = invoke_model()
        
        logger.info(f"Need clarification: {response.need_clarification}")
        logger.debug(f"Follow up: {response.follow_up_question}")
        logger.debug(f"RAG query: {response.intent_summary}")

        if response.need_clarification:
            follow_up = response.follow_up_question or "Could you share a bit more detail?"
            return {
                "messages": [AIMessage(content=follow_up)],
                "active_agent": "intent_classifier",
                "rag_query": None,
            }

        # Check if this is a conversational response (no medical query needed)
        intent_summary = response.intent_summary or ""
        if intent_summary.startswith("CONVERSATIONAL:"):
            conversational_response = intent_summary.replace("CONVERSATIONAL:", "").strip()
            logger.info("Conversational message detected, responding directly")
            return {
                "messages": [AIMessage(content=conversational_response)],
                "active_agent": "intent_classifier",
                "rag_query": None,
            }

        # Generate RAG query for medical information
        rag_query = intent_summary or "User intent unclear; please restate the concern."
        logger.info(f"RAG query generated: {rag_query}")
        return {
            "rag_query": rag_query,
            "active_agent": "medical_info"
        }
        
    except Exception as e:
        logger.error(f"Error in intent classifier agent: {e}")
        return {
            "messages": [AIMessage(content=create_error_response("llm"))],
            "active_agent": "intent_classifier",
            "rag_query": None,
        }

# ===== GRAPH CONSTRUCTION =====

intent_classifier_graph = StateGraph(AgentState, input_schema=AgentInputState)

intent_classifier_graph.add_node(clarify_with_user)

intent_classifier_graph.add_edge(START, "clarify_with_user")
intent_classifier_graph.add_edge("clarify_with_user", END)

graph = intent_classifier_graph.compile()

if __name__ == "__main__":
    # Guard graph visualization
    output_path = Path("intent_classifier_graph.png")
    graph.get_graph().draw_mermaid_png(output_file_path=output_path)
    logger.info(f"Graph exported to {output_path.resolve()}")

    logger.info("Starting Intent Classifier Agent (type 'quit' to exit)...")
    messages = []
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        
        # Sanitize user input
        user_input = sanitize_input(user_input)
        
        messages.append(HumanMessage(content=user_input))
        state = {"messages": messages}
        
        # Run the graph
        result = graph.invoke(state)
        
        # Append graph outputs to the transcript
        new_messages = result.get("messages", [])
        if isinstance(new_messages, list):
            messages.extend(new_messages)

        # Print the last message from the agent
        last_message = messages[-1]
        if isinstance(last_message, AIMessage):
            logger.info(f"Agent: {last_message.content}")

        # Check if the RAG query is ready
        if result.get("rag_query"):
            logger.info("RAG Query Ready:")
            logger.info(result["rag_query"])
            break


