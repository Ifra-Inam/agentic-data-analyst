import os
from dotenv import load_dotenv

load_dotenv()

if os.getenv("LANGSMITH_API_KEY"):
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_PROJECT", "agentic-data-analyst")

from langchain_groq import ChatGroq

def get_llm() -> ChatGroq:
    return ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))