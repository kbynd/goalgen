"""
Cosmos DB implementation for conversation mapping storage
"""

from frmk.conversation.datastore import ConversationDataStore
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from azure.cosmos import CosmosClient, PartitionKey
    COSMOS_AVAILABLE = True
except ImportError:
    COSMOS_AVAILABLE = False


class CosmosDBDataStore(ConversationDataStore):
    """
    Cosmos DB implementation for conversation mapping storage

    Schema:
        Container: conversation_mappings
        Partition Key: /tenant_id

        Document structure:
        {
            "id": "<thread_id>",
            "thread_id": "<thread_id>",
            "tenant_id": "<tenant_id>",
            "conversation_id": "<teams_conversation_id>",
            "user_id": "<azure_ad_object_id>",
            "conversation_type": "personal|groupChat|channel",
            "user_name": "John Doe",
            "channel_id": "19:channel@thread.tacv2",
            "service_url": "https://smba.trafficmanager.net/amer/",
            "langgraph_workflow_endpoint": "https://api.example.com",
            "created_at": "2024-12-02T10:00:00Z",
            "last_activity_at": "2024-12-02T15:30:00Z",
            "is_active": true,
            "metadata": {}
        }
    """

    def __init__(
        self,
        connection_string: str = None,
        endpoint: str = None,
        key: str = None,
        database_name: str = "goalgen",
        container_name: str = "conversation_mappings"
    ):
        if not COSMOS_AVAILABLE:
            raise ImportError(
                "azure-cosmos package required for CosmosDBDataStore. "
                "Install with: pip install azure-cosmos"
            )

        if connection_string:
            self.client = CosmosClient.from_connection_string(connection_string)
        elif endpoint and key:
            self.client = CosmosClient(endpoint, key)
        else:
            raise ValueError("Provide either connection_string or (endpoint + key)")

        self.database = self.client.get_database_client(database_name)
        self.container = self.database.get_container_client(container_name)

    def find_mapping(
        self,
        tenant_id: str,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find existing mapping"""
        query = """
            SELECT * FROM c
            WHERE c.tenant_id = @tenant_id
            AND c.conversation_id = @conversation_id
            AND c.user_id = @user_id
            AND c.is_active = true
        """

        items = list(self.container.query_items(
            query=query,
            parameters=[
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@conversation_id", "value": conversation_id},
                {"name": "@user_id", "value": user_id}
            ],
            partition_key=tenant_id
        ))

        return items[0] if items else None

    def get_by_thread_id(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get mapping by thread_id"""
        try:
            # Note: Cross-partition query (less efficient)
            # Consider maintaining secondary index if this is frequent
            query = "SELECT * FROM c WHERE c.thread_id = @thread_id"
            items = list(self.container.query_items(
                query=query,
                parameters=[{"name": "@thread_id", "value": thread_id}],
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception:
            return None

    def create_mapping(self, mapping_data: Dict[str, Any]) -> None:
        """Create new mapping"""
        mapping_data["id"] = mapping_data["thread_id"]

        # Convert datetime objects to ISO strings
        if isinstance(mapping_data.get("created_at"), datetime):
            mapping_data["created_at"] = mapping_data["created_at"].isoformat()
        if isinstance(mapping_data.get("last_activity_at"), datetime):
            mapping_data["last_activity_at"] = mapping_data["last_activity_at"].isoformat()

        self.container.create_item(body=mapping_data)

    def update_activity(self, thread_id: str) -> None:
        """Update last_activity_at"""
        mapping = self.get_by_thread_id(thread_id)
        if mapping:
            mapping["last_activity_at"] = datetime.utcnow().isoformat()
            self.container.upsert_item(body=mapping)

    def cleanup_inactive(self, cutoff_date: datetime) -> int:
        """Delete inactive mappings"""
        query = """
            SELECT * FROM c
            WHERE c.last_activity_at < @cutoff_date
            AND c.is_active = true
        """

        items = list(self.container.query_items(
            query=query,
            parameters=[{"name": "@cutoff_date", "value": cutoff_date.isoformat()}],
            enable_cross_partition_query=True
        ))

        count = 0
        for item in items:
            self.container.delete_item(item=item["id"], partition_key=item["tenant_id"])
            count += 1

        return count

    def get_active_conversations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get active conversations for tenant"""
        query = """
            SELECT * FROM c
            WHERE c.tenant_id = @tenant_id
            AND c.is_active = true
        """

        return list(self.container.query_items(
            query=query,
            parameters=[{"name": "@tenant_id", "value": tenant_id}],
            partition_key=tenant_id
        ))

    def deactivate(self, thread_id: str) -> None:
        """Mark conversation as inactive"""
        mapping = self.get_by_thread_id(thread_id)
        if mapping:
            mapping["is_active"] = False
            self.container.upsert_item(body=mapping)
