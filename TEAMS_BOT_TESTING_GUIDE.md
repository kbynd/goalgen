# Teams Bot Testing Guide

**Purpose**: Step-by-step guide to test generated Teams Bot with ConversationMapper

**Date**: 2025-12-03

---

## Testing Options

### Option 1: Bot Framework Emulator (Local Testing - Quickest)
- No Azure account needed
- Tests bot logic and conversation flow
- Cannot test Teams-specific features

### Option 2: Azure Bot Service + ngrok (Full Local Testing)
- Requires Azure subscription
- Tests full Teams integration locally
- Best for development

### Option 3: Azure Deployment (Production Testing)
- Full production environment
- Tests at scale
- Requires Azure resources

---

## Option 1: Bot Framework Emulator (Recommended First)

### Prerequisites

1. **Bot Framework Emulator**
   - Download: https://github.com/Microsoft/BotFramework-Emulator/releases
   - Install on macOS/Windows/Linux

2. **Python Environment**
   - Python 3.11+
   - Virtual environment

### Step-by-Step Test

#### 1. Generate Test Bot

```bash
cd /Users/kalyan/projects/goalgen

# Generate a test bot
python3.13 goalgen.py \
  --spec examples/travel_planning.json \
  --out /tmp/test_teams_bot \
  --targets scaffold,teams,api,langgraph,agents

cd /tmp/test_teams_bot
```

#### 2. Set Up Mock LangGraph API

Since we're testing locally, we need a mock LangGraph API endpoint:

```bash
# Create mock API for testing
cat > mock_langgraph_api.py << 'EOF'
"""
Mock LangGraph API for Teams Bot Testing

Simulates the LangGraph /api/v1/message endpoint
"""

from aiohttp import web
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_message(request):
    """Handle incoming message from Teams Bot"""
    data = await request.json()

    message = data.get("message", "")
    thread_id = data.get("thread_id", "")
    user_id = data.get("user_id", "")

    logger.info(f"Received message: {message}")
    logger.info(f"Thread ID: {thread_id}")
    logger.info(f"User ID: {user_id}")

    # Mock response
    response = {
        "message": f"I received your message: '{message}'. This is a mock response from the travel planning assistant. Thread ID: {thread_id}",
        "thread_id": thread_id,
        "status": "success"
    }

    return web.json_response(response)

async def health_check(request):
    """Health check endpoint"""
    return web.json_response({"status": "healthy"})

app = web.Application()
app.router.add_post('/api/v1/message', handle_message)
app.router.add_get('/health', health_check)

if __name__ == '__main__':
    print("🚀 Mock LangGraph API starting on http://localhost:8000")
    print("   POST /api/v1/message - Message endpoint")
    print("   GET  /health - Health check")
    web.run_app(app, host='localhost', port=8000)
EOF

# Install dependencies for mock API
pip3.13 install aiohttp
```

#### 3. Configure Bot

```bash
cd /tmp/test_teams_bot/teams_app

# Create .env from sample
cp .env.sample .env

# Edit .env
cat > .env << 'EOF'
# Mock credentials for local testing
MICROSOFT_APP_ID=test-app-id
MICROSOFT_APP_PASSWORD=test-app-password
AZURE_TENANT_ID=test-tenant-id

# Mock LangGraph API
LANGGRAPH_API_URL=http://localhost:8000

# Conversation mapping (hash strategy - no DB needed)
CONVERSATION_MAPPING_STRATEGY=hash

# Logging
LOG_LEVEL=INFO
EOF
```

#### 4. Create Bot Server

```bash
# Create server.py to run the bot
cat > server.py << 'EOF'
"""
Teams Bot Server for Local Testing

Run with: python server.py
"""

from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
import os
import sys
from pathlib import Path

# Add parent directory to path for frmk import
sys.path.insert(0, str(Path(__file__).parent.parent))

from teams_app.bot import TravelPlanningBot
from teams_app.config import Config

# Load configuration
config = Config.from_env()

# Create adapter
settings = BotFrameworkAdapterSettings(
    app_id=config.microsoft_app_id,
    app_password=config.microsoft_app_password
)
adapter = BotFrameworkAdapter(settings)

# Create bot
bot = TravelPlanningBot(config)

async def messages(req: Request) -> Response:
    """Handle incoming messages from Bot Framework"""
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await adapter.process_activity(activity, auth_header, bot.on_turn)
        if response:
            return Response(status=response.status, text=response.body)
        return Response(status=201)
    except Exception as e:
        print(f"Error: {e}")
        raise

# Create web app
app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    print("🤖 Teams Bot Server starting on http://localhost:3978")
    print("   POST /api/messages - Bot Framework endpoint")
    print("")
    print("📋 Next steps:")
    print("   1. Start Mock LangGraph API: python mock_langgraph_api.py")
    print("   2. Open Bot Framework Emulator")
    print("   3. Connect to: http://localhost:3978/api/messages")
    web.run_app(app, host="localhost", port=3978)
EOF
```

