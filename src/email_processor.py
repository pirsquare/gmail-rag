"""Email processing and document preparation for RAG."""
from typing import List, Dict
from bs4 import BeautifulSoup
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from .config import Config


class EmailProcessor:
    """Process emails for RAG ingestion."""
    
    def __init__(self):
        """Initialize email processor."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
        )
    
    def clean_text(self, text: str) -> str:
        """
        Clean email text by removing HTML, extra whitespace, etc.
        
        Args:
            text: Raw email text
        
        Returns:
            Cleaned text
        """
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses (keep in metadata instead)
        # text = re.sub(r'\S+@\S+', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?@-]', '', text)
        
        return text.strip()
    
    def process_emails(self, emails: List[Dict]) -> List[Document]:
        """
        Process emails into LangChain documents.
        
        Args:
            emails: List of email dictionaries
        
        Returns:
            List of LangChain Document objects
        """
        documents = []
        
        print(f"Processing {len(emails)} emails into documents...")
        
        for email in emails:
            # Clean and combine email content
            subject = email.get('subject', 'No Subject')
            body = self.clean_text(email.get('body', email.get('snippet', '')))
            
            # Skip if body is too short
            if len(body) < 50:
                continue
            
            # Create content with context
            content = f"Subject: {subject}\n\nContent: {body}"
            
            # Metadata for filtering and display
            metadata = {
                'email_id': email['id'],
                'subject': subject,
                'sender': email.get('sender', 'Unknown'),
                'date': email.get('date', 'Unknown'),
                'source': 'gmail'
            }
            
            # Create document
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            
            documents.append(doc)
        
        print(f"✓ Created {len(documents)} documents from emails")
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for embedding.
        
        Args:
            documents: List of documents
        
        Returns:
            List of chunked documents
        """
        print(f"Splitting {len(documents)} documents into chunks...")
        
        chunks = self.text_splitter.split_documents(documents)
        
        print(f"✓ Created {len(chunks)} chunks")
        return chunks
    
    def prepare_for_rag(self, emails: List[Dict]) -> List[Document]:
        """
        Full pipeline: process emails and chunk for RAG.
        
        Args:
            emails: List of email dictionaries
        
        Returns:
            List of chunked documents ready for embedding
        """
        documents = self.process_emails(emails)
        chunks = self.chunk_documents(documents)
        return chunks


if __name__ == "__main__":
    # Test email processor
    sample_emails = [
        {
            'id': '123',
            'subject': 'Meeting Tomorrow',
            'sender': 'john@example.com',
            'date': '2024-01-01',
            'body': 'Hi, let\'s meet tomorrow at 3pm to discuss the project. Looking forward to it!'
        },
        {
            'id': '124',
            'subject': 'Project Update',
            'sender': 'jane@example.com',
            'date': '2024-01-02',
            'body': 'The latest update on our project shows great progress. We\'ve completed 80% of the features.'
        }
    ]
    
    processor = EmailProcessor()
    chunks = processor.prepare_for_rag(sample_emails)
    
    print(f"\nProcessed {len(chunks)} chunks")
    if chunks:
        print(f"\nFirst chunk:")
        print(f"  Content: {chunks[0].page_content[:100]}...")
        print(f"  Metadata: {chunks[0].metadata}")
