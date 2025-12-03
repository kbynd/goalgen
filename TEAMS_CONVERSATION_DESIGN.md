# Teams Bot Conversation Lifecycle & Thread ID Mapping

**Purpose**: Design document for Teams Bot conversation management with LangGraph checkpointer integration

**Last Updated**: 2025-12-02

---

## Problem Statement

When implementing a Microsoft Teams Bot that uses LangGraph for agent orchestration, we need to:

1. **Initiate new conversations** - When user first messages the bot in Teams
2. **Serialize conversation state** - Map Teams conversation metadata to LangGraph thread_id
3. **Deserialize conversation state** - Retrieve LangGraph state from Teams context
4. **Track conversations** - Maintain mapping between Teams and LangGraph
5. **Propagate thread_id** - Ensure LangGraph checkpointer uses correct thread for persistence

---

## Architecture Overview

```
┌─────────────────┐
│  Microsoft      │
│  Teams User     │
└────────┬────────┘
         │ Message
         ▼
┌─────────────────┐
│  Teams Bot      │  ← Bot Framework SDK
│  Activity       │     (turn_context)
└────────┬────────┘
         │ Extract conversation.id
         │ + from.aadObjectId
         │ + serviceUrl
         ▼
┌─────────────────┐
│  Thread ID      │  ← Generate/Lookup
│  Mapping Layer  │     thread_id from Teams context
└────────┬────────┘
         │ thread_id (e.g., "teams-conv-123-user-abc")
         ▼
┌─────────────────┐
│  FastAPI        │  ← POST /message
│  /message       │     {message, thread_id}
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangGraph      │  ← config = {"configurable": {"thread_id": "..."}}
│  Orchestrator   │     graph.invoke(input, config)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Checkpointer   │  ← Cosmos DB / Redis / Azure Postgres
│  (State Store)  │     Stores state keyed by thread_id
└─────────────────┘
```

---

## Teams Bot Conversation Context

### Key Teams Identifiers

When a user messages a Teams bot, the Bot Framework provides these identifiers via `turn_context.activity`:

```python
{
    "conversation": {
        "id": "19:meeting_abc123...",  # Conversation ID (stable per conversation)
        "conversationType": "personal", # or "channel", "groupChat"
        "tenantId": "tenant-guid"
    },
    "from": {
        "id": "29:user-guid",           # User ID (stable per user)
        "aadObjectId": "user-aad-guid", # Azure AD Object ID (preferred)
        "name": "John Doe"
    },
    "channelId": "msteams",
    "serviceUrl": "https://smba.trafficmanager.net/amer/",
    "channelData": {
        "tenant": {"id": "tenant-guid"},
        "team": {"id": "team-guid"},    # If in team/channel
        "channel": {"id": "channel-guid"} # If in channel
    }
}
```

### Conversation Types

1. **Personal (1:1)**: `conversationType: "personal"`
   - conversation.id: Unique per user-bot pair
   - Stable across app restarts
   - Example: `19:user-abc123_conversation-xyz`

2. **Group Chat**: `conversationType: "groupChat"`
   - conversation.id: Unique per group chat
   - Shared across all participants
   - Example: `19:meeting_abc123@thread.v2`

3. **Channel**: `conversationType: "channel"`
   - conversation.id: Includes channel and thread info
   - Format: `19:channelId@thread.tacv2;messageid=threadId`
   - Changes per thread within channel

---

## Thread ID Generation Strategy

### Option 1: Direct Mapping (Simple)
**Use Teams conversation.id directly as LangGraph thread_id**

```python
# Pros: Simple, no lookup needed
# Cons: Exposes Teams internal IDs, may be long/complex

thread_id = turn_context.activity.conversation.id
# Example: "19:meeting_abc123@thread.v2"
```

### Option 2: Hash-Based Mapping (Recommended)
**Generate deterministic hash from Teams identifiers**

