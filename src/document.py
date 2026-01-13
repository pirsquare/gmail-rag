"""Document class for RAG pipeline - LangChain-free implementation."""
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Document:
    """A document with content and metadata."""
    
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        """String representation of document."""
        content_preview = self.page_content[:100] + "..." if len(self.page_content) > 100 else self.page_content
        return f"Document(page_content='{content_preview}', metadata={self.metadata})"
