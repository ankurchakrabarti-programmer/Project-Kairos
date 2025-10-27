import os
import chromadb
import arxiv
import google.generativeai as genai
from dotenv import load_dotenv
from dateutil import parser as date_parser # For handling dates

# --- 1. CONFIGURATION ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
    exit()

genai.configure(api_key=gemini_key)

# --- Use our confirmed, working models ---
EMBEDDING_MODEL_NAME = "models/text-embedding-004"
DB_PATH = "kairos_db"
COLLECTION_NAME = "kairos_memory"

# --- 2. CONNECT TO DATABASE ---
try:
    db_client = chromadb.PersistentClient(path=DB_PATH)
    collection = db_client.get_collection(name=COLLECTION_NAME)
    print(f"✅ [arXiv Ingestor] Successfully connected to ChromaDB collection: {COLLECTION_NAME}")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to ChromaDB. Please check your DB path and settings.")
    print(f"Details: {e}")
    exit()

def fetch_recent_arxiv_papers(query="generative ai", max_results=5):
    """
    Fetches recent papers from arXiv based on a query.
    """
    print(f"Researching arXiv for: '{query}'...")
    # Construct the search client
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate # Get the newest papers
    )
    
    results = list(arxiv.Client().results(search)) # Make the request
    print(f"Found {len(results)} recent papers.")
    return results

def process_and_store_papers(papers):
    """
    Processes a list of arXiv papers and stores new ones in ChromaDB.
    """
    new_papers_count = 0
    
    # --- 1. PREPARE DATA FROM ARXIV ---
    # Create lists of data we want to add
    documents_to_add = []
    metadatas_to_add = []
    ids_to_add = []

    for paper in papers:
        # The paper.entry_id is a unique URL like 'http://arxiv.org/abs/2410.12345v1'
        # This is a perfect unique ID for our database.
        paper_id = str(paper.entry_id)
        
        # Format the document for embedding
        document_content = (
            f"Title: {paper.title}\n"
            f"Authors: {', '.join([str(a) for a in paper.authors])}\n"
            f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
            f"Summary: {paper.summary}"
        )
        
        # Create metadata to store alongside the vector
        metadata = {
            "source": "arxiv.org",
            "title": paper.title,
            "published": str(paper.published),
            "url": paper_id
        }
        
        documents_to_add.append(document_content)
        metadatas_to_add.append(metadata)
        ids_to_add.append(paper_id)

    if not ids_to_add:
        print("No papers found to process.")
        return

    # --- 2. CRITICAL: CHECK FOR DUPLICATES ---
    print(f"Checking {len(ids_to_add)} found papers against {collection.count()} items in memory...")
    
    # Check if any of these IDs already exist in the collection
    existing_ids = collection.get(ids=ids_to_add)['ids']
    
    # Prepare final lists *excluding* existing papers
    final_documents = []
    final_metadatas = []
    final_ids = []

    for i, doc_id in enumerate(ids_to_add):
        if doc_id not in existing_ids:
            # This paper is new! Add it to our final lists.
            final_documents.append(documents_to_add[i])
            final_metadatas.append(metadatas_to_add[i])
            final_ids.append(ids_to_add[i])

    # --- 3. INGEST NEW PAPERS ---
    if not final_documents:
        print("All found papers are already in the memory. No new items to add.")
        return

    print(f"Found {len(final_ids)} new papers to add to memory.")
    print("⏳ Generating embeddings with Gemini... (This may take a moment)")
    
    try:
        # Generate embeddings for all new documents in one batch
        result = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=final_documents,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        embeddings = result['embedding']

        # Add the new papers to our ChromaDB collection
        collection.add(
            embeddings=embeddings,
            documents=final_documents,
            metadatas=final_metadatas,
            ids=final_ids
        )
        
        new_papers_count = len(final_ids)
        print(f"\n🎉 SUCCESS! 🎉")
        print(f"Memory successfully updated. {new_papers_count} new papers added to '{COLLECTION_NAME}'.")

    except Exception as e:
        print(f"❌ ERROR: Failed to ingest new papers.")
        print(f"Details: {e}")

# --- 4. MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Kairos Harvester: arXiv Edition...")
    
    # You can change this query to anything you want
    search_query = "generative ai AND (strategy OR finance)"
    
    papers = fetch_recent_arxiv_papers(query=search_query, max_results=10)
    
    if papers:
        process_and_store_papers(papers)
    
    print(f"Total items in memory: {collection.count()}")
    print("Harvester run complete.")