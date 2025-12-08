# Framework and Technology Choices

Complete listing of frameworks, libraries, and technologies for each component of GoalGen-generated projects.

---

## 1. ORCHESTRATOR (FastAPI Bot API)

### Core Framework
- **Language**: Python 3.11+
- **Web Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn (production) / Gunicorn + Uvicorn workers

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Web Framework | fastapi | ^0.104.0 | REST API framework |
| ASGI Server | uvicorn[standard] | ^0.24.0 | ASGI web server |
| Validation | pydantic | ^2.4.0 | Data validation & settings |
| HTTP Client | httpx | ^0.25.0 | Async HTTP requests |
| Azure Identity | azure-identity | ^1.14.0 | Managed Identity auth |
| Key Vault | azure-keyvault-secrets | ^4.7.0 | Secret management |
| Cosmos DB | azure-cosmos | ^4.5.0 | Cosmos DB client |
| Redis | redis[asyncio] | ^5.0.0 | Redis cache client |
| SignalR | msgpack | ^1.0.7 | SignalR serialization |
| Monitoring | azure-monitor-opentelemetry | ^1.0.0 | App Insights telemetry |
| OpenTelemetry | opentelemetry-api | ^1.20.0 | Distributed tracing |
| Logging | structlog | ^23.2.0 | Structured logging |
| Config | python-dotenv | ^1.0.0 | Environment config |
| JWT | python-jose[cryptography] | ^3.3.0 | JWT handling |
| Rate Limiting | slowapi | ^0.1.9 | Rate limiting |
| CORS | (built into FastAPI) | - | CORS middleware |

### Testing Stack
- **Test Framework**: pytest ^7.4.0
- **Async Testing**: pytest-asyncio ^0.21.0
- **Mocking**: pytest-mock ^3.12.0
- **HTTP Testing**: httpx (test client)
- **Coverage**: pytest-cov ^4.1.0

### Build & Package
- **Package Manager**: pip / poetry
- **Containerization**: Docker (multi-stage builds)
- **Base Image**: python:3.11-slim
- **Dependency Management**: requirements.txt / pyproject.toml

### Alternative Choices
- **Framework**: Flask + async extensions (simpler but less modern)
- **ASGI**: Hypercorn (alternative ASGI server)
- **Validation**: Marshmallow (older, more verbose)

---

## 2. LANGGRAPH (Quest Builder)

### Core Framework
- **Language**: Python 3.11+
- **Orchestration**: LangGraph ^0.0.35
- **LLM Framework**: LangChain ^0.1.0

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Orchestration | langgraph | ^0.0.35 | State graph orchestration |
| LLM Framework | langchain | ^0.1.0 | LLM abstractions |
| LLM Core | langchain-core | ^0.1.0 | Core interfaces |
| OpenAI | langchain-openai | ^0.0.5 | OpenAI/Azure OpenAI |
| Checkpointing | (custom adapter) | - | Cosmos/Redis checkpointer |
| Azure Cosmos | azure-cosmos | ^4.5.0 | Checkpointer backend |
| Redis | redis[asyncio] | ^5.0.0 | Checkpointer backend (alt) |
| State Mgmt | pydantic | ^2.4.0 | State schema validation |
| JSON Schema | jsonschema | ^4.19.0 | Tool schema validation |
| Async | asyncio | (stdlib) | Async execution |
| Concurrency | aiometer | ^0.4.0 | Concurrent task execution |

### Testing Stack
- **Test Framework**: pytest ^7.4.0
- **Async Testing**: pytest-asyncio ^0.21.0
- **LLM Mocking**: langchain-testing ^0.1.0
- **State Testing**: Custom fixtures

### Build & Package
- **Package Manager**: pip / poetry
- **Module Structure**: langgraph/ package
- **Entry Point**: quest_builder.py

