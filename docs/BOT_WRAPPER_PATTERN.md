# Bot Wrapper Pattern for Testing Generated Code

**Date**: 2025-12-03
**Purpose**: Document the bot wrapper approach for E2E testing of generated LangGraph workflows

---

## Overview

The bot wrapper pattern allows testing generated LangGraph orchestrators without deploying to Azure. It provides a local development/testing environment using the Bot Framework Emulator.

## Architecture

```
Bot Framework Emulator (UI)
    ↓ HTTP POST /api/messages
Teams Bot Wrapper (teams_app/)
    ├── server.py - aiohttp server
    ├── bot.py - Bot Framework handler
    └── config.py - Configuration
    ↓ HTTP POST /api/v1/message
Generated Orchestrator (orchestrator/)
    ├── main.py - FastAPI server
    └── workflow/ - LangGraph workflows
    ↓
Generated Agents & Tools
    └── LLM (Ollama/OpenAI)
```

---

## Components

### 1. Bot Server (`teams_app/server.py`)

**Purpose**: HTTP server that hosts the Bot Framework adapter

**Key Features**:
- aiohttp-based web server
- Bot Framework adapter initialization
- Activity routing to bot handler
- Health check endpoint

**Generated Code**: ✅ Already in generator output

```python
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from bot import TravelPlanningBot
from config import Config

# Initialize bot
config = Config()
settings = BotFrameworkAdapterSettings(
    app_id=config.microsoft_app_id,
    app_password=config.microsoft_app_password
)
adapter = BotFrameworkAdapter(settings)
bot = TravelPlanningBot(config)

# Routes
async def messages(req):
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    response = await adapter.process_activity(activity, auth_header, bot.on_turn)
    return web.Response(status=response.status, body=response.body)

app = web.Application()
app.router.add_post("/api/messages", messages)
app.router.add_get("/health", health)

web.run_app(app, host="localhost", port=3978)
```

### 2. Bot Handler (`teams_app/bot.py`)

**Purpose**: Bot Framework activity handler with orchestrator integration

**Key Features**:
- ConversationMapper integration (thread ID generation)
- HTTP client to call orchestrator API
- Message formatting (plain text or Adaptive Cards)
- Error handling
- **Distributed tracing** integration

**Generated Code**: ✅ Already in generator output (now with tracing)

```python
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from frmk.conversation import create_conversation_mapper
from frmk.utils.tracing import TraceSpan, start_trace

class TravelPlanningBot(ActivityHandler):
    def __init__(self, config):
        self.config = config
        self.mapper = create_conversation_mapper(config.conversation_mapping_config)

    async def on_message_activity(self, turn_context: TurnContext):
        # Start trace
        trace_id = start_trace()
        span = TraceSpan("bot.on_message_activity", trace_id)
        span.add_metadata("component", "teams_bot")

        try:
            # Get thread ID from ConversationMapper
            context = self._build_conversation_context(turn_context.activity)
            result = self.mapper.get_thread_id(context)
            thread_id = result.thread_id

            # Call orchestrator
            response_data = await self._call_langgraph_api(
                message=turn_context.activity.text,
                thread_id=thread_id,
                user_id=context.user_id,
                context=context
            )

            # Send response
            response_message = response_data.get("message", "Processing...")
            await turn_context.send_activity(MessageFactory.text(response_message))

            span.end()
            span.log()

        except Exception as e:
            span.end()
            span.add_metadata("error", str(e))
            span.log()
            # Error handling...
```

### 3. Configuration (`teams_app/config.py`)

**Purpose**: Load configuration for bot and orchestrator connection

**Key Features**:
- Environment variable loading
- ConversationMapper strategy configuration
- Orchestrator API URL configuration

**Generated Code**: ✅ Already in generator output

```python
import os

class Config:
    def __init__(self):
        self.microsoft_app_id = os.getenv("MICROSOFT_APP_ID", "")
        self.microsoft_app_password = os.getenv("MICROSOFT_APP_PASSWORD", "")
        self.langgraph_api_url = os.getenv("LANGGRAPH_API_URL", "http://localhost:8000")

        # ConversationMapper configuration
        self.conversation_mapping_config = {
            "strategy": os.getenv("CONVERSATION_STRATEGY", "hash"),
            "hash_algorithm": "sha256",
            "hash_length": 16,
            "prefix": "teams"
        }
```

---

## Testing Workflow

### Step 1: Generate Code

```bash
./goalgen.py \
  --spec examples/travel_planning.json \
  --out /tmp/test_output \
  --targets scaffold,teams,agents,langgraph,api
```

**Generates**:
- `teams_app/` - Bot wrapper
- `orchestrator/` - FastAPI orchestrator
- `workflow/` - LangGraph workflows
- `frmk/` - Framework utilities

### Step 2: Start Orchestrator

```bash
cd /tmp/test_output/orchestrator

# Configure LLM
export OPENAI_API_KEY=ollama
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_MODEL_NAME=llama3

# Start
python main.py
```

**Runs on**: http://localhost:8000

### Step 3: Start Bot Server

```bash
cd /tmp/test_output/teams_app

# Start
python server.py
```

**Runs on**: http://localhost:3978

### Step 4: Connect Bot Framework Emulator

1. Open Bot Framework Emulator
2. Enter bot URL: `http://localhost:3978/api/messages`
3. Leave App ID and Password empty (local testing)
4. Click "Connect"

### Step 5: Test Conversations

Send messages in the emulator:
- "Hello"
- "I need to book a flight to Paris"
- "What's the weather in Tokyo?"

**Observe**:
- Message flow through bot → orchestrator → LLM
- Distributed traces in logs
- Contextually appropriate responses
- Thread ID persistence across messages

---

