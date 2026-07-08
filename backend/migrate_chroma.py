"""
Migration script: Copy vector embeddings from local ChromaDB to Remote ChromaDB (Aiven/Hosted).
"""
import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

def migrate():
    # Local Client
    persist_dir = os.path.join(os.path.dirname(__file__), "chroma_data")
    if not os.path.exists(persist_dir):
        print(f"Local ChromaDB directory not found at {persist_dir}")
        return
        
    local_client = chromadb.PersistentClient(path=persist_dir)
    try:
        local_collection = local_client.get_collection("research_data")
    except Exception as e:
        print(f"Local collection 'research_data' not found: {e}")
        return

    # Remote Client
    api_key = os.getenv("CHROMA_API_KEY")
    if not api_key:
        print("CHROMA_API_KEY not found in .env")
        return
        
    print("Connecting to Remote ChromaDB Cloud...")
    remote_client = chromadb.CloudClient(
        api_key=api_key,
        tenant=os.getenv("CHROMA_TENANT", "default_tenant"),
        database=os.getenv("CHROMA_DATABASE", "default_database")
    )
    
    print("Creating remote collection 'research_data'...")
    remote_collection = remote_client.get_or_create_collection(
        name="research_data",
        metadata={"hnsw:space": "l2"}
    )
    
    # Fetch local data
    print("Fetching local vector embeddings...")
    data = local_collection.get(include=["embeddings", "metadatas", "documents"])
    
    ids = data.get("ids", [])
    embeddings = data.get("embeddings", [])
    metadatas = data.get("metadatas", [])
    documents = data.get("documents", [])
    
    print(f"Found {len(ids)} chunks to migrate.")
    
    if not ids:
        print("No data to migrate.")
        return
        
    # Chroma handles batching automatically for Python client
    # But it's safer to chunk it into batches of 100
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = i + batch_size
        print(f"Migrating batch {i} to {end}...")
        
        # We need to filter out None embeddings if they weren't fetched properly
        batch_ids = ids[i:end]
        batch_embeddings = embeddings[i:end] if embeddings is not None and len(embeddings) > 0 else None
        batch_metadatas = metadatas[i:end] if metadatas is not None and len(metadatas) > 0 else None
        batch_documents = documents[i:end] if documents is not None and len(documents) > 0 else None
        
        try:
            remote_collection.upsert(
                ids=batch_ids,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                documents=batch_documents
            )
        except Exception as e:
            print(f"Error migrating batch {i}-{end}: {e}")
            
    print("ChromaDB migration complete!")

if __name__ == "__main__":
    migrate()
