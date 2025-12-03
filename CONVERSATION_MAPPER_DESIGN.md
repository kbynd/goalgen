# ConversationMapper Design - Multi-Strategy Thread ID Management

**Purpose**: Flexible conversation mapping layer supporting multiple strategies for Teams ↔ LangGraph thread_id management

**Last Updated**: 2025-12-02

---

## Overview

The `ConversationMapper` provides a pluggable architecture for mapping Teams conversation context to LangGraph thread IDs. It supports three strategies with increasing sophistication:

1. **Strategy 1: Direct Mapping** - Simple, stateless, uses Teams conversation.id directly
2. **Strategy 2: Hash-Based Mapping** - Stateless, deterministic hashing for cleaner IDs
3. **Strategy 3: Database Mapping** - Stateful, enterprise-grade with persistence, analytics, and lifecycle management

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    ConversationMapper                     │
│                     (Abstract Base)                       │
└─────────────┬────────────────────────────────────────────┘
              │
    ┌─────────┴──────────┬──────────────┬─────────────────┐
    │                    │              │                 │
    ▼                    ▼              ▼                 ▼
┌─────────┐      ┌─────────────┐  ┌──────────────┐  ┌──────────┐
│ Direct  │      │ Hash-Based  │  │  Database    │  │ Custom   │
│ Mapper  │      │   Mapper    │  │    Mapper    │  │ Mapper   │
└─────────┘      └─────────────┘  └──────────────┘  └──────────┘
(Strategy 1)      (Strategy 2)     (Strategy 3)     (Extensible)
```

---

## Base Interface

```python
# frmk/conversation/mapper.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
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
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MappingResult:
    """Result of thread_id mapping operation"""
    thread_id: str                          # LangGraph thread_id
    is_new: bool                            # True if new mapping created
    conversation_context: ConversationContext
    created_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


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
```

---

## Strategy 1: Direct Mapping (Stateless)

**Use Case**: Development, testing, simple deployments

**Pros**: Zero configuration, no dependencies
**Cons**: Exposes internal Teams IDs, may be long/complex

```python
# frmk/conversation/mappers/direct.py

from frmk.conversation.mapper import ConversationMapper, ConversationContext, MappingResult
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
```

---

## Strategy 2: Hash-Based Mapping (Stateless)

**Use Case**: Production deployments without database requirement

**Pros**: Deterministic, cleaner IDs, stateless (no DB needed)
**Cons**: Cannot reverse lookup, no lifecycle tracking

```python
# frmk/conversation/mappers/hash.py

from frmk.conversation.mapper import ConversationMapper, ConversationContext, MappingResult
from typing import Optional, Dict, Any
import hashlib

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
```

---

## Strategy 3: Database Mapping (Stateful)

**Use Case**: Enterprise deployments, multi-tenant, analytics, lifecycle management

**Pros**: Full tracking, reverse lookup, lifecycle management, analytics
**Cons**: Requires database, more complex setup

```python
# frmk/conversation/mappers/database.py

