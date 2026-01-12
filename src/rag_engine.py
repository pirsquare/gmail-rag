"""RAG engine for Gmail semantic search."""
import os
from typing import List, Dict
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from .config import Config


class RAGEngine:
    """RAG engine for semantic search over Gmail."""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize RAG engine.
        
        Args:
            persist_directory: Directory to persist ChromaDB
        """
        self.persist_directory = persist_directory or Config.CHROMA_PERSIST_DIRECTORY
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.vectorstore = None
        self.conversation_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Load existing vectorstore if it exists
        if os.path.exists(self.persist_directory):
            self._load_vectorstore()
    
    def _load_vectorstore(self):
        """Load existing vectorstore from disk."""
        print(f"Loading existing vector database from {self.persist_directory}...")
        self.vectorstore = Chroma(
            collection_name=Config.COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        print(f"✓ Loaded vector database with {self.vectorstore._collection.count()} documents")
    
    def create_vectorstore(self, documents: List[Document]):
        """
        Create and persist vectorstore from documents.
        
        Args:
            documents: List of documents to embed
        """
        print(f"Creating vector database with {len(documents)} documents...")
        
        # Create vectorstore
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=Config.COLLECTION_NAME,
            persist_directory=self.persist_directory
        )
        
        print(f"✓ Created and persisted vector database to {self.persist_directory}")
    
    def setup_conversation_chain(self):
        """Set up conversational retrieval chain."""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Run create_vectorstore or load first.")
        
        # Create custom prompt
        prompt_template = """You are a helpful AI assistant that answers questions based on the user's Gmail inbox.
        
Use the following context from emails to answer the question. If you cannot find the answer in the context, say so.
Always cite which email(s) you're referencing by mentioning the subject line.

Context from emails:
{context}

Question: {question}

Helpful Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create LLM
        llm = ChatOpenAI(
            model_name=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Create retrieval chain
        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": Config.TOP_K_RESULTS}
            ),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": PROMPT}
        )
        
        print("✓ Conversation chain ready")
    
    def query(self, question: str) -> Dict:
        """
        Query the RAG system.
        
        Args:
            question: User question
        
        Returns:
            Dictionary with answer and source documents
        """
        if not self.conversation_chain:
            self.setup_conversation_chain()
        
        response = self.conversation_chain({"question": question})
        
        return {
            "answer": response["answer"],
            "source_documents": response["source_documents"],
            "chat_history": response.get("chat_history", [])
        }
    
    def semantic_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Perform semantic search without LLM.
        
        Args:
            query: Search query
            k: Number of results
        
        Returns:
            List of relevant documents
        """
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized")
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def reset_conversation(self):
        """Reset conversation memory."""
        self.memory.clear()
        print("✓ Conversation history cleared")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector database."""
        if not self.vectorstore:
            return {"status": "not_initialized"}
        
        count = self.vectorstore._collection.count()
        return {
            "status": "initialized",
            "document_count": count,
            "persist_directory": self.persist_directory
        }


if __name__ == "__main__":
    # Test RAG engine
    from .email_processor import EmailProcessor
    
    sample_emails = [
        {
            'id': '123',
            'subject': 'Meeting Tomorrow',
            'sender': 'john@example.com',
            'date': '2024-01-01',
            'body': 'Hi, let\'s meet tomorrow at 3pm to discuss the project. Looking forward to it!'
        }
    ]
    
    # Process emails
    processor = EmailProcessor()
    documents = processor.prepare_for_rag(sample_emails)
    
    # Create RAG engine
    rag = RAGEngine()
    rag.create_vectorstore(documents)
    
    # Test query
    result = rag.query("When is the meeting?")
    print(f"\nAnswer: {result['answer']}")
