import os
import chromadb
from langchain_community.document_loaders import TextLoader
import sys
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain.tools import tool
from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

data_path = PROJECT_ROOT / "agents" / "data" / "MI_data.md"

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


dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
sparse_retriever = BM25Retriever.from_documents(sparse_documents, k=5)
ensemble_retriever = EnsembleRetriever(retrievers=[dense_retriever, sparse_retriever], weights=[0.5, 0.5], c=0)

@tool
def retrieve_medical_info(query: str) -> list[str]:
    """
    Retrieve medical information related to the provided query using the ensemble retriever.
    Args:
    query (str): Natural-language question or keyword string describing the medical information to fetch.
    Returns:
    str: Concatenated textual content of all retrieved documents separated by blank lines.
    """
    docs = ensemble_retriever.invoke(query)
    # "\n\n".join([doc.page_content for doc in docs])
    return docs

retriever_tool = retrieve_medical_info

docs = retriever_tool.invoke({"query": "Underweight mothers "})

for doc in docs:
    print("\n#################")
    print(doc)