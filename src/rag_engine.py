"""RAG engine for Gmail semantic search.

This implementation keeps embeddings + vector search local (Chroma + sentence-transformers),
and uses OpenAI only for the final answer generation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from openai import OpenAI

from config import Config


@dataclass
class QueryResult:
    answer: str
    sources: List[Dict]


class RAGEngine:
    """RAG engine for semantic search over Gmail."""

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or Config.VECTORSTORE_DIR

        # Validate required config
        Config.validate()

        # Local embeddings (privacy-focused)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": Config.EMBEDDING_DEVICE},
        )

        self.vectorstore: Optional[Chroma] = None

        # OpenAI client (OpenAI Python SDK v1+)
        self._client = OpenAI(api_key=Config.OPENAI_API_KEY)

        # Keep a short conversation history (optional; used in prompt)
        self.conversation_history: List[Dict[str, str]] = []

        # Load existing vectorstore if present
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            self._load_vectorstore()

    def _load_vectorstore(self) -> None:
        """Load existing vectorstore from disk."""
        self.vectorstore = Chroma(
            collection_name=Config.COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def create_vectorstore(self, documents: List[Document]) -> None:
        """Create and persist a Chroma vectorstore from documents."""
        if not documents:
            raise ValueError("No documents provided to create_vectorstore().")

        os.makedirs(self.persist_directory, exist_ok=True)

        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=Config.COLLECTION_NAME,
            persist_directory=self.persist_directory,
        )
        # Ensure persistence on disk
        self.vectorstore.persist()

    def _retrieve_context(self, query: str, k: int) -> Tuple[str, List[Dict]]:
        """Retrieve relevant documents and format them for the LLM."""
        if not self.vectorstore:
            raise ValueError(
                "Vectorstore not initialized. Run indexing first (run_indexer.py) or create_vectorstore()."
            )

        docs: List[Document] = self.vectorstore.similarity_search(query, k=k)

        sources: List[Dict] = []
        context_parts: List[str] = []

        for d in docs:
            md = d.metadata or {}
            subject = md.get("subject", "(no subject)")
            sender = md.get("sender", "(unknown sender)")
            date = md.get("date", "(unknown date)")
            snippet = (d.page_content or "").strip()

            sources.append(
                {
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "snippet": snippet[:400] + ("…" if len(snippet) > 400 else ""),
                }
            )

            context_parts.append(
                f"Subject: {subject}\nFrom: {sender}\nDate: {date}\nContent:\n{snippet}\n"
            )

        context = "\n---\n".join(context_parts)
        return context, sources

    def _build_prompt(self, query: str, context: str) -> List[Dict[str, str]]:
        system = (
            "You are a helpful assistant that answers questions using the user's Gmail email excerpts. "
            "If the answer is not present in the excerpts, say you can't find it. "
            "When referencing information, cite the email by its Subject line."
        )

        user = f"""Question:
{query}

Email excerpts:
{context}

Instructions:
- Answer concisely.
- If relevant, include a short 'Citations:' section listing the Subject lines you relied on.
"""

        # Keep history short to reduce token usage
        history = self.conversation_history[-Config.MAX_HISTORY_MESSAGES :]
        messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": user}]
        return messages

    def query(self, query: str, k: int = None) -> Dict:
        """Run a RAG query: retrieve context then ask the LLM."""
        k = k or Config.TOP_K_RESULTS
        context, sources = self._retrieve_context(query, k=k)
        messages = self._build_prompt(query, context)

        resp = self._client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=messages,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_OUTPUT_TOKENS,
        )

        answer = resp.choices[0].message.content or ""

        # update history
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": answer})

        return {"answer": answer, "sources": sources}