#### 5. Install Bot Dependencies

```bash
# Install required packages
pip3.13 install -r requirements.txt

# Note: You may need to install frmk dependencies
pip3.13 install -e ../frmk
```

#### 6. Run Mock LangGraph API

```bash
# Terminal 1: Start mock LangGraph API
cd /tmp/test_teams_bot
python3.13 mock_langgraph_api.py

# Should see: "Mock LangGraph API starting on http://localhost:8000"
```

#### 7. Run Bot Server

```bash
# Terminal 2: Start Teams Bot server
cd /tmp/test_teams_bot/teams_app
python3.13 server.py

# Should see: "Teams Bot Server starting on http://localhost:3978"
```

#### 8. Test with Bot Framework Emulator

1. **Open Bot Framework Emulator**

2. **Create New Bot Configuration**
   - Bot URL: `http://localhost:3978/api/messages`
   - Microsoft App ID: `test-app-id`
   - Microsoft App Password: `test-app-password`

3. **Send Test Messages**
   ```
   You: Hello
   Bot: I received your message: 'Hello'. This is a mock response...

   You: I want to plan a trip to Tokyo
   Bot: I received your message: 'I want to plan a trip to Tokyo'...
   ```

4. **Verify ConversationMapper**
   - Check bot server logs for thread_id
   - Send multiple messages and verify same thread_id is used
   - Restart bot and verify thread_id persists (hash strategy)

---

## Option 2: Azure Bot Service + ngrok (Full Teams Testing)

### Prerequisites

1. **Azure Subscription** with permissions to create:
   - Azure Bot Service
   - App Registration

2. **ngrok** for local tunnel
   ```bash
   brew install ngrok  # macOS
   # or download from https://ngrok.com/
   ```

3. **Teams** account (Microsoft 365 or personal)

### Step-by-Step Setup

#### 1. Create Azure Bot Service

```bash
# Login to Azure
az login

# Set variables
RESOURCE_GROUP="rg-teams-bot-test"
BOT_NAME="goalgen-travel-bot-test"
LOCATION="eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Bot
az bot create \
  --resource-group $RESOURCE_GROUP \
  --name $BOT_NAME \
  --kind "azurebot" \
  --sku "F0" \
  --app-type "UserAssignedMSI"

# Get App ID and create password
az ad app create --display-name $BOT_NAME

# Note the appId from output
APP_ID="<your-app-id>"

# Create app password
az ad app credential reset --id $APP_ID

# Note the password from output
APP_PASSWORD="<your-app-password>"
```

#### 2. Configure Bot for Teams

```bash
# Enable Teams channel
az bot msteams create \
  --resource-group $RESOURCE_GROUP \
  --name $BOT_NAME
```

#### 3. Start ngrok Tunnel

```bash
# Terminal 1: Start ngrok
ngrok http 3978

# Note the HTTPS URL, e.g., https://abc123.ngrok.io
NGROK_URL="<your-ngrok-url>"
```

#### 4. Update Bot Messaging Endpoint

```bash
# Update bot with ngrok URL
az bot update \
  --resource-group $RESOURCE_GROUP \
  --name $BOT_NAME \
  --endpoint "${NGROK_URL}/api/messages"
```

#### 5. Update Bot Configuration

```bash
cd /tmp/test_teams_bot/teams_app

# Update .env with real Azure credentials
cat > .env << EOF
# Real Azure Bot credentials
MICROSOFT_APP_ID=${APP_ID}
MICROSOFT_APP_PASSWORD=${APP_PASSWORD}
AZURE_TENANT_ID=${TENANT_ID}

# LangGraph API (still using mock for testing)
LANGGRAPH_API_URL=http://localhost:8000

# Conversation mapping
CONVERSATION_MAPPING_STRATEGY=hash

LOG_LEVEL=INFO
EOF
```

#### 6. Run Bot Server

```bash
# Terminal 2: Mock LangGraph API
python3.13 mock_langgraph_api.py

# Terminal 3: Bot server
cd teams_app
python3.13 server.py
```

#### 7. Test in Teams

1. **Install Bot in Teams**
   - Go to Azure Portal → Bot Service → Channels → Microsoft Teams
   - Click "Open in Teams"
   - Click "Add" to install bot

2. **Start Conversation**
   ```
   You: Hello
   Bot: <Welcome Adaptive Card with bot info>

   You: I want to plan a trip to Paris
   Bot: <Response from mock LangGraph API>
   ```

3. **Verify Conversation Persistence**
   - Send message on desktop Teams
   - Open Teams on mobile
   - Continue conversation - should have same context
   - Check logs for consistent thread_id

---

## Option 3: Full Azure Deployment

### Prerequisites

1. Azure subscription
2. Generated Teams Bot project
3. Azure CLI

