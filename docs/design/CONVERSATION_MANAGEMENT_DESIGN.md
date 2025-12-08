# Conversation Management Architecture

How conversations are managed, stored, and integrated with Azure services.

---

## Design Decision: Hybrid Approach

**Use both:**
1. **LangGraph State** - Primary conversation storage (operational)
2. **Azure Conversation API** - Analytics, insights, compliance (observability)

```
┌─────────────────────────────────────────────────────────────┐
│                    User Message Flow                         │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Orchestrator                        │
│                                                               │
│  1. Receive message                                          │
│  2. Load thread state from Checkpointer                      │
│  3. Send to Azure Conversation API (async)                   │
│  4. Invoke LangGraph                                         │
│  5. Save updated state to Checkpointer                       │
│  6. Return response                                          │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│   LangGraph State    │    │ Azure Conversation API       │
│   (Operational)      │    │ (Analytics)                  │
│                      │    │                              │
│  Stored in:          │    │  Features:                   │
│  - Cosmos DB         │    │  - Intent tracking           │
│  - Redis             │    │  - Entity extraction         │
│  - Blob Storage      │    │  - Sentiment analysis        │
│                      │    │  - Topic modeling            │
│  Purpose:            │    │  - Conversation analytics    │
│  - Resume threads    │    │  - Compliance/audit          │
│  - Multi-turn logic  │    │  - Long-term insights        │
│  - Context tracking  │    │                              │
└──────────────────────┘    └──────────────────────────────┘
```

---

## 1. LangGraph State (Primary Storage)

### State Schema

```python
# frmk/langgraph/state_schema.py

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class ConversationState(TypedDict):
    """
    LangGraph conversation state

    This is the PRIMARY source of truth for active conversations.
    Stored in Checkpointer (Cosmos/Redis/Blob).
    """

    # Thread management
    thread_id: str
    user_id: str
    goal_id: str

    # Messages (conversation history)
    messages: List[BaseMessage]

    # Context (extracted entities, user preferences)
    context: Dict[str, Any]

    # Workflow state
    current_task: Optional[str]
    completed_tasks: List[str]
    pending_actions: List[str]

    # Metadata
    created_at: str
    updated_at: str
    message_count: int

    # Next node routing
    next: Optional[str]
```

### Checkpointer Storage

```python
# Cosmos DB document structure
{
  "id": "travel_a1b2c3d4-checkpoint-001",
  "thread_id": "travel_a1b2c3d4",
  "checkpoint_id": "001",
  "state": {
    "messages": [
      {"role": "user", "content": "Plan trip to Japan"},
      {"role": "assistant", "content": "Great! What's your budget?"}
    ],
    "context": {
      "destination": "Japan",
      "budget": null,
      "dates": null
    },
    "current_task": "research_flights"
  },
  "timestamp": "2024-11-29T19:00:00Z",
  "ttl": 2592000  // 30 days
}
```

---

## 2. Azure Conversation API (Analytics Layer)

### Integration Points

