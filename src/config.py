"""Configuration for Gmail RAG."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # LLM Provider ('openai' or 'ollama')
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Ollama (for local LLM)
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Gmail
    MAX_EMAILS = int(os.getenv("MAX_EMAILS", "500"))
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # Embeddings & RAG
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # ChromaDB
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    COLLECTION_NAME = "gmail_emails"
    
    @classmethod
    def validate(cls):
        if cls.LLM_PROVIDER == 'openai' and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required when LLM_PROVIDER=openai. Set it in .env file")
        if cls.LLM_PROVIDER == 'ollama':
            # Ollama doesn't need API key, but should be running
            pass
