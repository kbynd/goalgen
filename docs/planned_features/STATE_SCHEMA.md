# State Schema Guide

Guide for defining and using state schemas in GoalGen LangGraph workflows.

## Overview

Every LangGraph workflow has a **state schema** that defines:
- ✅ What data flows through the graph
- ✅ Type safety for state fields
- ✅ Documentation for developers
- ✅ IDE autocomplete support

GoalGen generates state schemas in two modes:

1. **Strongly-Typed** - When `context_fields` are defined in spec
2. **Generic** - When no `context_fields` (uses `Dict[str, Any]`)

## Default State Schema (Generic)

If you **don't define** `context_fields` in your spec, you get a generic schema:

```python
class TravelPlanningState(TypedDict):
    """State schema for travel_planning workflow"""

    # Messages (with automatic message reduction)
    messages: Annotated[List[BaseMessage], add_messages]

    # Generic context (no context_fields defined in spec)
    context: Dict[str, Any]

    # Routing
    next: Optional[str]

    # Task tracking
    completed_tasks: List[str]

    # Metadata
    thread_id: Optional[str]
    user_id: Optional[str]
    conversation_insights: Optional[Dict[str, Any]]
```

### Usage (Generic)

```python
state = {
    "messages": [HumanMessage(content="Hello")],
    "context": {
        "destination": "Paris",  # Any key-value pairs
        "dates": "Dec 15-22",
        "budget": 2000
    },
    "next": "supervisor_agent",
    "completed_tasks": [],
    "thread_id": "abc123",
    "user_id": "user456"
}
```

## Strongly-Typed State Schema

Define `context_fields` in your `goal_spec.json` for **type safety** and **validation**:

### Goal Spec with Context Fields

```json
{
  "id": "travel_planning",
  "title": "Travel Planning Assistant",
  "context_fields": {
    "destination": {
      "type": "str",
      "description": "Travel destination city or country",
      "required": true
    },
    "departure_date": {
      "type": "str",
      "description": "Departure date in YYYY-MM-DD format",
      "required": true
    },
    "return_date": {
      "type": "str",
      "description": "Return date in YYYY-MM-DD format",
      "required": true
    },
    "travelers": {
      "type": "int",
      "description": "Number of travelers",
      "required": false,
      "default": 1
    },
    "budget": {
      "type": "float",
      "description": "Maximum budget in USD",
      "required": false
    },
    "preferences": {
      "type": "Dict[str, Any]",
      "description": "User preferences (hotel class, airline, etc.)",
      "required": false
    }
  }
}
```

### Generated State Schema (Typed)

```python
class TravelPlanningState(TypedDict):
    """
    State schema for travel_planning workflow

    Fields:
    - messages: Conversation history (auto-reduced by LangGraph)
    - Context fields (strongly typed):
      - destination: Travel destination city or country
      - departure_date: Departure date in YYYY-MM-DD format
      - return_date: Return date in YYYY-MM-DD format
      - travelers: Number of travelers
      - budget: Maximum budget in USD
      - preferences: User preferences (hotel class, airline, etc.)
    - next: Next node to execute (for routing)
    - completed_tasks: List of completed task IDs
    """

    # Messages (with automatic message reduction)
    messages: Annotated[List[BaseMessage], add_messages]

    # Strongly-typed context fields from spec
    destination: Optional[str]  # Travel destination city or country
    departure_date: Optional[str]  # Departure date in YYYY-MM-DD format
    return_date: Optional[str]  # Return date in YYYY-MM-DD format
    travelers: Optional[int]  # Number of travelers
    budget: Optional[float]  # Maximum budget in USD
    preferences: Optional[Dict[str, Any]]  # User preferences (hotel class, airline, etc.)

    # Routing
    next: Optional[str]

    # Task tracking
    completed_tasks: List[str]

    # Metadata
    thread_id: Optional[str]
    user_id: Optional[str]
    conversation_insights: Optional[Dict[str, Any]]
```

### Usage (Typed)

```python
from langgraph.state_schema import TravelPlanningState

state: TravelPlanningState = {
    "messages": [HumanMessage(content="I want to go to Paris")],
    "destination": "Paris",  # ✅ Type-checked as str
    "departure_date": "2025-03-15",  # ✅ Type-checked as str
    "return_date": "2025-03-22",  # ✅ Type-checked as str
    "travelers": 2,  # ✅ Type-checked as int
    "budget": 3000.0,  # ✅ Type-checked as float
    "preferences": {"hotel_class": "4-star"},  # ✅ Type-checked as Dict
    "next": "flight_agent",
    "completed_tasks": [],
    "thread_id": "thread_123",
    "user_id": "user_456"
}

# Type errors caught by IDE and mypy:
state["travelers"] = "two"  # ❌ Type error: Expected int, got str
state["unknown_field"] = "value"  # ❌ Type error: Unknown key
```

## Supported Field Types

| Type | Python Type | Example Value | Use Case |
|------|-------------|---------------|----------|
| `str` | `str` | `"Paris"` | Text, dates, IDs |
| `int` | `int` | `2` | Counts, quantities |
| `float` | `float` | `2000.50` | Prices, ratings |
| `bool` | `bool` | `True` | Flags, toggles |
| `List[str]` | `List[str]` | `["NYC", "LA"]` | Lists of strings |
| `List[int]` | `List[int]` | `[1, 2, 3]` | Lists of numbers |
| `Dict[str, Any]` | `Dict[str, Any]` | `{"key": "value"}` | Nested data |
| `Any` | `Any` | Any value | Flexible fields |

### Example: E-Commerce Order State