### Alternative Choices
- **Orchestration**: Semantic Kernel (C#/.NET focused)
- **Orchestration**: LlamaIndex (RAG-focused)
- **Orchestration**: Custom state machine (full control, more work)

---

## 3. AGENTS

### Core Framework
- **Language**: Python 3.11+
- **Agent Framework**: LangChain Agents ^0.1.0
- **LLM Interface**: LangChain OpenAI ^0.0.5

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Agent Runtime | langchain | ^0.1.0 | Agent framework |
| OpenAI | langchain-openai | ^0.0.5 | OpenAI/Azure OpenAI |
| Tools | langchain-community | ^0.0.20 | Community tools |
| Function Calling | openai | ^1.3.0 | Native function calling |
| Retry Logic | tenacity | ^8.2.0 | Retry with backoff |
| Rate Limiting | ratelimit | ^2.2.1 | Rate limiting |
| Prompt Templates | langchain | ^0.1.0 | Prompt management |
| Response Parsing | langchain | ^0.1.0 | Output parsers |
| Memory | (via LangGraph state) | - | Agent memory |

### Testing Stack
- **Test Framework**: pytest ^7.4.0
- **LLM Mocking**: responses ^0.24.0
- **Agent Testing**: Custom harness

### Alternative Choices
- **Agent Framework**: AutoGPT (autonomous, less control)
- **Agent Framework**: CrewAI (multi-agent focus)
- **Direct LLM**: Direct OpenAI SDK (no abstractions)

---

## 4. EVALUATORS

**See `EVALUATOR_FRAMEWORK_OPTIONS.md` for comprehensive analysis of validation and rules engine choices.**

### Core Framework (Hybrid Approach)
- **Language**: Python 3.11+
- **Schema Validation**: Pydantic ^2.4.0 (primary)
- **Business Logic**: Custom Evaluator Classes (Strategy Pattern)
- **Complex Rules**: business-rules ^1.0.1 (optional, for declarative rules)
- **Expressions**: simpleeval ^0.9.13 (optional, for user-defined logic)

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Schema Validation | pydantic | ^2.4.0 | Fast type-safe validation (Rust-based) |
| JSON Schema | jsonschema | ^4.19.0 | JSON schema validation (optional) |
| Rules Engine | business-rules | ^1.0.1 | Declarative rules (optional) |
| Expression Eval | simpleeval | ^0.9.13 | Safe expression evaluation (optional) |
| Regex | re | (stdlib) | Pattern matching |
| Async | asyncio | (stdlib) | Async evaluation |
| Caching | cachetools | ^5.3.0 | Result caching |

### Evaluator Types Generated

| Evaluator Type | Implementation | Use Case |
|----------------|----------------|----------|
| **PresenceEvaluator** | Custom class | Check field exists |
| **RangeEvaluator** | Custom class | Numeric range validation |
| **RegexEvaluator** | Custom class | Pattern matching |
| **EnumEvaluator** | Custom class | Value in allowed set |
| **CustomEvaluator** | Custom class + func | Developer-defined logic |
| **CompositeEvaluator** | business-rules | Complex AND/OR/NOT rules |
| **ExpressionEvaluator** | simpleeval | User-defined expressions |

### Architecture Pattern

```python
from pydantic import BaseModel
from abc import ABC, abstractmethod

# Layer 1: Pydantic schema validation
class ContextSchema(BaseModel):
    destination: str
    budget: float
    dates: Optional[str] = None

# Layer 2: Custom evaluator interface
class BaseEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, context: dict) -> tuple[bool, str]:
        """Returns (is_valid, error_message)"""
        pass

# Layer 3: Specific evaluators (generated from spec)
class RangeEvaluator(BaseEvaluator):
    def __init__(self, field: str, min_val: float, max_val: float):
        self.field = field
        self.min_val = min_val
        self.max_val = max_val

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        value = context.get(self.field)
        if not (self.min_val <= value <= self.max_val):
            return False, f"{self.field} out of range"
        return True, ""

# Layer 4: Manager orchestrates all evaluators
class EvaluatorManager:
    async def evaluate_all(self, context: dict) -> tuple[bool, list[str]]:
        # Runs all evaluators, collects errors
        pass
```

### Testing Stack
- **Test Framework**: pytest ^7.4.0
- **Parametric Tests**: pytest-parametrize (built-in)
- **Async Testing**: pytest-asyncio ^0.21.0
- **Property Testing**: hypothesis ^6.90.0 (optional)
- **Mocking**: pytest-mock ^3.12.0

### Alternative Validation Frameworks Considered

| Framework | Pros | Cons | Verdict |
|-----------|------|------|---------|
| **Cerberus** | Declarative, serializable | Slower, no async | Good for dynamic schemas |
| **marshmallow** | Mature, serialization | Slower than Pydantic | Losing popularity |
| **jsonschema** | Standard, language-agnostic | Limited, slower | Use for API validation only |
| **fastjsonschema** | Fast (compiled) | Must pre-compile | Use if jsonschema too slow |

### Alternative Rules Engines Considered

| Framework | Pros | Cons | Verdict |
|-----------|------|------|---------|
| **business-rules** | Declarative, DB-storable | Not maintained | Good for complex rules |
| **durable-rules** | Forward-chaining, powerful | Heavy, steep learning curve | Overkill |
| **python-rules** | Simple, Pythonic | Not declarative | Use for simple cases |
| **simpleeval** | Safe expressions, flexible | Security concerns | Good for user-defined logic |
| **asteval** | More powerful than simpleeval | Slower, complex | Only if simpleeval insufficient |
| **Great Expectations** | Comprehensive data quality | Too heavy, batch-focused | Avoid |
| **Pandera** | DataFrame validation | Requires pandas | Avoid |

### Key Design Decisions

1. **Pydantic as Foundation**: Fast (Rust-based v2), type-safe, excellent DX
2. **Custom Classes for Business Logic**: Full control, async support, testable
3. **Optional business-rules**: For complex declarative rules if needed
4. **Avoid Heavy Frameworks**: Great Expectations, Pandera are overkill
5. **Caching**: Cache validation results for repeated evaluations
6. **Async First**: All evaluators support async (for external API calls)
7. **Composable**: Easy to add new evaluator types via inheritance

### When to Use Each Approach

- **Simple validation** (presence, type, range): Pydantic + Custom Evaluators
- **Complex business rules** (AND/OR/NOT composition): business-rules
- **User-defined validation**: simpleeval with safety constraints
- **External API validation**: Custom async evaluators
- **Dynamic schemas** (DB-stored): Cerberus or jsonschema

---

## 5. TOOLS (Azure Functions / HTTP Wrappers)

### Core Framework - HTTP Tools
- **Language**: Python 3.11+
- **HTTP Client**: httpx ^0.25.0 (async)
- **Alternative**: requests ^2.31.0 (sync)

### Core Framework - Azure Functions
- **Runtime**: Azure Functions Python 3.11
- **Framework**: azure-functions ^1.17.0

### Dependencies - HTTP Tools

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| HTTP Client | httpx | ^0.25.0 | Async HTTP |
| Retry | tenacity | ^8.2.0 | Retry logic |
| Circuit Breaker | pybreaker | ^1.0.0 | Circuit breaker pattern |
| Caching | cachetools | ^5.3.0 | Response caching |
| Azure Identity | azure-identity | ^1.14.0 | Managed Identity |
| Key Vault | azure-keyvault-secrets | ^4.7.0 | Secrets |

### Dependencies - Azure Functions

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Functions Runtime | azure-functions | ^1.17.0 | Function triggers/bindings |
| HTTP | httpx | ^0.25.0 | External API calls |
| Durable Functions | azure-functions-durable | ^1.2.0 | Orchestration (optional) |
| Azure Identity | azure-identity | ^1.14.0 | Managed Identity |

### Testing Stack
- **Test Framework**: pytest ^7.4.0
- **HTTP Mocking**: respx ^0.20.0 (for httpx)
- **Function Testing**: azure-functions-testing ^1.0.0

### Build & Package
- **Package Manager**: pip
- **Function Tools**: Azure Functions Core Tools v4
- **Deployment**: func azure functionapp publish

### Alternative Choices
- **HTTP Client**: aiohttp (alternative async)
- **Sync HTTP**: requests (simpler, blocking)
- **Function Runtime**: AWS Lambda (Python)
- **Function Runtime**: Google Cloud Functions

---

## 6. INFRASTRUCTURE (Bicep)

### Core Framework
- **Language**: Bicep 0.23+
- **Alternative**: Terraform (HCL)

### Dependencies

| Category | Tool | Version | Purpose |
|----------|------|---------|---------|
| IaC Language | Bicep | ^0.23.0 | Azure infrastructure |
| CLI | Azure CLI | ^2.54.0 | Deployment tool |
| Validation | bicep build | (built-in) | Syntax validation |
| Linting | bicep lint | (built-in) | Best practices |
| Testing | PSRule.Rules.Azure | ^1.30.0 | Infrastructure tests |

### Module Structure
```
infra/
├── main.bicep                    # Orchestration
├── modules/
│   ├── containerapp.bicep
│   ├── functionapp.bicep
│   ├── cosmos.bicep
│   ├── redis.bicep
│   ├── keyvault.bicep
│   ├── signalr.bicep
│   ├── loganalytics.bicep
│   └── appinsights.bicep
└── parameters/
    ├── dev.json
    ├── staging.json
    └── prod.json
```

### Testing Stack
- **Validation**: bicep build
- **Linting**: bicep lint
- **Testing**: PSRule.Rules.Azure
- **What-If**: az deployment group what-if

### Deployment Tools
- **CLI**: Azure CLI
- **CI/CD**: GitHub Actions / Azure DevOps
- **State**: No state file (ARM tracks deployment)

### Alternative Choices
- **IaC**: Terraform (multi-cloud, stateful)
- **IaC**: ARM Templates (JSON, verbose)
- **IaC**: Pulumi (TypeScript/Python/Go)
- **IaC**: Azure Developer CLI (azd)

---

## 7. SECURITY (Key Vault + Managed Identity)

### Core Framework
- **Identity**: Azure Managed Identity (System/User Assigned)
- **Secrets**: Azure Key Vault
- **SDK**: azure-identity + azure-keyvault-secrets

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Identity | azure-identity | ^1.14.0 | Authentication |
| Key Vault | azure-keyvault-secrets | ^4.7.0 | Secret retrieval |
| Certificates | azure-keyvault-certificates | ^4.7.0 | Cert management |
| Keys | azure-keyvault-keys | ^4.9.0 | Key management |
| RBAC | (Azure Portal/CLI) | - | Role assignments |

### Security Patterns
- **DefaultAzureCredential** - Auto chain: Managed Identity → Azure CLI → Environment
- **Secret Caching** - Cache secrets with TTL
- **Rotation** - Support for secret rotation via versioning
- **Network Security** - Private endpoints, firewall rules

### Testing Stack
- **Mocking**: Custom Key Vault mock
- **Local Dev**: Azure CLI authentication
- **Integration**: Test Key Vault in dev environment

### Alternative Choices
- **Secrets**: HashiCorp Vault (multi-cloud)
- **Secrets**: AWS Secrets Manager
- **Secrets**: Environment variables (less secure)
- **Identity**: Service Principal (manual rotation)

---

## 8. TEAMS BOT

### Core Framework
- **Language**: Python 3.11+ (integrated with Orchestrator)
- **Bot Framework**: Bot Framework SDK ^4.16.0
- **Adapter**: Teams Adapter (built into Bot Framework)

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Bot Framework | botbuilder-core | ^4.16.0 | Bot runtime |
| Teams Adapter | botbuilder-schema | ^4.16.0 | Teams schemas |
| Adaptive Cards | adaptivecards | ^1.5.0 | Card rendering |
| Auth | botframework-connector | ^4.16.0 | Teams auth |
| Storage | (shared with orchestrator) | - | State storage |

### Manifest Structure
```json
{
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "<app-id>",
  "bots": [{
    "botId": "<bot-id>",
    "scopes": ["personal", "team", "groupchat"]
  }],
  "validDomains": ["api.domain.com"]
}
```

### Testing Stack
- **Test Framework**: pytest ^7.4.0
- **Bot Testing**: botbuilder-testing ^4.16.0
- **Card Validation**: Adaptive Cards validator

### Deployment Tools
- **Teams Admin**: Teams App Studio / Developer Portal
- **CLI**: teamsfx CLI (alternative)
- **Packaging**: zip manifest + icons

### Alternative Choices
- **Framework**: Microsoft Bot Framework (C#)
- **Framework**: Proactive Bot Framework
- **Direct**: Microsoft Graph API (more control)

---

## 9. WEBCHAT SPA

### Core Framework
- **Language**: TypeScript 5.2+
- **UI Framework**: React 18.2+
- **Build Tool**: Vite 5.0+

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| UI Framework | react | ^18.2.0 | UI components |
| React DOM | react-dom | ^18.2.0 | DOM rendering |
| Build Tool | vite | ^5.0.0 | Fast dev server & build |
| TypeScript | typescript | ^5.2.0 | Type safety |
| State Management | zustand | ^4.4.0 | Lightweight state |
| HTTP Client | axios | ^1.6.0 | HTTP requests |
| SignalR Client | @microsoft/signalr | ^8.0.0 | Real-time communication |
| UI Components | @headlessui/react | ^1.7.17 | Accessible components |
| Styling | tailwindcss | ^3.3.0 | Utility-first CSS |
| Icons | lucide-react | ^0.292.0 | Icon library |
| Markdown | react-markdown | ^9.0.0 | Message rendering |
| Code Highlighting | react-syntax-highlighter | ^15.5.0 | Code blocks |
| Date/Time | date-fns | ^2.30.0 | Date formatting |
| Forms | react-hook-form | ^7.48.0 | Form handling |
| Validation | zod | ^3.22.0 | Schema validation |

### Testing Stack
- **Test Framework**: vitest ^1.0.0
- **React Testing**: @testing-library/react ^14.1.0
- **E2E**: playwright ^1.40.0
- **Component Tests**: @storybook/react ^7.5.0 (optional)

### Build & Package
- **Package Manager**: npm / pnpm / yarn
- **Dev Server**: vite dev
- **Build**: vite build (outputs to dist/)
- **Preview**: vite preview
- **Type Check**: tsc --noEmit
- **Linting**: eslint ^8.54.0
- **Formatting**: prettier ^3.1.0

### Deployment
- **Static Hosting**: Azure Static Web Apps
- **Alternative**: Azure Blob Storage + CDN
- **Alternative**: Netlify / Vercel
- **Container**: nginx-alpine (if containerized)

### Alternative Choices
- **UI Framework**: Vue 3 (alternative, composition API)
- **UI Framework**: Svelte (smaller bundle, compiler)
- **State Management**: Redux Toolkit (heavier, more features)
- **State Management**: Jotai (atoms-based)
- **Build Tool**: Webpack (more config, slower)
- **Build Tool**: Turbopack (newer, experimental)
- **Styling**: styled-components (CSS-in-JS)
- **Styling**: Emotion (CSS-in-JS)
- **SignalR**: socket.io (generic WebSocket)

---

## 10. CI/CD PIPELINE

### Core Framework
- **Platform**: GitHub Actions
- **Alternative**: Azure DevOps Pipelines
- **Alternative**: GitLab CI

### GitHub Actions Workflow

| Stage | Action/Tool | Purpose |
|-------|-------------|---------|
| Checkout | actions/checkout@v4 | Clone repository |
| Setup Python | actions/setup-python@v4 | Python environment |
| Setup Node | actions/setup-node@v4 | Node.js environment |
| Cache | actions/cache@v3 | Cache dependencies |
| Test | pytest + coverage | Run tests |
| Lint | ruff / pylint | Code quality |
| Security Scan | bandit + safety | Vulnerability scan |
| Build Images | docker/build-push-action@v5 | Build containers |
| Push to ACR | azure/docker-login@v1 | Push images |
| Deploy Infra | azure/cli@v1 | Deploy Bicep |
| Deploy Apps | azure/webapps-deploy@v2 | Deploy apps |
| Integration Tests | pytest (integration) | Post-deploy tests |
| Smoke Tests | curl + jq | Health checks |

### Dependencies

| Category | Tool | Purpose |
|----------|------|---------|
| Container Build | Docker 24+ | Image building |
| Azure Auth | Azure/login@v1 | Azure authentication |
| Bicep | Azure CLI | Infrastructure deployment |
| Secrets | GitHub Secrets | Secure variables |
| Environments | GitHub Environments | Deployment gates |
| Approval | GitHub Approvals | Manual gates |

### Testing in CI
- **Unit Tests**: pytest with coverage
- **Integration Tests**: pytest against deployed resources
- **E2E Tests**: Playwright tests
- **Load Tests**: Locust (optional)
- **Security**: Trivy container scanning

### Alternative Choices
- **Platform**: Azure DevOps (better Azure integration)
- **Platform**: GitLab CI (self-hosted option)
- **Platform**: Jenkins (full control, more setup)
- **Platform**: CircleCI (cloud-based)

---

## 11. DEPLOYMENT SCRIPTS

### Core Framework
- **Language**: Bash 5+ (Linux/macOS)
- **Alternative**: PowerShell 7+ (cross-platform)

### Dependencies

| Tool | Version | Purpose |
|------|---------|---------|
| Azure CLI | ^2.54.0 | Azure operations |
| jq | ^1.6 | JSON parsing |
| curl | ^7.0 | HTTP requests |
| yq | ^4.0 (optional) | YAML parsing |

### Script Structure
```bash
#!/usr/bin/env bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# deploy.sh
# - Pre-flight checks
# - Parameter validation
# - Bicep deployment
# - Health checks
# - Output summary
```

### Testing
- **Validation**: shellcheck (linting)
- **Testing**: bats (Bash Automated Testing System)
- **Dry-run**: --dry-run flag for validation

### Alternative Choices
- **Language**: PowerShell (Windows-first, cross-platform)
- **Language**: Python (more complex, better error handling)
- **Tool**: Azure Developer CLI (azd) - opinionated
- **Tool**: Terraform CLI (if using Terraform)

---

## 12. TESTS

### Core Framework - Backend
- **Language**: Python 3.11+
- **Test Framework**: pytest ^7.4.0

### Backend Testing Stack

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Test Framework | pytest | ^7.4.0 | Test runner |
| Async Tests | pytest-asyncio | ^0.21.0 | Async test support |
| Mocking | pytest-mock | ^3.12.0 | Mocking/stubbing |
| HTTP Mocking | respx | ^0.20.0 | HTTP mock |
| Coverage | pytest-cov | ^4.1.0 | Code coverage |
| Parametrize | pytest | (built-in) | Parametric tests |
| Fixtures | pytest | (built-in) | Test fixtures |
| Markers | pytest | (built-in) | Test categorization |
| Property Testing | hypothesis | ^6.90.0 | Property-based tests |

### Frontend Testing Stack

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Test Framework | vitest | ^1.0.0 | Fast unit tests |
| React Testing | @testing-library/react | ^14.1.0 | Component tests |
| User Events | @testing-library/user-event | ^14.5.0 | User interactions |
| E2E Framework | playwright | ^1.40.0 | Browser automation |
| Visual Testing | playwright | (built-in) | Screenshot comparison |

### Integration Testing

| Category | Tool | Purpose |
|----------|------|---------|
| Docker Compose | docker-compose | Local services |
| Cosmos Emulator | mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator | Cosmos local |
| Azurite | mcr.microsoft.com/azure-storage/azurite | Storage emulator |
| Redis | redis:7-alpine | Redis cache |

### Load Testing

| Tool | Purpose |
|------|---------|
| Locust | Python-based load testing |
| k6 | Modern load testing |
| Artillery | Node-based load testing |
| Azure Load Testing | Managed service |

### Test Organization
```
tests/
├── unit/                  # Fast, isolated tests
│   ├── test_agents.py
│   ├── test_evaluators.py
│   └── test_tools.py
├── integration/           # Service integration
│   ├── test_orchestrator_api.py
│   ├── test_langgraph_flow.py
│   └── test_cosmos_checkpointer.py
├── e2e/                   # End-to-end scenarios
│   ├── test_goal_workflow.py
│   └── playwright/
├── load/                  # Performance tests
│   └── locustfile.py
├── fixtures/              # Shared fixtures
│   └── spec_fixtures.py
├── conftest.py           # Pytest configuration
├── pytest.ini            # Pytest settings
└── docker-compose.yml    # Test services
```

### Alternative Choices
- **Python Test**: unittest (stdlib, less features)
- **Python Test**: nose2 (older)
- **E2E**: Selenium (older, more verbose)
- **E2E**: Cypress (E2E for web, Node-based)
- **Load Test**: JMeter (Java-based, GUI)

---

## 13. GOALGEN CLI (Generator Tool Itself)

### Core Framework
- **Language**: Python 3.11+
- **CLI Framework**: argparse (stdlib)
- **Template Engine**: Jinja2 ^3.1.0

### Dependencies

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| Template Engine | jinja2 | ^3.1.0 | Code generation |
| JSON Schema | jsonschema | ^4.19.0 | Spec validation |
| File Operations | pathlib | (stdlib) | Path manipulation |
| YAML | pyyaml | ^6.0.1 | YAML support (optional) |
| CLI Colors | colorama | ^0.4.6 | Colored output |
| Progress | tqdm | ^4.66.0 | Progress bars |
| Validation | pydantic | ^2.4.0 | Config validation |

### Template Structure
```
templates/
├── orchestrator/
│   ├── Dockerfile.j2
│   ├── requirements.txt.j2
│   ├── main.py.j2
│   └── config.py.j2
├── langgraph/
│   ├── quest_builder.py.j2
│   └── checkpointer_adapter.py.j2
├── infra/
│   ├── main.bicep.j2
│   └── modules/*.bicep.j2
└── webchat/
    ├── package.json.j2
    └── src/*.tsx.j2
```

### Testing Stack
- **Test Framework**: pytest ^7.4.0
- **Template Tests**: Test template rendering
- **Integration Tests**: Full generation tests
- **File System**: pytest-tmpdir

### Alternative Choices
- **CLI Framework**: click (more features)
- **CLI Framework**: typer (modern, type-based)
- **Template Engine**: Mako (Python-embedded)
- **Code Gen**: Cookiecutter (project templates)
- **Code Gen**: Yeoman (Node-based)

---

## SUMMARY: Technology Stack Overview

### Backend (Orchestrator, LangGraph, Agents, Tools)
- **Language**: Python 3.11+
- **Web**: FastAPI + Uvicorn
- **LLM**: LangChain + LangGraph + OpenAI
- **Database**: Azure Cosmos DB
- **Cache**: Redis
- **Identity**: Azure Managed Identity
- **Secrets**: Azure Key Vault
- **Monitoring**: Azure App Insights + OpenTelemetry

### Frontend (Webchat)
- **Language**: TypeScript 5.2+
- **Framework**: React 18.2
- **Build**: Vite 5.0
- **State**: Zustand
- **Styling**: Tailwind CSS
- **Real-time**: SignalR

### Infrastructure
- **IaC**: Bicep
- **Container**: Docker
- **Hosting**: Azure Container Apps
- **Functions**: Azure Functions
- **Storage**: Azure Cosmos DB, Redis, Blob Storage
- **Networking**: Azure SignalR, Application Gateway (optional)

### DevOps
- **CI/CD**: GitHub Actions
- **Registry**: Azure Container Registry
- **Deployment**: Azure CLI + Bicep
- **Testing**: pytest + Playwright
- **Monitoring**: Azure Monitor + Application Insights

### Code Generation (GoalGen itself)
- **Language**: Python 3.11+
- **Templates**: Jinja2
- **Validation**: Pydantic + JSON Schema
- **CLI**: argparse

### Key Design Decisions

1. **Python-First Backend**: Consistent language across all backend components
2. **Modern Python**: 3.11+ for performance and type hints
3. **FastAPI**: Industry standard for async Python APIs
4. **LangChain/LangGraph**: De facto standard for LLM orchestration
5. **React + TypeScript**: Type-safe, modern frontend
6. **Vite**: Fast builds and dev experience
7. **Bicep**: Native Azure IaC, less verbose than ARM
8. **Managed Identity**: Passwordless authentication
9. **Container Apps**: Serverless container hosting
10. **GitHub Actions**: Native GitHub integration

### Version Pinning Strategy
- **Major versions**: Locked (^) for stability
- **Patch updates**: Allowed for security fixes
- **Dev dependencies**: More flexible
- **Review cadence**: Quarterly dependency updates
