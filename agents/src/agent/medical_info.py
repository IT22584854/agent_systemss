"""Medical information agent with RAG retrieval and critique loop."""
import os
import uuid
import chromadb
from langchain_community.document_loaders import TextLoader
import sys
from typing import Any, Dict, List
from typing_extensions import Literal
from langgraph.types import Command
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langsmith import traceable
from pydantic import BaseModel, Field

# Path setup
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AGENTS_ROOT = Path(__file__).resolve().parents[2]
if str(AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTS_ROOT))

from agents.src.prompts.medi_info import (
    score_document_prompt, rewrite_prompt, generate_prompt, 
    generate_query_or_respond_prompt, critique_prompt
)
from agents.src.config import (
    LLM_MODEL, LLM_TEMPERATURE, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME,
    RETRIEVAL_TOP_K, ENSEMBLE_DENSE_WEIGHT, MAX_CRITIQUE_ATTEMPTS, MAX_REWRITE_ATTEMPTS
)
from agents.src.utils import setup_logger, retry_on_error, create_error_response
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# ===== LOGGING =====
logger = setup_logger("medical_info_agent")

# ===== CONFIGURATION =====
from dotenv import load_dotenv
load_dotenv()

from agents.src.graph.state import AgentState, AgentInputState

# ===== DATA INGEST =====
data_path = AGENTS_ROOT / "data" / "MI_data.md"

logger.info(f"Loading medical data from {data_path}")
loader = TextLoader(data_path)
docs = loader.load()
docs = docs[0].page_content

# Split
character_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""],
    chunk_size=200,
    chunk_overlap=50
)

splits = character_splitter.split_text(docs)
logger.info(f"Created {len(splits)} document chunks")

dense_documents = [Document(page_content=text, metadata={"id": str(i), "source": "dense"}) for i, text in enumerate(splits)]
sparse_documents = [Document(page_content=text, metadata={"id": str(i), "source": "sparse"}) for i, text in enumerate(splits)]

# ===== RETRIEVAL STACK (Persistent ChromaDB) =====
embedding_function = OpenAIEmbeddings()

# Use persistent ChromaDB
logger.info(f"Initializing ChromaDB with persist directory: {CHROMA_PERSIST_DIR}")
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Check if collection exists, if not create it
try:
    existing_collection = chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
    logger.info(f"Using existing ChromaDB collection: {CHROMA_COLLECTION_NAME}")
    vectorstore = Chroma(
        client=chroma_client,
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_function
    )
except Exception:
    logger.info(f"Creating new ChromaDB collection: {CHROMA_COLLECTION_NAME}")
    vectorstore = Chroma.from_documents(
        documents=dense_documents,
        embedding=embedding_function,
        collection_name=CHROMA_COLLECTION_NAME,
        client=chroma_client
    )

# Combine a dense retriever with BM25
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_TOP_K})
sparse_retriever = BM25Retriever.from_documents(sparse_documents, k=RETRIEVAL_TOP_K)
sparse_weight = 1.0 - ENSEMBLE_DENSE_WEIGHT
ensemble_retriever = EnsembleRetriever(
    retrievers=[dense_retriever, sparse_retriever], 
    weights=[ENSEMBLE_DENSE_WEIGHT, sparse_weight], 
    c=0
)

# ===== RETRIEVAL TOOL =====
@tool("retrieve_medical_info")
def retrieve_medical_info(query: str) -> str:
    """
    Retrieve medical information related to the provided query using the ensemble retriever.
    Args:
        query (str): Natural-language question or keyword string describing the medical information to fetch.
    Returns:
        str: Concatenated textual content of all retrieved documents separated by blank lines.
    """
    try:
        docs = ensemble_retriever.invoke(query)
        logger.debug(f"Query passed to tool: {query}")
        logger.info(f"Retrieved {len(docs)} documents")
        return "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return "Unable to retrieve information at this time."

retriever_tool = retrieve_medical_info
response_model = init_chat_model(LLM_MODEL, temperature=LLM_TEMPERATURE)


