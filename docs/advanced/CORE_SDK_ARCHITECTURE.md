# Core SDK Architecture

Complete architecture for GoalGen Core SDK with Azure AI Foundry integration.

---

## Overview

The **GoalGen Core SDK (`frmk`)** is a shared library that all generated applications use. It abstracts Azure AI Foundry integrations, tool execution, and common patterns.

```
┌─────────────────────────────────────────────────────────────┐
│              Generated Application (travel_planning)         │
│                                                               │
│  Generated Code (Spec-Driven Templates):                     │
│  ├── flight_agent.py          ← Uses BaseAgent              │
│  ├── hotel_agent.py           ← Uses BaseAgent              │
│  ├── supervisor_agent.py      ← Uses BaseAgent              │
│  └── quest_builder.py         ← Uses ToolRegistry           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Depends on: goalgen-frmk==1.0.0               │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              GoalGen Core SDK (frmk)                         │
│              Shared across ALL generated apps                │
│                                                               │
│  frmk/                                                        │
│  ├── agents/                                                 │
│  │   └── base_agent.py         # BaseAgent class            │
│  ├── tools/                                                  │
│  │   ├── base_tool.py          # Tool interface             │
│  │   ├── http_tool.py          # HTTP/Azure Functions       │
│  │   ├── websocket_tool.py     # WebSocket/Container Apps   │
│  │   └── function_tool.py      # Local Python functions     │
│  ├── core/                                                   │
│  │   ├── prompt_loader.py      # Azure AI Foundry prompts   │
│  │   ├── tool_registry.py      # Tool discovery             │
│  │   ├── state_manager.py      # State/checkpointing        │
│  │   └── config.py             # Configuration              │
│  ├── checkpointers/                                          │
│  │   ├── cosmos_checkpointer.py                             │
│  │   ├── redis_checkpointer.py                              │
│  │   └── blob_checkpointer.py                               │
│  └── utils/                                                  │
│      ├── logging.py            # Structured logging          │
│      ├── retry.py              # Retry with backoff          │
│      └── metrics.py            # App Insights integration    │
│                                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Azure Services                              │
│                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ AI Foundry     │  │ Functions      │  │ Container    │  │
│  │ (Prompts)      │  │ (HTTP Tools)   │  │ Apps (WS)    │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Cosmos DB      │  │ Redis          │  │ Key Vault    │  │
│  │ (Checkpoints)  │  │ (Cache)        │  │ (Secrets)    │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. **PromptLoader** (frmk/core/prompt_loader.py)

**Purpose**: Load prompts from Azure AI Foundry with versioning and caching.

**Features**:
- ✅ Azure AI Foundry integration
- ✅ Local file fallback
- ✅ In-memory caching with TTL
- ✅ Template variable substitution
- ✅ Version pinning per agent
- ✅ A/B testing support

**Usage in Generated Code**:
```python
# Automatically used by BaseAgent
prompt_loader = get_prompt_loader(goal_config["prompt_repository"])
prompt = prompt_loader.load(
    agent_name="flight_agent",
    version="v2.1.0",
    variables={"max_results": 10}
)
```

**Spec Configuration**:
```json
{
  "prompt_repository": {
    "source": "azure_ai_foundry",
    "configuration": {
      "endpoint": "${AI_FOUNDRY_ENDPOINT}",
      "project_name": "travel-planning-prompts"
    },
    "versioning": {
      "agent_versions": {
        "flight_agent": "v2.1.0",
        "hotel_agent": "latest"
      }
    }
  }
}
```

---

### 2. **ToolRegistry** (frmk/core/tool_registry.py)

**Purpose**: Discover and instantiate tools from spec.

**Features**:
- ✅ Auto-discovers tools from spec
- ✅ Supports HTTP, WebSocket, Function tools
- ✅ LangChain tool conversion
- ✅ Connection pooling
- ✅ Graceful shutdown

**Tool Types**:

| Type | Implementation | Use Case | Azure Service |
|------|----------------|----------|---------------|
| **http** | HTTPTool | REST APIs, Azure Functions | Azure Functions |
| **websocket** | WebSocketTool | Real-time services | Container Apps |
| **function** | FunctionTool | Local Python functions | N/A |

**Usage in Generated Code**:
```python
# Automatically used by BaseAgent
tool_registry = get_tool_registry(goal_config)
tools = tool_registry.get_langchain_tools(["flight_api", "hotel_api"])
llm_with_tools = llm.bind_tools(tools)
```

---

### 3. **HTTPTool** (frmk/tools/http_tool.py)

**Purpose**: Call Azure Functions or external APIs via HTTP.

**Features**:
- ✅ Automatic retry with exponential backoff
- ✅ Environment variable resolution (`${VAR}`)
- ✅ Multiple auth types (key, bearer, managed_identity)
- ✅ Request/response logging
- ✅ Timeout handling
- ✅ Connection pooling

**Spec Configuration**:
```json
{
  "tools": {
    "flight_api": {
      "type": "http",
      "spec": {
        "url": "${FLIGHT_API_URL}/search",
        "method": "POST",
        "auth": "key",
        "timeout": 30,
        "retry_attempts": 3,
        "headers": {
          "Content-Type": "application/json"
        }
      }
    }
  }
}
```

**Generated Azure Function** (tools/flight_api/):
```python
# tools/flight_api/function_app.py (generated)

