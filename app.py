import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime

# Import your two powerful crew "engines"
try:
    from main import run_kairos_crew as run_blue_ocean_crew
except ImportError as e: # --- THIS IS THE FIX ---
    st.error(f"FATAL ERROR ON 'main.py' IMPORT: {e}")
    st.stop()
try:
    from dashboard_crew import run_kairos_crew as run_diligence_crew
except ImportError as e: # --- THIS IS THE FIX ---
    st.error(f"FATAL ERROR ON 'dashboard_crew.py' IMPORT: {e}")
    st.stop()


# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Project Kairos",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GLOBAL STYLING ---
st.markdown("""
    <style>
    /* Import Google Font 'Inter' */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Apply font to all text */
    html, body, [class*="st-"], .st-emotion-cache-16txtl3 {
        font-family: 'Inter', sans-serif;
    }

    /* Clean up headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700; /* Bolder headers */
    }

    /* Ensure all text is dark and legible on light theme */
    body, .st-emotion-cache-16txtl3, .st-emotion-cache-1r6slb0, .st-emotion-cache-ue6h4q, .st-emotion-cache-1y4p8pa {
        color: #212529; /* Dark charcoal color */
    }
    
    /* Sidebar styling */
    .st-emotion-cache-6qob1r {
        background-color: #F8F9FA; /* Very light grey */
    }

    /* Button styling */
    .stButton>button {
        background-color: #004E9A; /* Authoritative Blue */
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #003B73;
        color: white;
    }
    
    /* FIX for text overlap (from your screenshots) */
    div[data-testid="stMarkdown"] {
        word-wrap: break-word; /* Ensures long text wraps */
        overflow-wrap: break-word; /* A more modern property */
    }
    /* Target specific classes for info/warning/error boxes to fix wrap */
    .st-emotion-cache-gh2jqd, .st-emotion-cache-eqpbba, .st-emotion-cache-zw513S, .st-emotion-cache-1wmy9hl { 
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    /* Catch-all for any other Streamlit containers */
    div[class*="st-"] {
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PAGE TITLE & TABS ---
st.title("Project Kairos")
st.subheader("Autonomous Strategic Analysis & Diligence Platform")

tab1, tab2 = st.tabs(["📊 Diligence Co-Pilot", "📰 Kairos Bulletin"])


# --- TAB 1: THE INTERACTIVE DILIGENCE CO-PILOT ---
with tab1:
    st.header("Run New Diligence Report")
    
    col1_form, col2_form = st.columns(2)
    
    with col1_form:
        topic = st.text_input(
            "Enter Business Idea or Company:",
            placeholder="e.g., 'B2B SaaS for AI-powered compliance in India'"
        )
    with col2_form:
        is_hypothetical = st.checkbox("Run as a hypothetical 'what-if' scenario?")
    
    hypothetical_premise = ""
    if is_hypothetical:
        hypothetical_premise = st.text_area(
            "Enter the hypothetical premise:",
            placeholder="e.g., 'What if the Indian govt mandates 100% data localization?'"
        )

    run_button = st.button("Generate Diligence Dashboard")

    st.divider()

    if run_button:
        if not topic:
            st.error("Please enter a business idea or company to analyze.")
        else:
            final_topic = topic
            if is_hypothetical and hypothetical_premise:
                final_topic = (
                    f"Analyze this hypothetical scenario: '{hypothetical_premise}' "
                    f"in the context of the business idea: '{topic}'"
                )

            with st.spinner("🚀 Assembling Specialist Crew... This will take 5-10 minutes..."):
                try:
                    # Call our powerful "dashboard_crew" engine
                    report = run_diligence_crew(final_topic)
                    
                    st.success("Diligence Dashboard Complete!")
                    st.markdown(report)
                    
                    # --- Chart Generation ---
                    try:
                        tables = pd.read_html(report)
                        for i, df in enumerate(tables):
                            if 'Net Profit' in df.columns or 'Revenue' in df.columns:
                                st.subheader(f"Financial Projections")
                                chart_df = df.set_index(df.columns[0]).copy()
                                # Clean data for charting (remove $, ,, (, ))
                                chart_df = chart_df.replace({'\$': '', ',': '', '\(': '-', '\)': ''}, regex=True)
                                chart_df = chart_df.apply(pd.to_numeric, errors='coerce')
                                st.bar_chart(chart_df)
                            elif 'SWOT' in df.to_string() or 'Strengths' in df.columns:
                                st.subheader("SWOT Analysis")
                                st.table(df)
                    except Exception as e:
                        st.warning(f"Could not automatically generate charts. Details: {e}")
                        
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.info("Enter a business idea and click 'Generate Diligence Dashboard' to begin.")


# --- TAB 2: THE AUTONOMOUS KAIROS BULLETIN ---
with tab2:
    st.header("Kairos Insights Bulletin")
    st.markdown("Automated reports generated by our 24/7 scanning crew. New reports appear here daily.")

    # Find all saved bulletin files
    bulletin_files = sorted(glob.glob("Kairos_Bulletin_*.md"), reverse=True)

    if not bulletin_files:
        st.warning("No autonomous bulletins have been generated yet.")
        st.info("The `newsletter_crew.py` script is scheduled to run automatically. "
                "You can also run it manually to generate your first bulletin: "
                "`python newsletter_crew.py`")
    else:
        latest_file = bulletin_files[0]
        
        # Display the most recent bulletin by default
        with open(latest_file, 'r', encoding='utf-8') as f:
            st.markdown(f.read())