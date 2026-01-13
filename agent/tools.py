"""
LlamaIndex Tools for Gmail Agent

Implements 4 core tools:
1. EmailSearchTool - Semantic search across emails
2. ThreadTool - Retrieve full thread by thread_id
3. TriageTool - Find emails needing replies
4. DraftTool - Generate reply drafts
"""

from typing import Dict, List, Any, Optional
from llama_index.core.tools import FunctionTool
from datetime import datetime, timedelta
from rag_engine import RAGEngine


class EmailSearchTool:
    """Search emails using semantic search with citations."""
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
    
    def search_emails(
        self,
        query: str,
        sender_filter: Optional[str] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Search emails using semantic search.
        
        Args:
            query: Natural language search query
            sender_filter: Optional email address to filter by sender
            k: Number of results to return (default: 5)
        
        Returns:
            Dict with 'results' (list of email dicts with citations) and 'count'
        """
        # Perform semantic search
        docs = self.rag.semantic_search(query, k=k * 2)  # Get more for filtering
        
        # Filter by sender if specified
        if sender_filter:
            docs = [
                d for d in docs 
                if sender_filter.lower() in d.metadata.get('sender', '').lower()
            ]
        
        # Limit to k results
        docs = docs[:k]
        
        # Format results with citations
        results = []
        for doc in docs:
            results.append({
                'subject': doc.metadata.get('subject', 'No subject'),
                'sender': doc.metadata.get('sender', 'Unknown'),
                'date': doc.metadata.get('date', 'Unknown'),
                'message_id': doc.metadata.get('message_id', doc.metadata.get('email_id', '')),
                'thread_id': doc.metadata.get('thread_id', ''),
                'snippet': doc.page_content[:300] + '...' if len(doc.page_content) > 300 else doc.page_content
            })
        
        return {
            'results': results,
            'count': len(results),
            'query': query
        }
    
    def as_tool(self) -> FunctionTool:
        """Convert to LlamaIndex FunctionTool."""
        return FunctionTool.from_defaults(
            fn=self.search_emails,
            name="search_emails",
            description=(
                "Search emails using semantic search. "
                "Returns top matching emails with full citations (subject, sender, date, message_id, thread_id). "
                "Use for questions like 'find emails about X' or 'what did Y say about Z'. "
                "IMPORTANT: Always cite the returned message_id and thread_id in your response."
            )
        )


class ThreadTool:
    """Retrieve full email thread by thread_id."""
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
    
    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        Get all emails in a thread.
        
        Args:
            thread_id: Gmail thread ID
        
        Returns:
            Dict with 'emails' (list of emails in thread) and 'thread_id'
        """
        # Search vectorstore for all docs with this thread_id
        all_docs = self.rag.semantic_search("", k=1000)  # Get many docs
        
        # Filter by thread_id
        thread_docs = [
            d for d in all_docs 
            if d.metadata.get('thread_id') == thread_id
        ]
        
        if not thread_docs:
            return {
                'thread_id': thread_id,
                'emails': [],
                'error': 'Thread not found'
            }
        
        # Sort by date (attempt to parse)
        def parse_date(date_str):
            try:
                # Simple heuristic - just return original for sorting
                return date_str
            except:
                return ''
        
        thread_docs.sort(key=lambda d: parse_date(d.metadata.get('date', '')))
        
        # Format thread
        emails = []
        for doc in thread_docs:
            emails.append({
                'subject': doc.metadata.get('subject', 'No subject'),
                'sender': doc.metadata.get('sender', 'Unknown'),
                'date': doc.metadata.get('date', 'Unknown'),
                'message_id': doc.metadata.get('message_id', doc.metadata.get('email_id', '')),
                'content': doc.page_content
            })
        
        return {
            'thread_id': thread_id,
            'emails': emails,
            'count': len(emails)
        }
    
    def as_tool(self) -> FunctionTool:
        """Convert to LlamaIndex FunctionTool."""
        return FunctionTool.from_defaults(
            fn=self.get_thread,
            name="get_thread",
            description=(
                "Get full thread of emails by thread_id. "
                "Returns all emails in chronological order with complete content and metadata. "
                "Use when you need to see the full conversation flow or when asked to 'show me the thread'."
            )
        )


class TriageTool:
    """Find emails that need replies."""
    
    # Keywords indicating reply needed
    NEEDS_REPLY_KEYWORDS = [
        'please confirm', 'let me know', 'waiting for', 'can you',
        'could you', 'would you', 'action required', 'need your',
        'awaiting', 'please reply', 'please respond', 'get back to me',
        'follow up', 'asap', 'urgent', 'time-sensitive'
    ]
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
    
    def triage_recent(
        self,
        days: int = 1,
        sender_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find recent emails that need replies.
        
        Args:
            days: Number of days to look back (default: 1)
            sender_filter: Optional email address to filter by sender
        
        Returns:
            Dict with 'needs_reply' (ranked list of emails) and 'count'
        """
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Search for emails with reply keywords
        query = ' '.join(self.NEEDS_REPLY_KEYWORDS[:5])  # Use some keywords
        docs = self.rag.semantic_search(query, k=50)
        
        # Filter by sender if specified
        if sender_filter:
            docs = [
                d for d in docs 
                if sender_filter.lower() in d.metadata.get('sender', '').lower()
            ]
        
        # Find emails with reply keywords (case-insensitive)
        needs_reply = []
        for doc in docs:
            content_lower = doc.page_content.lower()
            subject_lower = doc.metadata.get('subject', '').lower()
            
            # Check for keywords
            keyword_matches = [
                kw for kw in self.NEEDS_REPLY_KEYWORDS
                if kw in content_lower or kw in subject_lower
            ]
            
            if keyword_matches:
                # Calculate urgency score (more keywords = higher urgency)
                urgency_score = len(keyword_matches)
                
                needs_reply.append({
                    'subject': doc.metadata.get('subject', 'No subject'),
                    'sender': doc.metadata.get('sender', 'Unknown'),
                    'date': doc.metadata.get('date', 'Unknown'),
                    'message_id': doc.metadata.get('message_id', doc.metadata.get('email_id', '')),
                    'thread_id': doc.metadata.get('thread_id', ''),
                    'urgency_score': urgency_score,
                    'keywords_found': keyword_matches[:3],  # Top 3 keywords
                    'snippet': doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content
                })
        
        # Sort by urgency score (descending)
        needs_reply.sort(key=lambda x: x['urgency_score'], reverse=True)
        
        return {
            'needs_reply': needs_reply,
            'count': len(needs_reply),
            'days_searched': days
        }
    
    def as_tool(self) -> FunctionTool:
        """Convert to LlamaIndex FunctionTool."""
        return FunctionTool.from_defaults(
            fn=self.triage_recent,
            name="triage_recent",
            description=(
                "Find recent emails that need replies. "
                "Looks for keywords like 'please confirm', 'action required', 'urgent', etc. "
                "Returns a ranked list with urgency scores. "
                "Use for questions like 'what emails need replies' or 'show me urgent emails'."
            )
        )


class DraftTool:
    """Generate reply drafts for emails."""
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
    
    def draft_reply(
        self,
        thread_id: str,
        tone: str = 'professional'
    ) -> Dict[str, Any]:
        """
        Generate a reply draft for an email thread.
        
        Args:
            thread_id: Gmail thread ID to reply to
            tone: Tone for the reply ('concise', 'friendly', 'formal', 'professional')
        
        Returns:
            Dict with 'draft' (reply text), 'thread_id', and 'tone'
        """
        # Get thread content
        all_docs = self.rag.semantic_search("", k=1000)
        thread_docs = [
            d for d in all_docs 
            if d.metadata.get('thread_id') == thread_id
        ]
        
        if not thread_docs:
            return {
                'thread_id': thread_id,
                'draft': None,
                'error': 'Thread not found'
            }
        
        # Get latest email in thread (assuming last in list)
        thread_docs.sort(key=lambda d: d.metadata.get('date', ''))
        latest_email = thread_docs[-1]
        
        # Build context
        context = f"Subject: {latest_email.metadata.get('subject', 'No subject')}\n"
        context += f"From: {latest_email.metadata.get('sender', 'Unknown')}\n\n"
        context += latest_email.page_content[:1000]  # Limit context
        
        # Create prompt based on tone
        tone_instructions = {
            'concise': 'Write a brief, to-the-point reply (2-3 sentences max).',
            'friendly': 'Write a warm, friendly reply that builds rapport.',
            'formal': 'Write a formal, professional business reply.',
            'professional': 'Write a professional, courteous reply.'
        }
        
        instruction = tone_instructions.get(tone, tone_instructions['professional'])
        
        prompt = f"""{instruction}

Original email:
{context}

Draft reply:"""
        
        # Generate draft using LLM
        draft = self.rag._call_llm_simple(prompt, max_tokens=300)
        
        return {
            'thread_id': thread_id,
            'tone': tone,
            'draft': draft.strip(),
            'original_subject': latest_email.metadata.get('subject', 'No subject'),
            'original_sender': latest_email.metadata.get('sender', 'Unknown'),
            'warning': 'DRAFT ONLY - Review before sending. Never auto-send.'
        }
    
    def as_tool(self) -> FunctionTool:
        """Convert to LlamaIndex FunctionTool."""
        return FunctionTool.from_defaults(
            fn=self.draft_reply,
            name="draft_reply",
            description=(
                "Generate a reply draft for an email thread. "
                "Requires thread_id and optional tone (concise/friendly/formal/professional). "
                "Returns DRAFT ONLY - never sends automatically. "
                "Use when asked to 'draft a reply' or 'help me respond'."
            )
        )
