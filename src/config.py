"""Configuration for Gmail RAG."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))
    
    # Gmail
    MAX_EMAILS = int(os.getenv("MAX_EMAILS", "500"))
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # Embeddings & RAG
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    TOP_K_RESULTS = 5
    
    # ChromaDB
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    COLLECTION_NAME = "gmail_emails"
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required. Set it in .env file")
