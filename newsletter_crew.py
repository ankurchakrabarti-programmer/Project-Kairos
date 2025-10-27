import os
import chromadb
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from datetime import datetime, timedelta
import argparse
import sys
import subprocess

# --- 1. IMPORT TIMEZONE LIBRARY ---
try:
    import pytz
except ImportError:
    print("pytz library not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytz"])
    import pytz

# --- 2. CONFIGURATION ---
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
GENERATION_MODEL_NAME = "gemini/gemini-2.5-flash" 

DB_PATH = "kairos_db"
COLLECTION_NAME = "kairos_memory"

# --- 3. CONNECT TO DATABASE ---
try:
    db_client = chromadb.PersistentClient(path=DB_PATH)
    collection = db_client.get_collection(name=COLLECTION_NAME)
    print(f"✅ [Newsletter Crew] Successfully connected to ChromaDB.")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to ChromaDB. {e}")
    exit()

# --- 4. DEFINE THE AUTONOMOUS AGENTS (Loading from .env) ---
signal_agent = Agent(
    role=os.getenv("SIGNAL_ANALYST_ROLE"),
    goal=os.getenv("SIGNAL_ANALYST_GOAL"),
    backstory=os.getenv("SIGNAL_ANALYST_BACKSTORY"),
    verbose=True,
    allow_delegation=False,
    llm=GENERATION_MODEL_NAME
)

strategist_agent = Agent(
    # Re-using the same professional prompt from main.py
    role=os.getenv("STRATEGIST_ROLE"),
    goal=os.getenv("STRATEGIST_GOAL"),
    backstory=os.getenv("STRATEGIST_BACKSTORY"),
    verbose=True,
    allow_delegation=False,
    llm=GENERATION_MODEL_NAME
)

# --- 5. DEFINE THE DATA FUNCTION ---
def get_recent_memories(hours=24):
    """
    Queries ChromaDB for documents added in the last X hours.
    """
    try:
        utc = pytz.UTC
        now = datetime.now(utc)
        cutoff_time = now - timedelta(hours=hours)
        
        all_items = collection.get(include=["metadatas"])
        
        recent_documents = []
        for i, meta in enumerate(all_items['metadatas']):
            if meta is None or 'published' not in meta or meta['published'] is None:
                continue
            
            try:
                published_date = datetime.fromisoformat(meta['published'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                try:
                    published_date = datetime.strptime(meta['published'], '%Y-%m-%d')
                    published_date = published_date.replace(tzinfo=utc) 
                except (ValueError, TypeError):
                    continue 
            
            if published_date > cutoff_time:
                doc_id = all_items['ids'][i]
                doc_content = collection.get(ids=[doc_id], include=["documents"])['documents'][0]
                recent_documents.append(f"Source: {meta.get('source', 'N/A')}\nURL: {meta.get('url', 'N/A')}\nContent: {doc_content}")
        
        if not recent_documents:
            return "No new significant information has been added to the knowledge base in the last 24 hours."

        return "\n\n---\n\n".join(recent_documents)
        
    except Exception as e:
        print(f"❌ ERROR: Failed to query recent memories from ChromaDB. {e}")
        return "Error: Could not access the knowledge base."

# --- 6. FUNCTION TO CREATE THE CREW ---
def create_newsletter_crew(run_hours=24):
    """Creates a crew designed to run for a specific lookback period."""
    
    ist = pytz.timezone('Asia/Kolkata')
    current_date_str = datetime.now(ist).strftime('%B %d, %Y')
    
    signal_task = Task(
      description=f"Analyze the following new data ingested in the last {run_hours} hours. Identify the top 1-3 most strategically significant signals. A signal is a piece of information that suggests a new market trend, a competitive threat, a technological breakthrough, or a major policy shift.\n\nNewly Ingested Data:\n---\n{get_recent_memories(hours=run_hours)}",
      expected_output="A numbered list of the 1-3 most important signals, each with a brief explanation of why it is strategically significant. If the input is 'No new significant information has been added...', state that clearly.",
      agent=signal_agent
    )

    strategy_task = Task(
      description=f"Using the list of significant signals provided, synthesize them into a concise, insightful 'Kairos Insights Bulletin'. The bulletin MUST be dated **{current_date_str}**. If no significant signals were found, write a brief 'Forward Posture' memo stating that no new signals were detected and outlining the team's ongoing strategic focus, and still date it **{current_date_str}**.",
      expected_output=f"A professionally formatted Markdown document titled 'Kairos Insights Bulletin' and explicitly dated with **{current_date_str}**.",
      agent=strategist_agent,
      context=[signal_task]
    )

    return Crew(
      agents=[signal_agent, strategist_agent],
      tasks=[signal_task, strategy_task],
      process=Process.sequential,
      verbose=True
    )

# --- 7. KICK OFF THE AUTONOMOUS RUN ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24, help="The lookback period in hours.")
    args = parser.parse_args()

    print(f"🚀 Starting Autonomous Kairos Bulletin Run... (Lookback: {args.hours} hours)")
    
    newsletter_crew = create_newsletter_crew(run_hours=args.hours)
    result = newsletter_crew.kickoff()
    
    print("\n\n===== KAIROS BULLETIN GENERATION COMPLETE =====")
    
    final_report_body = result.raw if hasattr(result, 'raw') else str(result)
    
    ist = pytz.timezone('Asia/Kolkata')
    current_date_str = datetime.now(ist).strftime('%B %d, %Y')
    
    full_report_content = (
        f"# Kairos Insights Bulletin\n\n"
        f"**Date:** {current_date_str}\n\n"
        f"---\n\n"
        f"{final_report_body}"
    )
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"Kairos_Bulletin_{timestamp}.md"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(full_report_content)
        print(f"✅ Bulletin successfully saved to: {filename}")
    except Exception as e:
        print(f"❌ ERROR: Failed to save bulletin to file. {e}")

    print("==========================================")