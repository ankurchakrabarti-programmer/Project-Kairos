import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- 1. LOAD API KEYS ---
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("❌ ERROR: Gemini API key not found. Please check your .env file.")
else:
    try:
        # --- 2. CONFIGURE THE API ---
        genai.configure(api_key=gemini_key)

        print("--- Finding All Available Models ---")
        
        usable_generation_models = []
        usable_embedding_models = []

        # --- 3. ASK GOOGLE FOR THE LIST OF MODELS (CORRECTED) ---
        for m in genai.list_models():
            # Check for "talker" models (for main.py)
            if 'generateContent' in m.supported_generation_methods:
                usable_generation_models.append(m.name)
            
            # Check for "fingerprinter" models (for ingest.py)
            if 'embedContent' in m.supported_generation_methods:
                usable_embedding_models.append(m.name)
        
        print("\n✅ Found Usable GENERATION Models (for main.py):")
        if usable_generation_models:
            for name in usable_generation_models:
                print(f"   - {name}")
        else:
            print("   - None found.")

        print("\n✅ Found Usable EMBEDDING Models (for ingest.py):")
        if usable_embedding_models:
            for name in usable_embedding_models:
                print(f"   - {name}")
        else:
            print("   - None found.")
                
        print("\n---------------------------------")
        print("Please use a 'generation' model in main.py and an 'embedding' model in ingest.py")

    except Exception as e:
        print(f"❌ ERROR: Failed to list models. {e}")