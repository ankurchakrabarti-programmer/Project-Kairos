import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from newsapi import NewsApiClient # The new library we just installed

# --- 1. CONFIGURATION ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
news_key = os.getenv("NEWS_API_KEY") # The key you just added to .env

if not gemini_key or not news_key:
    print("❌ ERROR: API keys (GEMINI_API_KEY, NEWS_API_KEY) not found in .env file.")
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
    print(f"✅ [News Ingestor] Successfully connected to ChromaDB collection: {COLLECTION_NAME}")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to ChromaDB.")
    print(f"Details: {e}")
    exit()

def fetch_recent_news(query, language='en', page_size=20):
    """
    Fetches recent news articles from NewsAPI.org based on a query.
    """
    print(f"Researching NewsAPI for: '{query}'...")
    try:
        # Initialize the client
        newsapi = NewsApiClient(api_key=news_key)
        
        # Make the request
        # 'get_everything' is powerful. We sort by 'publishedAt' to get the newest articles.
        # Note: The free tier can only fetch articles from the last month.
        articles = newsapi.get_everything(
            q=query,
            language=language,
            sort_by='publishedAt',
            page_size=page_size
        )
        
        print(f"Found {articles['totalResults']} total results. Processing the first {len(articles['articles'])} articles.")
        return articles['articles']
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch news from NewsAPI.")
        print(f"Details: {e}")
        return []

def process_and_store_articles(articles):
    """
    Processes a list of news articles and stores new ones in ChromaDB.
    This logic is very similar to our arXiv ingestor.
    """
    if not articles:
        print("No articles to process.")
        return

    documents_to_add = []
    metadatas_to_add = []
    ids_to_add = []

    for article in articles:
        # The article URL is a perfect unique ID
        article_id = str(article['url'])
        
        # Format the document content for embedding
        document_content = (
            f"Title: {article['title']}\n"
            f"Source: {article['source']['name']}\n"
            f"Author: {article.get('author', 'N/A')}\n"
            f"Published: {article['publishedAt']}\n"
            f"Content: {article.get('description', '') or article.get('content', '')}"
        )
        
        # Create metadata to store alongside the vector
        metadata = {
            "source": "newsapi.org",
            "title": str(article['title']),
            "published": str(article['publishedAt']),
            "url": article_id
        }
        
        documents_to_add.append(document_content)
        metadatas_to_add.append(metadata)
        ids_to_add.append(article_id)

    # --- CRITICAL: CHECK FOR DUPLICATES ---
    print(f"Checking {len(ids_to_add)} found articles against {collection.count()} items in memory...")
    existing_ids = collection.get(ids=ids_to_add)['ids']
    
    final_documents = []
    final_metadatas = []
    final_ids = []

    for i, doc_id in enumerate(ids_to_add):
        if doc_id not in existing_ids:
            final_documents.append(documents_to_add[i])
            final_metadatas.append(metadatas_to_add[i])
            final_ids.append(ids_to_add[i])

    # --- INGEST NEW ARTICLES ---
    if not final_documents:
        print("All found articles are already in the memory. No new items to add.")
        return

    print(f"Found {len(final_ids)} new articles to add to memory.")
    print("⏳ Generating embeddings with Gemini... (This may take a moment)")
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL_NAME,
            content=final_documents,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        embeddings = result['embedding']

        collection.add(
            embeddings=embeddings,
            documents=final_documents,
            metadatas=final_metadatas,
            ids=final_ids
        )
        
        print(f"\n🎉 SUCCESS! 🎉")
        print(f"Memory successfully updated. {len(final_ids)} new articles added.")

    except Exception as e:
        print(f"❌ ERROR: Failed to ingest new articles.")
        print(f"Details: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Kairos Harvester: NewsAPI Edition...")
    
    # This is a powerful, professional query to find investment signals
    search_query = '("venture capital" OR "startup funding" OR "seed round" OR M&A) AND (AI OR SaaS OR biotech)'
    
    articles = fetch_recent_news(query=search_query, page_size=20)
    
    if articles:
        process_and_store_articles(articles)
    
    print(f"Total items in memory now: {collection.count()}")
    print("Harvester run complete.")

#```
#
#/**3. Run Your New News Harvester**
#
#1.  **Save** your new `ingest_news.py` file.
#2.  In your active `(EarlyStageVCvenv)` terminal, run the script:
#    ```powershell
#    python ingest_news.py
#    ```
#3.  **Analyze the Output:** You should see it connect, find a number of articles, check for duplicates (finding none the first time), and then add the new articles to your memory. The final line should show a new total count (e.g., `Total items in memory now: 35`).
#
#4.  **Run it a second time** to confirm the duplicate check works perfectly. The output should say "All found articles are already in the memory."
#
#**4. Commit Your New Harvester**
#
#Let's save this new capability to your GitHub repository.
#
#1.  In your terminal:
#    ```powershell
#    git add ingest_news.py
#    ```
#2.  Commit the change:
#    ```powershell
#    git commit -m "Feat: Add 'ingest_news' harvester for autonomous pipeline"
#    ```
#3.  Push to the cloud:
#    ```powershell
#    git push
#