import os
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq

def get_llm() -> ChatGroq:
    return ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))