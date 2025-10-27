import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from newsapi import NewsApiClient

# --- 1. CONFIGURATION ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
news_key = os.getenv("NEWS_API_KEY")

if not gemini_key or not news_key:
    print("❌ ERROR: API keys (GEMINI_API_KEY, NEWS_API_KEY) not found.")
    exit()

genai.configure(api_key=gemini_key)

EMBEDDING_MODEL_NAME = "models/text-embedding-004"
DB_PATH = "kairos_db"
COLLECTION_NAME = "kairos_memory"

# --- 2. CONNECT TO DATABASE ---
try:
    db_client = chromadb.PersistentClient(path=DB_PATH)
    collection = db_client.get_collection(name=COLLECTION_NAME)
    print(f"✅ [India Filings Ingestor] Connected to ChromaDB: {COLLECTION_NAME}")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to ChromaDB. {e}")
    exit()

def fetch_india_financial_news(query, sources, page_size=20):
    """
    Fetches recent news from specific Indian financial sources.
    """
    print(f"Researching Indian financial news for: '{query}'...")
    try:
        newsapi = NewsApiClient(api_key=news_key)
        
        # We use 'get_everything' but scope it to specific, high-quality sources
        articles = newsapi.get_everything(
            q=query,
            sources=','.join(sources), # Comma-separated list of source IDs
            language='en',
            sort_by='publishedAt',
            page_size=page_size
        )
        
        print(f"Found {articles['totalResults']} total results. Processing the first {len(articles['articles'])} articles.")
        return articles['articles']
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch news from NewsAPI.")
        # NewsAPI can throw specific errors if a source is not found on the free plan
        print("Note: The free developer plan for NewsAPI has limitations on which sources can be queried.")
        print(f"Details: {e}")
        return []

# (The process_and_store_articles function is identical to the one in ingest_news.py,
#  so we can copy it here for simplicity or eventually move it to a shared 'utils.py' file)
def process_and_store_articles(articles):
    if not articles:
        print("No articles to process.")
        return

    documents_to_add, metadatas_to_add, ids_to_add = [], [], []

    for article in articles:
        article_id = str(article['url'])
        document_content = (
            f"Title: {article['title']}\n"
            f"Source: {article['source']['name']}\n"
            f"Published: {article['publishedAt']}\n"
            f"Content: {article.get('description', '') or article.get('content', '')}"
        )
        metadata = {
            "source": "newsapi.org", "type": "india_filing_news",
            "title": str(article['title']), "published": str(article['publishedAt']),
            "url": article_id, "company": str(article['source']['name']) # Or parse from title
        }
        documents_to_add.append(document_content)
        metadatas_to_add.append(metadata)
        ids_to_add.append(article_id)

    print(f"Checking {len(ids_to_add)} articles against memory...")
    existing_ids = collection.get(ids=ids_to_add)['ids']
    
    final_documents = [doc for i, doc in enumerate(documents_to_add) if ids_to_add[i] not in existing_ids]
    final_metadatas = [meta for i, meta in enumerate(metadatas_to_add) if ids_to_add[i] not in existing_ids]
    final_ids = [id for id in ids_to_add if id not in existing_ids]

    if not final_documents:
        print("All found articles are already in the memory.")
        return

    print(f"Found {len(final_ids)} new articles to add to memory.")
    print("⏳ Generating embeddings...")
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL_NAME, content=final_documents, task_type="RETRIEVAL_DOCUMENT"
        )
        collection.add(
            embeddings=result['embedding'], documents=final_documents,
            metadatas=final_metadatas, ids=final_ids
        )
        print(f"\n🎉 SUCCESS! 🎉 Memory updated with {len(final_ids)} new articles.")
    except Exception as e:
        print(f"❌ ERROR: Failed to ingest new articles. {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Kairos Harvester: India Financial News Edition...")
    
    # A powerful query to find strategic corporate actions
    search_query = (
        '("quarterly results" OR "board meeting" OR "strategic partnership" OR '
        '"acquisition" OR "demerger" OR "SEBI filing") AND '
        '(Reliance OR "Tata Motors" OR Infosys OR HDFC OR ICICI)'
    )
    
    # High-trust Indian financial news sources available on NewsAPI's free tier
    # (Note: This list can change, 'the-hindu', 'google-news-in' are good options)
    target_sources = ['the-times-of-india', 'google-news-in']
    
    articles = fetch_india_financial_news(query=search_query, sources=target_sources, page_size=15)
    
    if articles:
        process_and_store_articles(articles)
    
    print(f"Total items in memory now: {collection.count()}")
    print("Harvester run complete.")