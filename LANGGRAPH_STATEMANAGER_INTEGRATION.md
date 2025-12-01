# LangGraph + StateManager Integration

How StateManager integrates conversation tracking into LangGraph workflows.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph Workflow                         │
│                                                               │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐              │
│  │ Node │ -> │ Node │ -> │ Node │ -> │ END  │              │
│  │  1   │    │  2   │    │  3   │    │      │              │
│  └───┬──┘    └───┬──┘    └───┬──┘    └──────┘              │
│      │           │           │                               │
│      │ State     │ State     │ State                         │
│      │ Update    │ Update    │ Update                        │
│      ▼           ▼           ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         StateManager (Intercepts all saves)          │   │
│  │                                                       │   │
│  │  1. Validate state                                   │   │
│  │  2. Save to checkpointer ───────────────────┐       │   │
│  │  3. Track conversation (async) ──────────┐  │       │   │
│  │  4. Track metrics (async) ────────────┐  │  │       │   │
│  └────────────────────────────────────┼──┼──┼──┼───────┘   │
└───────────────────────────────────────┼──┼──┼──┼───────────┘
                                        │  │  │  │
                    ┌───────────────────┘  │  │  │
                    │   ┌──────────────────┘  │  │
                    │   │   ┌─────────────────┘  │
                    │   │   │   ┌────────────────┘
                    ▼   ▼   ▼   ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
│ Checkpointer │  │ Conversation │  │  AI Foundry     │
│ (Cosmos/     │  │ API          │  │  (Metrics)      │
│  Redis)      │  │ (Analytics)  │  │                 │
└──────────────┘  └──────────────┘  └─────────────────┘
```

---

## Implementation

### 1. Create Checkpointer with StateManager

```python
# langgraph/quest_builder.py (generated)

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver  # or CosmosCheckpointer, etc.

from frmk.core.state_manager import create_state_manager
from frmk.checkpointers.cosmos_checkpointer import CosmosCheckpointer

import json


def load_goal_config():
    """Load goal configuration"""
    with open("config/goal_spec.json") as f:
        return json.load(f)


def build_graph():
    """
    Build LangGraph with StateManager integration

    StateManager automatically:
    - Tracks conversations in Azure Conversation API
    - Tracks metrics in AI Foundry
    - Validates state schema
    """

    # Load config
    goal_config = load_goal_config()

    # Create checkpointer (Cosmos/Redis/Blob)
    checkpointer = CosmosCheckpointer(
        endpoint=goal_config["state_management"]["checkpointing"]["configuration"]["cosmos"]["endpoint"],
        database=goal_config["state_management"]["checkpointing"]["configuration"]["cosmos"]["database"],
        container=goal_config["state_management"]["checkpointing"]["configuration"]["cosmos"]["container"]
    )

    # Create StateManager (wraps checkpointer with tracking)
    state_manager = create_state_manager(goal_config, checkpointer)

    # Build graph
    from .state_schema import QuestState
    graph = StateGraph(QuestState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("flight_agent", flight_agent_node)
    graph.add_node("hotel_agent", hotel_agent_node)

    # Wire edges
    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "flight_agent")
    graph.add_edge("flight_agent", "hotel_agent")
    graph.add_edge("hotel_agent", END)

    # Compile with StateManager's checkpointer
    # The checkpointer will call StateManager on every save
    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph, state_manager
```

### 2. Custom Checkpointer Wrapper

**Problem**: LangGraph's checkpointer interface doesn't have hooks for StateManager

**Solution**: Wrap the checkpointer to intercept saves

```python
# frmk/core/tracked_checkpointer.py

from langgraph.checkpoint import BaseCheckpointSaver
from typing import Dict, Any, Optional
from frmk.core.state_manager import StateManager
from frmk.utils.logging import get_logger
import asyncio

logger = get_logger("tracked_checkpointer")