```python
import hashlib

def generate_thread_id(conversation_id: str, user_id: str, conversation_type: str) -> str:
    """
    Generate stable thread_id from Teams context

    Args:
        conversation_id: Teams conversation.id
        user_id: Teams from.aadObjectId (preferred) or from.id
        conversation_type: personal/groupChat/channel

    Returns:
        thread_id: Stable identifier for LangGraph checkpointer
    """
    if conversation_type == "personal":
        # For 1:1 chats, thread_id is unique per user
        # This ensures user has single persistent conversation with bot
        key = f"teams-personal-{user_id}"
    elif conversation_type == "groupChat":
        # For group chats, thread_id is per conversation
        # All users in group share conversation state
        key = f"teams-group-{conversation_id}"
    elif conversation_type == "channel":
        # For channels, thread_id is per channel thread
        # Each thread in channel has separate conversation state
        key = f"teams-channel-{conversation_id}"
    else:
        # Fallback
        key = f"teams-{conversation_id}"

    # Hash to create shorter, stable ID
    thread_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
    return f"teams-{thread_hash}"

# Example output: "teams-a1b2c3d4e5f67890"
```

### Option 3: Database Mapping (Enterprise)
**Store bidirectional mapping in database**

```python
# Table: conversation_mappings
# Columns:
#   - teams_conversation_id (indexed)
#   - teams_user_id (indexed)
#   - langgraph_thread_id (indexed, unique)
#   - conversation_type
#   - tenant_id
#   - created_at
#   - last_activity_at
#   - metadata (JSON)

class ConversationMapper:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_or_create_thread_id(
        self,
        conversation_id: str,
        user_id: str,
        conversation_type: str,
        tenant_id: str,
        metadata: dict = None
    ) -> str:
        """
        Get existing thread_id or create new one
        """
        # Try to find existing mapping
        query = """
            SELECT langgraph_thread_id
            FROM conversation_mappings
            WHERE teams_conversation_id = ? AND teams_user_id = ?
        """
        result = self.db.execute(query, (conversation_id, user_id))

        if result:
            # Update last_activity_at
            thread_id = result[0]
            self.db.execute(
                "UPDATE conversation_mappings SET last_activity_at = NOW() WHERE langgraph_thread_id = ?",
                (thread_id,)
            )
            return thread_id

        # Create new mapping
        thread_id = f"teams-{uuid.uuid4().hex[:16]}"
        self.db.execute("""
            INSERT INTO conversation_mappings
            (teams_conversation_id, teams_user_id, langgraph_thread_id,
             conversation_type, tenant_id, created_at, last_activity_at, metadata)
            VALUES (?, ?, ?, ?, ?, NOW(), NOW(), ?)
        """, (conversation_id, user_id, thread_id, conversation_type, tenant_id, json.dumps(metadata or {})))

        return thread_id
```

---

## Implementation Flow

### 1. Teams Bot Receives Message

```python
# teams_bot.py (Bot Framework integration)

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes
import httpx

class GoalGenTeamsBot(ActivityHandler):
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming message from Teams user"""

        # Extract Teams context
        activity = turn_context.activity
        conversation_id = activity.conversation.id
        user_id = activity.from_property.aad_object_id or activity.from_property.id
        conversation_type = activity.conversation.conversation_type
        tenant_id = activity.conversation.tenant_id
        user_message = activity.text

        # Generate thread_id for LangGraph
        thread_id = self.generate_thread_id(
            conversation_id=conversation_id,
            user_id=user_id,
            conversation_type=conversation_type
        )

        # Call FastAPI /message endpoint
        response = await self.send_to_api(
            message=user_message,
            thread_id=thread_id,
            user_id=user_id,
            metadata={
                "conversation_id": conversation_id,
                "conversation_type": conversation_type,
                "tenant_id": tenant_id,
                "user_name": activity.from_property.name,
                "channel_id": activity.channel_id
            }
        )

        # Send response back to Teams
        await turn_context.send_activity(Activity(
            type=ActivityTypes.message,
            text=response["message"]
        ))

    def generate_thread_id(self, conversation_id: str, user_id: str, conversation_type: str) -> str:
        """Generate stable thread_id from Teams context (Option 2)"""
        import hashlib

        if conversation_type == "personal":
            key = f"teams-personal-{user_id}"
        elif conversation_type == "groupChat":
            key = f"teams-group-{conversation_id}"
        elif conversation_type == "channel":
            key = f"teams-channel-{conversation_id}"
        else:
            key = f"teams-{conversation_id}"

        thread_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return f"teams-{thread_hash}"

    async def send_to_api(self, message: str, thread_id: str, user_id: str, metadata: dict) -> dict:
        """Send message to FastAPI orchestrator"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/v1/message",
                json={
                    "message": message,
                    "thread_id": thread_id,
                    "user_id": user_id,
                    "metadata": metadata
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
```

---