### Deployment Steps

#### 1. Deploy LangGraph API to Azure Container Apps

```bash
# Follow the existing E2E deployment guide
cd /tmp/test_teams_bot

# Build and deploy orchestrator (with LangGraph)
./scripts/prepare_build_context.sh

az acr build \
  --registry <your-acr> \
  --image travel-planning:v1 \
  --file build_context/Dockerfile \
  build_context/

# Deploy to Container Apps (use generated Bicep)
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file infra/main-simple.bicep \
  --parameters openAiApiKey=<key>

# Get deployed API URL
API_URL=$(az containerapp show \
  --resource-group $RESOURCE_GROUP \
  --name travel-planning-app \
  --query properties.configuration.ingress.fqdn \
  --output tsv)

echo "LangGraph API: https://${API_URL}"
```

#### 2. Deploy Teams Bot to Azure

```bash
# Create App Service for Teams Bot
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan <app-service-plan> \
  --name ${BOT_NAME}-app \
  --runtime "PYTHON:3.11"

# Configure app settings
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name ${BOT_NAME}-app \
  --settings \
    MICROSOFT_APP_ID=$APP_ID \
    MICROSOFT_APP_PASSWORD=$APP_PASSWORD \
    AZURE_TENANT_ID=$TENANT_ID \
    LANGGRAPH_API_URL=https://${API_URL} \
    CONVERSATION_MAPPING_STRATEGY=hash

# Deploy code
cd teams_app
zip -r ../teams_bot.zip .
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name ${BOT_NAME}-app \
  --src ../teams_bot.zip

# Update bot endpoint
BOT_URL=$(az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name ${BOT_NAME}-app \
  --query defaultHostName \
  --output tsv)

az bot update \
  --resource-group $RESOURCE_GROUP \
  --name $BOT_NAME \
  --endpoint "https://${BOT_URL}/api/messages"
```

#### 3. Test in Production

1. Open Teams
2. Find bot in Apps or via link from Azure Portal
3. Send messages
4. Verify responses from real LangGraph workflow

---

## Verification Checklist

### Basic Functionality
- [ ] Bot responds to messages
- [ ] Welcome message displays correctly
- [ ] Adaptive Cards render properly (if enabled)
- [ ] Error handling works

### ConversationMapper
- [ ] Thread ID generated on first message
- [ ] Same thread ID used for subsequent messages
- [ ] Conversation persists across bot restarts (hash/database)
- [ ] Logs show correct thread ID format

### LangGraph Integration
- [ ] Messages reach LangGraph API
- [ ] Responses return from LangGraph
- [ ] Thread ID passed correctly
- [ ] User ID passed correctly

### Multi-User (Group Chat)
- [ ] Multiple users in group chat
- [ ] Shared conversation state
- [ ] All users see same thread ID in logs

### Cross-Device
- [ ] Send message on desktop
- [ ] Continue conversation on mobile
- [ ] Same conversation context maintained

---

## Troubleshooting

### Bot doesn't respond

**Check**:
1. Bot server running? `curl http://localhost:3978/api/messages`
2. LangGraph API running? `curl http://localhost:8000/health`
3. Check bot server logs for errors
4. Verify credentials in .env

### "Cannot find module frmk.conversation"

**Fix**:
```bash
cd /tmp/test_teams_bot
pip3.13 install -e ./frmk
```

### "MICROSOFT_APP_ID environment variable is required"

**Fix**:
```bash
# Make sure .env file exists and is loaded
cd teams_app
cat .env  # Verify contents
```

### Thread ID not consistent

**Check**:
1. Conversation mapping strategy: `echo $CONVERSATION_MAPPING_STRATEGY`
2. Bot logs: Look for "thread_id" in output
3. Verify hash strategy config is correct

### Adaptive Cards not showing

**Check**:
1. `use_adaptive_cards` in goal spec
2. Bot logs for card rendering
3. Teams supports Adaptive Cards v1.4

---

## Next Steps After Testing

1. **If Local Testing Works**:
   - Deploy to Azure for production testing
   - Set up database strategy for enterprise features
   - Configure monitoring and logging

2. **If Issues Found**:
   - Review logs (bot server and LangGraph API)
   - Check ConversationMapper configuration
   - Verify Bot Framework SDK version

3. **Production Readiness**:
   - Switch to database strategy (Cosmos/Postgres)
   - Enable Azure Application Insights
   - Set up CI/CD pipeline
   - Create Teams app package for distribution

---

## Summary

This guide provides three testing approaches:

1. **🚀 Quick Test**: Bot Framework Emulator (15 min)
2. **🔧 Full Local**: Azure Bot + ngrok (1 hour)
3. **☁️ Production**: Full Azure deployment (2-3 hours)

**Recommended**: Start with Option 1 to verify bot logic and ConversationMapper, then move to Option 2 for full Teams integration testing.

---

*Generated 2025-12-03*
