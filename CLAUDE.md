# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GoalGen is a code generator CLI for creating multi-goal, persistent, cross-device conversational agent systems. It scaffolds complete projects that use LangGraph for workflow orchestration and Azure services for deployment.

The system operates on a "goal spec" (JSON) as input and generates:
- LangGraph-based agent orchestration code
- Teams Bot and Webchat SPA UX components
- Azure Bicep infrastructure templates
- Tool integrations and security configurations
- Deployment and CI/CD assets

## Running GoalGen

```bash
# Basic usage
./goalgen.py --spec <path-to-spec.json> --out <output-directory>

# Selective generation
./goalgen.py --spec spec.json --out ./output --targets scaffold,langgraph,orchestrator

# Dry run to preview
./goalgen.py --spec spec.json --out ./output --dry-run
```

**Available targets**: `scaffold`, `langgraph`, `api`, `teams`, `webchat`, `tools`, `agents`, `evaluators`, `infra`, `security`, `assets`, `cicd`, `deployment`, `tests`

## Architecture

### Generator System
- **Entry point**: `goalgen.py` - Core CLI that parses spec, validates, and orchestrates sub-generators
- **Sub-generators**: Located in `generators/` directory, each implementing a `generate(spec, out_dir, dry_run)` function
- **Spec-driven**: All generators consume a JSON spec describing the goal-oriented system to build
- **Modular**: Each generator produces independent artifacts (code, infra, configs) for specific concerns

### Generator Modules

**1. scaffold** - Repository skeleton
- Creates base project structure (LICENSE, README.md, .gitignore)
- Initializes directory layout for app/, infra/, tests/, tools/, prompts/

**2. langgraph** - LangGraph workflow orchestration
- Emits `quest_builder.py` - main LangGraph graph construction
- Creates LangGraph nodes: supervisor, evaluators, agent bindings
- Wires checkpointer (Cosmos DB or Redis-based) for conversation persistence
- Generates state definitions and routing logic

**3. api** - FastAPI service layer
- Emits FastAPI app with `/message` endpoint
- Thread ID mapping for multi-session support
- Bot Orchestrator integration (calls LangGraph host)
- OpenAPI/Swagger documentation generation

**4. teams** - Microsoft Teams Bot UX
- Bot Framework manifest and configuration
- Teams app package (manifest.json, color/outline icons)
- Adaptive Card templates for rich messaging
- Teams-specific deployment script

**5. webchat** - Web chat interface
- React/Vite SPA with modern chat UI
- SignalR client for real-time message streaming
- WebSocket connection handling
- Responsive design components

**6. tools** - Tool implementations
- Folder structure for tool modules
- HTTP API wrappers for external services
- Azure Function triggers for tool execution
- Sample tool code with retry/error handling

**7. agents** - Agent implementations
- Agent code stubs per agent defined in spec
- LLM call wrappers (OpenAI/Azure OpenAI)
- Retry policies and error handling
- Agent-specific configuration

**8. evaluators** - Validation & testing
- Evaluator logic based on spec checks
- Unit test cases for each evaluator
- Integration test scenarios
- Test data fixtures

**9. infra** - Azure Bicep infrastructure
- Per-service Bicep modules: Container Apps, Function Apps, Cosmos DB, Redis, Key Vault, SignalR
- Parameter files for dev/staging/prod environments
- Orchestration Bicep that composes all modules
- Resource naming and tagging conventions

**10. security** - Security configuration
- Key Vault secret definitions
- Managed Identity assignments (Bicep)
- Sample code to fetch secrets using `DefaultAzureCredential`
- RBAC role assignments for service principals

**11. assets** - Static resources
- Copies images and logos from spec-defined paths
- Generates sample prompt templates in `prompts/`
- Adaptive Card JSON templates
- Localization resources (if specified)

**12. cicd** - CI/CD automation
- GitHub Actions workflow for full deployment pipeline
- Container image build and push to ACR
- Bicep deployment steps
- Integration test execution
- Environment-specific deployment gates

**13. deployment** - Deployment playbooks
- `deploy.sh` - main deployment orchestrator
- `destroy.sh` - teardown script
- Per-target deploy commands (dev, staging, prod)
- Pre-flight validation checks

