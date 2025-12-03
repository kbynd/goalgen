"""
Abstract interface for conversation mapping storage

Allows pluggable backends: Cosmos DB, PostgreSQL, Redis, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime


class ConversationDataStore(ABC):
    """
    Abstract interface for conversation mapping storage

    Allows pluggable backends: Cosmos DB, PostgreSQL, Redis, etc.
    """

    @abstractmethod
    def find_mapping(
        self,
        tenant_id: str,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find existing mapping by Teams identifiers

        Args:
            tenant_id: Azure AD tenant ID
            conversation_id: Teams conversation.id
            user_id: Teams user.aadObjectId

        Returns:
            Mapping dict if found, None otherwise
        """
        pass

    @abstractmethod
    def get_by_thread_id(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get mapping by LangGraph thread_id

        Args:
            thread_id: LangGraph thread_id

        Returns:
            Mapping dict if found, None otherwise
        """
        pass

    @abstractmethod
    def create_mapping(self, mapping_data: Dict[str, Any]) -> None:
        """
        Create new mapping

        Args:
            mapping_data: Mapping data including thread_id, conversation context, etc.
        """
        pass

    @abstractmethod
    def update_activity(self, thread_id: str) -> None:
        """
        Update last_activity_at timestamp

        Args:
            thread_id: LangGraph thread_id
        """
        pass

    @abstractmethod
    def cleanup_inactive(self, cutoff_date: datetime) -> int:
        """
        Delete mappings inactive since cutoff_date

        Args:
            cutoff_date: Remove mappings with last_activity_at before this date

        Returns:
            Number of mappings cleaned up
        """
        pass

    @abstractmethod
    def get_active_conversations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get all active conversations for tenant

        Args:
            tenant_id: Azure AD tenant ID

        Returns:
            List of active conversation mappings
        """
        pass

    @abstractmethod
    def deactivate(self, thread_id: str) -> None:
        """
        Mark conversation as inactive

        Args:
            thread_id: LangGraph thread_id
        """
        pass
