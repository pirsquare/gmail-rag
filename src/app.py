"""Streamlit web interface for Gmail RAG chatbot."""
import streamlit as st
import os
from gmail_client import GmailClient
from email_processor import EmailProcessor
from rag_engine import RAGEngine
from config import Config


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'rag_engine' not in st.session_state:
        st.session_state.rag_engine = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'vectorstore_ready' not in st.session_state:
        st.session_state.vectorstore_ready = False


def load_or_create_vectorstore():
    """Load existing vectorstore or create new one."""
    rag = RAGEngine()
    
    # Check if vectorstore exists
    if os.path.exists(Config.CHROMA_PERSIST_DIRECTORY):
        stats = rag.get_stats()
        if stats['status'] == 'initialized' and stats['document_count'] > 0:
            st.success(f"✓ Loaded {stats['document_count']} documents from vector database")
            return rag, True
    
    return rag, False


def fetch_and_index_emails(rag_engine: RAGEngine, max_emails: int):
    """Fetch emails and create vector database."""
    try:
        with st.spinner('Authenticating with Gmail...'):
            gmail_client = GmailClient()
        
        with st.spinner(f'Fetching up to {max_emails} emails...'):
            emails = gmail_client.fetch_emails(max_results=max_emails)
        
        if not emails:
            st.error("No emails fetched. Please check your Gmail connection.")
            return False
        
        with st.spinner('Processing and embedding emails...'):
            processor = EmailProcessor()
            documents = processor.prepare_for_rag(emails)
            rag_engine.create_vectorstore(documents)
        
        st.success(f"✓ Successfully indexed {len(emails)} emails!")
        return True
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Gmail RAG Chatbot",
        page_icon="📧",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("📧 Gmail RAG Settings")
        st.caption("🔒 Privacy-first: Local embeddings, email stays on your machine")
        
        st.markdown("---")
        
        # Check API key
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_api_key_here":
            st.error("⚠️ OpenAI API key not configured!")
            st.info("Please set OPENAI_API_KEY in your .env file")
            return
        
        st.success("✓ OpenAI API key configured")
        
        st.markdown("---")
        
        # Initialize RAG engine
        if st.session_state.rag_engine is None:
            rag_engine, vectorstore_exists = load_or_create_vectorstore()
            st.session_state.rag_engine = rag_engine
            st.session_state.vectorstore_ready = vectorstore_exists
        
        # Vector database status
        st.subheader("Vector Database")
        stats = st.session_state.rag_engine.get_stats()
        
        if stats['status'] == 'initialized':
            st.success(f"✓ {stats['document_count']} documents indexed")
        else:
            st.warning("⚠️ No emails indexed yet")
        
        st.markdown("---")
        
        # Email indexing
        st.subheader("Index Emails")
        max_emails = st.number_input(
            "Max emails to fetch",
            min_value=10,
            max_value=1000,
            value=100,
            step=10
        )
        
        if st.button("🔄 Fetch & Index Emails", type="primary"):
            if fetch_and_index_emails(st.session_state.rag_engine, max_emails):
                st.session_state.vectorstore_ready = True
                st.rerun()
        
        st.markdown("---")
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            if st.session_state.rag_engine:
                st.session_state.rag_engine.reset_conversation()
            st.rerun()
        
        st.markdown("---")
        st.caption(f"Model: {Config.LLM_MODEL}")
        st.caption(f"Top K: {Config.TOP_K_RESULTS}")
    
    # Main chat interface
    st.title("💬 Chat with Your Gmail Inbox")
    
    if not st.session_state.vectorstore_ready:
        st.info("👈 Please index your emails using the sidebar to get started!")
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources if available
            if "sources" in message and message["sources"]:
                with st.expander("📎 View Sources"):
                    for i, doc in enumerate(message["sources"], 1):
                        st.markdown(f"**Source {i}:** {doc.metadata.get('subject', 'No subject')}")
                        st.caption(f"From: {doc.metadata.get('sender', 'Unknown')} | Date: {doc.metadata.get('date', 'Unknown')}")
                        st.text(doc.page_content[:200] + "...")
                        st.markdown("---")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your emails..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag_engine.query(prompt)
                    answer = response["answer"]
                    sources = response["source_documents"]
                    
                    st.markdown(answer)
                    
                    # Show sources
                    if sources:
                        with st.expander("📎 View Sources"):
                            for i, doc in enumerate(sources, 1):
                                st.markdown(f"**Source {i}:** {doc.metadata.get('subject', 'No subject')}")
                                st.caption(f"From: {doc.metadata.get('sender', 'Unknown')} | Date: {doc.metadata.get('date', 'Unknown')}")
                                st.text(doc.page_content[:200] + "...")
                                st.markdown("---")
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


if __name__ == "__main__":
    main()
