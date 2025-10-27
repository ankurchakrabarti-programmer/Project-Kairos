# Project Kairos - Phase 4: Autonomous Scheduling Guide

## Objective
This guide details the steps to transform our manually-run harvester scripts into a fully autonomous, 24/7 data pipeline using the Windows Task Scheduler.

---

### Prerequisites: The Three Core Paths

For every scheduled task, you will need these three specific pieces of information.

1.  **Program/Script (The Python Engine):**
    This is the full path to the Python executable located *inside* your virtual environment.
    `E:\Code and Scripts\Python\Learn Again\EarlyStageVC\EarlyStageVCvenv\Scripts\python.exe`

2.  **Start in (The Project's Home):**
    This is the root directory of your project. This is crucial so the scripts can find the `.env` file.
    `E:\Code and Scripts\Python\Learn Again\EarlyStageVC`

3.  **Add arguments (The Specific Script):**
    This is the full path to the specific harvester script we want to run. This path will change for each task.

---

### Task 1: Schedule `ingest_news.py` (Global News)

* **Schedule:** Daily at 7:00 AM.
* **Steps:**
    1.  Open **Task Scheduler**.
    2.  Click **"Create Basic Task..."**.
    3.  **Name:** `Kairos Harvester - Global News`
    4.  **Trigger:** Set to **Daily** at `7:00:00 AM`.
    5.  **Action:** Choose **"Start a program"** and fill in:
        * **Program/script:** `E:\Code and Scripts\Python\Learn Again\EarlyStageVC\EarlyStageVCvenv\Scripts\python.exe`
        * **Add arguments:** `E:\Code and Scripts\Python\Learn Again\EarlyStageVC\ingest_news.py`
        * **Start in:** `E:\Code and Scripts\Python\Learn Again\EarlyStageVC`
    6.  Click **Finish**.

### Task 2: Schedule `ingest_arxiv.py` (Academic Papers)
* **Schedule:** Daily at 2:00 AM.
* **Steps:** Repeat the process above with these details:
    * **Name:** `Kairos Harvester - arXiv Papers`
    * **Argument (Script Path):** `E:\Code and Scripts\Python\Learn Again\EarlyStageVC\ingest_arxiv.py`

### Task 3: Schedule `ingest_sec.py` (US Financials)
* **Schedule:** Daily at 9:00 AM.
* **Steps:** Repeat the process with these details:
    * **Name:** `Kairos Harvester - US SEC Filings`
    * **Argument (Script Path):** `E:\Code and Scripts\Python\Learn Again\EarlyStageVC\ingest_sec.py`

### Task 4: Schedule `ingest_india_filings.py` (Indian News/Filings)
* **Schedule:** Daily at 8:00 PM.
* **Steps:** Repeat the process with these details:
    * **Name:** `Kairos Harvester - India Filings`
    * **Argument (Script Path):** `E:\Code and Scripts\Python\Learn Again\EarlyStageVC\ingest_india_filings.py`

### Task 5: Schedule `ingest_market_data.py` (Market Pulse)
* **Schedule:** Daily at 10:00 PM.
* **Steps:** Repeat the process with these details:
    * **Name:** `Kairos Harvester - Market Pulse`
    * **Argument (Script Path):** `E:\Code and Scripts\Python\Learn Again\EarlyStageVC\ingest_market_data.py`

---

### Verification
To verify, open Task Scheduler, click **"Task Scheduler Library"**, and you should see your five new tasks. You can right-click any task and select **"Run"** to test it immediately.