```python
# frmk/conversation/azure_conversation_tracker.py

from azure.ai.language.conversations import ConversationAnalysisClient
from azure.identity import DefaultAzureCredential
from typing import Dict, Any, List
from frmk.utils.logging import get_logger

logger = get_logger("conversation_tracker")


class AzureConversationTracker:
    """
    Track conversations in Azure Conversation API

    Purpose:
    - Analytics and insights
    - Compliance and audit trail
    - Long-term conversation history
    - Intent/entity extraction
    - Sentiment analysis
    """

    def __init__(self, config: Dict[str, Any]):
        self.credential = DefaultAzureCredential()

        conversation_config = config.get("conversation_api", {})

        self.enabled = conversation_config.get("enabled", False)

        if self.enabled:
            self.client = ConversationAnalysisClient(
                endpoint=conversation_config["endpoint"],
                credential=self.credential
            )

            self.project_name = conversation_config["project_name"]
            self.deployment_name = conversation_config.get("deployment_name", "production")

    async def track_message(
        self,
        thread_id: str,
        user_id: str,
        message: str,
        role: str,  # "user" or "assistant"
        metadata: Dict[str, Any]
    ):
        """
        Send message to Azure Conversation API for tracking

        This is ASYNC and non-blocking - doesn't delay user response
        """

        if not self.enabled:
            return

        try:
            # Send to Azure Conversation API
            result = await self.client.analyze_conversation(
                task={
                    "kind": "Conversation",
                    "analysisInput": {
                        "conversationItem": {
                            "id": metadata.get("message_id"),
                            "participantId": user_id,
                            "text": message,
                            "role": role
                        }
                    },
                    "parameters": {
                        "projectName": self.project_name,
                        "deploymentName": self.deployment_name,
                        "stringIndexType": "TextElement_V8",
                        "verbose": True
                    }
                }
            )

            # Extract insights
            insights = {
                "intent": result.prediction.top_intent if hasattr(result, 'prediction') else None,
                "entities": result.prediction.entities if hasattr(result, 'prediction') else [],
                "sentiment": getattr(result, 'sentiment', None)
            }

            logger.info(f"Conversation tracked: {thread_id}", extra={
                "thread_id": thread_id,
                "insights": insights
            })

        except Exception as e:
            # Don't fail the main flow if analytics fails
            logger.error(f"Failed to track conversation: {e}")

    async def get_conversation_insights(
        self,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Get analytics for a conversation thread

        Returns:
        - Common intents
        - Extracted entities
        - Sentiment trends
        - Topic distribution
        """

        if not self.enabled:
            return {}

        try:
            # Query conversation history
            # Azure Conversation API provides aggregated insights

            # TODO: Implement conversation history query

            return {
                "thread_id": thread_id,
                "message_count": 0,
                "intents": [],
                "entities": [],
                "sentiment": "neutral"
            }

        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            return {}


# Global singleton
_conversation_tracker = None


def get_conversation_tracker(config: Dict[str, Any] = None):
    """Get or create conversation tracker"""
    global _conversation_tracker

    if _conversation_tracker is None:
        _conversation_tracker = AzureConversationTracker(config or {})

    return _conversation_tracker
```

---

## 3. Integration in Orchestrator

### FastAPI Message Handler

```python
# orchestrator/app/main.py (generated)

from fastapi import FastAPI, Depends
from frmk.conversation.azure_conversation_tracker import get_conversation_tracker
from frmk.langgraph.graph_builder import GraphBuilder
import asyncio

app = FastAPI()


@app.post("/api/v1/goal/{goal_id}/message")
async def send_message(
    goal_id: str,
    request: MessageRequest,
    user: UserContext = Depends(get_current_user)
):
    """
    Send message to goal

    Flow:
    1. Load state from checkpointer
    2. Track in Azure Conversation API (async, non-blocking)
    3. Invoke LangGraph
    4. Save state to checkpointer
    5. Track response in Azure Conversation API (async)
    6. Return response
    """

    # Load goal config
    goal_config = load_goal_config(goal_id)

    # Get or create thread
    thread_id = request.thread_id or create_thread_id(goal_id, user.user_id)

    # Track user message (async, don't wait)
    conversation_tracker = get_conversation_tracker(goal_config)
    asyncio.create_task(
        conversation_tracker.track_message(
            thread_id=thread_id,
            user_id=user.user_id,
            message=request.message,
            role="user",
            metadata={"goal_id": goal_id}
        )
    )

    # Invoke LangGraph (primary flow)
    graph = GraphBuilder(goal_config).build_from_spec()

    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"messages": [("user", request.message)]},
        config=config
    )

    # Extract response
    assistant_message = result["messages"][-1].content

    # Track assistant response (async, don't wait)
    asyncio.create_task(
        conversation_tracker.track_message(
            thread_id=thread_id,
            user_id=user.user_id,
            message=assistant_message,
            role="assistant",
            metadata={"goal_id": goal_id}
        )
    )

    return MessageResponse(
        response=assistant_message,
        thread_id=thread_id,
        context=result.get("context", {})
    )
```

---

## 4. Spec Configuration

