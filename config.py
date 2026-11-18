import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

MODEL_NAME = "groq/openai/gpt-oss-120b"

def get_llm():
    """Create the Groq-backed CrewAI LLM after checking configuration."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add your key to the .env file, then restart Streamlit."
        )
    return LLM(
        model=MODEL_NAME,
        api_key=api_key,
        temperature=0.3,
    )
