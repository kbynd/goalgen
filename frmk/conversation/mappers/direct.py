"""
Direct Mapping Strategy

Uses Teams conversation.id directly as LangGraph thread_id.
Simplest strategy, no transformation, completely stateless.
"""

from frmk.conversation.mapper import (
    ConversationMapper,
    ConversationContext,
    MappingResult
)
from typing import Optional, Dict, Any


class DirectMapper(ConversationMapper):
    """
    Strategy 1: Direct Mapping

    Uses Teams conversation.id directly as LangGraph thread_id
    No transformation, no storage, completely stateless.

    Config:
        None required

    Example:
        mapper = DirectMapper({})
        result = mapper.get_thread_id(context)
        # thread_id = "19:meeting_abc123@thread.v2"
    """

    def get_thread_id(self, context: ConversationContext) -> MappingResult:
        """
        Return conversation.id directly as thread_id
        """
        return MappingResult(
            thread_id=context.conversation_id,
            is_new=False,  # Cannot determine, assume existing
            conversation_context=context
        )

    def get_conversation_context(self, thread_id: str) -> Optional[ConversationContext]:
        """
        Cannot reverse lookup without state
        """
        return None