```json
{
  "id": "travel_planning",

  "state_management": {
    "checkpointing": {
      "backend": "cosmos",
      "configuration": {
        "cosmos": {
          "database": "goalgen",
          "container": "checkpoints",
          "partition_key": "/thread_id",
          "ttl_seconds": 2592000
        }
      }
    },
    "threads": {
      "id_generation": {
        "strategy": "uuid",
        "prefix": "travel_"
      }
    }
  },

  "conversation_api": {
    "enabled": true,
    "endpoint": "${CONVERSATION_API_ENDPOINT}",
    "project_name": "travel-planning-conversations",
    "deployment_name": "production",

    "features": {
      "intent_recognition": true,
      "entity_extraction": true,
      "sentiment_analysis": true,
      "topic_modeling": true
    },

    "analytics": {
      "enabled": true,
      "retention_days": 90,
      "export_to_blob": true
    }
  }
}
```

---

## 5. Comparison: State vs Conversation API

| Aspect | LangGraph State | Azure Conversation API |
|--------|----------------|------------------------|
| **Purpose** | Operational (runtime) | Analytics (insights) |
| **Storage** | Cosmos/Redis/Blob | Azure Conversation Service |
| **Lifetime** | 30 days (configurable) | 90+ days |
| **Access Pattern** | Read/write per message | Write-heavy, query for insights |
| **Latency** | Low (5-10ms) | Medium (50-100ms) |
| **Cost** | Medium | Low (analytics tier) |
| **Features** | - Thread resumption<br>- Context tracking<br>- Workflow state | - Intent recognition<br>- Entity extraction<br>- Sentiment analysis<br>- Topic modeling |
| **Use Cases** | - Resume conversation<br>- Multi-turn logic<br>- Routing decisions | - Conversation analytics<br>- Compliance/audit<br>- Product insights<br>- User behavior |

---

## 6. Benefits of Hybrid Approach

### ✅ Separation of Concerns
- **LangGraph State**: Fast, operational, drives workflow
- **Conversation API**: Analytics, compliance, insights

### ✅ No Latency Impact
- Conversation API tracking is async (fire-and-forget)
- User doesn't wait for analytics

### ✅ Compliance & Audit
- Full conversation history in Azure Conversation API
- Retention policies separate from operational state
- Queryable for compliance (GDPR, data requests)

### ✅ Product Insights
- Intent trends: "Users ask about flights 3x more than hotels"
- Entity patterns: "80% specify budget, only 20% specify dates"
- Sentiment: "Users frustrated when missing context fields"

### ✅ Cost Optimization
- Short-lived operational state (30 days TTL)
- Long-term analytics in cheaper tier (90+ days)

---

## 7. Alternative: Conversation API Only

**Could we use ONLY Azure Conversation API?**

❌ **Not recommended** because:
1. **Higher latency** - Every message requires API call
2. **No checkpointing** - Can't resume LangGraph mid-execution
3. **No workflow state** - Conversation API doesn't track task progress
4. **Coupling** - LangGraph tightly coupled to Azure service

**LangGraph needs its own state for:**
- Checkpointing (resume from interrupts)
- Routing decisions (which node next?)
- Workflow tracking (which tasks completed?)

---

## 8. Core SDK Bridge

```python
# Add to frmk/conversation/__init__.py

from .azure_conversation_tracker import (
    AzureConversationTracker,
    get_conversation_tracker
)

__all__ = [
    "AzureConversationTracker",
    "get_conversation_tracker"
]
```

---

## Summary

### ✅ **Recommendation: Hybrid Approach**

1. **LangGraph State (Primary)**
   - Stored in Checkpointer (Cosmos/Redis/Blob)
   - Fast operational access
   - Drives workflow logic
   - 30-day TTL

2. **Azure Conversation API (Analytics)**
   - Async tracking (non-blocking)
   - Intent/entity/sentiment extraction
   - Long-term retention (90+ days)
   - Compliance & insights

### Implementation

```
frmk/conversation/
├── azure_conversation_tracker.py    # NEW - Conversation API bridge
└── __init__.py

generators/api.py                    # Update to add tracking calls
```

**This gives us the best of both worlds: fast operational state + rich analytics!**
