# State Management and Thread Persistence Design

Explicit design decisions for LangGraph state management, serialization, and thread persistence.

---

## Core Principle

**State management, checkpointing, and thread persistence are explicit infrastructure concerns that must be declared in the spec, not inferred.**

### Why Explicit?

1. **Production Critical** - State persistence is essential for reliability
2. **Performance Impact** - Different backends have different characteristics
3. **Cost Implications** - Cosmos vs Redis vs Blob have different pricing
4. **Compliance Requirements** - Data residency, retention policies
5. **Recovery Strategy** - Different backends support different recovery scenarios
6. **Multi-Tenancy** - Thread isolation requirements vary
7. **Debugging** - Need clear understanding of where state lives

---

## State Management Layers

### Layer 1: State Schema (Type Definition)

Defines the structure of conversation state.

**Explicit Declaration Required**:
```json
{
  "state": {
    "schema": {
      "context_fields": ["destination", "budget", "dates", "num_travelers"],
      "metadata_fields": ["user_id", "session_start", "goal_id"],
      "messages": "list[Message]",
      "intermediate_results": "dict",
      "error_history": "list[Error]"
    },
    "validation": {
      "strict": true,
      "allow_extra_fields": false
    }
  }
}
```

**Generated Code**:
```python
from typing import TypedDict, List, Dict, Optional
from pydantic import BaseModel

class QuestState(TypedDict):
    """State schema for travel_planning goal"""

    # Context fields from spec
    destination: Optional[str]
    budget: Optional[float]
    dates: Optional[str]
    num_travelers: Optional[int]

    # Metadata
    user_id: str
    session_start: str
    goal_id: str

    # System fields
    messages: List[Message]
    intermediate_results: Dict[str, Any]
    error_history: List[Error]

    # LangGraph required
    next: Optional[str]
```

---

### Layer 2: Checkpointing Backend

Where and how state is persisted.

**Explicit Declaration Required**:
```json
{
  "checkpointing": {
    "backend": "cosmos|redis|blob|postgres|sqlite",
    "configuration": {
      "cosmos": {
        "database": "goalgen",
        "container": "checkpoints",
        "partition_key": "/thread_id",
        "consistency": "session",
        "throughput": 400
      },
      "redis": {
        "host": "${REDIS_HOST}",
        "port": 6380,
        "ssl": true,
        "db": 0,
        "key_prefix": "langgraph:checkpoints:"
      },
      "blob": {
        "container": "checkpoints",
        "storage_account": "${STORAGE_ACCOUNT}",
        "path_pattern": "{thread_id}/{checkpoint_id}.json"
      }
    },
    "retention": {
      "ttl_seconds": 2592000,
      "max_checkpoints_per_thread": 100,
      "cleanup_strategy": "auto"
    }
  }
}
```

**Backend Comparison**:

| Backend | Latency | Cost | Scalability | Use Case |
|---------|---------|------|-------------|----------|
| **Cosmos DB** | Low (5-10ms) | High | Excellent | Production, multi-region |
| **Redis** | Very Low (1-2ms) | Medium | Good | High-throughput, short TTL |
| **Blob Storage** | Medium (50-100ms) | Low | Excellent | Long-term, archival |
| **PostgreSQL** | Low (10-20ms) | Medium | Good | Self-hosted, SQL queries |
| **SQLite** | Very Low (<1ms) | Free | Poor | Development, testing |

---

### Layer 3: Thread Management

How threads are created, identified, and managed.

**Explicit Declaration Required**:
```json
{
  "threads": {
    "id_generation": {
      "strategy": "uuid|user_provided|deterministic",
      "prefix": "travel_",
      "format": "{prefix}{timestamp}_{user_id}_{random}"
    },
    "isolation": {
      "multi_tenant": true,
      "partition_by": "user_id",
      "access_control": "rbac"
    },
    "lifecycle": {
      "max_duration_seconds": 86400,
      "idle_timeout_seconds": 3600,
      "auto_cleanup": true
    }
  }
}
```