**14. tests** - Test infrastructure
- pytest configuration and test stubs
- Unit test scaffolding
- Integration test harness
- Local dev runner (docker-compose option for local Azure emulation)

### Framework Package (`frmk/`)
Reference implementation and templates:
- `app/agents/`: Agent implementation stubs
- `app/secure_config.py`: Security configuration template
- `infra/main.bicep`: Infrastructure template
- `tools/spec_generator.py`: Tool for generating goal specs

### Design Philosophy
- **Goal-oriented architecture**: Tasks, agents, evaluators, tools, supervisors working toward defined goals
- **Persistent conversations**: Long-term memory, multi-device support, resumable threads
- **Template-driven generation**: Generators use templates to produce consistent, deployable code
- **Azure-native**: Built for Azure Container Apps, Functions, Cosmos DB, Redis, SignalR

### Generated Code Runtime Architecture

The generated project follows this request flow:

1. **User Interface Layer** (Teams Bot / Webchat)
   - User sends message via Teams or Webchat SPA
   - Message routed to FastAPI `/message` endpoint with thread_id

2. **API Layer** (FastAPI)
   - FastAPI receives message and thread_id
   - Calls Bot Orchestrator (LangGraph runtime)
   - Returns response to UI layer

3. **LangGraph Orchestration** (quest_builder.py)
   - Loads conversation state from checkpointer (Cosmos/Redis)
   - Routes message through supervisor node
   - Supervisor determines which agent/task to invoke based on goal spec
   - Executes evaluators to validate context completeness
   - Invokes agents with appropriate tools
   - Persists updated state back to checkpointer

4. **Agent Execution**
   - Agent receives task from supervisor
   - Makes LLM calls (OpenAI/Azure OpenAI) with tool bindings
   - Tools execute (HTTP calls, function triggers)
   - Results flow back through LangGraph graph

5. **State Persistence**
   - All conversation state stored in Cosmos DB or Redis
   - Thread IDs map to checkpointer state
   - Cross-device resume supported via thread_id
   - History maintained for multi-turn conversations

## Generated Project Structure

When you run `goalgen --spec travel_planning.json --out ./generated/travel_planning`, the generators create:

```
travel_planning/
├── README.md                     # Project overview, setup instructions
├── LICENSE
├── .gitignore
├── infra/                        # Azure Bicep infrastructure
│   ├── main.bicep               # Composes all modules
│   ├── modules/
│   │   ├── containerapp.bicep   # Container Apps hosting
│   │   ├── functionapp.bicep    # Azure Functions for tools
│   │   ├── cosmos.bicep         # Cosmos DB for checkpointer
│   │   ├── redis.bicep          # Redis cache
│   │   ├── keyvault.bicep       # Key Vault for secrets
│   │   └── signalr.bicep        # SignalR for real-time events
│   └── parameters.json          # Environment-specific parameters
├── orchestrator/                 # FastAPI Bot Orchestrator
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              # FastAPI app with /message endpoint
│   │   ├── orchestrator.py      # LangGraph integration
│   │   ├── session_store.py     # Cosmos + Redis wiring
│   │   └── secure_config.py     # DefaultAzureCredential usage
│   └── tests/
├── langgraph/                    # LangGraph workflow
│   ├── quest_builder.py         # Main graph construction
│   ├── agents/                  # Agent implementations
│   │   ├── supervisor.py        # Supervisor routing logic
│   │   ├── flight_agent.py      # Per-agent implementations
│   │   └── hotel_agent.py
│   ├── evaluators/              # Evaluator logic
│   │   └── missing_info.py
│   └── checkpointer_adapter.py  # Cosmos/Redis checkpointer
├── api/                          # Optional separate API service
│   └── (only if not combined with orchestrator)
├── teams_app/                    # Microsoft Teams Bot
│   ├── manifest.json            # Teams app manifest
│   ├── adaptive_cards/          # Adaptive Card templates
│   │   └── travel_response.json
│   └── deploy_team.sh           # Teams deployment script
├── webchat/                      # Web chat SPA
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.tsx              # Main chat UI
│       └── signalr-client.ts    # SignalR connection
├── tools/                        # Tool implementations
│   ├── flight_api/
│   │   ├── function_app/        # Azure Function wrapper
│   │   │   ├── function_app.py
│   │   │   └── host.json
│   │   └── README.md
│   ├── hotel_api/
│   └── calculator/
├── prompts/                      # Prompt templates
│   ├── supervisor.md.tpl        # Supervisor system prompt
│   ├── flight_agent.md.tpl      # Agent-specific prompts
│   └── evaluator.md.tpl
├── assets/                       # Static resources
│   ├── logo.png
│   └── images/
├── ci/                           # CI/CD configuration
│   └── github-actions.yml       # GitHub Actions workflow
├── scripts/                      # Deployment scripts
│   ├── deploy.sh                # Main deployment orchestrator
│   ├── destroy.sh               # Teardown script
│   └── local_run.sh             # Local development runner
└── tests/                        # Test infrastructure
    ├── pytest.ini
    ├── unit/
    ├── integration/
    └── docker-compose.yml       # Local Azure service emulation
```