from frmk.conversation.mapper import ConversationMapper, ConversationContext, MappingResult
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
import json

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

            return MappingResult(
                thread_id=existing["thread_id"],
                is_new=False,
                conversation_context=context,
                created_at=existing.get("created_at"),
                last_activity_at=datetime.utcnow(),
                metadata=existing.get("metadata")
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
            metadata=mapping.get("metadata")
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
```

---

## DataStore Abstraction

```python
# frmk/conversation/datastore.py

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
        """Find existing mapping by Teams identifiers"""
        pass

    @abstractmethod
    def get_by_thread_id(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get mapping by LangGraph thread_id"""
        pass

    @abstractmethod
    def create_mapping(self, mapping_data: Dict[str, Any]) -> None:
        """Create new mapping"""
        pass

    @abstractmethod
    def update_activity(self, thread_id: str) -> None:
        """Update last_activity_at timestamp"""
        pass

    @abstractmethod
    def cleanup_inactive(self, cutoff_date: datetime) -> int:
        """Delete mappings inactive since cutoff_date"""
        pass

    @abstractmethod
    def get_active_conversations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all active conversations for tenant"""
        pass

    @abstractmethod
    def deactivate(self, thread_id: str) -> None:
        """Mark conversation as inactive"""
        pass
```

---

## DataStore Implementations

### Cosmos DB Implementation

```python
# frmk/conversation/datastores/cosmosdb.py

from frmk.conversation.datastore import ConversationDataStore
from azure.cosmos import CosmosClient, PartitionKey
from typing import Optional, Dict, Any, List
from datetime import datetime

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
        mapping_data["created_at"] = mapping_data["created_at"].isoformat()
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
```

### PostgreSQL Implementation

```python
# frmk/conversation/datastores/postgres.py

from frmk.conversation.datastore import ConversationDataStore
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

class PostgreSQLDataStore(ConversationDataStore):
    """
    PostgreSQL implementation for conversation mapping storage

    Schema:
        CREATE TABLE conversation_mappings (
            thread_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(128) NOT NULL,
            conversation_id VARCHAR(256) NOT NULL,
            user_id VARCHAR(128) NOT NULL,
            conversation_type VARCHAR(32) NOT NULL,
            user_name VARCHAR(256),
            channel_id VARCHAR(256),
            service_url VARCHAR(512),
            langgraph_workflow_endpoint VARCHAR(512),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            metadata JSONB,
            UNIQUE(tenant_id, conversation_id, user_id)
        );

        CREATE INDEX idx_tenant_conversation ON conversation_mappings(tenant_id, conversation_id);
        CREATE INDEX idx_tenant_user ON conversation_mappings(tenant_id, user_id);
        CREATE INDEX idx_last_activity ON conversation_mappings(last_activity_at) WHERE is_active = TRUE;
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._ensure_schema()

    def _get_connection(self):
        return psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)

    def _ensure_schema(self):
        """Create table if not exists"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_mappings (
                        thread_id VARCHAR(64) PRIMARY KEY,
                        tenant_id VARCHAR(128) NOT NULL,
                        conversation_id VARCHAR(256) NOT NULL,
                        user_id VARCHAR(128) NOT NULL,
                        conversation_type VARCHAR(32) NOT NULL,
                        user_name VARCHAR(256),
                        channel_id VARCHAR(256),
                        service_url VARCHAR(512),
                        langgraph_workflow_endpoint VARCHAR(512),
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        metadata JSONB,
                        UNIQUE(tenant_id, conversation_id, user_id)
                    )
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tenant_conversation
                    ON conversation_mappings(tenant_id, conversation_id)
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tenant_user
                    ON conversation_mappings(tenant_id, user_id)
                """)

                conn.commit()

    def find_mapping(
        self,
        tenant_id: str,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find existing mapping"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM conversation_mappings
                    WHERE tenant_id = %s
                    AND conversation_id = %s
                    AND user_id = %s
                    AND is_active = TRUE
                """, (tenant_id, conversation_id, user_id))

                return dict(cur.fetchone()) if cur.rowcount > 0 else None

    def get_by_thread_id(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get mapping by thread_id"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM conversation_mappings
                    WHERE thread_id = %s
                """, (thread_id,))

                return dict(cur.fetchone()) if cur.rowcount > 0 else None

    def create_mapping(self, mapping_data: Dict[str, Any]) -> None:
        """Create new mapping"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversation_mappings
                    (thread_id, tenant_id, conversation_id, user_id, conversation_type,
                     user_name, channel_id, service_url, langgraph_workflow_endpoint,
                     created_at, last_activity_at, is_active, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    mapping_data["thread_id"],
                    mapping_data["tenant_id"],
                    mapping_data["conversation_id"],
                    mapping_data["user_id"],
                    mapping_data["conversation_type"],
                    mapping_data.get("user_name"),
                    mapping_data.get("channel_id"),
                    mapping_data.get("service_url"),
                    mapping_data.get("langgraph_workflow_endpoint"),
                    mapping_data["created_at"],
                    mapping_data["last_activity_at"],
                    mapping_data.get("is_active", True),
                    json.dumps(mapping_data.get("metadata", {}))
                ))
                conn.commit()

    def update_activity(self, thread_id: str) -> None:
        """Update last_activity_at"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE conversation_mappings
                    SET last_activity_at = NOW()
                    WHERE thread_id = %s
                """, (thread_id,))
                conn.commit()

    def cleanup_inactive(self, cutoff_date: datetime) -> int:
        """Delete inactive mappings"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM conversation_mappings
                    WHERE last_activity_at < %s
                    AND is_active = TRUE
                """, (cutoff_date,))
                conn.commit()
                return cur.rowcount

    def get_active_conversations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get active conversations for tenant"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM conversation_mappings
                    WHERE tenant_id = %s
                    AND is_active = TRUE
                    ORDER BY last_activity_at DESC
                """, (tenant_id,))

                return [dict(row) for row in cur.fetchall()]

    def deactivate(self, thread_id: str) -> None:
        """Mark conversation as inactive"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE conversation_mappings
                    SET is_active = FALSE
                    WHERE thread_id = %s
                """, (thread_id,))
                conn.commit()
```

---

## Configuration & Factory

```python
# frmk/conversation/factory.py

from frmk.conversation.mapper import ConversationMapper, MappingStrategy
from frmk.conversation.mappers.direct import DirectMapper
from frmk.conversation.mappers.hash import HashMapper
from frmk.conversation.mappers.database import DatabaseMapper
from frmk.conversation.datastores.cosmosdb import CosmosDBDataStore
from frmk.conversation.datastores.postgres import PostgreSQLDataStore
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
                "type": "cosmosdb" | "postgres" | "redis",
                "connection_string": "...",
                # or
                "endpoint": "...",
                "key": "...",
                "database_name": "goalgen",
                "container_name": "conversation_mappings"
            },
            "tenant_id": "tenant-123",
            "langgraph_workflow_endpoint": "https://api.example.com",
            "cleanup_inactive_days": 90
        }
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
            datastore = CosmosDBDataStore(
                connection_string=datastore_config.get("connection_string"),
                endpoint=datastore_config.get("endpoint"),
                key=datastore_config.get("key"),
                database_name=datastore_config.get("database_name", "goalgen"),
                container_name=datastore_config.get("container_name", "conversation_mappings")
            )
        elif datastore_type == "postgres":
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
            "cleanup_inactive_days": config.get("cleanup_inactive_days", 90)
        })

    else:
        raise ValueError(f"Unsupported mapping strategy: {strategy}")
```

---

## Usage Examples

### Example 1: Simple Hash-Based (Development/Production without DB)

```python
from frmk.conversation.factory import create_conversation_mapper
from frmk.conversation.mapper import ConversationContext

# Configuration
config = {
    "strategy": "hash",
    "hash_algorithm": "sha256",
    "hash_length": 16,
    "prefix": "teams"
}

mapper = create_conversation_mapper(config)

# Teams bot receives message
context = ConversationContext(
    conversation_id="19:meeting_abc123@thread.v2",
    user_id="user-aad-guid-123",
    conversation_type="personal",
    tenant_id="tenant-guid-456"
)

# Get thread_id
result = mapper.get_thread_id(context)
print(result.thread_id)  # "teams-a1b2c3d4e5f67890"

# Call LangGraph API
response = requests.post("https://api.example.com/message", json={
    "message": user_message,
    "thread_id": result.thread_id
})
```

### Example 2: Database-Backed (Enterprise/Multi-Tenant)

```python
from frmk.conversation.factory import create_conversation_mapper

# Configuration (from environment or config file)
config = {
    "strategy": "database",
    "datastore": {
        "type": "cosmosdb",
        "connection_string": os.getenv("COSMOS_CONNECTION_STRING"),
        "database_name": "goalgen",
        "container_name": "conversation_mappings"
    },
    "tenant_id": "contoso-tenant-123",
    "langgraph_workflow_endpoint": "https://goalgen-api.contoso.com",
    "cleanup_inactive_days": 90
}

mapper = create_conversation_mapper(config)

# Get or create thread_id (stored in Cosmos DB)
result = mapper.get_thread_id(context)

if result.is_new:
    print(f"New conversation started: {result.thread_id}")
else:
    print(f"Continuing conversation: {result.thread_id}")
    print(f"Last activity: {result.last_activity_at}")

# Call LangGraph API
response = requests.post(
    f"{config['langgraph_workflow_endpoint']}/message",
    json={
        "message": user_message,
        "thread_id": result.thread_id
    }
)

# Update activity timestamp
mapper.update_activity(result.thread_id)
```

### Example 3: Reverse Lookup (Database strategy only)

```python
# Get conversation context from thread_id
thread_id = "teams-a1b2c3d4e5f6"
context = mapper.get_conversation_context(thread_id)

if context:
    print(f"Conversation: {context.conversation_id}")
    print(f"User: {context.user_name}")
    print(f"Type: {context.conversation_type}")
```

### Example 4: Cleanup Inactive Conversations

```python
# Scheduled job (runs daily)
from frmk.conversation.factory import create_conversation_mapper

config = {...}  # Database strategy config
mapper = create_conversation_mapper(config)

# Cleanup conversations inactive for 90+ days
count = mapper.cleanup_inactive(inactive_days=90)
print(f"Cleaned up {count} inactive conversations")
```

### Example 5: Multi-Tenant Analytics

```python
# Get all active conversations for tenant
active_convs = mapper.get_active_conversations(tenant_id="contoso-tenant-123")

print(f"Active conversations: {len(active_convs)}")
for conv in active_convs:
    print(f"  {conv['thread_id']}: {conv['user_name']} - {conv['last_activity_at']}")
```

---

## Integration with Teams Bot

```python
# teams_app/bot.py

from botbuilder.core import ActivityHandler, TurnContext
from frmk.conversation.factory import create_conversation_mapper
from frmk.conversation.mapper import ConversationContext
import httpx
import os

class GoalGenTeamsBot(ActivityHandler):
    def __init__(self):
        # Load mapper config from environment/config file
        mapper_config = {
            "strategy": os.getenv("CONVERSATION_MAPPING_STRATEGY", "hash"),
            "tenant_id": os.getenv("AZURE_TENANT_ID"),
            "langgraph_workflow_endpoint": os.getenv("LANGGRAPH_API_URL"),
        }

        # If database strategy, add datastore config
        if mapper_config["strategy"] == "database":
            mapper_config["datastore"] = {
                "type": os.getenv("DATASTORE_TYPE", "cosmosdb"),
                "connection_string": os.getenv("COSMOS_CONNECTION_STRING"),
                "database_name": os.getenv("COSMOS_DATABASE", "goalgen")
            }

        self.mapper = create_conversation_mapper(mapper_config)
        self.api_url = mapper_config["langgraph_workflow_endpoint"]

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle message from Teams user"""
        activity = turn_context.activity

        # Build conversation context
        context = ConversationContext(
            conversation_id=activity.conversation.id,
            user_id=activity.from_property.aad_object_id,
            conversation_type=activity.conversation.conversation_type,
            tenant_id=activity.conversation.tenant_id,
            user_name=activity.from_property.name,
            channel_id=activity.channel_data.get("channel", {}).get("id") if activity.channel_data else None,
            service_url=activity.service_url
        )

        # Get thread_id
        result = self.mapper.get_thread_id(context)

        # Call LangGraph API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/message",
                json={
                    "message": activity.text,
                    "thread_id": result.thread_id,
                    "user_id": context.user_id
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        # Send response back to Teams
        await turn_context.send_activity(data["message"])

        # Update activity timestamp (if database strategy)
        self.mapper.update_activity(result.thread_id)

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """Handle bot added/removed from conversation"""
        if turn_context.activity.members_removed:
            for member in turn_context.activity.members_removed:
                if member.id == turn_context.activity.recipient.id:
                    # Bot removed, deactivate conversation
                    # (Only works with database strategy)
                    # Extract thread_id and call mapper.deactivate(thread_id)
                    pass
```

---

## Configuration in Goal Spec

```json
{
  "id": "travel_planning",
  "title": "Travel Planning Assistant",

  "ux": {
    "teams": {
      "enabled": true,
      "conversation_mapping": {
        "strategy": "database",
        "datastore": {
          "type": "cosmosdb",
          "database_name": "goalgen",
          "container_name": "conversation_mappings"
        },
        "cleanup_inactive_days": 90
      }
    }
  }
}
```

---

## Summary

✅ **Modular architecture** - Three strategies (direct, hash, database) with pluggable datastores
✅ **Multi-tenant support** - tenant_id isolation in database strategy
✅ **Lifecycle management** - Automatic cleanup of inactive conversations
✅ **Reverse lookup** - Get Teams context from thread_id (database strategy)
✅ **Analytics ready** - Track conversation metrics, user engagement
✅ **Extensible** - Custom mappers and datastores can be added

**Next Step**: Implement this design in `frmk/conversation/` and generate Teams bot code using `generators/teams.py`

---

*This design provides production-ready conversation lifecycle management for Teams ↔ LangGraph integration.*