import azure.functions as func
from frmk.utils.logging import get_logger

logger = get_logger("flight_api")

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="search", methods=["POST"])
async def search(req: func.HttpRequest) -> func.HttpResponse:
    """Search for flights"""

    try:
        data = req.get_json()

        # Call external flight API
        # (Actual implementation here)

        return func.HttpResponse(
            json.dumps({"flights": []}),
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Flight search failed: {e}")
        return func.HttpResponse(str(e), status_code=500)
```

---

### 4. **WebSocketTool** (frmk/tools/websocket_tool.py)

**Purpose**: Connect to real-time services on Container Apps.

**Features**:
- ✅ Auto-reconnect on disconnect
- ✅ Heartbeat/ping-pong
- ✅ Request-response pattern
- ✅ Streaming support
- ✅ Connection pooling

**Spec Configuration**:
```json
{
  "tools": {
    "realtime_translator": {
      "type": "websocket",
      "spec": {
        "url": "wss://translator.azurecontainerapps.io/ws",
        "auth": "bearer",
        "reconnect": true,
        "heartbeat_interval": 30
      }
    }
  }
}
```

**Usage**:
```python
# Request-response
result = await translator_tool.execute(text="Hello", target_lang="es")

# Streaming
async for chunk in translator_tool.stream(text="Long text..."):
    print(chunk.data)
```

---

### 5. **BaseAgent** (frmk/agents/base_agent.py)

**Purpose**: Base class for all generated agents.

**Responsibilities**:
1. Load prompts from Azure AI Foundry
2. Initialize LLM with spec config
3. Bind tools from registry
4. Format system prompts with context
5. Track invocation count
6. Handle max loop limits

**Generated Agent**:
```python
# langgraph/agents/flight_agent.py (generated)

from frmk.agents.base_agent import BaseAgent

class FlightAgent(BaseAgent):
    """Generated agent using Core SDK"""

    def __init__(self, goal_config):
        super().__init__(
            agent_name="flight_agent",
            agent_config=goal_config["agents"]["flight_agent"],
            goal_config=goal_config
        )
        # BaseAgent handles:
        # ✅ Prompt loading from AI Foundry
        # ✅ LLM initialization
        # ✅ Tool binding
        # ✅ Logging setup

    async def _process_response(self, state, response):
        """Agent-specific logic"""

        if response.tool_calls:
            return {
                "messages": state["messages"] + [response],
                "next": "tools"
            }

        return {
            "messages": state["messages"] + [response],
            "next": "END"
        }
```

---

## Tool Deployment Patterns

### Pattern 1: Azure Functions (HTTP Tools)

```
Agent → HTTP Request → Azure Function → External API
```

**When to Use**:
- Serverless, event-driven
- Infrequent calls
- Cost-optimized

**Generated Files**:
```
tools/
└── flight_api/
    ├── function_app.py          # Function code
    ├── requirements.txt
    ├── host.json
    └── local.settings.json.sample
```

### Pattern 2: Container Apps (WebSocket Tools)

```
Agent → WebSocket → Container App → Real-time Service
```

**When to Use**:
- Long-running connections
- Streaming responses
- High throughput

**Generated Files**:
```
tools/
└── realtime_translator/
    ├── Dockerfile
    ├── app.py                   # WebSocket server
    ├── requirements.txt
    └── ws_handler.py
```

---

## Benefits of Core SDK

| Benefit | Impact |
|---------|--------|
| **DRY** | No duplicated Azure integration code across generated apps |
| **Upgradeable** | Update SDK → all apps get new features |
| **Testable** | Mock SDK in tests, not Azure services |
| **Consistent** | All apps use same patterns |
| **Versioned** | SDK versioned independently (`goalgen-frmk==1.2.0`) |
| **Documented** | Single place to document integrations |
| **Type-Safe** | Pydantic models for validation |
| **Async** | Full async/await support |

---

## Distribution

### PyPI Package
```bash
pip install goalgen-frmk==1.0.0
```

### Generated App Dependencies
```txt
# requirements.txt (generated)
goalgen-frmk==1.0.0
langgraph==0.1.0
langchain-openai==0.1.0
fastapi==0.104.0
httpx==0.25.0
websockets==12.0
```

---

## Complete Flow Example

### 1. Spec Defines Tools
```json
{
  "tools": {
    "flight_api": {
      "type": "http",
      "spec": {"url": "${FLIGHT_API_URL}/search", "method": "POST"}
    }
  },
  "agents": {
    "flight_agent": {
      "tools": ["flight_api"],
      "llm_config": {"model": "gpt-4"}
    }
  }
}
```

### 2. Generator Creates Agent
```python
# langgraph/agents/flight_agent.py (generated)
from frmk.agents.base_agent import BaseAgent

class FlightAgent(BaseAgent):
    # BaseAgent auto-loads tools from registry
    pass
```

### 3. ToolRegistry Instantiates HTTPTool
```python
# Core SDK automatically:
tool_registry = ToolRegistry(goal_config)
flight_tool = HTTPTool("flight_api", ..., config)
tools = [flight_tool.to_langchain_tool()]
```

### 4. Agent Uses Tool via LLM
```python
# LangChain binds tool to LLM
llm_with_tools = llm.bind_tools(tools)
response = await llm_with_tools.ainvoke(messages)

# If LLM calls tool:
if response.tool_calls:
    result = await flight_tool.execute(**tool_args)
```

### 5. HTTPTool Calls Azure Function
```python
# HTTPTool makes HTTP POST to Azure Function
response = await http_client.post(
    "https://flight-func.azurewebsites.net/api/search",
    json={"origin": "SFO", "destination": "NYC"}
)
```

### 6. Azure Function Deployed
```bicep
// infra/modules/function-app.bicep (generated)
resource functionApp 'Microsoft.Web/sites@2022-09-01' = {
  name: 'flight-api-func'
  kind: 'functionapp,linux'
  properties: {
    functionRuntime: 'python'
    functionVersion: '~4'
  }
}
```

---

## Summary

✅ **Core SDK** (`frmk`) abstracts all Azure integrations
✅ **Generated agents** inherit from `BaseAgent`
✅ **Tools** deployed as Azure Functions (HTTP) or Container Apps (WebSocket)
✅ **Prompts** loaded from Azure AI Foundry with versioning
✅ **Spec-driven** - all configuration from goal spec
✅ **Testable** - mock SDK in tests
✅ **Upgradeable** - update SDK, all apps benefit

**This architecture ensures generated applications are production-ready, maintainable, and follow Azure best practices.**
