# GoalGen Configuration Matrix

This document identifies all configuration requirements for each component at build time, deploy time, and runtime.

## 1. Orchestrator (FastAPI API Service)

### Build Time (Developer Choices in Spec)
- `goal_id` - Identifier for the goal being orchestrated
- `api.base_path` - API endpoint path pattern (e.g., `/api/v1/goal/{goal_id}`)
- `api.auth_type` - Authentication mechanism (jwt, api_key, none)
- Token limits for LLM calls
- Request timeout values
- Retry policies (max attempts, backoff strategy)
- Logging level and format
- CORS allowed origins pattern

### Deploy Time (Infrastructure Deployment)
- Container registry URL (ACR)
- Container image tag
- Key Vault URL
- Cosmos DB connection endpoint
- Redis cache endpoint
- SignalR/WebPubSub connection string
- Managed Environment ID (Container Apps)
- CPU/Memory resource limits (initial)
- Min/Max replica count (initial)
- Azure region/location
- Resource group name
- Subscription ID

### Runtime (Operational Changes)
- Scaling rules (CPU threshold, memory threshold, HTTP queue depth)
- Number of replicas (horizontal scaling)
- Circuit breaker thresholds
- Rate limiting rules
- Feature flags (enable/disable specific goals)
- A/B test percentages
- Cache TTL values
- Request timeout overrides
- Log level changes
- Emergency maintenance mode

---

## 2. LangGraph (Quest Builder)

### Build Time
- `context_fields` - State schema fields from spec
- `tasks` - Task definitions and execution order
- Task graph structure (sequential, parallel, conditional)
- Checkpointer type (cosmos, redis, blob)
- Supervisor routing policy (`simple_router`, `llm_router`, custom)
- Max iterations per goal
- Human-in-the-loop interrupt points
- State persistence strategy
- Error handling strategy (retry, skip, fail)
- Task timeout defaults

### Deploy Time
- Checkpointer backend connection string (Cosmos/Redis)
- Checkpointer database/container names
- Checkpointer partition key strategy
- LLM endpoint URLs (OpenAI/Azure OpenAI)
- LLM API version
- Model deployment names

### Runtime
- LLM model selection (gpt-4, gpt-4-turbo, gpt-3.5)
- Temperature settings per agent
- Max tokens per LLM call
- Checkpointer TTL (conversation expiry)
- Enable/disable specific tasks
- Task routing weights (for A/B testing)
- Interrupt thresholds (confidence levels)
- Graph execution timeout

---

## 3. Agents

### Build Time
- Agent names and types from `spec.agents`
- Agent kind (`llm_agent`, `function_agent`, `supervisor`)
- Tool bindings per agent
- `max_loop` - Maximum iterations per agent
- Prompt template selection
- Response parsing strategy
- Agent chaining logic

### Deploy Time
- LLM API key/endpoint (from Key Vault)
- Model deployment names
- Tool endpoint URLs
- Default prompt template paths

### Runtime
- LLM model selection per agent
- Temperature (0.0-2.0)
- Top-p sampling
- Frequency/presence penalty
- Max tokens per response
- Max tool calls per turn
- Streaming enabled/disabled
- Prompt template overrides
- Agent-specific feature flags
- Retry attempts for failed LLM calls

---

## 4. Evaluators

### Build Time
- Evaluator IDs and types from `spec.evaluators`
- Check conditions (field presence, value validation)
- Actions on failure (`ask_user`, `set_default`, `abort`)
- Validation rules (regex, range, enum)
- Custom evaluator logic

### Deploy Time
- Reference data endpoints (for validation lookups)
- Validation service URLs
- Rule engine configuration

### Runtime
- Enable/disable specific evaluators
- Validation strictness levels
- Error threshold before abort
- Validation timeout
- Cache validation results (TTL)

---

## 5. Tools (Azure Functions / HTTP Wrappers)

### Build Time (per tool in `spec.tools`)
- Tool name and type (`http`, `internal`, `function`)
- HTTP method (GET, POST, etc.)
- Request/response schema
- Authentication type (`key`, `oauth`, `managed_identity`)
- Retry policy
- Timeout
- Rate limiting requirements
- Response caching strategy

### Deploy Time
- Tool endpoint URLs (e.g., `{FLIGHT_API_URL}`)
- API keys/secrets (Key Vault references)
- Function App URLs (if Azure Functions)
- Function App identity (System/User Assigned)
- Regional endpoints
- Failover endpoints

### Runtime
- Enable/disable specific tools
- Request timeout overrides
- Retry attempts
- Rate limit adjustments
- Circuit breaker thresholds
- Cache TTL for responses
- A/B test endpoints (primary/secondary)
- Mock mode (for testing)

---

## 6. Infrastructure (Bicep Modules)

### Build Time
- Target deployment platforms (`containerapps`, `functions`, `aks`)
- Azure services to provision (Cosmos, Redis, Key Vault, SignalR, etc.)
- Network topology (public, vnet-integrated, private endpoints)
- High availability requirements (multi-region, zone-redundant)
- Backup/DR strategy
- Monitoring stack (App Insights, Log Analytics)

