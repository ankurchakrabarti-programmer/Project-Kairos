import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# --- CONFIGURATION ---
# 1. SET YOUR EMBEDDING MODEL NAME
#    (This is the name you just found from running check_models.py)
EMBEDDING_MODEL_NAME = "models/text-embedding-004" 

# 2. SET THE FOLDER NAME FOR YOUR DATABASE
DB_PATH = "kairos_db"

# 3. SET THE NAME FOR YOUR "COLLECTION" (like a table in SQL)
COLLECTION_NAME = "kairos_memory"

# --- 1. LOAD API KEYS ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
    exit()

print("✅ API Key Loaded.")
genai.configure(api_key=gemini_key)

# --- 2. SOME SAMPLE DOCUMENTS TO "TEACH" OUR AI ---
documents = [
    "QuantumScape, a solid-state battery company, reported promising test results for its QSE-5 cell, delivering high energy density and over 1,000 cycles.",
    "A recent Stanford study highlighted the 'lithium-metal solid-state' (LMFP) battery as a potential game-changer for electric vehicles (EVs), promising a 50% increase in range.",
    "The Indian government announced a new $2 billion PLI (Production Linked Incentive) scheme to boost domestic manufacturing of advanced chemistry cells, focusing on solid-state technology.",
    "Generative AI, particularly transformers, is being used to discover new material compositions for battery electrolytes, dramatically speeding up R&D.",
    "Nvidia's new 'Blackwell' GPU architecture is set to revolutionize AI training, offering massive performance gains for large language models."
]

# We need unique IDs for each document
document_ids = [
    "doc_quantumscape_qse5",
    "doc_stanford_lmfp",
    "doc_india_pli_scheme",
    "doc_genai_materials",
    "doc_nvidia_blackwell"
]

print(f"📚 Found {len(documents)} documents to ingest.")

# --- 3. INITIALIZE THE DATABASE ---
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

print(f"🤖 ChromaDB client initialized. Using collection: '{COLLECTION_NAME}'")

# --- 4. GENERATE EMBEDDINGS AND INGEST DATA ---
print("⏳ Generating embeddings with Gemini... (This may take a moment)")

try:
    # Use Gemini's 'embed_content' function to create the "fingerprints"
    result = genai.embed_content(
        model=EMBEDDING_MODEL_NAME,  # This now uses your confirmed model name
        content=documents,
        task_type="RETRIEVAL_DOCUMENT"
    )
    
    embeddings = result['embedding']
    print("✅ Embeddings generated. Ingesting into database...")

    # --- 5. ADD TO CHROMA DB ---
    collection.add(
        embeddings=embeddings,
        documents=documents,
        ids=document_ids
    )
    
    print("\n🎉 SUCCESS! 🎉")
    print(f"Memory successfully updated. {len(documents)} new items added to '{COLLECTION_NAME}'.")
    
    count = collection.count()
    print(f"Total items in memory: {count}")

except Exception as e:
    print(f"❌ ERROR: Failed to ingest data.")
    print(f"Details: {e}")