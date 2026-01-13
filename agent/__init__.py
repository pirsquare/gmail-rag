"""
LlamaIndex-based Gmail Agent

This module provides an intelligent agent layer for Gmail RAG using LlamaIndex.
"""

from agent.controller import GmailAgent
from agent.tools import EmailSearchTool, ThreadTool, TriageTool, DraftTool

__all__ = ['GmailAgent', 'EmailSearchTool', 'ThreadTool', 'TriageTool', 'DraftTool']