## Development Workflow

When implementing generator modules:
1. Each generator receives: `spec` (dict), `out_dir` (str), `dry_run` (bool)
2. Parse relevant sections from the spec
3. Generate files/directories in `out_dir` (skip writes if `dry_run=True`)
4. Print progress/status messages prefixed with `[generator-name]`
5. Use templates from `frmk/` directory where applicable

### Goal Spec Schema

**See `CONFIG_SPEC_SCHEMA.md` for the complete schema with all configuration options.**

The goal spec is a JSON document defining a complete conversational goal system. Key sections:

- **Identity**: `id`, `title`, `description` - Goal identification and purpose
- **Triggers**: Keywords that activate this goal in conversation
- **Context**: `context_fields` - Data fields tracked for this goal (e.g., destination, dates, budget)
- **Tasks**: Ordered workflow steps, each with:
  - `id`, `type` (evaluator/task), `tools` (optional list of tool IDs)
- **Agents**: Named agent configurations with `kind` (supervisor/llm_agent), `policy`, `tools`, `max_loop`
- **Tools**: Tool definitions with `type` (http/internal) and `spec` (URL, auth, etc.)
- **Evaluators**: Validation logic with `checks` (field presence, actions like ask_user)
- **UX**: Configuration for `teams`, `api`, `webchat` interfaces
- **Assets**: Paths to logos, prompts, templates
- **Deployment**: Target platforms (containerapps/functions), environment variables

Example: A "travel_planning" goal spec would define flight/hotel research tasks, agents using flight_api/hotel_api tools, evaluators checking for required dates/budget, and UX config for Teams Bot + Webchat deployment.

Generators access spec via: `spec.get("key", "default")` or `spec["section"]["subsection"]`

## Key Concepts

### Goals
A "goal" represents a complete conversational workflow (e.g., travel planning, expense reporting). Each goal has:
- Trigger words that activate it
- Context fields to track throughout the conversation
- Tasks to execute (in sequence or parallel)
- Agents that perform the tasks
- Tools available to agents
- Evaluators that validate completeness

### Supervisor Pattern
The supervisor is a special agent that:
- Receives user messages
- Determines which goal is active based on triggers
- Routes to appropriate agents/tasks based on goal spec
- Uses simple_router or custom routing policies
- Orchestrates multi-step workflows

### Checkpointing
LangGraph's checkpointing enables:
- Conversation state persistence across messages
- Multi-turn conversation memory
- Cross-device conversation resume via thread_id
- Human-in-the-loop workflows (pause/resume)
- Backed by Cosmos DB or Redis

### Tool Binding
Tools are bound to agents in the spec:
- HTTP tools wrap external APIs (flight_api, hotel_api)
- Internal tools are Python functions (calculator)
- Azure Functions can host tool implementations
- Tools accessed via OpenAI function calling

## Agentic Design Patterns

GoalGen supports several agentic design patterns out of the box, with more planned for future releases.

### Patterns Supported in v0.2.0