```json
{
  "context_fields": {
    "order_id": {
      "type": "str",
      "description": "Unique order identifier"
    },
    "items": {
      "type": "List[Dict[str, Any]]",
      "description": "List of items in cart"
    },
    "total": {
      "type": "float",
      "description": "Order total in USD"
    },
    "shipping_address": {
      "type": "Dict[str, str]",
      "description": "Shipping address details"
    },
    "is_paid": {
      "type": "bool",
      "description": "Payment status"
    }
  }
}
```

Generated schema:
```python
class EcommerceOrderState(TypedDict):
    order_id: Optional[str]
    items: Optional[List[Dict[str, Any]]]
    total: Optional[float]
    shipping_address: Optional[Dict[str, str]]
    is_paid: Optional[bool]
    # ... standard fields
```

## Standard Fields (Always Present)

These fields are **automatically included** in every state schema:

### `messages`
```python
messages: Annotated[List[BaseMessage], add_messages]
```
- **Type**: List of LangChain messages
- **Purpose**: Conversation history
- **Annotation**: `add_messages` - automatic message reduction
- **Usage**: Append messages, LangGraph handles deduplication

### `next`
```python
next: Optional[str]
```
- **Type**: Optional string
- **Purpose**: Routing - which node to execute next
- **Usage**: Supervisor/router nodes set this
- **Example**: `"flight_agent"`, `"ask_missing"`, `"END"`

### `completed_tasks`
```python
completed_tasks: List[str]
```
- **Type**: List of strings
- **Purpose**: Track which tasks/steps are done
- **Usage**: Agents append task IDs as they complete
- **Example**: `["research_flights", "book_hotel"]`

### `thread_id`
```python
thread_id: Optional[str]
```
- **Type**: Optional string
- **Purpose**: Unique conversation identifier for checkpointing
- **Usage**: Resume conversations across sessions
- **Example**: `"thread_abc123"`

### `user_id`
```python
user_id: Optional[str]
```
- **Type**: Optional string
- **Purpose**: User identifier for multi-user systems
- **Usage**: Track which user owns the conversation
- **Example**: `"user_456"`

### `conversation_insights`
```python
conversation_insights: Optional[Dict[str, Any]]
```
- **Type**: Optional dictionary
- **Purpose**: Metadata and analytics
- **Usage**: Store metrics, classifications, sentiment
- **Example**: `{"sentiment": "positive", "intent": "book_flight"}`

## Accessing State in Agents

### In Agent Nodes

```python
async def flight_agent_node(state: TravelPlanningState) -> Dict[str, Any]:
    """Agent node function"""

    # Access typed context fields
    destination = state.get("destination")
    departure_date = state.get("departure_date")
    travelers = state.get("travelers", 1)  # With default

    # Access messages
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    # Access metadata
    user_id = state.get("user_id")

    # Return state updates
    return {
        "messages": [AIMessage(content="Searching flights...")],
        "next": "supervisor_agent",
        "completed_tasks": state["completed_tasks"] + ["search_flights"]
    }
```

### In BaseAgent Subclasses

```python
from frmk.agents.base_agent import BaseAgent

class FlightAgent(BaseAgent):
    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Access state fields
        destination = state.get("destination")

        if not destination:
            return {
                "messages": [AIMessage(content="Where would you like to go?")],
                "next": "ask_missing"
            }

        # Process with LLM
        result = await super().invoke(state)

        # Update state
        result["completed_tasks"] = state["completed_tasks"] + ["flight_search"]

        return result
```

## Validation & Required Fields

Use evaluator nodes to validate required context:

```python
async def check_required_fields(state: TravelPlanningState) -> Dict[str, Any]:
    """Validate all required context fields are present"""

    required = ["destination", "departure_date", "return_date"]
    missing = [field for field in required if not state.get(field)]

    if missing:
        return {
            "next": "ask_missing",
            "missing_fields": missing
        }

    return {"next": "search_flights"}
```

## Best Practices

### 1. Define Context Fields for Complex Workflows

✅ **Good** - Typed fields for multi-step workflow:
```json
{
  "context_fields": {
    "loan_amount": {"type": "float"},
    "credit_score": {"type": "int"},
    "employment_status": {"type": "str"}
  }
}
```

❌ **Less Ideal** - Generic dict for complex data:
```json
{
  "context_fields": {}  // Everything in context: Dict[str, Any]
}
```

### 2. Use Descriptive Field Names

✅ **Good**:
```json
{
  "departure_date": {"type": "str", "description": "ISO 8601 date"},
  "return_date": {"type": "str"}
}
```

❌ **Bad**:
```json
{
  "d1": {"type": "str"},
  "d2": {"type": "str"}
}
```

### 3. Document Field Purpose

```json
{
  "context_fields": {
    "budget": {
      "type": "float",
      "description": "Maximum budget in USD for the entire trip",
      "required": false,
      "default": null
    }
  }
}
```

### 4. Use Appropriate Types

```json
{
  "travelers": {"type": "int"},        // ✅ Count
  "price": {"type": "float"},          // ✅ Money
  "confirmed": {"type": "bool"},       // ✅ Flag
  "preferences": {"type": "Dict[str, Any]"}  // ✅ Complex nested data
}
```

## Migration from Generic to Typed

If you start with generic state and want to add types later:

**Before (generic):**
```python
state = {
    "context": {
        "destination": "Paris",
        "travelers": 2
    }
}
```

**After (typed):**
```python
state = {
    "destination": "Paris",  # Now top-level, typed field
    "travelers": 2           # Type-checked as int
}
```

Update agent code:
```python
# Before
destination = state.get("context", {}).get("destination")

# After
destination = state.get("destination")
```

---

**Generated by GoalGen** | [Documentation](https://github.com/yourorg/goalgen)
