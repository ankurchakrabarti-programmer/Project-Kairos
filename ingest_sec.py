import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from sec_api import QueryApi # The new library

# --- 1. CONFIGURATION ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
sec_key = os.getenv("SEC_API_KEY")

if not gemini_key or not sec_key:
    print("❌ ERROR: API keys (GEMINI_API_KEY, SEC_API_KEY) not found.")
    exit()

genai.configure(api_key=gemini_key)

EMBEDDING_MODEL_NAME = "models/text-embedding-004"
DB_PATH = "kairos_db"
COLLECTION_NAME = "kairos_memory"

# Initialize the SEC API client
queryApi = QueryApi(api_key=sec_key)

# --- 2. CONNECT TO DATABASE ---
try:
    db_client = chromadb.PersistentClient(path=DB_PATH)
    collection = db_client.get_collection(name=COLLECTION_NAME)
    print(f"✅ [SEC Ingestor] Connected to ChromaDB: {COLLECTION_NAME}")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to ChromaDB. {e}")
    exit()

def fetch_latest_filings(query, max_results=5):
    """
    Fetches the latest 10-K and 10-Q filings from the SEC EDGAR database.
    """
    print(f"Researching SEC EDGAR for: '{query}'...")
    try:
        response = queryApi.get_filings(query)
        filings = response.get('filings', [])
        
        # Sort by filing date to be sure, and take the latest
        filings.sort(key=lambda x: x['filedAt'], reverse=True)
        recent_filings = filings[:max_results]
        
        print(f"Found {len(filings)} total filings. Processing the latest {len(recent_filings)}.")
        return recent_filings
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch SEC filings. {e}")
        return []

def process_and_store_filings(filings):
    """
    Processes filings, extracts MD&A, and stores new ones in ChromaDB.
    """
    if not filings:
        print("No filings to process.")
        return

    documents_to_add = []
    metadatas_to_add = []
    ids_to_add = []

    for filing in filings:
        # The filing URL is a perfect unique ID
        filing_id = str(filing['linkToFilingDetails'])
        
        try:
            # ** THE MAGIC **: Extract just the MD&A section ("Item 7")
            # This is the most valuable part for strategic analysis.
            print(f"  -> Extracting MD&A from {filing['ticker']} {filing['formType']}...")
            mda_text = queryApi.extract_section(
                filing_url=filing_id,
                section="item7" # 'item7' is MD&A, 'item1a' is Risk Factors
            )

            if not mda_text:
                print(f"  -> No MD&A found for {filing_id}. Skipping.")
                continue

            document_content = (
                f"Company: {filing['companyName']} ({filing['ticker']})\n"
                f"Filing Type: {filing['formType']}\n"
                f"Filed At: {filing['filedAt']}\n"
                f"Period of Report: {filing['periodOfReport']}\n\n"
                f"Management's Discussion and Analysis (MD&A):\n"
                f"---\n{mda_text[:4000]}..." # Truncate for manageability
            )
            
            metadata = {
                "source": "sec.gov",
                "title": f"{filing['ticker']} {filing['formType']} - {filing['periodOfReport']}",
                "published": str(filing['filedAt']),
                "url": filing_id,
                "company": filing['companyName'],
                "ticker": filing['ticker']
            }
            
            documents_to_add.append(document_content)
            metadatas_to_add.append(metadata)
            ids_to_add.append(filing_id)

        except Exception as e:
            print(f"  -> ERROR processing filing {filing_id}. {e}")

    if not ids_to_add:
        print("No new filings with MD&A found to process.")
        return

    # Check for duplicates
    print(f"Checking {len(ids_to_add)} filings against {collection.count()} items in memory...")
    existing_ids = collection.get(ids=ids_to_add)['ids']
    
    final_documents = [doc for i, doc in enumerate(documents_to_add) if ids_to_add[i] not in existing_ids]
    final_metadatas = [meta for i, meta in enumerate(metadatas_to_add) if ids_to_add[i] not in existing_ids]
    final_ids = [id for id in ids_to_add if id not in existing_ids]

    if not final_documents:
        print("All found filings are already in the memory.")
        return

    print(f"Found {len(final_ids)} new filings to add to memory.")
    print("⏳ Generating embeddings with Gemini...")
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=final_documents,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        collection.add(
            embeddings=result['embedding'],
            documents=final_documents,
            metadatas=final_metadatas,
            ids=final_ids
        )
        
        print(f"\n🎉 SUCCESS! 🎉")
        print(f"Memory successfully updated. {len(final_ids)} new filings added.")

    except Exception as e:
        print(f"❌ ERROR: Failed to ingest new filings. {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Kairos Harvester: SEC EDGAR Edition...")
    
    # Query for recent annual (10-K) and quarterly (10-Q) reports
    # for major US tech companies.
    search_query = {
        "query": { "query_string": {
            "query": "formType:\"10-K\" OR formType:\"10-Q\""
        }},
        "from": "0",
        "size": "10",
        "sort": [{ "filedAt": { "order": "desc" }}]
    }
    
    filings = fetch_latest_filings(query=search_query, max_results=5)
    
    if filings:
        process_and_store_filings(filings)
    
    print(f"Total items in memory now: {collection.count()}")
    print("Harvester run complete.")