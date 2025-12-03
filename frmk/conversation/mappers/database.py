"""
Database Mapping Strategy

Stores bidirectional mapping in database with full lifecycle tracking.
Supports analytics, cleanup, reverse lookups, and multi-tenant isolation.
"""

from frmk.conversation.mapper import (
    ConversationMapper,
    ConversationContext,
    MappingResult
)
from frmk.conversation.datastore import ConversationDataStore
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid


class DatabaseMapper(ConversationMapper):
    """
    Strategy 3: Database Mapping

    Stores bidirectional mapping in database with full lifecycle tracking.
    Supports analytics, cleanup, reverse lookups, and multi-tenant isolation.

    Config:
        datastore: ConversationDataStore - Database abstraction
        tenant_id: str - Azure AD tenant ID for multi-tenant isolation
        langgraph_workflow_endpoint: str - URL of LangGraph API
        thread_id_prefix: str (default: "teams") - Prefix for generated IDs
        cleanup_inactive_days: int (default: 90) - Days before cleanup
        enable_analytics: bool (default: True) - Track usage metrics

    Example:
        from frmk.conversation.datastores import CosmosDBDataStore

        datastore = CosmosDBDataStore(connection_string="...", database="goalgen")

        mapper = DatabaseMapper({
            "datastore": datastore,
            "tenant_id": "tenant-123",
            "langgraph_workflow_endpoint": "https://api.example.com",
            "cleanup_inactive_days": 90
        })

        result = mapper.get_thread_id(context)
        # thread_id = "teams-a1b2c3d4e5f6"
        # Also stored in database with full context
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Required config
        if "datastore" not in config:
            raise ValueError("DatabaseMapper requires 'datastore' in config")

        self.datastore: ConversationDataStore = config["datastore"]
        self.tenant_id = config.get("tenant_id")
        self.langgraph_workflow_endpoint = config.get("langgraph_workflow_endpoint")

        # Optional config
        self.thread_id_prefix = config.get("thread_id_prefix", "teams")
        self.cleanup_inactive_days = config.get("cleanup_inactive_days", 90)
        self.enable_analytics = config.get("enable_analytics", True)

    def get_thread_id(self, context: ConversationContext) -> MappingResult:
        """
        Get existing thread_id or create new mapping in database
        """
        # Try to find existing mapping
        existing = self.datastore.find_mapping(
            tenant_id=self.tenant_id or context.tenant_id,
            conversation_id=context.conversation_id,
            user_id=context.user_id
        )

        if existing:
            # Update last activity timestamp
            self.datastore.update_activity(existing["thread_id"])

            # Parse datetime from string if needed
            created_at = existing.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

            return MappingResult(
                thread_id=existing["thread_id"],
                is_new=False,
                conversation_context=context,
                created_at=created_at,
                last_activity_at=datetime.utcnow(),
                metadata=existing.get("metadata", {})
            )

        # Create new mapping
        thread_id = f"{self.thread_id_prefix}-{uuid.uuid4().hex[:16]}"

        mapping_data = {
            "thread_id": thread_id,
            "tenant_id": self.tenant_id or context.tenant_id,
            "conversation_id": context.conversation_id,
            "user_id": context.user_id,
            "conversation_type": context.conversation_type,
            "user_name": context.user_name,
            "channel_id": context.channel_id,
            "service_url": context.service_url,
            "langgraph_workflow_endpoint": self.langgraph_workflow_endpoint,
            "created_at": datetime.utcnow(),
            "last_activity_at": datetime.utcnow(),
            "is_active": True,
            "metadata": context.metadata or {}
        }

        self.datastore.create_mapping(mapping_data)

        return MappingResult(
            thread_id=thread_id,
            is_new=True,
            conversation_context=context,
            created_at=mapping_data["created_at"],
            last_activity_at=mapping_data["last_activity_at"]
        )

    def get_conversation_context(self, thread_id: str) -> Optional[ConversationContext]:
        """
        Reverse lookup: Get conversation context from thread_id
        """
        mapping = self.datastore.get_by_thread_id(thread_id)

        if not mapping:
            return None

        return ConversationContext(
            conversation_id=mapping["conversation_id"],
            user_id=mapping["user_id"],
            conversation_type=mapping["conversation_type"],
            tenant_id=mapping["tenant_id"],
            user_name=mapping.get("user_name"),
            channel_id=mapping.get("channel_id"),
            service_url=mapping.get("service_url"),
            metadata=mapping.get("metadata", {})
        )

    def update_activity(self, thread_id: str) -> None:
        """
        Update last activity timestamp
        """
        self.datastore.update_activity(thread_id)

    def cleanup_inactive(self, inactive_days: int = None) -> int:
        """
        Cleanup conversations inactive for specified days
        """
        days = inactive_days or self.cleanup_inactive_days
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return self.datastore.cleanup_inactive(cutoff_date)

    def get_active_conversations(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all active conversations for tenant
        """
        return self.datastore.get_active_conversations(
            tenant_id=tenant_id or self.tenant_id
        )

    def deactivate_conversation(self, thread_id: str) -> None:
        """
        Mark conversation as inactive (e.g., bot removed from Teams)
        """
        self.datastore.deactivate(thread_id)