**1. Tool Use Pattern** ✅
- Agents bind to tools (HTTP APIs, functions) defined in the spec
- LLM uses function calling to determine when to invoke tools
- Generated code includes tool wrappers with retry logic and error handling
- Configured via `agents.<agent_name>.tools` array in spec

**Example**:
```json
{
  "agents": {
    "flight_agent": {
      "kind": "llm_agent",
      "tools": ["flight_api", "calculator"]
    }
  },
  "tools": {
    "flight_api": {
      "type": "http",
      "spec": {"url": "${FLIGHT_API_URL}/search"}
    }
  }
}
```

**2. Multi-Agent Collaboration Pattern** ✅
- Supervisor agent coordinates multiple specialist agents
- Each agent focuses on a specific domain (flights, hotels, etc.)
- Conversation state shared across agents via LangGraph checkpointer
- Agents communicate through shared state fields

**Example**:
```json
{
  "agents": {
    "supervisor_agent": {
      "kind": "supervisor",
      "policy": "simple_router"
    },
    "flight_agent": {"kind": "llm_agent"},
    "hotel_agent": {"kind": "llm_agent"}
  }
}
```

**3. Supervisor/Router Pattern** ✅
- Supervisor agent routes user messages to appropriate specialist agents
- Routes based on conversation intent and goal triggers
- Supports simple_router policy (evaluator-based routing)
- Can implement custom routing logic via policy configuration

**How it works**:
- User message → Supervisor analyzes intent
- Supervisor checks evaluators for context completeness
- Routes to appropriate agent or asks for missing information
- Specialist agent completes task and returns control to supervisor

**4. Context Completeness Validation** ✅
- Evaluators check if required context fields are present
- Human-in-the-loop: pauses workflow to ask user for missing info
- Configured via `evaluators` section in spec
- Prevents agents from executing with incomplete information

**Example**:
```json
{
  "evaluators": {
    "check_travel_context": {
      "checks": [
        {"field": "destination", "required": true},
        {"field": "dates", "required": true}
      ],
      "on_missing": "ask_user"
    }
  }
}
```

### Patterns Planned for v0.3.0

**Reflection Pattern** 🚧
- Agent evaluates its own output before returning to user
- Self-correction loop: generate → evaluate → refine
- Useful for quality control and error detection
- Will be configured via `agents.<name>.reflection: true`

**ReAct (Reasoning + Acting)** 🚧
- Agent explicitly reasons about next steps before taking action
- Thought → Action → Observation cycle
- Improves agent decision-making transparency
- Will be available as `agents.<name>.pattern: "react"`

**Chain of Thought** 🚧
- Agent breaks down complex problems into reasoning steps
- Explicit intermediate reasoning before final answer
- Configured via prompt templates or agent pattern setting

**Planning Pattern** 🚧
- Agent creates multi-step plan before execution
- Plan → Execute → Monitor cycle
- Useful for complex, multi-stage goals
- Will extend task orchestration capabilities

**Memory/RAG Pattern** 🚧
- Long-term memory beyond conversation checkpoints
- Vector DB integration for semantic search over past conversations
- Configured via `state_management.memory` section

### Using Patterns in Generated Code

**Manual Pattern Implementation (v0.2.0)**:
You can manually implement additional patterns in generated agent code:

1. **Edit `langgraph/agents/<agent_name>.py`**
2. **Modify agent prompts in `prompts/<agent_name>.md.tpl`**
3. **Add reflection/planning logic in agent node functions**

**Example - Adding Reflection**:
```python
# In langgraph/agents/flight_agent.py
async def flight_agent_node(state):
    # Generate initial response
    response = await llm.ainvoke(messages)

    # Reflection step (manually added)
    reflection_prompt = f"Evaluate this response for accuracy: {response}"
    evaluation = await llm.ainvoke(reflection_prompt)

    if "needs improvement" in evaluation.lower():
        # Regenerate with feedback
        response = await llm.ainvoke(messages + [evaluation])

    return {"messages": [response]}
```

**Automatic Pattern Generation (v0.3.0+)**:
Future releases will auto-generate pattern implementations based on spec configuration:

```json
{
  "agents": {
    "flight_agent": {
      "kind": "llm_agent",
      "pattern": "react",
      "reflection": true,
      "tools": ["flight_api"]
    }
  }
}
```

### Pattern Selection Guidelines

- **Simple query-response**: Use basic llm_agent without patterns
- **Multi-domain tasks**: Use supervisor + multi-agent collaboration
- **External API calls**: Use tool use pattern
- **Quality-critical outputs**: Manually add reflection (or wait for v0.3.0)
- **Complex planning**: Use evaluators + multi-step tasks (or wait for planning pattern in v0.3.0)
- **Long-term context**: Use checkpointing (current) or memory/RAG (v0.3.0)

## Template Architecture

Generators use Jinja2 templates parameterized from the goal spec. Key templates:

### 1. quest_builder.py (LangGraph Generator)

Generates LangGraph state machine with:
- `QuestState` class schema reflecting `context_fields` from spec
- Nodes:
  - `supervisor(state)` - Routes based on intent & evaluator results
  - `ask_missing(state)` - Raises human interrupts via SignalR
  - `run_task_<task_id>(state)` - Wrappers calling agents or tools (one per task in spec)
  - `evaluator_<id>(state)` - Checks conditions from evaluator spec
- Checkpointer adapter code (Cosmos or Redis)
- Graph construction and invoke snippet for orchestrator

Example template logic (Jinja2):
```python
class QuestState(dict):
    pass

graph = StateGraph(QuestState)

def supervisor(state):
    {% for f in context_fields %}
    if not state.get("context", {}).get("{{f}}"):
        return {"next": "ask_missing", "missing":"{{f}}"}
    {% endfor %}
    return {"next": "run_tasks"}

# Register nodes for each task
{% for task in spec.tasks %}
graph.add_node("run_task_{{task.id}}", run_task_{{task.id}})
{% endfor %}
```

### 2. orchestrator/main.py (API Generator)

FastAPI service with:
- `/message` endpoint with JWT authentication (Azure AD)
- Session loading: `session_store.load_session(thread_id)`
- LangGraph invocation: `LangGraphHost.resume_or_run(thread_id, goal, message)`
- Real-time event push to SignalR/WebPubSub
- OpenAPI documentation

### 3. teams_app/manifest.json (Teams Generator)

Teams app package with:
- Bot ID placeholder from spec
- Message extensions (if specified)
- Valid domains including orchestrator URL
- Adaptive Card templates in `teams_app/adaptive_cards/`
- `deploy_team.sh` script for Teams deployment

### 4. tools/<tool_name>/function_app (Tools Generator)

Per-tool Azure Function or HTTP wrapper:
- Handler using Key Vault secrets via Managed Identity
- HTTP client for external provider calls
- Test stubs and `local.settings.json.sample`
- Tool definition matching spec `tools` section

### 5. prompts/*.md.tpl (Assets Generator)

Prompt templates with placeholders:
- `{{context}}` - Current conversation context
- `{{history}}` - Message history
- `{{task_name}}` - Active task
- `{{tool_schema}}` - Available tools JSON schema

Templates per agent/evaluator/supervisor for LLM requests.

### 6. infra/modules/*.bicep (Infra Generator)

Bicep modules with parameters:

**containerapp.bicep** - Container Apps with managed identity:
```bicep
param name string
param image string
param envName string
param kvName string

resource ca 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: resourceGroup().location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: resourceId('Microsoft.App/managedEnvironments', envName)
    configuration: {
      secrets: [
        { name: 'COSMOS_CONN', value: listSecret(kvName, 'COSMOS_CONN') }
      ]
    }
    template: {
      containers: [{
        name: 'api'
        image: image
        env: [{ name: 'KEYVAULT_URL', value: 'https://${kvName}.vault.azure.net/' }]
      }]
    }
  }
}
```

**Other modules**: keyvault.bicep, signalr.bicep, cosmos.bicep, redis.bicep, functionapp.bicep

### 7. secure_config.py (Security Generator)

