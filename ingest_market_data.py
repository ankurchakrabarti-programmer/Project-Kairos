import os
import time
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.commodities import Commodities
from datetime import date

# --- 1. CONFIGURATION ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY")

if not gemini_key or not alpha_vantage_key:
    print("❌ ERROR: API keys (GEMINI_API_KEY, ALPHA_VANTAGE_KEY) not found.")
    exit()

genai.configure(api_key=gemini_key)

EMBEDDING_MODEL_NAME = "models/text-embedding-004"
DB_PATH = "kairos_db"
COLLECTION_NAME = "kairos_memory"

# --- 2. CONNECT TO DATABASE ---
try:
    db_client = chromadb.PersistentClient(path=DB_PATH)
    collection = db_client.get_collection(name=COLLECTION_NAME)
    print(f"✅ [Market Pulse Ingestor] Connected to ChromaDB: {COLLECTION_NAME}")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to ChromaDB. {e}")
    exit()

def fetch_and_narrate_market_data():
    """
    Fetches various market data points and converts them into narrative sentences.
    """
    print("Fetching market data from Alpha Vantage...")
    narratives = []
    today = date.today().strftime("%Y-%m-%d")

    try:
        ts = TimeSeries(key=alpha_vantage_key, output_format='pandas')
        co = Commodities(key=alpha_vantage_key, output_format='pandas')

        # 1. US Market: S&P 500 (SPY ETF)
        print(" -> Fetching S&P 500 data...")
        spy_df, _ = ts.get_quote_endpoint(symbol='SPY')
        
        # ** THE FIX **: Check for the correct column name '05. price'
        if not spy_df.empty and '05. price' in spy_df.columns:
            # ** THE FIX **: Use the correct column names from the debug output
            price = spy_df['05. price'].iloc[0]
            change = spy_df['09. change'].iloc[0]
            narratives.append({
                "id": f"market_pulse_spy_{today}",
                "text": f"On {today}, the US stock market index S&P 500 (via SPY ETF) closed at ${price}, a change of ${change} for the day.",
                "meta": {"source": "Alpha Vantage", "type": "market_index", "region": "US", "ticker": "SPY"}
            })
        else:
            print("⚠️ WARNING: SPY data frame was empty or did not contain expected columns.")

        # Increased sleep time to be safe with free tier limits (5 calls/min)
        time.sleep(13)

        # 2. India Market: Reliance Industries (as a proxy)
        print(" -> Fetching India market data...")
        reliance_df, _ = ts.get_quote_endpoint(symbol='RELIANCE.BSE')
        
        if not reliance_df.empty and '05. price' in reliance_df.columns:
            price = reliance_df['05. price'].iloc[0]
            change = reliance_df['09. change'].iloc[0]
            narratives.append({
                "id": f"market_pulse_reliance_{today}",
                "text": f"On {today}, a key indicator for the Indian market, Reliance Industries (RELIANCE.BSE), closed at ₹{price}, a change of ₹{change} for the day.",
                 "meta": {"source": "Alpha Vantage", "type": "market_indicator", "region": "India", "ticker": "RELIANCE.BSE"}
            })
        else:
            print("⚠️ WARNING: Reliance data frame was empty or did not contain expected columns.")

        time.sleep(13)

        # 3. Commodity: WTI Crude Oil
        print(" -> Fetching WTI Crude Oil data...")
        wti_df, _ = co.get_wti(interval='daily')

        if not wti_df.empty and 'value' in wti_df.columns:
            price = wti_df['value'].iloc[0]
            if price != ".":
                narratives.append({
                    "id": f"market_pulse_wti_{today}",
                    "text": f"On {today}, the price of WTI Crude Oil was approximately ${price} per barrel.",
                    "meta": {"source": "Alpha Vantage", "type": "commodity", "region": "Global", "ticker": "WTI"}
                })
        else:
            print("⚠️ WARNING: WTI data frame was empty or did not contain expected columns.")


        print(f"Successfully fetched and narrated {len(narratives)} market data points.")
        return narratives

    except Exception as e:
        print(f"❌ ERROR: Failed to fetch data from Alpha Vantage. Free tier limit may be exceeded or data format is unexpected.")
        print(f"Details: {e}")
        return []

def process_and_store_narratives(narratives):
    """
    Processes a list of narrative sentences and stores new ones in ChromaDB.
    """
    if not narratives:
        print("No market narratives to process.")
        return

    documents_to_add = [n['text'] for n in narratives]
    metadatas_to_add = [n['meta'] for n in narratives]
    ids_to_add = [n['id'] for n in narratives]
    
    print(f"Checking {len(ids_to_add)} narratives against memory...")
    existing_ids = collection.get(ids=ids_to_add)['ids']
    
    final_documents = [doc for i, doc in enumerate(documents_to_add) if ids_to_add[i] not in existing_ids]
    final_metadatas = [meta for i, meta in enumerate(metadatas_to_add) if ids_to_add[i] not in existing_ids]
    final_ids = [id for id in ids_to_add if id not in existing_ids]

    if not final_documents:
        print("All of today's market data is already in memory.")
        return

    print(f"Found {len(final_ids)} new market data points to add.")
    print("⏳ Generating embeddings...")
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL_NAME, content=final_documents, task_type="RETRIEVAL_DOCUMENT"
        )
        collection.add(
            embeddings=result['embedding'], documents=final_documents,
            metadatas=final_metadatas, ids=final_ids
        )
        print(f"\n🎉 SUCCESS! 🎉 Memory updated with {len(final_ids)} new market data points.")
    except Exception as e:
        print(f"❌ ERROR: Failed to ingest new market data. {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Kairos Harvester: Market Pulse Edition...")
    
    narratives = fetch_and_narrate_market_data()
    
    if narratives:
        process_and_store_narratives(narratives)
    
    print(f"Total items in memory now: {collection.count()}")
    print("Harvester run complete.")

