"""
Factory function for creating ConversationMapper instances
"""

from frmk.conversation.mapper import ConversationMapper, MappingStrategy
from frmk.conversation.mappers.direct import DirectMapper
from frmk.conversation.mappers.hash import HashMapper
from frmk.conversation.mappers.database import DatabaseMapper
from typing import Dict, Any


def create_conversation_mapper(config: Dict[str, Any]) -> ConversationMapper:
    """
    Factory function to create ConversationMapper from configuration

    Config structure:
        {
            "strategy": "direct" | "hash" | "database",

            # For strategy="hash"
            "hash_algorithm": "sha256",
            "hash_length": 16,
            "prefix": "teams",

            # For strategy="database"
            "datastore": {
                "type": "cosmosdb" | "postgres",
                "connection_string": "...",
                # or (for Cosmos DB)
                "endpoint": "...",
                "key": "...",
                "database_name": "goalgen",
                "container_name": "conversation_mappings"
            },
            "tenant_id": "tenant-123",
            "langgraph_workflow_endpoint": "https://api.example.com",
            "cleanup_inactive_days": 90
        }

    Args:
        config: Configuration dictionary

    Returns:
        ConversationMapper instance

    Raises:
        ValueError: If strategy is unsupported or required config is missing
    """
    strategy = MappingStrategy(config.get("strategy", "hash"))

    if strategy == MappingStrategy.DIRECT:
        return DirectMapper(config)

    elif strategy == MappingStrategy.HASH:
        return HashMapper(config)

    elif strategy == MappingStrategy.DATABASE:
        # Create datastore
        datastore_config = config.get("datastore", {})
        datastore_type = datastore_config.get("type", "cosmosdb")

        if datastore_type == "cosmosdb":
            from frmk.conversation.datastores.cosmosdb import CosmosDBDataStore

            datastore = CosmosDBDataStore(
                connection_string=datastore_config.get("connection_string"),
                endpoint=datastore_config.get("endpoint"),
                key=datastore_config.get("key"),
                database_name=datastore_config.get("database_name", "goalgen"),
                container_name=datastore_config.get("container_name", "conversation_mappings")
            )
        elif datastore_type == "postgres":
            from frmk.conversation.datastores.postgres import PostgreSQLDataStore

            if "connection_string" not in datastore_config:
                raise ValueError("PostgreSQL datastore requires 'connection_string'")

            datastore = PostgreSQLDataStore(
                connection_string=datastore_config["connection_string"]
            )
        else:
            raise ValueError(f"Unsupported datastore type: {datastore_type}")

        # Create database mapper
        return DatabaseMapper({
            "datastore": datastore,
            "tenant_id": config.get("tenant_id"),
            "langgraph_workflow_endpoint": config.get("langgraph_workflow_endpoint"),
            "cleanup_inactive_days": config.get("cleanup_inactive_days", 90),
            "thread_id_prefix": config.get("thread_id_prefix", "teams")
        })

    else:
        raise ValueError(f"Unsupported mapping strategy: {strategy}")