Security configuration showing:
- `DefaultAzureCredential` usage
- `SecretClient` for Key Vault access
- Secret retrieval patterns
- Managed Identity RBAC assignments in Bicep

### 8. ci/github-actions.yml (CI/CD Generator)

GitHub Actions workflow:
- Build container images
- Push to Azure Container Registry
- Run integration tests
- Deploy via `az containerapp update`
- Environment-specific gates (dev/staging/prod)

## Generator → Output Mapping

Quick reference for which generator produces what:

| Generator | Primary Outputs |
|-----------|----------------|
| `scaffold` | `README.md`, `LICENSE`, `.gitignore`, directory structure |
| `langgraph` | `langgraph/quest_builder.py`, `langgraph/agents/`, `langgraph/evaluators/`, `langgraph/checkpointer_adapter.py` |
| `api` | `orchestrator/app/main.py`, `orchestrator/app/orchestrator.py`, `orchestrator/app/session_store.py` |
| `teams` | `teams_app/manifest.json`, `teams_app/adaptive_cards/`, `teams_app/deploy_team.sh` |
| `webchat` | `webchat/package.json`, `webchat/src/App.tsx`, `webchat/src/signalr-client.ts` |
| `tools` | `tools/<tool_name>/function_app/`, `tools/<tool_name>/README.md` (per tool in spec) |
| `agents` | `langgraph/agents/<agent_name>.py` (per agent in spec) |
| `evaluators` | `langgraph/evaluators/<evaluator_id>.py`, test cases (per evaluator in spec) |
| `infra` | `infra/main.bicep`, `infra/modules/*.bicep`, `infra/parameters.json` |
| `security` | `orchestrator/app/secure_config.py`, Key Vault definitions in Bicep |
| `assets` | `prompts/*.md.tpl`, `assets/logo.png`, `assets/images/` |
| `cicd` | `ci/github-actions.yml` |
| `deployment` | `scripts/deploy.sh`, `scripts/destroy.sh`, `scripts/local_run.sh` |
| `tests` | `tests/pytest.ini`, `tests/unit/`, `tests/integration/`, `tests/docker-compose.yml` |

## Technology Stack

**See `FRAMEWORK_CHOICES.md` for detailed framework and library choices for each component.**
**See `TESTING_FRAMEWORKS.md` for comprehensive testing strategies and frameworks.**
**See `EVALUATOR_FRAMEWORK_OPTIONS.md` for detailed evaluator validation options.**

### Quick Reference
- **Backend**: Python 3.11+, FastAPI, LangChain/LangGraph, Azure SDK
- **Frontend**: TypeScript 5.2+, React 18, Vite 5, Tailwind CSS
- **Infrastructure**: Bicep, Azure Container Apps, Azure Functions
- **CI/CD**: GitHub Actions, Docker, Azure CLI
- **Testing**: pytest (backend), Vitest (frontend), Playwright (E2E), Locust (load)
- **Code Gen**: Python 3.11+, Jinja2

## Configuration Management

**See `CONFIGURATION_MATRIX.md` for detailed configuration requirements across all components.**
**See `COMPONENT_CONFIG_INVENTORY.md` for complete config parameter inventory.**

### Configuration Stages

1. **Build Time** - Developer choices in goal spec (token limits, graph structure, agent types)
2. **Deploy Time** - Infrastructure parameters (URLs, resource names, regions, sizing)
3. **Runtime** - Operational changes (scaling, feature flags, timeouts, model selection)

### Configuration Precedence

```
Runtime Override > Deploy Time > Build Time (Spec) > Generator Defaults
```

### Key Configuration Files Generated

- `infra/parameters.{env}.json` - Environment-specific infrastructure parameters
- `orchestrator/.env.sample` - Local development template
- `orchestrator/app/config.py` - Application configuration loader
- `config/scaling-rules.json` - Container Apps scaling configuration
- `infra/secrets.bicep` - Key Vault secret definitions

## Project Status

Currently in early development:
- CLI skeleton and generator dispatch implemented
- All 14 sub-generators have stubs
- Framework templates exist in `frmk/` for reference
- Configuration matrix and schema documented
- Next phase: Implement each generator with Jinja2 template rendering