class TrackedCheckpointer(BaseCheckpointSaver):
    """
    Checkpointer wrapper that integrates StateManager

    Intercepts all save operations to:
    1. Track conversations
    2. Track metrics
    3. Validate state
    """

    def __init__(
        self,
        underlying_checkpointer: BaseCheckpointSaver,
        state_manager: StateManager,
        user_id_extractor: Optional[callable] = None
    ):
        """
        Args:
            underlying_checkpointer: Real checkpointer (Cosmos/Redis/Blob)
            state_manager: StateManager instance
            user_id_extractor: Function to extract user_id from config
        """

        self.checkpointer = underlying_checkpointer
        self.state_manager = state_manager
        self.user_id_extractor = user_id_extractor or self._default_user_id_extractor

    def put(
        self,
        config: Dict,
        checkpoint: Dict,
        metadata: Dict
    ) -> Dict:
        """
        Save checkpoint and track in Azure services

        This is called by LangGraph after every node execution
        """

        thread_id = config["configurable"]["thread_id"]
        user_id = self.user_id_extractor(config)

        # Extract state from checkpoint
        state = checkpoint.get("state", checkpoint)  # Handle different checkpoint formats

        # Save via StateManager (which tracks conversation + metrics)
        # Run async tracking but return immediately
        asyncio.create_task(
            self.state_manager.save_state(
                thread_id=thread_id,
                user_id=user_id,
                state=state,
                checkpoint_metadata=metadata
            )
        )

        # Delegate to underlying checkpointer for actual save
        return self.checkpointer.put(config, checkpoint, metadata)

    def get(self, config: Dict) -> Optional[Dict]:
        """Load checkpoint"""
        return self.checkpointer.get(config)

    def list(self, config: Dict) -> list:
        """List checkpoints"""
        return self.checkpointer.list(config)

    def _default_user_id_extractor(self, config: Dict) -> str:
        """Extract user_id from config"""
        return config.get("configurable", {}).get("user_id", "unknown")


def create_tracked_checkpointer(
    checkpointer: BaseCheckpointSaver,
    state_manager: StateManager,
    user_id_extractor: Optional[callable] = None
) -> TrackedCheckpointer:
    """
    Create tracked checkpointer

    Usage:
        checkpointer = CosmosCheckpointer(...)
        state_manager = create_state_manager(goal_config, checkpointer)

        tracked = create_tracked_checkpointer(checkpointer, state_manager)

        graph = graph.compile(checkpointer=tracked)
    """

    return TrackedCheckpointer(checkpointer, state_manager, user_id_extractor)
```

### 3. Updated Graph Builder

```python
# langgraph/quest_builder.py (updated)

from frmk.core.state_manager import create_state_manager
from frmk.core.tracked_checkpointer import create_tracked_checkpointer
from frmk.checkpointers.cosmos_checkpointer import CosmosCheckpointer


def build_graph():
    """Build graph with conversation tracking"""

    goal_config = load_goal_config()

    # 1. Create underlying checkpointer
    checkpointer = CosmosCheckpointer(
        endpoint=goal_config["state_management"]["checkpointing"]["configuration"]["cosmos"]["endpoint"],
        # ... other config
    )

    # 2. Create StateManager
    state_manager = create_state_manager(goal_config, checkpointer)

    # 3. Wrap checkpointer with tracking
    tracked_checkpointer = create_tracked_checkpointer(
        checkpointer=checkpointer,
        state_manager=state_manager,
        user_id_extractor=lambda config: config["configurable"].get("user_id", "unknown")
    )

    # 4. Build graph
    graph = StateGraph(QuestState)
    # ... add nodes ...

    # 5. Compile with tracked checkpointer
    compiled_graph = graph.compile(checkpointer=tracked_checkpointer)

    return compiled_graph
```

### 4. Usage in Orchestrator

```python
# orchestrator/app/main.py (generated)

from fastapi import FastAPI, Depends
from langgraph.quest_builder import build_graph

app = FastAPI()

# Build graph once at startup
graph = build_graph()


@app.post("/api/v1/goal/{goal_id}/message")
async def send_message(
    goal_id: str,
    request: MessageRequest,
    user: UserContext = Depends(get_current_user)
):
    """
    Send message to goal

    Conversation tracking happens automatically via TrackedCheckpointer
    """

    thread_id = request.thread_id or create_thread_id(goal_id, user.user_id)

    # Invoke graph
    # TrackedCheckpointer intercepts every state save and:
    # 1. Tracks in Conversation API
    # 2. Tracks in AI Foundry
    # 3. Validates state
    result = await graph.ainvoke(
        {"messages": [("user", request.message)]},
        config={
            "configurable": {
                "thread_id": thread_id,
                "user_id": user.user_id  # StateManager uses this
            }
        }
    )

    # Response ready - tracking happened in background
    return MessageResponse(
        response=result["messages"][-1].content,
        thread_id=thread_id,
        context=result.get("context", {})
    )
