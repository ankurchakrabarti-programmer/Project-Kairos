import os
import chromadb
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from datetime import datetime, timedelta
import argparse
import sys
import subprocess

# At the top, after your other imports:
from dotenv import load_dotenv
import os
load_dotenv()

# ...

# --- 2. DEFINE THE SPECIALIST AGENTS ---
market_analyst = Agent(
    role=os.getenv("MARKET_ANALYST_ROLE"),
    goal=os.getenv("MARKET_ANALYST_GOAL"),
    backstory=os.getenv("MARKET_ANALYST_BACKSTORY"),
    verbose=True,
    allow_delegation=False,
    llm=GENERATION_MODEL_NAME
)

financial_analyst = Agent(
    role=os.getenv("FINANCIAL_ANALYST_ROLE"),
    goal=os.getenv("FINANCIAL_ANALYST_GOAL"),
    backstory=os.getenv("FINANCIAL_ANALYST_BACKSTORY"),
    verbose=True,
    allow_delegation=False,
    llm=GENERATION_MODEL_NAME
)

# ... (Do the same for your other agents) ...




# --- 1. IMPORT TIMEZONE LIBRARY ---
try:
    import pytz
except ImportError:
    print("pytz library not found. Installing...")
    # This block ensures pytz is installed if it's missing
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

# --- 4. DEFINE THE AUTONOMOUS AGENTS ---
signal_agent = Agent(
    role='Lead Intelligence Analyst',
    goal='Identify the most significant and strategically relevant new pieces of information added to the knowledge base in the last 24 hours.',
    backstory=(
        "You are the first line of analysis for a top-tier VC firm. "
        "Your expertise is in rapidly scanning large volumes of new data "
        "(patents, news, filings) and identifying the 1-3 'signals' that "
        "truly matter for strategic investment decisions. You ignore noise and "
        "focus exclusively on impactful, non-obvious developments."
    ),
    verbose=True,
    allow_delegation=False,
    llm=GENERATION_MODEL_NAME
)

strategist_agent = Agent(
    role='Lead VC Strategist & Blue Ocean Expert',
    goal='Synthesize the identified signals into a compelling, forward-looking "Kairos Insights Bulletin" for the firm\'s partners.',
    backstory=(
        "You are the star analyst at the firm, known for your ability "
        "to see the second and third-order implications of new developments. "
        "You take the critical signals identified by your team and weave them "
        "into a narrative of emerging threats and Blue Ocean opportunities."
    ),
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
        # Use UTC for reliable comparison
        utc = pytz.UTC
        now = datetime.now(utc)
        cutoff_time = now - timedelta(hours=hours)
        
        all_items = collection.get(include=["metadatas"])
        
        recent_documents = []
        for i, meta in enumerate(all_items['metadatas']):
            if meta is None or 'published' not in meta or meta['published'] is None:
                continue
            
            try:
                # Try parsing full ISO 8601 format (e.g., from newsapi)
                published_date = datetime.fromisoformat(meta['published'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                try:
                    # Try parsing just the date (e.g., from sec harvester)
                    published_date = datetime.strptime(meta['published'], '%Y-%m-%d')
                    published_date = published_date.replace(tzinfo=utc) # Assume UTC
                except (ValueError, TypeError):
                    continue # Skip if format is still wrong
            
            # Ensure cutoff is timezone-aware for comparison
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
    
    # --- THIS IS THE FIX ---
    # Get the *actual* current date in IST
    ist = pytz.timezone('Asia/Kolkata')
    current_date_str = datetime.now(ist).strftime('%B %d, %Y') # e.g., October 26, 2025
    
    # Task 1: Find the Signals
    signal_task = Task(
      description=f"Analyze the following new data ingested in the last {run_hours} hours. Identify the top 1-3 most strategically significant signals. A signal is a piece of information that suggests a new market trend, a competitive threat, a technological breakthrough, or a major policy shift.\n\nNewly Ingested Data:\n---\n{get_recent_memories(hours=run_hours)}",
      expected_output="A numbered list of the 1-3 most important signals, each with a brief explanation of why it is strategically significant. If the input is 'No new significant information has been added...', state that clearly.",
      agent=signal_agent
    )

    # Task 2: Write the Bulletin
    # --- THE PROMPT IS NOW FIXED ---
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
    
    # Create the crew with the specified lookback period
    newsletter_crew = create_newsletter_crew(run_hours=args.hours)
    result = newsletter_crew.kickoff()
    
    print("\n\n===== KAIROS BULLETIN GENERATION COMPLETE =====")
    
    final_report = result.raw if hasattr(result, 'raw') else str(result)
    
    # Use today's date for the filename
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"Kairos_Bulletin_{timestamp}.md"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_report)
        print(f"✅ Bulletin successfully saved to: {filename}")
    except Exception as e:
        print(f"❌ ERROR: Failed to save bulletin to file. {e}")

    print("==========================================")