**Thread ID Strategies**:

1. **UUID** - Random, globally unique
   ```python
   thread_id = f"travel_{uuid.uuid4()}"
   ```

2. **User-Provided** - Client specifies ID (resumable sessions)
   ```python
   thread_id = request.headers.get("X-Thread-ID")
   ```

3. **Deterministic** - Based on user + session
   ```python
   thread_id = f"travel_{user_id}_{session_date}"
   ```

---

### Layer 4: Serialization Strategy

How state is serialized/deserialized.

**Explicit Declaration Required**:
```json
{
  "serialization": {
    "format": "json|pickle|msgpack|protobuf",
    "json": {
      "ensure_ascii": false,
      "indent": null,
      "custom_encoders": {
        "datetime": "iso8601",
        "Decimal": "string"
      }
    },
    "compression": {
      "enabled": true,
      "algorithm": "gzip|zstd|lz4",
      "level": 6
    },
    "encryption": {
      "enabled": false,
      "algorithm": "AES-256-GCM",
      "key_source": "key_vault"
    }
  }
}
```

**Serialization Formats**:

| Format | Speed | Size | Human-Readable | Type Safety |
|--------|-------|------|----------------|-------------|
| **JSON** | Medium | Large | Yes | Weak |
| **Pickle** | Fast | Medium | No | Strong (Python) |
| **MessagePack** | Fast | Small | No | Weak |
| **Protobuf** | Very Fast | Very Small | No | Strong |

---

### Layer 5: Checkpoint Strategy

When and how checkpoints are created.

**Explicit Declaration Required**:
```json
{
  "checkpoint_strategy": {
    "frequency": "every_node|every_n_nodes|on_error|manual",
    "every_n_nodes": 3,
    "on_events": ["error", "human_interrupt", "tool_call"],
    "versioning": {
      "enabled": true,
      "max_versions": 10,
      "branching_allowed": true
    },
    "metadata": {
      "include": ["timestamp", "node_name", "agent_name", "cost"],
      "custom_fields": ["model_used", "tokens_consumed"]
    }
  }
}
```

**Checkpoint Frequency Options**:

1. **Every Node** - Maximum recovery granularity, highest overhead
2. **Every N Nodes** - Balanced approach
3. **On Error** - Minimal overhead, recovery from failures only
4. **Manual** - Developer-controlled checkpointing

---

## Complete State Management Spec Section

```json
{
  "id": "travel_planning",
  "title": "Travel Planning Assistant",

  "state_management": {

    "state": {
      "schema": {
        "context_fields": ["destination", "budget", "dates", "num_travelers"],
        "metadata_fields": ["user_id", "session_start", "goal_id"],
        "messages": "list[Message]",
        "intermediate_results": "dict"
      },
      "validation": {
        "strict": true,
        "allow_extra_fields": false
      },
      "initial_state": {
        "goal_id": "travel_planning",
        "intermediate_results": {}
      }
    },

    "checkpointing": {
      "backend": "cosmos",
      "configuration": {
        "cosmos": {
          "endpoint": "${COSMOS_ENDPOINT}",
          "key_source": "managed_identity",
          "database": "goalgen",
          "container": "checkpoints",
          "partition_key": "/thread_id",
          "consistency": "session",
          "throughput": 400
        }
      },
      "retention": {
        "ttl_seconds": 2592000,
        "max_checkpoints_per_thread": 100,
        "cleanup_strategy": "auto"
      }
    },

    "threads": {
      "id_generation": {
        "strategy": "uuid",
        "prefix": "travel_"
      },
      "isolation": {
        "multi_tenant": true,
        "partition_by": "user_id"
      },
      "lifecycle": {
        "max_duration_seconds": 86400,
        "idle_timeout_seconds": 3600
      }
    },

    "serialization": {
      "format": "json",
      "compression": {
        "enabled": true,
        "algorithm": "gzip"
      },
      "encryption": {
        "enabled": false
      }
    },

    "checkpoint_strategy": {
      "frequency": "every_node",
      "on_events": ["error", "human_interrupt"],
      "versioning": {
        "enabled": true,
        "max_versions": 10
      },
      "metadata": {
        "include": ["timestamp", "node_name", "cost"]
      }
    }
  }
}
```