def _latest_user_text(messages: List[BaseMessage]) -> str:
    """Return the most recent human utterance to use as a fallback query."""
    for msg in reversed(messages or []):
        if isinstance(msg, HumanMessage):
            return msg.content
    return messages[-1].content if messages else ""


# ===== STRUCTURED OUTPUT SCHEMAS =====
class CritiqueResult(BaseModel):
    """Schema for critique evaluation."""
    needs_refinement: bool = Field(description="Whether the answer needs refinement")
    issues: List[str] = Field(default=[], description="List of specific issues found")
    feedback: str = Field(default="", description="Constructive feedback for improvement")


# ===== GRAPH NODES =====
@traceable(name="generate_query_or_respond")
def generate_query_or_respond(state: AgentState) -> Command[Literal["retrieve", "__end__"]]:
    """Let the model either issue a retrieval tool call or directly answer the user."""
    
    try:
        system_prompt = SystemMessage(content=generate_query_or_respond_prompt)
        rag_query = state.get("rag_query")
        
        if rag_query:
            response = AIMessage(
                content="",
                tool_calls=[{
                    "name": retriever_tool.name,
                    "args": {"query": rag_query},
                    "id": f"call_{uuid.uuid4().hex}",
                }],
                additional_kwargs={"source": "triage_query"},
            )
            return Command(
                goto="retrieve",
                update={"messages": [response]},
            )

        query_text = _latest_user_text(state["messages"])
        user_message = HumanMessage(content=query_text)
        conversation = [system_prompt, user_message]

        @retry_on_error(logger=logger)
        def invoke_model():
            return (
                response_model
                .bind_tools([retriever_tool], tool_choice=retriever_tool.name)
                .invoke(conversation)
            )
        
        response = invoke_model()

        if response.tool_calls:
            return Command(
                goto="retrieve",
                update={"messages": [response]},
            )

        return Command(
            goto=END,
            update={"messages": [response]},
        )
        
    except Exception as e:
        logger.error(f"Error in generate_query_or_respond: {e}")
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=create_error_response("llm"))]},
        )


@traceable(name="score_document")
def score_document(state: AgentState) -> Command[Literal["generate_answer", "improve"]]:
    """Score document relevance and decide whether to improve the query."""
    
    try:
        class Scoring(BaseModel):
            binary_score: str = Field(description="relevance score 'yes' or 'no'")
        
        structured_output_model = response_model.with_structured_output(Scoring)

        latest_context = state["messages"][-1].content
        original_question = state.get("rag_query") or _latest_user_text(state["messages"])
        
        @retry_on_error(logger=logger)
        def invoke_model():
            return structured_output_model.invoke([
                HumanMessage(content=score_document_prompt.format(
                    context=latest_context,
                    question=original_question
                ))
            ])
        
        response = invoke_model()
        score = response.binary_score
        logger.info(f"Document relevance score: {score}")

        if score == 'yes':
            return Command(goto="generate_answer")
        else:
            # Check rewrite limit
            rewrite_attempts = state.get("rewrite_attempts", 0)
            if rewrite_attempts >= MAX_REWRITE_ATTEMPTS:
                logger.warning(f"Max rewrite attempts ({MAX_REWRITE_ATTEMPTS}) reached, proceeding to generate")
                return Command(goto="generate_answer")
            return Command(goto="improve", update={"rewrite_attempts": rewrite_attempts + 1})
            
    except Exception as e:
        logger.error(f"Error in score_document: {e}")
        return Command(goto="generate_answer")


@traceable(name="improve")
def improve(state: AgentState):
    """Rewrite the original user question."""
    try:
        question = state.get("rag_query") or _latest_user_text(state.get("messages", []))
        prompt = rewrite_prompt.format(question=question)
        
        @retry_on_error(logger=logger)
        def invoke_model():
            return response_model.invoke([{"role": "user", "content": prompt}])
        
        response = invoke_model()
        logger.info("Query improved/rewritten")
        return {"messages": [AIMessage(content=response.content)]}
        
    except Exception as e:
        logger.error(f"Error in improve: {e}")
        return {"messages": [AIMessage(content=state.get("rag_query", ""))]}