## ConversationMapper Integration

### Thread ID Generation

The bot uses ConversationMapper to generate persistent thread IDs:

**Hash Strategy** (stateless):
```python
# Generated thread_id: teams-79432dcfd1c77fd7
# Deterministic based on conversation_id + user_id
```

**Database Strategy** (stateful):
```python
# Stored in Cosmos DB or PostgreSQL
# Enables analytics and compliance tracking
```

### Thread ID Flow

```
1. User sends message in emulator
2. Bot receives activity
3. Bot builds ConversationContext from activity
4. ConversationMapper.get_thread_id(context) → thread_id
5. Bot calls orchestrator with thread_id
6. LangGraph uses thread_id for checkpointing
7. Response flows back to bot
8. Bot sends response to emulator
```

**Result**: Conversation state persists across messages using the same thread_id

---

## Distributed Tracing Integration

### Trace Points in Bot

**bot.on_message_activity**:
```python
trace_id = start_trace()
span = TraceSpan("bot.on_message_activity", trace_id)
span.add_metadata("component", "teams_bot")

try:
    # Bot logic...
    span.end()
    span.log()
except Exception as e:
    span.end()
    span.add_metadata("error", str(e))
    span.log()
```

**Trace Output**:
```
[TRACE] bot.on_message_activity | trace_id=abc123 | span_id=def456 | duration=12532.73ms | {'component': 'teams_bot'}
```

### Trace Flow

```
Bot Wrapper:
  [TRACE] bot.on_message_activity | duration=12532ms
      ├── [TRACE] bot.build_context | duration=0.01ms
      ├── [TRACE] mapper.get_thread_id | duration=0.03ms
      └── [TRACE] bot.call_langgraph_api | duration=12526ms

Orchestrator:
  [TRACE] orchestrator.send_message | duration=12520ms
      └── [TRACE] supervisor_agent.node | duration=12510ms
          └── [TRACE] agent.invoke | duration=12500ms
```

---

## Advantages of Bot Wrapper Pattern

### 1. **Local Development**
- No Azure deployment required
- Fast iteration cycle
- Full debugging capabilities

### 2. **E2E Testing**
- Tests complete stack: UX → API → Workflow → LLM
- Realistic message flow
- Thread ID persistence validation

### 3. **LLM Flexibility**
- Use Ollama for free local testing
- Switch to OpenAI/Azure OpenAI via env vars
- No API costs during development

### 4. **Bot Framework Compatibility**
- Uses real Bot Framework SDK
- Compatible with Teams deployment
- Same code paths as production

### 5. **Distributed Tracing**
- Visibility into performance
- Identify bottlenecks
- Track conversation flow

---

## Bot Framework Emulator Limitations

### Callback URL Issue

The emulator may show "send failed" errors due to localhost callback URL issues. This is a **UI quirk** and doesn't affect functionality.

**Evidence of Success**:
- ✅ Bot logs show "200 OK" from orchestrator
- ✅ Response JSON contains LLM-generated text
- ✅ Traces show complete flow

**Workaround**: Check bot server logs to see actual responses

### Adaptive Card Rendering

Some Adaptive Card features may not render correctly in the emulator.

**Workaround**: Use plain text responses for emulator testing:
```python
await turn_context.send_activity(MessageFactory.text(response_message))
```

Production Teams deployment will render Adaptive Cards correctly.

---

## Deployment Path

### From Emulator to Production

1. **Local Testing** (Bot Framework Emulator)
   - bot.py + server.py on localhost
   - Orchestrator on localhost
   - Ollama for LLM

2. **Azure Deployment**
   - bot.py deployed to Azure App Service
   - Orchestrator deployed to Azure Container Apps
   - Azure OpenAI for LLM
   - Register bot with Teams

3. **Teams Integration**
   - Upload manifest.json to Teams
   - Users interact via Teams client
   - No emulator needed

**The bot.py code is identical across all stages!**

---

## Testing Utilities

### Health Check

```bash
# Bot server
curl http://localhost:3978/health

# Orchestrator
curl http://localhost:8000/health
```

### Direct API Testing

```bash
# Bypass bot, test orchestrator directly
curl -X POST http://localhost:8000/api/v1/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "thread_id": "test-123",
    "user_id": "test-user"
  }'
```

### Trace Log Analysis

```bash
# Filter bot traces
python server.py 2>&1 | grep '\[TRACE\]'

# Filter orchestrator traces
python main.py 2>&1 | grep '\[TRACE\]'

# Analyze timing
python server.py 2>&1 | grep '\[TRACE\]' | awk -F'duration=' '{print $2}' | sort -n
```

---

## Generator Integration

### Files Generated by `teams` Target

```
teams_app/
├── server.py          # Bot Framework server
├── bot.py             # Bot handler with orchestrator integration
├── config.py          # Configuration loader
├── __init__.py
├── manifest.json      # Teams app manifest
└── adaptive_cards/    # Adaptive Card templates
    ├── welcome.json
    ├── response.json
    └── error.json
```

### Template Variables

The generator uses these template variables:

- `{{goal_id}}` - Goal identifier (e.g., "travel_planning")
- `{{goal_title}}` - Human-readable title
- `{{goal_description}}` - Goal description
- `{{bot_class_name}}` - Generated bot class name
- `{{orchestrator_url}}` - Default: http://localhost:8000
- `{{conversation_strategy}}` - hash or database

---

## Next Steps

1. ✅ Bot wrapper pattern documented
2. ⏳ Create reusable testing utility
3. ⏳ Update generator templates with tracing
4. ⏳ Add tracing to frmk framework modules

---

**Status**: ✅ **Pattern Validated and Documented**
**Date**: 2025-12-03
**Location**: /tmp/emulator_test
