"""Streamlit web interface for Gmail RAG chatbot."""
import streamlit as st
import os
import sys

# Add parent directory to path for agent imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from gmail_client import GmailClient
from email_processor import EmailProcessor
from rag_engine import RAGEngine
from agent.controller import create_agent
from config import Config


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'rag_engine' not in st.session_state:
        st.session_state.rag_engine = None
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'vectorstore_ready' not in st.session_state:
        st.session_state.vectorstore_ready = False
    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = Config.LLM_PROVIDER


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
        
        # Check API key for OpenAI mode
        if st.session_state.llm_provider == 'openai':
            if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_api_key_here":
                st.error("⚠️ OpenAI API key not configured!")
                st.info("Please set OPENAI_API_KEY in your .env file")
                return
            st.success("✓ OpenAI API key configured")
        else:
            st.info(f"🤖 Using Ollama: {Config.OLLAMA_MODEL}")
            st.caption(f"URL: {Config.OLLAMA_BASE_URL}")
        
        st.markdown("---")
        
        # Initialize RAG engine and Agent
        if st.session_state.rag_engine is None:
            rag_engine, vectorstore_exists = load_or_create_vectorstore()
            st.session_state.rag_engine = rag_engine
            st.session_state.agent = create_agent(rag_engine, st.session_state.llm_provider)
            st.session_state.vectorstore_ready = vectorstore_exists
        
        # Vector database status
        st.subheader("Vector Database")
        stats = st.session_state.rag_engine.get_stats()
        
        if stats['status'] == 'initialized':
            st.success(f"✓ {stats['document_count']} documents indexed")
        else:
            st.warning("⚠️ No emails indexed yet")
        
        st.markdown("---")
        
        # LLM Provider selector
        st.subheader("🤖 LLM Provider")
        llm_provider = st.radio(
            "Choose LLM",
            ["openai", "ollama"],
            index=0 if st.session_state.llm_provider == 'openai' else 1,
            help="OpenAI (cloud) or Ollama (local)"
        )
        
        if llm_provider != st.session_state.llm_provider:
            st.session_state.llm_provider = llm_provider
            # Recreate agent with new provider
            if st.session_state.rag_engine:
                st.session_state.agent = create_agent(st.session_state.rag_engine, llm_provider)
                st.success(f"Switched to {llm_provider}")
        
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
            if st.session_state.agent:
                st.session_state.agent.reset()
            st.rerun()
        
        st.markdown("---")
        st.caption(f"Provider: {st.session_state.llm_provider}")
        if st.session_state.llm_provider == 'openai':
            st.caption(f"Model: {Config.LLM_MODEL}")
        else:
            st.caption(f"Model: {Config.OLLAMA_MODEL}")
    
    # Main chat interface
    st.title("💬 Gmail Agent - LlamaIndex Powered")
    
    if not st.session_state.vectorstore_ready:
        st.info("👈 Please index your emails using the sidebar to get started!")
        return
    
    st.caption("🤖 Intelligent agent with 4 tools: search_emails, get_thread, triage_recent, draft_reply")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources if available
            if "sources" in message and message["sources"]:
                with st.expander("📎 View Citations"):
                    for i, src in enumerate(message["sources"], 1):
                        st.markdown(f"**📧 Source {i}**")
                        st.markdown(f"**Subject:** {src.get('subject', 'No subject')}")
                        st.caption(f"**From:** {src.get('sender', 'Unknown')}")
                        st.caption(f"**Date:** {src.get('date', 'Unknown')}")
                        if 'message_id' in src:
                            st.caption(f"**Message ID:** `{src['message_id']}`")
                        if 'thread_id' in src:
                            st.caption(f"**Thread ID:** `{src['thread_id']}`")
                        st.markdown("---")
            
            # Show triage results in table format
            if message.get("is_triage") and "triage_data" in message:
                st.subheader("📥 Emails Needing Reply")
                triage_data = message["triage_data"]
                if triage_data:
                    import pandas as pd
                    df = pd.DataFrame(triage_data)
                    # Select columns to display
                    display_cols = ['subject', 'sender', 'date', 'urgency_score']
                    if all(col in df.columns for col in display_cols):
                        st.dataframe(df[display_cols], use_container_width=True)
            
            # Show draft warning
            if message.get("is_draft"):
                st.warning("⚠️ DRAFT ONLY - Review before sending. Never auto-send.")
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your emails..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from LlamaIndex agent
        with st.chat_message("assistant"):
            with st.spinner("🤖 Agent thinking..."):
                try:
                    # Build chat history for agent
                    chat_history = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.messages[:-1]  # Exclude current message
                    ]
                    
                    # Call agent
                    result = st.session_state.agent.run(prompt, chat_history)
                    
                    # Display response
                    st.markdown(result['response'])
                    
                    # Show citations
                    if result['sources']:
                        with st.expander("📎 View Citations"):
                            for i, src in enumerate(result['sources'], 1):
                                st.markdown(f"**📧 Source {i}**")
                                st.markdown(f"**Subject:** {src.get('subject', 'No subject')}")
                                st.caption(f"**From:** {src.get('sender', 'Unknown')}")
                                st.caption(f"**Date:** {src.get('date', 'Unknown')}")
                                if 'message_id' in src:
                                    st.caption(f"**Message ID:** `{src['message_id']}`")
                                if 'thread_id' in src:
                                    st.caption(f"**Thread ID:** `{src['thread_id']}`")
                                st.markdown("---")
                    
                    # Show triage results
                    if result.get('is_triage') and result.get('needs_reply'):
                        st.subheader("📥 Emails Needing Reply")
                        import pandas as pd
                        df = pd.DataFrame(result['needs_reply'])
                        display_cols = ['subject', 'sender', 'date', 'urgency_score']
                        if all(col in df.columns for col in display_cols):
                            st.dataframe(df[display_cols], use_container_width=True)
                    
                    # Show draft warning
                    if result.get('is_draft'):
                        st.warning("⚠️ DRAFT ONLY - Review before sending. Never auto-send.")
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result['response'],
                        "sources": result['sources'],
                        "is_triage": result.get('is_triage', False),
                        "is_draft": result.get('is_draft', False),
                        "triage_data": result.get('needs_reply', [])
                    })
                
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


if __name__ == "__main__":
    main()