---

## Generated Checkpointer Code

### Cosmos DB Checkpointer

```python
# langgraph/checkpointer_adapter.py (generated)

from typing import Optional
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from langgraph.checkpoint import BaseCheckpointSaver
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata
import json
import gzip

class CosmosCheckpointer(BaseCheckpointSaver):
    """
    Cosmos DB checkpointer for travel_planning goal.

    Generated from spec:
    - Database: goalgen
    - Container: checkpoints
    - Partition Key: thread_id
    - TTL: 2592000 seconds (30 days)
    - Compression: gzip
    """

    def __init__(
        self,
        endpoint: str,
        database: str = "goalgen",
        container: str = "checkpoints",
        credential: Optional[DefaultAzureCredential] = None
    ):
        self.client = CosmosClient(
            endpoint,
            credential=credential or DefaultAzureCredential()
        )
        self.database = self.client.get_database_client(database)
        self.container = self.database.get_container_client(container)

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata
    ) -> dict:
        """Save checkpoint to Cosmos DB"""

        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        # Serialize checkpoint
        serialized = json.dumps(checkpoint)

        # Compress (from spec: gzip enabled)
        compressed = gzip.compress(serialized.encode())

        # Create Cosmos document
        document = {
            "id": f"{thread_id}_{checkpoint_id}",
            "thread_id": thread_id,  # Partition key
            "checkpoint_id": checkpoint_id,
            "checkpoint_data": compressed.hex(),  # Store as hex string
            "metadata": {
                "timestamp": metadata.get("timestamp"),
                "node_name": metadata.get("node_name"),
                "cost": metadata.get("cost")
            },
            "ttl": 2592000  # 30 days (from spec)
        }

        # Write to Cosmos
        self.container.upsert_item(document)

        return config

    def get(self, config: dict) -> Optional[Checkpoint]:
        """Load checkpoint from Cosmos DB"""

        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        if not checkpoint_id:
            # Get latest checkpoint
            query = f"""
                SELECT TOP 1 * FROM c
                WHERE c.thread_id = '{thread_id}'
                ORDER BY c._ts DESC
            """
        else:
            # Get specific checkpoint
            query = f"""
                SELECT * FROM c
                WHERE c.thread_id = '{thread_id}'
                AND c.checkpoint_id = '{checkpoint_id}'
            """

        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=False,
            partition_key=thread_id
        ))

        if not items:
            return None

        document = items[0]

        # Decompress
        compressed = bytes.fromhex(document["checkpoint_data"])
        serialized = gzip.decompress(compressed).decode()

        # Deserialize
        checkpoint = json.loads(serialized)

        return checkpoint

    def list(self, config: dict) -> list[Checkpoint]:
        """List all checkpoints for a thread"""

        thread_id = config["configurable"]["thread_id"]

        query = f"""
            SELECT * FROM c
            WHERE c.thread_id = '{thread_id}'
            ORDER BY c._ts DESC
        """

        items = self.container.query_items(
            query=query,
            enable_cross_partition_query=False,
            partition_key=thread_id
        )

        checkpoints = []
        for document in items:
            compressed = bytes.fromhex(document["checkpoint_data"])
            serialized = gzip.decompress(compressed).decode()
            checkpoint = json.loads(serialized)
            checkpoints.append(checkpoint)

        return checkpoints[:100]  # Max 100 (from spec)


# Factory function
def create_checkpointer(config: dict) -> CosmosCheckpointer:
    """Create checkpointer from configuration"""

    return CosmosCheckpointer(
        endpoint=config["COSMOS_ENDPOINT"],
        database=config.get("COSMOS_DATABASE", "goalgen"),
        container=config.get("COSMOS_CONTAINER", "checkpoints")
    )
```

