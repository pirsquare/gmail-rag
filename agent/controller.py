"""
LlamaIndex Gmail Agent Controller

Manages the agent lifecycle, tool routing, and response formatting.
"""

import os
from typing import Dict, Any, List, Optional
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage, MessageRole

from agent.tools import EmailSearchTool, ThreadTool, TriageTool, DraftTool
from rag_engine import RAGEngine
from config import Config


# System prompt with strict citation policy
SYSTEM_PROMPT = """You are an intelligent Gmail inbox assistant. Your job is to help users search, organize, and manage their emails.

CRITICAL RULES:
1. ALWAYS use the provided tools to access email data. Never make up or hallucinate email content.
2. ALWAYS cite emails using the exact message_id and thread_id returned by tools.
3. When showing search results, include: subject, sender, date, message_id, and thread_id.
4. For triage results, show the urgency_score and keywords_found.
5. For drafts, ALWAYS include the warning that it's a draft and must be reviewed before sending.
6. NEVER claim to send emails. You can only draft replies.
7. If you don't have information, say so clearly. Don't guess.

TOOL USAGE:
- search_emails: For "find emails about X", "what did Y say about Z"
- get_thread: For "show me the full thread", "what's the conversation history"
- triage_recent: For "what needs replies", "urgent emails", "action items"
- draft_reply: For "draft a reply to X", "help me respond"

CITATION FORMAT:
When referencing an email, always use:
"📧 Subject: [subject]
From: [sender]
Date: [date]
Message ID: [message_id]
Thread ID: [thread_id]"

Be helpful, accurate, and always cite your sources."""


class GmailAgent:
    """LlamaIndex-based agent for Gmail inbox management."""
    
    def __init__(self, rag_engine: RAGEngine, llm_provider: str = 'openai'):
        """
        Initialize Gmail Agent.
        
        Args:
            rag_engine: Initialized RAGEngine instance
            llm_provider: 'openai' or 'ollama' (default: 'openai')
        """
        self.rag = rag_engine
        self.llm_provider = llm_provider
        
        # Initialize LLM
        if llm_provider == 'ollama':
            self.llm = Ollama(
                model=Config.OLLAMA_MODEL,
                base_url=Config.OLLAMA_BASE_URL,
                temperature=Config.TEMPERATURE,
                request_timeout=120.0
            )
        else:  # openai
            self.llm = OpenAI(
                model=Config.LLM_MODEL,
                temperature=Config.TEMPERATURE,
                api_key=Config.OPENAI_API_KEY
            )
        
        # Initialize tools
        self.email_search_tool = EmailSearchTool(rag_engine)
        self.thread_tool = ThreadTool(rag_engine)
        self.triage_tool = TriageTool(rag_engine)
        self.draft_tool = DraftTool(rag_engine)
        
        # Create tool list
        tools = [
            self.email_search_tool.as_tool(),
            self.thread_tool.as_tool(),
            self.triage_tool.as_tool(),
            self.draft_tool.as_tool()
        ]
        
        # Create ReAct agent
        self.agent = ReActAgent.from_tools(
            tools=tools,
            llm=self.llm,
            verbose=True,
            max_iterations=10
        )
    
    def run(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Run agent with user message.
        
        Args:
            message: User message/query
            chat_history: Optional list of previous messages [{"role": "user"/"assistant", "content": "..."}]
        
        Returns:
            Dict with:
                - response: Agent's response text
                - sources: List of cited sources (if any)
                - tool_calls: List of tools called
                - needs_reply: List of emails needing reply (for triage)
                - draft: Draft reply (if generated)
        """
        try:
            # Build chat messages
            messages = []
            
            # Add system prompt
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT))
            
            # Add chat history
            if chat_history:
                for msg in chat_history[-10:]:  # Last 10 messages
                    role = MessageRole.USER if msg['role'] == 'user' else MessageRole.ASSISTANT
                    messages.append(ChatMessage(role=role, content=msg['content']))
            
            # Add current message
            messages.append(ChatMessage(role=MessageRole.USER, content=message))
            
            # Run agent
            response = self.agent.chat(message)
            
            # Extract information from response
            result = {
                'response': str(response),
                'sources': [],
                'tool_calls': [],
                'needs_reply': [],
                'draft': None
            }
            
            # Parse sources from response (look for message_ids and thread_ids)
            response_text = str(response)
            sources = self._extract_citations(response_text)
            result['sources'] = sources
            
            # Check if triage was called (look for "needs_reply" in response)
            if 'urgency_score' in response_text.lower() or 'needs reply' in response_text.lower():
                # Mark as triage result
                result['is_triage'] = True
            
            # Check if draft was generated
            if 'DRAFT ONLY' in response_text or 'draft:' in response_text.lower():
                result['is_draft'] = True
            
            return result
            
        except Exception as e:
            return {
                'response': f"Error: {str(e)}",
                'sources': [],
                'tool_calls': [],
                'needs_reply': [],
                'draft': None,
                'error': str(e)
            }
    
    def _extract_citations(self, response_text: str) -> List[Dict[str, str]]:
        """
        Extract email citations from response text.
        
        Args:
            response_text: Agent's response
        
        Returns:
            List of source dicts with subject, sender, date, message_id, thread_id
        """
        sources = []
        
        # Simple parsing - look for citation patterns
        lines = response_text.split('\n')
        current_source = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Subject:') or line.startswith('📧 Subject:'):
                if current_source:
                    sources.append(current_source)
                current_source = {'subject': line.split(':', 1)[1].strip()}
            
            elif line.startswith('From:') and current_source:
                current_source['sender'] = line.split(':', 1)[1].strip()
            
            elif line.startswith('Date:') and current_source:
                current_source['date'] = line.split(':', 1)[1].strip()
            
            elif line.startswith('Message ID:') and current_source:
                current_source['message_id'] = line.split(':', 1)[1].strip()
            
            elif line.startswith('Thread ID:') and current_source:
                current_source['thread_id'] = line.split(':', 1)[1].strip()
        
        # Add last source
        if current_source:
            sources.append(current_source)
        
        return sources
    
    def reset(self):
        """Reset agent conversation history."""
        # ReActAgent doesn't maintain state, so nothing to reset
        pass


def create_agent(rag_engine: RAGEngine, llm_provider: Optional[str] = None) -> GmailAgent:
    """
    Factory function to create Gmail Agent.
    
    Args:
        rag_engine: Initialized RAGEngine
        llm_provider: 'openai' or 'ollama' (if None, uses Config.LLM_PROVIDER)
    
    Returns:
        GmailAgent instance
    """
    if llm_provider is None:
        llm_provider = getattr(Config, 'LLM_PROVIDER', 'openai')
    
    return GmailAgent(rag_engine, llm_provider)
