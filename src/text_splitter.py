"""Text splitter implementation - LangChain-free."""
from typing import List, Callable
from .document import Document


class RecursiveCharacterTextSplitter:
    """Split text into chunks recursively by different separators."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
        separators: List[str] = None
    ):
        """
        Initialize text splitter.
        
        Args:
            chunk_size: Maximum size of chunks
            chunk_overlap: Overlap between chunks
            length_function: Function to measure text length
            separators: List of separators to try, in order
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.separators = separators or ["\n\n", "\n", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if self.length_function(text) <= self.chunk_size:
            return [text]
        
        # Find the best separator
        separator = self.separators[-1]
        for sep in self.separators:
            if sep in text:
                separator = sep
                break
        
        # Split by separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
        
        # Combine splits into chunks
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_len = self.length_function(split)
            
            if current_length + split_len + (len(separator) if current_chunk else 0) > self.chunk_size:
                if current_chunk:
                    chunk_text = separator.join(current_chunk)
                    chunks.append(chunk_text)
                    
                    # Handle overlap
                    overlap_chunks = []
                    overlap_length = 0
                    for i in range(len(current_chunk) - 1, -1, -1):
                        chunk_piece_len = self.length_function(current_chunk[i])
                        if overlap_length + chunk_piece_len <= self.chunk_overlap:
                            overlap_chunks.insert(0, current_chunk[i])
                            overlap_length += chunk_piece_len + len(separator)
                        else:
                            break
                    
                    current_chunk = overlap_chunks
                    current_length = overlap_length
            
            current_chunk.append(split)
            current_length += split_len + (len(separator) if len(current_chunk) > 1 else 0)
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(separator.join(current_chunk))
        
        return chunks
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        chunked_docs = []
        
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                # Create new document with same metadata plus chunk info
                metadata = doc.metadata.copy()
                metadata['chunk'] = i
                metadata['total_chunks'] = len(chunks)
                
                chunked_docs.append(Document(
                    page_content=chunk,
                    metadata=metadata
                ))
        
        return chunked_docs