---

### Redis Checkpointer

```python
# langgraph/checkpointer_adapter.py (Redis variant)

import redis
import json
import gzip
from typing import Optional
from langgraph.checkpoint import BaseCheckpointSaver

class RedisCheckpointer(BaseCheckpointSaver):
    """
    Redis checkpointer for travel_planning goal.

    Generated from spec:
    - Host: from config
    - Port: 6380 (SSL)
    - DB: 0
    - Key Prefix: langgraph:checkpoints:
    - TTL: 2592000 seconds
    """

    def __init__(
        self,
        host: str,
        port: int = 6380,
        password: Optional[str] = None,
        ssl: bool = True,
        db: int = 0,
        key_prefix: str = "langgraph:checkpoints:"
    ):
        self.redis = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=ssl,
            db=db,
            decode_responses=False  # Binary mode for compression
        )
        self.key_prefix = key_prefix
        self.ttl = 2592000  # From spec

    def put(self, config: dict, checkpoint: Checkpoint, metadata: CheckpointMetadata) -> dict:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        # Serialize + compress
        serialized = json.dumps(checkpoint)
        compressed = gzip.compress(serialized.encode())

        # Redis key
        key = f"{self.key_prefix}{thread_id}:{checkpoint_id}"

        # Store with TTL
        self.redis.setex(key, self.ttl, compressed)

        # Also store metadata separately for listing
        meta_key = f"{self.key_prefix}{thread_id}:meta:{checkpoint_id}"
        meta_data = json.dumps({
            "checkpoint_id": checkpoint_id,
            "timestamp": metadata.get("timestamp"),
            "node_name": metadata.get("node_name")
        })
        self.redis.setex(meta_key, self.ttl, meta_data)

        # Add to sorted set for ordering
        list_key = f"{self.key_prefix}{thread_id}:list"
        timestamp = metadata.get("timestamp", 0)
        self.redis.zadd(list_key, {checkpoint_id: timestamp})
        self.redis.expire(list_key, self.ttl)

        return config

    def get(self, config: dict) -> Optional[Checkpoint]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        if not checkpoint_id:
            # Get latest
            list_key = f"{self.key_prefix}{thread_id}:list"
            latest = self.redis.zrevrange(list_key, 0, 0)
            if not latest:
                return None
            checkpoint_id = latest[0].decode()

        # Retrieve checkpoint
        key = f"{self.key_prefix}{thread_id}:{checkpoint_id}"
        compressed = self.redis.get(key)

        if not compressed:
            return None

        # Decompress + deserialize
        serialized = gzip.decompress(compressed).decode()
        checkpoint = json.loads(serialized)

        return checkpoint

    def list(self, config: dict) -> list[Checkpoint]:
        thread_id = config["configurable"]["thread_id"]

        # Get all checkpoint IDs from sorted set
        list_key = f"{self.key_prefix}{thread_id}:list"
        checkpoint_ids = self.redis.zrevrange(list_key, 0, 99)  # Max 100

        checkpoints = []
        for checkpoint_id_bytes in checkpoint_ids:
            checkpoint_id = checkpoint_id_bytes.decode()
            checkpoint = self.get({
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id
                }
            })
            if checkpoint:
                checkpoints.append(checkpoint)

        return checkpoints
```

---

## Thread Management Code

### Thread ID Generation

