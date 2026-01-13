"""CLI script to index Gmail emails into vector database."""
import argparse
from gmail_client import GmailClient
from email_processor import EmailProcessor
from rag_engine import RAGEngine
from db_manager import export_gmail_metadata_to_sqlite
from config import Config


def main():
    """Index Gmail emails via CLI."""
    parser = argparse.ArgumentParser(description='Index Gmail emails for RAG')
    parser.add_argument(
        '--max-emails',
        type=int,
        default=Config.MAX_EMAILS,
        help=f'Maximum number of emails to fetch (default: {Config.MAX_EMAILS})'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-indexing even if vector database exists'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Gmail RAG - Email Indexing")
    print("=" * 60)
    print()
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    # Check if vectorstore exists
    stats = rag_engine.get_stats()
    if stats['status'] == 'initialized' and not args.force:
        print(f"⚠️  Vector database already exists with {stats['document_count']} documents")
        print("   Use --force to re-index")
        return
    
    # Fetch emails
    print("Step 1: Fetching emails from Gmail")
    print("-" * 60)
    gmail_client = GmailClient()
    emails = gmail_client.fetch_emails(max_results=args.max_emails)
    
    if not emails:
        print("❌ No emails fetched. Exiting.")
        return
    
    print()
    
    # Process emails
    print("Step 2: Processing emails")
    print("-" * 60)
    processor = EmailProcessor()
    documents = processor.prepare_for_rag(emails)
    
    print()
    
    # Create vectorstore
    print("Step 3: Creating vector database")
    print("-" * 60)
    rag_engine.create_vectorstore(documents)
    
    print()
    
    # Export metadata to SQLite
    print("Step 4: Exporting metadata to SQLite")
    print("-" * 60)
    export_gmail_metadata_to_sqlite(emails)
    
    print()
    print("=" * 60)
    print("✓ Indexing complete!")
    print(f"  - Indexed {len(emails)} emails")
    print(f"  - Created {len(documents)} document chunks")
    print(f"  - Vector DB: {rag_engine.persist_directory}")
    print(f"  - SQLite DB: data/gmail_stats.db")
    print()
    print("Next steps:")
    print("  - Chat: streamlit run src/app.py")
    print("  - Analytics: streamlit run src/dashboard.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
