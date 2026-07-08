import asyncio
import logging
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the RAG service functions
from services.rag import add_texts_to_rag, retrieve_context

async def run_test():
    print("========================================")
    print("[TEST] STARTING RAG VECTOR DB TEST")
    print("========================================")
    
    # Generate a fake session ID for testing
    test_session_id = str(uuid.uuid4())
    print(f"[*] Generated Test Session ID: {test_session_id}")
    
    # 1. Dummy data to ingest
    # We will simulate the raw text scraped from a webpage
    dummy_scraped_text = """
    Anthropic has just announced its Series F funding round, securing $4 billion in new capital. 
    The round was heavily supported by major tech giants and venture capitalists.
    This brings their total valuation to nearly $18 billion.
    
    In product news, Anthropic released the new 'Mythos' language model, designed specifically 
    for regulated industries like healthcare and finance. Mythos boasts a 99.9% compliance rate 
    with standard financial regulations and can process up to 250,000 tokens of context.
    
    The company continues to focus on AI safety, releasing Constitutional AI v2.0 framework
    for better alignment.
    """
    
    dummy_url = "https://example-news.com/anthropic-funding"
    
    print("\n[1] Ingesting dummy raw HTML text into ChromaDB...")
    # Add text to RAG (this will chunk it and create embeddings)
    await add_texts_to_rag(session_id=test_session_id, text=dummy_scraped_text, url=dummy_url)
    print("    [OK] Ingestion complete!")
    
    # 2. Test Retrieval
    test_queries = [
        "How much money did Anthropic raise in their latest funding round?",
        "What is the name of Anthropic's new language model and what industries is it for?",
        "What is their token context limit?"
    ]
    
    print("\n[2] Testing Vector Similarity Search Retrieval...")
    for query in test_queries:
        print(f"\n   [?] Query: '{query}'")
        
        # Retrieve the top 2 chunks
        results = await retrieve_context(session_id=test_session_id, query=query, top_k=2)
        
        if results:
            print(f"   [!] Retrieved {len(results)} chunks from ChromaDB:")
            for i, res in enumerate(results):
                print(f"      --- Chunk {i+1} ---")
                print(f"      {res.strip()}")
        else:
            print("   [X] No chunks retrieved!")
            
    print("\n========================================")
    print("[OK] RAG TEST COMPLETE")
    print("========================================")

if __name__ == "__main__":
    # Ensure we run from the backend directory so paths line up
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the async test
    asyncio.run(run_test())