```python
# orchestrator/app/thread_manager.py (generated)

import uuid
from datetime import datetime
from typing import Optional

class ThreadManager:
    """
    Thread management for travel_planning goal.

    Generated from spec:
    - Strategy: uuid
    - Prefix: travel_
    - Multi-tenant: true
    - Partition by: user_id
    """

    def __init__(self, checkpointer):
        self.checkpointer = checkpointer

    def create_thread(
        self,
        user_id: str,
        goal_id: str = "travel_planning"
    ) -> str:
        """
        Create new thread ID.

        Strategy from spec: uuid with prefix
        Format: travel_{uuid}
        """
        thread_id = f"travel_{uuid.uuid4()}"

        # Initialize thread metadata
        self._init_thread_metadata(thread_id, user_id, goal_id)

        return thread_id

    def resume_thread(
        self,
        thread_id: str,
        user_id: str
    ) -> bool:
        """
        Resume existing thread.

        Validates:
        - Thread exists
        - User has access (multi-tenant isolation)
        - Thread not expired
        """
        metadata = self._get_thread_metadata(thread_id)

        if not metadata:
            return False

        # Multi-tenant check (from spec: partition_by user_id)
        if metadata["user_id"] != user_id:
            raise PermissionError(f"User {user_id} cannot access thread {thread_id}")

        # Lifecycle check (from spec: max_duration 86400s)
        age_seconds = (datetime.utcnow() - metadata["created_at"]).total_seconds()
        if age_seconds > 86400:
            raise ValueError(f"Thread {thread_id} expired (age: {age_seconds}s)")

        return True

    def _init_thread_metadata(self, thread_id: str, user_id: str, goal_id: str):
        """Initialize thread metadata in checkpointer"""
        metadata = {
            "thread_id": thread_id,
            "user_id": user_id,
            "goal_id": goal_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }

        # Store in checkpointer backend
        # (Implementation varies by backend - Cosmos/Redis/etc)
        pass

    def _get_thread_metadata(self, thread_id: str) -> Optional[dict]:
        """Retrieve thread metadata from checkpointer"""
        # (Implementation varies by backend)
        pass
```

---

## Session Store Integration

### Orchestrator Session Management

```python
# orchestrator/app/session_store.py (generated)

from typing import Optional
from langgraph.checkpointer_adapter import create_checkpointer
from langgraph.quest_builder import build_graph

class SessionStore:
    """
    Session management for travel_planning goal.

    Integrates:
    - Thread management
    - Checkpointer backend
    - LangGraph execution
    """

    def __init__(self, config: dict):
        # Create checkpointer from spec configuration
        self.checkpointer = create_checkpointer(config)

        # Build LangGraph with checkpointer
        self.graph = build_graph(checkpointer=self.checkpointer)

        # Thread manager
        self.thread_manager = ThreadManager(self.checkpointer)

    def create_session(self, user_id: str) -> str:
        """Create new conversation session"""
        thread_id = self.thread_manager.create_thread(user_id)
        return thread_id

    def resume_session(self, thread_id: str, user_id: str) -> bool:
        """Resume existing session"""
        return self.thread_manager.resume_thread(thread_id, user_id)

    async def invoke(
        self,
        thread_id: str,
        user_id: str,
        message: str
    ) -> dict:
        """
        Invoke LangGraph with thread persistence.

        Automatically:
        - Loads previous state from checkpointer
        - Executes graph
        - Saves new state to checkpointer
        """

        # Validate access
        self.resume_session(thread_id, user_id)

        # Configure for this thread
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id
            }
        }

        # Invoke graph (checkpointing handled automatically)
        result = await self.graph.ainvoke(
            {"messages": [("user", message)]},
            config=config
        )

        return result
```

---

## Testing State Persistence

### Checkpoint Test Suite

