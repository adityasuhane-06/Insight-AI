import os
# Force transformers to use PyTorch and skip TensorFlow to bypass Protobuf conflicts
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import logging
from typing import List

# Langchain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Initialize embeddings and Chroma DB
# We use a persistent local directory for Chroma so it survives server restarts
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_data")
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Using a lightweight, fast, local embedding model
try:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
except Exception as e:
    logger.error(f"[rag] Failed to initialize embeddings: {e}")
    embeddings = None

# Create the vector store
if embeddings:
    # Check if we are using Chroma Cloud
    chroma_api_key = os.getenv("CHROMA_API_KEY")
    if chroma_api_key:
        import chromadb
        logger.info("[rag] Initializing Remote ChromaDB Cloud Client")
        chroma_client = chromadb.CloudClient(
            api_key=chroma_api_key,
            tenant=os.getenv("CHROMA_TENANT", "default_tenant"),
            database=os.getenv("CHROMA_DATABASE", "default_database")
        )
        vector_store = Chroma(
            client=chroma_client,
            collection_name="research_data",
            embedding_function=embeddings,
        )
    else:
        logger.info("[rag] Initializing Local Persistent ChromaDB")
        vector_store = Chroma(
            collection_name="research_data",
            embedding_function=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )
else:
    vector_store = None

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

async def add_texts_to_rag(session_id: str, text: str, url: str = ""):
    """
    Split the raw HTML text and embed it into ChromaDB, 
    tagged with the session_id so it can be filtered during retrieval.
    """
    if vector_store is None or not text.strip():
        return
        
    try:
        # Split text into chunks
        chunks = text_splitter.split_text(text)
        
        # Create documents with metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={"session_id": session_id, "url": url}
            )
            for chunk in chunks
        ]
        
        # Generate explicit unique string IDs
        import uuid
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        # Add to vector database
        # Chroma operations are synchronous, but they are fast.
        vector_store.add_documents(documents, ids=ids)
        logger.info(f"[rag] Added {len(documents)} chunks to vector store for session {session_id} (url: {url})")
        
    except Exception as e:
        logger.warning(f"[rag] Failed to add texts to vector store: {e}")

async def retrieve_context(session_id: str, query: str, top_k: int = 5) -> List[str]:
    """
    Retrieve the most relevant raw text chunks for a given query and session_id.
    """
    if vector_store is None:
        return []
        
    try:
        # We use a filter to ONLY search within the current research session
        results = vector_store.similarity_search(
            query,
            k=top_k,
            filter={"session_id": session_id}
        )
        
        formatted_chunks = []
        for res in results:
            url = res.metadata.get("url", "unknown source")
            formatted_chunks.append(f"[Source: {url}]\n{res.page_content}")
            
        return formatted_chunks
        
    except Exception as e:
        logger.warning(f"[rag] Failed to retrieve context: {e}")
        return []
