"""Email processing and document preparation for RAG."""
from bs4 import BeautifulSoup
import re
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import Config


class EmailProcessor:
    """Process emails for RAG."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
    
    def clean_text(self, text):
        """Clean email text."""
        # Remove HTML
        text = BeautifulSoup(text, 'html.parser').get_text()
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def process_emails(self, emails):
        """Process emails into documents with full content."""
        documents = []
        print(f"Processing {len(emails)} emails...")
        
        skipped = 0
        for email in emails:
            subject = email.get('subject', 'No Subject')
            # Always prefer full body over snippet
            body = email.get('body', '').strip()
            if not body:
                body = email.get('snippet', '').strip()
            
            body = self.clean_text(body)
            
            # Only skip if completely empty
            if not body:
                skipped += 1
                continue
            
            doc = Document(
                page_content=f"Subject: {subject}\n\nContent: {body}",
                metadata={
                    'email_id': email['id'],
                    'message_id': email.get('message_id', email['id']),
                    'thread_id': email.get('thread_id', email['id']),
                    'subject': subject,
                    'sender': email.get('sender', 'Unknown'),
                    'date': email.get('date', 'Unknown'),
                    'source': 'gmail'
                }
            )
            documents.append(doc)
        
        print(f"✓ Created {len(documents)} documents (skipped {skipped} empty emails)")
        return documents
    
    def chunk_documents(self, documents):
        """Split documents into chunks."""
        print(f"Chunking {len(documents)} documents...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"✓ Created {len(chunks)} chunks")
        return chunks
    
    def prepare_for_rag(self, emails):
        """Process and chunk emails for RAG."""
        documents = self.process_emails(emails)
        return self.chunk_documents(documents)