### Deploy Time
- Resource naming convention
- Azure region(s)
- Resource group name(s)
- Subscription ID(s)
- Virtual network configuration
- Subnet IDs
- Private DNS zones
- Container Apps Environment ID
- ACR registry name
- Key Vault name
- Cosmos account name
- Redis cache name
- SignalR resource name
- Log Analytics workspace ID
- Application Insights instrumentation key
- Tags (cost center, environment, owner)

### Runtime
- Scale-out rules (per service)
- Cosmos RU/s throughput
- Redis cache size tier
- SignalR unit count
- Container Apps replica count
- Function App plan tier
- Diagnostic settings (log retention)

---

## 7. Security (Key Vault + Managed Identity)

### Build Time
- Secrets required by application
- Managed Identity type (System, User Assigned)
- RBAC role assignments needed
- Access policy strategy (RBAC vs Access Policies)
- Secret rotation policy
- Audit logging requirements

### Deploy Time
- Key Vault URL
- Secret names and initial values
- Managed Identity client IDs
- RBAC role assignments (scope, principal, role)
- Network rules (firewall, service endpoints)
- Key Vault access policies (if using)
- Certificate requirements (SSL/TLS)

### Runtime
- Secret rotation triggers
- Access policy updates
- Emergency key revocation
- Audit log queries
- Compliance reporting

---

## 8. Teams Bot

### Build Time (from `spec.ux.teams`)
- Bot name (`bot_name`)
- Message style (`text`, `adaptiveCard`)
- Supported commands
- Message extension configuration
- Adaptive Card templates
- Multi-language support

### Deploy Time
- Bot Framework App ID
- Bot Framework App Secret (Key Vault)
- Messaging endpoint (Orchestrator URL)
- Teams App ID
- Allowed domains
- Manifest version
- Bot capabilities (messaging, calling, etc.)

### Runtime
- Enable/disable bot
- Command routing updates
- Adaptive Card template updates
- Response timeout
- Typing indicator behavior
- Message throttling

---

## 9. Webchat SPA

### Build Time (from `spec.ux.webchat`)
- UI framework choice (React, Vue, Angular)
- Theme/styling
- Supported features (file upload, voice, video)
- Message rendering (markdown, html)
- Accessibility requirements
- Analytics integration

### Deploy Time
- API endpoint URL
- SignalR connection URL
- SignalR hub name
- Authentication endpoint
- CDN URL (for static assets)
- Environment (dev, staging, prod)
- Analytics keys (GA, App Insights)

### Runtime
- Feature flags (enable/disable features)
- Theme switching (light/dark mode)
- Message polling interval
- SignalR reconnection policy
- File upload size limits
- Session timeout
- A/B test variants

---

## 10. CI/CD Pipeline

### Build Time
- Git repository structure
- Branch strategy (gitflow, trunk-based)
- Build triggers (push, PR, manual)
- Test stages (unit, integration, e2e)
- Deployment stages (dev, staging, prod)
- Approval gates
- Rollback strategy

### Deploy Time
- Azure subscription credentials (Service Principal)
- ACR credentials
- Resource group per environment
- Deployment slot strategy
- Blue-green vs canary deployment
- Health check endpoints
- Smoke test endpoints

### Runtime
- Enable/disable automated deployments
- Approval workflow changes
- Deployment schedule (maintenance windows)
- Rollback triggers
- Alert thresholds

---

## 11. Deployment Scripts

### Build Time
- Deployment orchestration strategy
- Pre-flight validation checks
- Deployment order (infra → services → config)
- Post-deployment verification
- Rollback procedures

### Deploy Time
- Environment name (dev, staging, prod)
- Azure subscription
- Resource group
- Terraform/Bicep state location
- Deployment credentials
- Parameter files per environment

### Runtime
- Deployment dry-run mode
- Force flag (skip confirmations)
- Specific component deployment
- Health check intervals

---

## 12. Tests

### Build Time
- Test framework (pytest, unittest)
- Test types (unit, integration, e2e, load)
- Test data strategy
- Mock/stub strategy
- Code coverage requirements

### Deploy Time
- Test database connection strings
- Azure emulator endpoints (Cosmos, Storage)
- Test Key Vault
- Test SignalR endpoint
- Test identity credentials
- Docker Compose configuration

### Runtime
- Test selection (markers, tags)
- Parallel test execution
- Test timeout
- Retry flaky tests
- Generate test reports

---

## Configuration Management Strategy

### Where Configurations Live

1. **Build Time Configs** → `goal spec JSON` + generator defaults
2. **Deploy Time Configs** → `infra/parameters.json` + environment-specific files
3. **Runtime Configs** → Azure App Configuration / Key Vault / Environment Variables

### Configuration Precedence

```
Runtime Override > Deploy Time > Build Time (Spec) > Generator Defaults
```

### Generated Configuration Files

1. **parameters.dev.json** - Development environment
2. **parameters.staging.json** - Staging environment
3. **parameters.prod.json** - Production environment
4. **.env.sample** - Local development template
5. **config.py** - Application configuration loader
6. **secrets.bicep** - Key Vault secret definitions
7. **scaling-rules.json** - Container Apps scaling configuration

### Tooling Requirements

- Azure App Configuration SDK (for runtime config changes)
- Key Vault SDK (for secret retrieval)
- Feature flag library (LaunchDarkly, Azure App Config)
- Configuration validation (Pydantic models)