```python
# tests/integration/test_checkpointing.py (generated)

import pytest
from langgraph.checkpointer_adapter import create_checkpointer
from langgraph.quest_builder import build_graph

@pytest.fixture
def checkpointer(cosmos_test_config):
    """Create test checkpointer"""
    return create_checkpointer(cosmos_test_config)

@pytest.fixture
def graph(checkpointer):
    """Create graph with checkpointer"""
    return build_graph(checkpointer=checkpointer)

@pytest.mark.asyncio
async def test_checkpoint_persistence(graph):
    """Test that state persists across invocations"""

    thread_id = "test_thread_123"
    config = {"configurable": {"thread_id": thread_id}}

    # First message
    result1 = await graph.ainvoke(
        {"messages": [("user", "I want to travel to Japan")]},
        config=config
    )

    # Verify state saved
    assert result1["context"]["destination"] == "Japan"

    # Second message (should have previous context)
    result2 = await graph.ainvoke(
        {"messages": [("user", "My budget is $5000")]},
        config=config
    )

    # Verify state persisted
    assert result2["context"]["destination"] == "Japan"  # From first message
    assert result2["context"]["budget"] == 5000  # From second message

@pytest.mark.asyncio
async def test_checkpoint_resume_after_error(graph):
    """Test resuming from checkpoint after error"""

    thread_id = "test_thread_error"
    config = {"configurable": {"thread_id": thread_id}}

    # First invocation succeeds
    result1 = await graph.ainvoke(
        {"messages": [("user", "Plan trip to Japan")]},
        config=config
    )

    # Simulate error in second invocation
    # (State should be saved up to point of error)
    try:
        await graph.ainvoke(
            {"messages": [("user", "Invalid input that causes error")]},
            config=config
        )
    except Exception:
        pass

    # Resume from last good checkpoint
    result3 = await graph.ainvoke(
        {"messages": [("user", "Budget is $5000")]},
        config=config
    )

    # Should have state from first invocation
    assert result3["context"]["destination"] == "Japan"

@pytest.mark.asyncio
async def test_checkpoint_versioning(graph, checkpointer):
    """Test checkpoint versioning"""

    thread_id = "test_thread_versions"
    config = {"configurable": {"thread_id": thread_id}}

    # Create multiple checkpoints
    for i in range(5):
        await graph.ainvoke(
            {"messages": [("user", f"Message {i}")]},
            config=config
        )

    # List all checkpoints
    checkpoints = checkpointer.list(config)

    # Should have multiple versions (max 10 from spec)
    assert len(checkpoints) >= 5
    assert len(checkpoints) <= 10

@pytest.mark.asyncio
async def test_checkpoint_ttl(graph, checkpointer):
    """Test checkpoint TTL cleanup"""

    thread_id = "test_thread_ttl"
    config = {"configurable": {"thread_id": thread_id}}

    # Create checkpoint
    await graph.ainvoke(
        {"messages": [("user", "Test message")]},
        config=config
    )

    # Verify TTL set (2592000 seconds from spec)
    # (Implementation depends on backend - Cosmos, Redis, etc)
    pass
```

---

## Summary

### Explicit State Management Configuration

All state management decisions are **explicit in the spec**:

1. ✅ **State Schema** - Typed fields, validation rules
2. ✅ **Checkpointing Backend** - Cosmos, Redis, Blob, etc.
3. ✅ **Thread Management** - ID generation, isolation, lifecycle
4. ✅ **Serialization** - Format, compression, encryption
5. ✅ **Checkpoint Strategy** - Frequency, versioning, metadata

### No Inference

State management is **never inferred** because:
- ❌ Too critical for production
- ❌ Performance implications
- ❌ Cost implications
- ❌ Compliance requirements
- ❌ Recovery strategy varies

### Generated Code

GoalGen generates:
- ✅ Typed state schema (Pydantic/TypedDict)
- ✅ Backend-specific checkpointer adapter
- ✅ Thread manager with lifecycle management
- ✅ Session store integration
- ✅ Test suite for persistence

### Default Configuration

If not specified, use **safe defaults**:
```json
{
  "state_management": {
    "checkpointing": {
      "backend": "sqlite",  // Development only
      "warn": "SQLite is for development only. Configure Cosmos/Redis for production."
    }
  }
}
```

This ensures state persistence is **always explicit and production-ready**.
