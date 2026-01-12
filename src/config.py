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
    
    # Gmail Settings
    MAX_EMAILS = int(os.getenv("MAX_EMAILS", "500"))
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # ChromaDB Settings
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    COLLECTION_NAME = "gmail_emails"
    
    # Embedding Settings
    EMBEDDING_MODEL = "text-embedding-ada-002"  # OpenAI embeddings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # RAG Settings
    TOP_K_RESULTS = 5
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in .env file")


# Validate configuration on import
Config.validate()
