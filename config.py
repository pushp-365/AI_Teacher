import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file.")

# Initialize global Groq client
client = Groq(api_key=api_key)

DEFAULT_MODEL = "openai/gpt-oss-20b"

# Load model variables from .env
MODEL_PARSER = os.getenv("MODEL_PARSER", "qwen/qwen3.8-27b")
MODEL_ORCHESTRATOR = os.getenv("MODEL_ORCHESTRATOR", DEFAULT_MODEL)
MODEL_PPT = os.getenv("MODEL_PPT", "qwen/qwen3.8-27b")
MODEL_QUIZ = os.getenv("MODEL_QUIZ", DEFAULT_MODEL)
MODEL_SCRIPT = os.getenv("MODEL_SCRIPT", "openai/gpt-oss-120b")
MODEL_REPROMPT = os.getenv("MODEL_REPROMPT", "openai/gpt-oss-120b")