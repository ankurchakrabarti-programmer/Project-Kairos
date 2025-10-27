import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import TavilySearchTool
from kairos_tools import memory_tool # Our custom RAG tool

# --- 1. CONFIGURATION ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

# Set the GOOGLE_API_KEY environment variable for CrewAI/LiteLLM
os.environ["GOOGLE_API_KEY"] = gemini_key
os.environ["TAVILY_API_KEY"] = tavily_key

# --- 2. DEFINE THE CALLABLE FUNCTION ---
def run_kairos_crew(topic: str) -> str:
    """
    Runs the Kairos Crew for a given topic and returns the raw
    Markdown report.
    """

    # --- THIS IS THE FIX ---
    # Initialize all tools and agents INSIDE the function.
    # This ensures they are created only when the function is called,
    # by which time all Hugging Face secrets are loaded.
    
    GENERATION_MODEL_NAME = "gemini/gemini-2.5-flash" 

    tavily_tool = TavilySearchTool(api_key=tavily_key, max_results=5)
    
    # --- DEFINE THE "AGENTS" ---
    researcher = Agent(
        role=os.getenv("RESEARCHER_ROLE"),
        goal=os.getenv("RESEARCHER_GOAL"),
        backstory=os.getenv("RESEARCHER_BACKSTORY"),
        verbose=True,
        allow_delegation=False,
        tools=[tavily_tool, memory_tool],
        llm=GENERATION_MODEL_NAME
    )

    strategist = Agent(
        role=os.getenv("STRATEGIST_ROLE"),
        goal=os.getenv("STRATEGIST_GOAL"),
        backstory=os.getenv("STRATEGIST_BACKSTORY"),
        verbose=True,
        allow_delegation=False,
        llm=GENERATION_MODEL_NAME
    )
    
    # --- Define Tasks ---
    research_task = Task(
        description=(
            f'Investigate the topic: "{topic}". '
            'Find the latest breakthroughs, key players, and market trends. '
            'You MUST use the "Kairos Internal Memory" tool first.'
        ),
        expected_output=(
            'A concise, 3-5 bullet point summary of the *most critical* breakthroughs, '
            'key players, and market trends. This summary will be the *only* context '
            'given to the strategist, so make it high-signal.'
        ),
        agent=researcher
    )

    strategy_task = Task(
        description=(
            f'Analyze the research report provided on the topic: "{topic}". '
            'Identify 3-5 novel "Blue Ocean" investment opportunities. '
            'For each opportunity, provide a full analysis using the "Four Actions Framework" '
            '(Eliminate, Reduce, Raise, Create).'
        ),
        expected_output=(
            'A full "Kairos Insight Report" with 3-5 scannable, high-value '
            'opportunities, each with a complete "Four Actions" breakdown.'
        ),
        agent=strategist,
        context=[research_task] 
    )

    # --- Define the Crew ---
    kairos_crew = Crew(
        agents=[researcher, strategist],
        tasks=[research_task, strategy_task],
        process=Process.sequential,
        verbose=True
    )

    # --- Kick off the Work ---
    print(f"Co-pilot: 🫡  OK. Assembling the Kairos Crew to analyze: '{topic}'...")
    kickoff_inputs = {'topic': topic}
    
    try:
        result = kairos_crew.kickoff(inputs=kickoff_inputs)
        
        final_report = result.raw if hasattr(result, 'raw') else str(result)

        # --- Save Output to File (optional on server, but good practice) ---
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Kairos_Report_{safe_topic}_{timestamp}.md"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Kairos Insight Report: {topic}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                f.write(final_report)
            print(f"✅ Report successfully saved to: {filename}")
        except Exception as e:
            # Don't crash the app if file save fails (e.g., read-only filesystem)
            print(f"⚠️ WARNING: Failed to save report to file. {e}")


        return final_report # Return the raw string
            
    except Exception as e:
        print(f"❌ ERROR: Crew kickoff failed.")
        print(f"Details: {e}")
        return f"An error occurred while running the analysis: {e}"

# --- 3. MAIN EXECUTION (for command-line testing) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Kairos Crew to analyze a topic.")
    parser.add_argument("topic", nargs='?', default="Latest trends in Generative AI for education", help="The topic for the crew to research and analyze.")
    args = parser.parse_args()
    
    final_report = run_kairos_crew(args.topic)
    
    print("\n\n===== KAIROS CREW: ANALYSIS COMPLETE =====")
    print(final_report)
    print("==========================================")