```

---

## Flow Diagram

### Message Flow with StateManager

```
User sends message
    ↓
FastAPI receives request
    ↓
LangGraph.invoke(state, config)
    ↓
┌────────────────────────────────────────┐
│  LangGraph executes nodes              │
│                                        │
│  Node 1 (supervisor)                   │
│    ↓                                   │
│  Update state                          │
│    ↓                                   │
│  Checkpointer.put() ──────────────┐   │
│                                    │   │
│  Node 2 (agent)                    │   │
│    ↓                                   │
│  Update state                          │
│    ↓                                   │
│  Checkpointer.put() ──────────────┤   │
│                                    │   │
│  Node 3 (evaluator)                │   │
│    ↓                                   │
│  Update state                          │
│    ↓                                   │
│  Checkpointer.put() ──────────────┤   │
│                                    │   │
└────────────────────────────────────┼───┘
                                     │
                                     ▼
              ┌────────────────────────────────────┐
              │  TrackedCheckpointer.put()         │
              │                                    │
              │  1. Extract state & thread_id      │
              │  2. Call StateManager.save_state() │
              │     ├─> Validate state             │
              │     ├─> Save to Cosmos/Redis       │
              │     ├─> Track conversation (async) │
              │     └─> Track metrics (async)      │
              │  3. Return to LangGraph            │
              └────────────────────────────────────┘
                                     │
                                     ▼
              ┌────────────────────────────────────┐
              │  Async tasks (non-blocking):       │
              │                                    │
              │  ┌──────────────────────────────┐ │
              │  │ Conversation API             │ │
              │  │ - Track user message         │ │
              │  │ - Track assistant response   │ │
              │  │ - Extract intent/entities    │ │
              │  └──────────────────────────────┘ │
              │                                    │
              │  ┌──────────────────────────────┐ │
              │  │ AI Foundry                   │ │
              │  │ - Log message count          │ │
              │  │ - Log context completeness   │ │
              │  │ - Log node transitions       │ │
              │  └──────────────────────────────┘ │
              └────────────────────────────────────┘
                                     │
                                     │ (happens in background)
                                     ▼
              User receives response immediately
```

---

## Benefits

### ✅ **Automatic Integration**
- No manual tracking code in nodes
- LangGraph doesn't know about Azure services
- Clean separation of concerns

### ✅ **Non-Blocking**
- Conversation tracking is async
- Doesn't slow down graph execution
- User gets immediate response

### ✅ **Consistent**
- Every state change is tracked
- No missed messages
- Complete audit trail

### ✅ **Configurable**
- Enable/disable via spec
- Different tracking per environment
- Cost control (disable in dev, enable in prod)

---

## Spec Configuration

```json
{
  "state_management": {
    "checkpointing": {
      "backend": "cosmos",
      "tracking": {
        "enabled": true,
        "track_conversations": true,
        "track_metrics": true,
        "track_state_changes": true
      }
    }
  },

  "conversation_api": {
    "enabled": true,
    "endpoint": "${CONVERSATION_API_ENDPOINT}"
  },

  "ai_foundry": {
    "enabled": true,
    "tracing": {
      "enabled": true,
      "sample_rate": 1.0
    }
  }
}
```

---

## Summary

### StateManager Integration Points

| Integration | Where | How |
|-------------|-------|-----|
| **LangGraph** | Via TrackedCheckpointer | Wraps checkpointer.put() |
| **Conversation API** | Async tracking | Fires on every message |
| **AI Foundry** | Async metrics | Fires on every state change |
| **Checkpointer** | Direct delegation | Cosmos/Redis/Blob save |

### Key Classes

```
TrackedCheckpointer (wrapper)
    └─> StateManager (orchestrator)
        ├─> Checkpointer (storage)
        ├─> ConversationTracker (analytics)
        └─> AIFoundryClient (metrics)
```

**This architecture ensures conversation tracking is automatic, non-blocking, and seamlessly integrated into LangGraph workflows!**
