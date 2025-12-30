import os
import chromadb
from langchain_community.document_loaders import TextLoader
import sys
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
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel,Field

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AGENTS_ROOT = Path(__file__).resolve().parents[2]
if str(AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENTS_ROOT))

from agents.src.prompts.medi_info import score_document_prompt,rewrite_prompt,generate_prompt
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# ===== CONFIGURATION =====
from dotenv import load_dotenv
load_dotenv()

from src.graph.state import AgentState, AgentInputState

# ===== DATA INGEST =====
data_path = AGENTS_ROOT / "data" / "MI_data.md"

# Load the medical info document and print its text content
loader = TextLoader(data_path)
docs = loader.load()

docs=docs[0].page_content

# Split
character_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""],
    chunk_size=200,
    chunk_overlap=50
)

splits = character_splitter.split_text(docs)

dense_documents = [Document(page_content=text, metadata={"id": str(i), "source": "dense"}) for i, text in enumerate(splits)]
sparse_documents = [Document(page_content=text, metadata={"id": str(i), "source": "sparse"}) for i, text in enumerate(splits)]

# ===== RETRIEVAL STACK =====
embedding_function = OpenAIEmbeddings()
collection_name = "medical_info"
# Chroma Vector Store
chroma_client = chromadb.Client()
vectorstore = Chroma.from_documents(
    documents=dense_documents,
    embedding=embedding_function,
    collection_name=collection_name,
    client=chroma_client
)


# Combine a dense retriever with BM25 so factual answers benefit from both semantic and lexical matches.
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
sparse_retriever = BM25Retriever.from_documents(sparse_documents, k=5)
ensemble_retriever = EnsembleRetriever(retrievers=[dense_retriever, sparse_retriever], weights=[0.5, 0.5], c=0)

# ===== RETRIEVAL TOOL =====
@tool
def retrieve_medical_info(query: str) -> str:
    """
    Retrieve medical information related to the provided query using the ensemble retriever.
    Args:
    query (str): Natural-language question or keyword  string describing the medical information to fetch.
    Returns:
    str: Concatenated textual content of all retrieved documents separated by blank lines.
    """
    docs = ensemble_retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])

retriever_tool = retrieve_medical_info
response_model = init_chat_model("gpt-4o", temperature=0)


# ===== GRAPH NODES =====
def generate_query_or_respond(state: AgentState) -> Command[Literal["retrieve", "__end__"]]:
    """Let the model either issue a retrieval tool call or directly answer the user."""
    response = (
        response_model
        .bind_tools([retriever_tool]).invoke(state["messages"])
    )

    if response.tool_calls:
        return Command(goto="retrieve", update={"messages": [response]})

    return Command(goto=END, update={"messages": [response]})


def score_document(state: AgentState) -> Command[Literal["generate_answer", "improve"]]:
    
    #Data model - returns a binary score for the relevance check
    class scoring(BaseModel):
        binary_score: str = Field(description="relevence score 'yes' or 'no' ")
    
    structured_output_model = response_model.with_structured_output(scoring)

    latest_context = state["messages"][-1].content
    original_question = state["messages"][0].content

    response = structured_output_model.invoke([
        HumanMessage(content=score_document_prompt.format(
            context=latest_context,
            question=original_question
        ))
    ])

    score = response.binary_score

    if score == 'yes':
        return Command(
            goto="generate_answer"
        )
    else:
        return Command(
            goto="improve"
        )


# Improve node
def improve(state: AgentState):
    """Rewrite the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = rewrite_prompt.format(question=question)
    response = response_model.invoke([{"role": "user", "content":prompt}])
    return {"messages": [HumanMessage(content=response.content)]}

# Generate node
def generate_answer(state: AgentState):
    """Generate an answer."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = generate_prompt.format(question=question, context=context)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}

#Assemble the graph
workflow = StateGraph(AgentState, input_schema=AgentInputState)

# Define the nodes
workflow.add_node("generate_query_or_respond", generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node("score_document", score_document)
workflow.add_node("improve", improve)
workflow.add_node("generate_answer", generate_answer)

#define worksflow
workflow.add_edge(START, "generate_query_or_respond")
workflow.add_edge("retrieve", "score_document")
workflow.add_edge("improve", "generate_query_or_respond")
workflow.add_edge("generate_answer", END)

medical_info_graph = workflow.compile()

graph_output_path = Path("medical_info_graph.png")
medical_info_graph.get_graph().draw_mermaid_png(output_file_path=graph_output_path)
print(f"Graph exported to {graph_output_path.resolve()}")



