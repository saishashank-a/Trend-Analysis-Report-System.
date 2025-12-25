"""
Configuration package for LLM client abstraction
"""

from .llm_client import get_llm_client, LLMProvider

__all__ = ['get_llm_client', 'LLMProvider']
