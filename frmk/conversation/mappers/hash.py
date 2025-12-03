"""
Hash-Based Mapping Strategy

Generates deterministic thread_id by hashing Teams identifiers.
Stateless - same input always produces same thread_id.
"""

from frmk.conversation.mapper import (
    ConversationMapper,
    ConversationContext,
    MappingResult
)
from typing import Optional, Dict, Any
import hashlib
from frmk.utils.tracing import trace_span


class HashMapper(ConversationMapper):
    """
    Strategy 2: Hash-Based Mapping

    Generates deterministic thread_id by hashing Teams identifiers.
    Stateless - same input always produces same thread_id.

    Config:
        hash_algorithm: str (default: "sha256")
        hash_length: int (default: 16) - Length of hash to use
        prefix: str (default: "teams") - Prefix for thread_id

    Example:
        mapper = HashMapper({
            "hash_algorithm": "sha256",
            "hash_length": 16,
            "prefix": "teams"
        })
        result = mapper.get_thread_id(context)
        # thread_id = "teams-a1b2c3d4e5f67890"
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.hash_algorithm = config.get("hash_algorithm", "sha256")
        self.hash_length = config.get("hash_length", 16)
        self.prefix = config.get("prefix", "teams")

    @trace_span("mapper.get_thread_id", component="conversation_mapper")
    def get_thread_id(self, context: ConversationContext) -> MappingResult:
        """
        Generate deterministic thread_id from conversation context
        """
        # Build key based on conversation type
        if context.conversation_type == "personal":
            # For 1:1 chats, thread_id is unique per user
            # Ensures single persistent conversation per user
            key = f"{self.prefix}-personal-{context.user_id}"
        elif context.conversation_type == "groupChat":
            # For group chats, thread_id is per conversation
            # All users share conversation state
            key = f"{self.prefix}-group-{context.conversation_id}"
        elif context.conversation_type == "channel":
            # For channels, thread_id is per channel thread
            # Each thread in channel has separate state
            key = f"{self.prefix}-channel-{context.conversation_id}"
        else:
            # Fallback
            key = f"{self.prefix}-{context.conversation_id}"

        # Hash to create shorter, stable ID
        hasher = hashlib.new(self.hash_algorithm)
        hasher.update(key.encode())
        thread_hash = hasher.hexdigest()[:self.hash_length]
        thread_id = f"{self.prefix}-{thread_hash}"

        return MappingResult(
            thread_id=thread_id,
            is_new=False,  # Cannot determine, deterministic mapping
            conversation_context=context
        )

    def get_conversation_context(self, thread_id: str) -> Optional[ConversationContext]:
        """
        Cannot reverse lookup hash without state
        """
        return None