### 2. FastAPI Receives Message with thread_id

```python
# orchestrator/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from workflow.quest_builder import build_graph
from langgraph.checkpoint.postgres import PostgresSaver  # or CosmosDBSaver, RedisSaver

app = FastAPI()

# Initialize checkpointer (Azure Postgres example)
checkpointer = PostgresSaver.from_conn_string(
    conn_string=os.getenv("POSTGRES_CONN_STRING")
)

# Build LangGraph graph
graph = build_graph(checkpointer=checkpointer)

class MessageRequest(BaseModel):
    message: str
    thread_id: str
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/v1/message")
async def handle_message(request: MessageRequest):
    """
    Handle incoming message with thread_id

    The thread_id is used by LangGraph checkpointer to:
    1. Load existing conversation state (if thread_id seen before)
    2. Save updated state after processing message
    3. Maintain conversation history and context
    """
    try:
        # Configure LangGraph with thread_id
        config = {
            "configurable": {
                "thread_id": request.thread_id,  # ← Key for checkpointer
                "user_id": request.user_id,
                "metadata": request.metadata or {}
            }
        }

        # Invoke LangGraph graph with message
        # The graph will:
        # 1. Load previous state from checkpointer using thread_id
        # 2. Process message through supervisor -> agents -> tools
        # 3. Save updated state to checkpointer
        result = graph.invoke(
            {
                "messages": [{"role": "user", "content": request.message}],
                "user_id": request.user_id
            },
            config=config
        )

        # Extract response
        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, "content") else str(last_message)

        return {
            "message": response_text,
            "thread_id": request.thread_id,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 3. LangGraph Uses thread_id for Checkpointing

```python
# workflow/quest_builder.py

from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict, List

class QuestState(TypedDict):
    messages: List[dict]
    user_id: str
    context: dict
    current_step: str

def build_graph(checkpointer: PostgresSaver):
    """Build LangGraph graph with checkpointer"""

    graph = StateGraph(QuestState)

    # Define nodes (supervisor, agents, etc.)
    def supervisor(state: QuestState):
        # Supervisor logic
        return state

    def flight_agent(state: QuestState):
        # Flight agent logic
        return state

    # Add nodes and edges
    graph.add_node("supervisor", supervisor)
    graph.add_node("flight_agent", flight_agent)
    graph.add_edge("supervisor", "flight_agent")

    # Set entry point
    graph.set_entry_point("supervisor")

    # Compile with checkpointer
    # The checkpointer automatically:
    # 1. Loads state when thread_id is provided in config
    # 2. Saves state after each node execution
    # 3. Maintains conversation history
    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph
```

---

## Checkpointer Storage Options

### Option 1: Azure Cosmos DB (Recommended for Azure deployments)
```python
from langgraph.checkpoint.cosmos import CosmosDBSaver

checkpointer = CosmosDBSaver(
    connection_string=os.getenv("COSMOS_CONNECTION_STRING"),
    database_name="goalgen",
    container_name="checkpoints"
)
```

### Option 2: Azure Database for PostgreSQL
```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    conn_string=os.getenv("POSTGRES_CONN_STRING")
)
```

### Option 3: Azure Cache for Redis
```python
from langgraph.checkpoint.redis import RedisSaver

checkpointer = RedisSaver(
    redis_url=os.getenv("REDIS_URL")
)
```

### Option 4: In-Memory (Dev/Testing only)
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
# Note: State lost on restart, not suitable for production
```

---

## Conversation State Management

### What Gets Persisted

When using a checkpointer, LangGraph automatically persists:

1. **Conversation History**
   - All messages in the conversation thread
   - User inputs and bot responses
   - Agent intermediate steps

2. **Context State**
   - Extracted entities (e.g., destination, dates, budget)
   - Partial information from ongoing tasks
   - User preferences

3. **Workflow Position**
   - Current node in the graph
   - Pending tasks
   - Completed evaluations

4. **Metadata**
   - User ID, conversation type, tenant ID
   - Timestamps
   - Custom metadata from Teams

### State Retrieval

```python
# Get conversation history for a thread
history = checkpointer.list(config={"configurable": {"thread_id": "teams-abc123"}})

# Resume conversation from specific checkpoint
result = graph.invoke(
    {"messages": [{"role": "user", "content": "Continue"}]},
    config={"configurable": {"thread_id": "teams-abc123"}}
)
```

---

