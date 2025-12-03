"""
Conversation Mapping Framework

Provides flexible thread ID mapping for Teams Bot ↔ LangGraph integration.
Supports multiple strategies: direct, hash-based, and database-backed.
"""

from frmk.conversation.mapper import (
    ConversationMapper,
    ConversationContext,
    MappingResult,
    MappingStrategy
)
from frmk.conversation.factory import create_conversation_mapper

__all__ = [
    "ConversationMapper",
    "ConversationContext",
    "MappingResult",
    "MappingStrategy",
    "create_conversation_mapper"
]
