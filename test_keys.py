import os
from dotenv import load_dotenv

# This line loads the .env file and sets the variables as environment variables
load_dotenv()

# Now we can read them using Python's 'os' library
gemini_key = os.getenv("GEMINI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

print("--- Key Loading Test ---")

if gemini_key:
    print(f"✅ Gemini Key Loaded: [Starts with {gemini_key[:4]}...]")
else:
    print("❌ ERROR: Gemini Key not found.")

if tavily_key:
    print(f"✅ Tavily Key Loaded: [Starts with {tavily_key[:4]}...]")
else:
    print("❌ ERROR: Tavily Key not found.")

print("--------------------------")