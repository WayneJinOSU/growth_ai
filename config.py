import os
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY", "yiQrRNxbbe4TofnvMPGPz62QSTuT6Pbe")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "https://openrouter.ai/api/v1")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")

if not FMP_API_KEY:
    print("Warning: FMP_API_KEY not found in environment variables.")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables.")
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not found in environment variables.")

