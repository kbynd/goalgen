"""
Base classes for conversation mapping strategies
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MappingStrategy(Enum):
    """Conversation mapping strategies"""
    DIRECT = "direct"           # Strategy 1: Use conversation.id directly
    HASH = "hash"               # Strategy 2: Hash-based deterministic mapping
    DATABASE = "database"       # Strategy 3: Database-backed mapping with lifecycle
    CUSTOM = "custom"           # Custom implementation


@dataclass
class ConversationContext:
    """Teams conversation context"""
    conversation_id: str                    # Teams conversation.id
    user_id: str                            # Teams from.aadObjectId (preferred) or from.id
    conversation_type: str                  # personal/groupChat/channel
    tenant_id: str                          # Azure AD tenant ID
    user_name: Optional[str] = None         # Display name
    channel_id: Optional[str] = None        # Teams channel (if applicable)
    service_url: Optional[str] = None       # Bot Framework service URL
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class MappingResult:
    """Result of thread_id mapping operation"""
    thread_id: str                          # LangGraph thread_id
    is_new: bool                            # True if new mapping created
    conversation_context: ConversationContext
    created_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


class ConversationMapper(ABC):
    """
    Abstract base class for conversation mapping strategies

    Provides pluggable architecture for mapping Teams conversation
    context to LangGraph thread IDs.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mapper with configuration

        Args:
            config: Strategy-specific configuration
        """
        self.config = config

    @abstractmethod
    def get_thread_id(self, context: ConversationContext) -> MappingResult:
        """
        Get or create thread_id for given conversation context

        Args:
            context: Teams conversation context

        Returns:
            MappingResult with thread_id and metadata
        """
        pass

    @abstractmethod
    def get_conversation_context(self, thread_id: str) -> Optional[ConversationContext]:
        """
        Reverse lookup: Get conversation context from thread_id

        Args:
            thread_id: LangGraph thread_id

        Returns:
            ConversationContext if found, None otherwise
        """
        pass

    def update_activity(self, thread_id: str) -> None:
        """
        Update last activity timestamp for thread

        Default implementation does nothing (stateless strategies)
        Override in stateful strategies (e.g., Database)

        Args:
            thread_id: LangGraph thread_id
        """
        pass

    def cleanup_inactive(self, inactive_days: int) -> int:
        """
        Cleanup inactive conversations

        Default implementation does nothing (stateless strategies)
        Override in stateful strategies (e.g., Database)

        Args:
            inactive_days: Remove conversations inactive for this many days

        Returns:
            Number of conversations cleaned up
        """
        return 0

    def deactivate_conversation(self, thread_id: str) -> None:
        """
        Mark conversation as inactive

        Default implementation does nothing (stateless strategies)
        Override in stateful strategies (e.g., Database)

        Args:
            thread_id: LangGraph thread_id
        """
        pass
