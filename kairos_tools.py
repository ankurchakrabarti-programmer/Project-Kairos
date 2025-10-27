import os
import chromadb
import google.generativeai as genai
from crewai import tools  # Import the decorator from the core crewai library
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)
EMBEDDING_MODEL_NAME = "models/text-embedding-004" # Your confirmed embedding model
DB_PATH = "kairos_db"
COLLECTION_NAME = "kairos_memory"

# --- 2. INITIALIZE THE DATABASE (runs once when file is imported) ---
try:
    db_client = chromadb.PersistentClient(path=DB_PATH)
    collection = db_client.get_collection(name=COLLECTION_NAME)
    print(f"✅ [KairosMemoryTool] Successfully connected to ChromaDB collection: {COLLECTION_NAME}")
except Exception as e:
    collection = None
    print(f"❌ ERROR [KairosMemoryTool]: Failed to connect to ChromaDB.")
    print(f"Details: {e}")

# --- 3. DEFINE THE TOOL ---
@tools.tool("Kairos Internal Memory") # Use the decorator directly
#def memory_tool(query: str) -> str:
#    """
#    Searches the Kairos vector database for information relevant to a query.
#    Use this tool FIRST to find internal knowledge, past research, or stored facts
#    before searching the public web.
#    """
#    global collection # Use the globally initialized collection
#
#    if collection is None:
#        return "Error: Kairos Memory (ChromaDB) is not connected."
#
#    try:
#        # 1. Create the "search fingerprint" for the agent's query
#        query_embedding = genai.embed_content(
#            model=EMBEDDING_MODEL_NAME,
#            content=query,
#            task_type="RETRIEVAL_QUERY"
#        )
#
#        # 2. Query the database for the top 3 most similar memories
#        memory_results = collection.query(
#            query_embeddings=[query_embedding['embedding']],
#            n_results=3
#        )
#
#        # 3. Extract and format the text from the memory results
#        recalled_memories = "\n".join(memory_results['documents'][0])
#
#        if not recalled_memories:
#            return "No relevant memories found in the database for this query."
#
#        return (
#            f"Found {len(memory_results['documents'][0])} relevant memories:\n"
#            f"---\n{recalled_memories}\n---"
#        )
#
#    except Exception as e:
#        # Provide more specific error feedback to the agent
#        print(f"❌ ERROR [KairosMemoryTool._run]: {e}") # Log the full error
#        return f"Error while searching memory. Please try rephrasing your query or check system logs."
def memory_tool(query: str) -> str:
    """
    Searches the Kairos vector database for information relevant to a query.
    Use this tool FIRST to find internal knowledge, past research, or stored facts
    before searching the public web.
    """
    global collection 

    if collection is None:
        return "Error: Kairos Memory (ChromaDB) is not connected."

    try: # <-- START OF NEW TRY BLOCK
        # 1. Create the "search fingerprint"
        query_embedding = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=query,
            task_type="RETRIEVAL_QUERY"
        )

        # 2. Query the database
        memory_results = collection.query(
            query_embeddings=[query_embedding['embedding']],
            n_results=3
        )

        # 3. Extract and format results
        # Check if results and documents exist and are not empty
        if not memory_results or not memory_results.get('documents') or not memory_results['documents'][0]:
            return "No relevant memories found in the database for this query."

        recalled_memories = "\n".join(memory_results['documents'][0])

        return (
            f"Found {len(memory_results['documents'][0])} relevant memories:\n"
            f"---\n{recalled_memories}\n---"
        )

    except Exception as e: # <-- START OF NEW EXCEPT BLOCK
        # Provide more specific error feedback to the agent
        print(f"❌ ERROR [KairosMemoryTool._run]: Failed during memory search.")
        print(f"Query: '{query}'")
        print(f"Error Details: {e}") # Log the full error for debugging
        # Return a message the agent can understand
        return f"Error encountered while searching memory. The system administrators have been notified. Please try rephrasing your query or continue without this information."