"""RAG engine for Gmail semantic search."""
import os
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from config import Config


class LocalEmbeddings:
    """Wrapper for sentence-transformers to work with Chroma."""
    
    def __init__(self, model_name, device="cpu"):
        self.model = SentenceTransformer(model_name, device=device)
    
    def embed_documents(self, texts):
        """Embed a list of documents."""
        return self.model.encode(texts, show_progress_bar=False).tolist()
    
    def embed_query(self, text):
        """Embed a single query."""
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


class RAGEngine:
    """RAG engine for semantic search over Gmail."""

    def __init__(self, persist_directory=None):
        self.persist_directory = persist_directory or Config.CHROMA_PERSIST_DIRECTORY
        Config.validate()

        # Local embeddings (sentence-transformers directly)
        self.embeddings = LocalEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            device=Config.EMBEDDING_DEVICE
        )
        self.vectorstore = None
        self._client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None

        # Load existing vectorstore
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            self._load_vectorstore()

    def _load_vectorstore(self):
        self.vectorstore = Chroma(
            collection_name=Config.COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def create_vectorstore(self, documents):
        """Create vectorstore from documents."""
        if not documents:
            raise ValueError("No documents provided")

        os.makedirs(self.persist_directory, exist_ok=True)
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=Config.COLLECTION_NAME,
            persist_directory=self.persist_directory
        )

    def semantic_search(self, query, k=5):
        """Search without LLM (used by agent tools)."""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized")
        return self.vectorstore.similarity_search(query, k=k)
    
    def _call_llm_simple(self, prompt, max_tokens=500):
        """Simple LLM call for agent tools (OpenAI only)."""
        if not self._client:
            raise ValueError("OpenAI client not initialized")
        resp = self._client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=Config.TEMPERATURE,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content or ""

    def get_stats(self):
        """Get vectorstore stats."""
        if not self.vectorstore:
            return {"status": "not_initialized", "document_count": 0}
        
        try:
            count = self.vectorstore._collection.count()
        except:
            count = 0

        return {
            "status": "initialized",
            "document_count": count
        }
