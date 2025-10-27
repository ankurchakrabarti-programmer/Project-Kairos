import os
import chromadb
import google.generativeai as genai
from crewai import tools
from dotenv import load_dotenv

# --- 1. CONFIGURATION (Load environment variables) ---
load_dotenv()

# --- 2. DEFINE GLOBAL VARIABLES (but do not initialize!) ---
# We will use these to cache the clients after their first use.
_collection = None
_genai_configured = False
EMBEDDING_MODEL_NAME = "models/text-embedding-004"
DB_PATH = "kairos_db"
COLLECTION_NAME = "kairos_memory"

def _initialize_clients():
    """
    A private helper function to configure clients ONCE on the first tool call.
    This is the core of the fix.
    """
    global _collection, _genai_configured
    
    try:
        # 1. Configure GenAI
        if not _genai_configured:
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                print("❌ ERROR [KairosMemoryTool]: GEMINI_API_KEY secret not found.")
                return False
            genai.configure(api_key=gemini_key)
            _genai_configured = True
            print("✅ [KairosMemoryTool] GenAI configured successfully.")

        # 2. Connect to ChromaDB
        if _collection is None:
            # Note: ChromaDB might be read-only or ephemeral on HF Spaces.
            # We'll use an in-memory client as a fallback.
            try:
                db_client = chromadb.PersistentClient(path=DB_PATH)
                _collection = db_client.get_collection(name=COLLECTION_NAME)
                print(f"✅ [KairosMemoryTool] Successfully connected to Persistent ChromaDB: {COLLECTION_NAME}")
            except Exception as e:
                print(f"⚠️ WARNING [KairosMemoryTool]: Could not load persistent DB ({e}). Using in-memory database.")
                # This is a fallback for read-only filesystems
                db_client = chromadb.Client() 
                _collection = db_client.get_or_create_collection(name=COLLECTION_NAME)

        return True

    except Exception as e:
        print(f"❌ ERROR [KairosMemoryTool]: Failed during client initialization.")
        print(f"Details: {e}")
        return False

# --- 3. DEFINE THE TOOL ---
@tools.tool("Kairos Internal Memory")
def memory_tool(query: str) -> str:
    """
    Searches the Kairos vector database for information relevant to a query.
    Use this tool FIRST to find internal knowledge, past research, or stored facts
    before searching the public web.
    """
    global _collection, _genai_configured
    
    # Run the initialization
    if not _genai_configured or _collection is None:
        if not _initialize_clients():
            return "Error: Kairos Memory (ChromaDB) or GenAI is not configured. Check server logs."

    try:
        # 1. Create the "search fingerprint"
        query_embedding = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=query,
            task_type="RETRIEVAL_QUERY"
        )

        # 2. Query the database
        memory_results = _collection.query(
            query_embeddings=[query_embedding['embedding']],
            n_results=3
        )

        # 3. Extract and format results
        if not memory_results or not memory_results.get('documents') or not memory_results['documents'][0]:
            return "No relevant memories found in the database for this query."

        recalled_memories = "\n".join(memory_results['documents'][0])

        return (
            f"Found {len(memory_results['documents'][0])} relevant memories:\n"
            f"---\n{recalled_memories}\n---"
        )

    except Exception as e:
        print(f"❌ ERROR [KairosMemoryTool._run]: Failed during memory search.")
        print(f"Query: '{query}'")
        print(f"Error Details: {e}") 
        return f"Error encountered while searching memory. The system administrators have been notified."