@traceable(name="generate_answer")
def generate_answer(state: AgentState):
    """Generate an answer based on retrieved context."""
    try:
        question = state.get("rag_query") or _latest_user_text(state["messages"])
        
        # Use critique feedback if available
        critique_feedback = state.get("critique_feedback")
        context = state["messages"][-1].content
        
        if critique_feedback:
            prompt = f"{generate_prompt.format(question=question, context=context)}\n\nPREVIOUS FEEDBACK TO ADDRESS:\n{critique_feedback}"
            logger.info("Generating answer with critique feedback")
        else:
            prompt = generate_prompt.format(question=question, context=context)
        
        @retry_on_error(logger=logger)
        def invoke_model():
            return response_model.invoke([{"role": "user", "content": prompt}])
        
        response = invoke_model()
        logger.info("Answer generated")
        return {"messages": [response], "critique_feedback": None}
        
    except Exception as e:
        logger.error(f"Error in generate_answer: {e}")
        return {"messages": [AIMessage(content=create_error_response("llm"))]}


@traceable(name="critique_answer")
def critique_answer(state: AgentState) -> Command[Literal["generate_answer", "__end__"]]:
    """Critique the generated answer and decide if refinement is needed."""
    
    try:
        critique_attempts = state.get("critique_attempts", 0)
        
        # Check if max critique iterations reached
        if critique_attempts >= MAX_CRITIQUE_ATTEMPTS:
            logger.info(f"Max critique attempts ({MAX_CRITIQUE_ATTEMPTS}) reached, finalizing answer")
            return Command(goto=END)
        
        question = state.get("rag_query") or _latest_user_text(state["messages"])
        answer = state["messages"][-1].content
        
        structured_output_model = response_model.with_structured_output(CritiqueResult)
        
        @retry_on_error(logger=logger)
        def invoke_model():
            return structured_output_model.invoke([
                HumanMessage(content=critique_prompt.format(
                    question=question,
                    answer=answer
                ))
            ])
        
        response = invoke_model()
        logger.info(f"Critique result - needs refinement: {response.needs_refinement}")
        
        if response.needs_refinement and response.feedback:
            logger.info(f"Critique issues: {response.issues}")
            return Command(
                goto="generate_answer",
                update={
                    "critique_attempts": critique_attempts + 1,
                    "critique_feedback": response.feedback
                }
            )
        
        logger.info("Answer passed critique, finalizing")
        return Command(goto=END)
        
    except Exception as e:
        logger.error(f"Error in critique_answer: {e}")
        return Command(goto=END)


# ===== ASSEMBLE THE GRAPH =====
workflow = StateGraph(AgentState, input_schema=AgentInputState)

# Define the nodes
workflow.add_node("generate_query_or_respond", generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node("score_document", score_document)
workflow.add_node("improve", improve)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("critique_answer", critique_answer)

# Define workflow edges
workflow.add_edge(START, "generate_query_or_respond")
workflow.add_edge("retrieve", "score_document")
workflow.add_edge("improve", "generate_query_or_respond")
workflow.add_edge("generate_answer", "critique_answer")  # New: go to critique after answer

medical_info_graph = workflow.compile()

# Guard graph visualization
if __name__ == "__main__":
    output_path = Path("medical_info_graph.png")
    medical_info_graph.get_graph().draw_mermaid_png(output_file_path=output_path)
    logger.info(f"Graph exported to {output_path.resolve()}")
    
    for chunk in medical_info_graph.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "2 hospitals in sri lanka",
                }
            ]
        }
    ):
        for node, update in chunk.items():
            logger.info(f"Update from node: {node}")
            if not update:
                continue

            messages = update.get("messages")
            if not messages:
                continue

            terminal_message = messages[-1]
            if hasattr(terminal_message, "pretty_print"):
                terminal_message.pretty_print()
            else:
                logger.info(terminal_message)
