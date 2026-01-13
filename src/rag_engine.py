"""RAG engine for Gmail semantic search."""
import os
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from openai import OpenAI
from config import Config


class RAGEngine:
    """RAG engine for semantic search over Gmail."""

    def __init__(self, persist_directory=None):
        self.persist_directory = persist_directory or Config.CHROMA_PERSIST_DIRECTORY
        Config.validate()

        # Local embeddings (sentence-transformers)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": Config.EMBEDDING_DEVICE}
        )
        self.vectorstore = None
        self._client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.conversation_history = []

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

    def _retrieve_context(self, query, k):
        """Retrieve relevant documents."""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Run indexing first.")

        docs = self.vectorstore.similarity_search(query, k=k)
        sources = []
        context_parts = []

        for d in docs:
            md = d.metadata or {}
            subject = md.get("subject", "(no subject)")
            sender = md.get("sender", "(unknown)")
            date = md.get("date", "(unknown)")
            snippet = (d.page_content or "").strip()

            sources.append({
                "subject": subject,
                "sender": sender,
                "date": date,
                "snippet": snippet[:400] + ("…" if len(snippet) > 400 else "")
            })
            context_parts.append(
                f"Subject: {subject}\nFrom: {sender}\nDate: {date}\nContent:\n{snippet}\n"
            )

        return "\n---\n".join(context_parts), sources

    def _build_prompt(self, query, context):
        """Build prompt for LLM."""
        system = (
            "You are a helpful assistant that answers questions using Gmail email excerpts. "
            "If the answer is not in the excerpts, say so. Cite emails by Subject line."
        )
        user = f"Question: {query}\n\nEmail excerpts:\n{context}\n\nAnswer concisely and cite sources."
        
        history = self.conversation_history[-Config.MAX_HISTORY_MESSAGES:]
        return [{"role": "system", "content": system}, *history, {"role": "user", "content": user}]

    def query(self, query, k=None):
        """Query the RAG system."""
        k = k or Config.TOP_K_RESULTS
        context, sources = self._retrieve_context(query, k)
        messages = self._build_prompt(query, context)

        resp = self._client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=messages,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_OUTPUT_TOKENS
        )
        answer = resp.choices[0].message.content or ""

        # Update history
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": answer})

        return {
            "answer": answer,
            "sources": sources,
            "source_documents": self.vectorstore.similarity_search(query, k=k)
        }

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
            "document_count": count,
            "conversation_turns": len(self.conversation_history) // 2
        }

    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []

    def semantic_search(self, query, k=5):
        """Search without LLM."""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized")
        return self.vectorstore.similarity_search(query, k=k)
