"""Configuration management for Gmail RAG application."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    # Storage / vector DB
    VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "./vectorstore")

    # Embeddings
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

    # Indexing / chunking

    # Chat behavior
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
    
    # Gmail Settings
    MAX_EMAILS = int(os.getenv("MAX_EMAILS", "500"))
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # ChromaDB Settings
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    COLLECTION_NAME = "gmail_emails"
    
    # Embedding Settings (Local - No data sent to external APIs)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local sentence-transformer model
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # RAG Settings
    TOP_K_RESULTS = 5
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for LLM. Please set it in .env file")