## Multi-Device & Cross-Platform Support

### Scenario: User switches from Teams to Webchat

Because thread_id is derived from Teams user identity:

1. **Teams**: User messages bot in Teams
   - thread_id = `teams-a1b2c3d4` (derived from aadObjectId)
   - LangGraph persists state with this thread_id

2. **Webchat**: Same user opens webchat
   - Webchat authenticates user (Azure AD SSO)
   - Derives same thread_id = `teams-a1b2c3d4` using aadObjectId
   - LangGraph loads existing state
   - Conversation continues seamlessly

**Key**: Use stable user identity (Azure AD Object ID) across platforms

---

## Conversation Lifecycle Events

### New Conversation (conversationUpdate)
```python
async def on_conversation_update_activity(self, turn_context: TurnContext):
    """Handle conversation creation, bot added to conversation, etc."""
    if turn_context.activity.members_added:
        for member in turn_context.activity.members_added:
            if member.id != turn_context.activity.recipient.id:
                # Bot added to conversation, send welcome message
                await turn_context.send_activity("Hi! I'm your travel planning assistant.")

                # Optionally initialize thread_id in mapping DB
                thread_id = self.generate_thread_id(...)
                # Store in DB for analytics/monitoring
```

### Conversation Deletion
```python
async def on_conversation_update_activity(self, turn_context: TurnContext):
    """Handle bot removed from conversation"""
    if turn_context.activity.members_removed:
        for member in turn_context.activity.members_removed:
            if member.id == turn_context.activity.recipient.id:
                # Bot removed from conversation
                # Optionally mark thread_id as inactive in mapping DB
                pass
```

---

## Proactive Messaging

Teams bots can send proactive messages using stored conversation reference:

```python
from botbuilder.core import BotFrameworkAdapter, ConversationReference

async def send_proactive_message(
    adapter: BotFrameworkAdapter,
    conversation_reference: ConversationReference,
    message: str
):
    """Send proactive message to Teams user"""
    async def callback(turn_context: TurnContext):
        await turn_context.send_activity(message)

    await adapter.continue_conversation(
        conversation_reference,
        callback,
        bot_app_id=os.getenv("MICROSOFT_APP_ID")
    )
```

**Use Case**: Agent completes background task, sends update to user in Teams

---

## Security Considerations

### 1. Tenant Isolation
```python
# Verify tenant_id matches expected tenant
if activity.conversation.tenant_id not in ALLOWED_TENANTS:
    raise UnauthorizedError("Tenant not authorized")
```

### 2. User Authentication
```python
# Use Azure AD Object ID (aadObjectId) as primary user identifier
# More stable than Teams user ID
user_id = activity.from_property.aad_object_id
if not user_id:
    raise ValueError("Azure AD Object ID required")
```

### 3. Thread ID Validation
```python
# Validate thread_id format before using with checkpointer
import re
if not re.match(r'^teams-[a-f0-9]{16}$', thread_id):
    raise ValueError("Invalid thread_id format")
```

---

## Recommended Implementation Strategy

### Phase 1: Basic Teams Bot (teams generator)
- ✅ Bot Framework integration
- ✅ Handle on_message_activity
- ✅ Generate thread_id using Option 2 (hash-based)
- ✅ Call FastAPI /message endpoint
- ✅ Return responses to Teams

### Phase 2: Conversation Mapping (Optional)
- Store conversation metadata in database
- Track active conversations
- Analytics and monitoring

### Phase 3: Advanced Features
- Proactive messaging
- Adaptive Cards for rich responses
- Multi-turn dialogs with confirmations
- Human-in-the-loop approvals

---

## Summary: Thread ID Mapping Flow

```
Teams User → Teams Bot → Extract context → Generate thread_id → FastAPI
                            (conversation.id)   (deterministic hash)
                            (from.aadObjectId)
                            (conversation_type)

FastAPI → LangGraph → Checkpointer → Load/Save State
          config={                    (keyed by thread_id)
            "thread_id": "teams-a1b2c3d4"
          }

Next Message → Same thread_id → State retrieved → Conversation continues
```

**Key Insight**: The thread_id acts as the bridge between Teams' conversation context and LangGraph's persistent state management. By generating a stable, deterministic thread_id from Teams identifiers, we ensure conversation continuity across messages, restarts, and even platform switches.

---

*This design will be implemented in the `teams` generator to produce working Teams Bot code.*
