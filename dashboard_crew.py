import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from datetime import datetime
import argparse 

# --- 1. CONFIGURATION ---
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY") 

# --- 2. DEFINE THE DILIGENCE TASKS (Helper Function) ---
# We make this a helper function that *takes agents* as arguments
def create_diligence_tasks(business_idea, market_analyst, financial_analyst, risk_analyst, investment_advisor):
    
    market_analysis_task = Task(
        description=f"Conduct a detailed market analysis for the business idea: '{business_idea}'. "
                    "Your report must include sections for TAM/SAM/SOM sizing and a full "
                    "Porter's Five Forces analysis. "
                    "Conclude with a final, data-driven summary of the market.",
        expected_output="A structured market analysis report formatted in Markdown, ending with a "
                        "concise 'Market Analysis Summary'.",
        agent=market_analyst
    )

    financial_projection_task = Task(
        description="Based on the market analysis summary, create a 3-year pro-forma financial projection. "
                    "**Crucially, you MUST generate a 5-case scenario analysis:** "
                    "1. Worst Case (e.g., minimal market penetration, high CAC) "
                    "2. Bad Case "
                    "3. Usual Case (This is your most likely baseline) "
                    "4. Good Case "
                    "5. Ideal Case (e.g., rapid adoption, low CAC) "
                    "For each scenario, clearly state your key assumptions (e.g., pricing, customer acquisition, churn) and project "
                    "Revenue, Net Profit, and an estimated seed funding requirement. "
                    "Format this output as a series of Markdown tables for easy parsing. "
                    "Conclude with a final, data-driven 'Financial Outlook Summary'.",
        expected_output="A structured financial projection report in Markdown. It MUST include "
                        "a main assumptions table and a 5-case scenario projection table. "
                        "It must end with a concise 'Financial Outlook Summary'.",
        agent=financial_analyst,
        context=[market_analysis_task]
    )

    risk_analysis_task = Task(
        description="Based on the market summary and the 5-case financial projections, conduct a comprehensive risk analysis. "
                    "Your SWOT analysis must be directly informed by the scenarios (e.g., the 'Worst Case' scenario informs 'Threats', "
                    "the 'Ideal Case' scenario informs 'Opportunities'). "
                    "Your risk register must identify the top 5 risks with mitigation strategies. "
                    "Conclude with a final, data-driven 'Risk Profile Summary'.",
        expected_output="A structured risk analysis report in Markdown, with a SWOT analysis and risk register. "
                        "It must end with a concise 'Risk Profile Summary'.",
        agent=risk_analyst,
        context=[market_analysis_task, financial_projection_task]
    )

    investment_memo_task = Task(
        description="Synthesize the 'Market Analysis Summary', 'Financial Outlook Summary', and 'Risk Profile Summary' into a final investment memo. "
                    "The memo should be addressed to the 'Kairos Investment Committee' and must include: "
                    "1. Executive Summary. "
                    "2. The Core Opportunity. "
                    "3. Key Strengths & Risks (informed by the SWOT). "
                    "4. Financial Outlook (summarizing the 5-case scenarios). "
                    "5. Final Verdict ('Recommend' or 'Decline') with a 2-sentence justification, "
                    "stating which scenario you believe is most likely.",
        expected_output="A final, polished investment memo in Markdown format.",
        agent=investment_advisor,
        context=[market_analysis_task, financial_projection_task, risk_analysis_task]
    )
    
    return [market_analysis_task, financial_projection_task, risk_analysis_task, investment_memo_task]

# --- 3. CREATE THE CALLABLE FUNCTION FOR THE APP ---
def run_kairos_crew(topic: str) -> str:
    """
    Runs the Kairos Diligence Crew for a given topic and returns the raw
    Markdown report.
    """

    # --- THIS IS THE FIX ---
    # Initialize all tools and agents INSIDE the function.
    GENERATION_MODEL_NAME = "gemini/gemini-2.5-flash" 
    
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

    risk_analyst = Agent(
        role=os.getenv("RISK_ANALYST_ROLE"),
        goal=os.getenv("RISK_ANALYST_GOAL"),
        backstory=os.getenv("RISK_ANALYST_BACKSTORY"),
        verbose=True,
        allow_delegation=False,
        llm=GENERATION_MODEL_NAME
    )

    investment_advisor = Agent(
        role=os.getenv("INVESTMENT_ADVISOR_ROLE"),
        goal=os.getenv("INVESTMENT_ADVISOR_GOAL"),
        backstory=os.getenv("INVESTMENT_ADVISOR_BACKSTORY"),
        verbose=True,
        allow_delegation=False,
        llm=GENERATION_MODEL_NAME
    )
    # --- END OF FIX ---
    
    print(f"🚀 Starting Kairos Diligence Dashboard Run (v2 - 5-Case Scenario) for: '{topic}'...")
    
    diligence_tasks = create_diligence_tasks(topic, market_analyst, financial_analyst, risk_analyst, investment_advisor)
    
    dashboard_crew = Crew(
        agents=[market_analyst, financial_analyst, risk_analyst, investment_advisor],
        tasks=diligence_tasks,
        process=Process.sequential,
        verbose=True
    )
    
    # Kick off the work
    result = dashboard_crew.kickoff()
    
    final_memo = result.raw if hasattr(result, 'raw') else str(result)
    
    # --- Save the final memo (optional on server, but good practice) ---
    print("\n\n===== KAIROS DILIGENCE DASHBOARD COMPLETE =====")
    safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Kairos_Diligence_Memo_{safe_topic}_{timestamp}.md"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_memo)
        print(f"✅ Diligence Memo successfully saved to: {filename}")
    except Exception as e:
        print(f"❌ ERROR: Failed to save memo to file. {e}")
    
    return final_memo

# --- 4. MAIN EXECUTION (for command-line testing) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Kairos Diligence Crew to analyze a topic.")
    parser.add_argument("topic", nargs='?', default="A B2B SaaS platform that uses AI to automate compliance and reporting for small to medium-sized financial institutions in India.", help="The topic for the crew to research and analyze.")
    args = parser.parse_args()
    
    run_kairos_crew(args.topic)