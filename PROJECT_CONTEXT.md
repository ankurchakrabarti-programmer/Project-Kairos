# Project Kairos - Context Brief (As of 2025-10-21)

## 1. Golden Circle (The Vision)

* **WHY:** To systematically create strategic serendipity, giving organizations the peripheral vision to find and build their next "Blue Ocean" before competitors do.
* **HOW:** By using autonomous AI agents to scan diverse global data sources (news, patents, financials, research), find non-obvious connections, and synthesize them into investment opportunities.
* **WHAT:** An AI-powered co-pilot for VCs and strategists that delivers a portfolio of validated, novel business opportunities, complete with diligence dashboards.

## 2. The Chosen Roadmap: "Deep Tech Build"

We are prioritizing the development of the sophisticated backend engine first, before building the final UI.
* **Phase 1-3:** Build the core agentic engine with RAG capabilities. (Completed)
* **Phase 4:** Build and automate a fleet of "harvester" scripts to populate a knowledge base 24/7. (In Progress)
* **Phase 5:** Build an autonomous "Newsletter" crew that uses this data.
* **Phase 6:** Build the "Specialist Dashboard" crew for deep-dive analysis.
* **Phase 7:** Build the final interactive Streamlit UI.

## 3. Current Project Files & Status

* **`main.py`:** The core CrewAI script. Defines the `Researcher` and `Strategist` agents and tasks. Refactored into a callable function `run_kairos_crew()`.
* **`app.py`:** A functional Streamlit web app that provides a UI for `main.py`. (Currently stable, UI enhancements paused).
* **`kairos_tools.py`:** Defines our custom `memory_tool` for agents to query the ChromaDB vector database (RAG).
* **`kairos_db/`:** The local ChromaDB vector database folder (our AI's "memory").
* **`ingest_*.py` files (5 total):** Our fleet of "harvester" scripts for learning from arXiv, NewsAPI, SEC EDGAR, Indian Filings (via NewsAPI), and Alpha Vantage market data.
* **`.env`:** Stores all our secret API keys.

## 4. Current Task

The immediate next step is to complete Phase 4 by using Windows Task Scheduler to automate the execution of our five `ingest_*.py` harvester scripts.