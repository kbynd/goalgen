# Component Configuration Inventory

Detailed listing of every configuration parameter for each component across build, deploy, and runtime stages.

---

## 1. ORCHESTRATOR (FastAPI Bot API)

### Build-Time Configs (from spec → code generation)

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `id` | string | spec.id | required | Goal identifier in routes |
| `ux.api.enabled` | boolean | spec.ux.api.enabled | true | Whether to generate API |
| `ux.api.base_path` | string | spec.ux.api.base_path | `/api/v1/goal/{id}` | FastAPI route prefix |
| `ux.api.auth_type` | enum | spec.ux.api.auth_type | "jwt" | Authentication: jwt\|api_key\|none |
| `ux.api.cors_origins` | string[] | spec.ux.api.cors_origins | ["*"] | CORS allowed origins |
| `ux.api.request_timeout` | int | spec.ux.api.request_timeout | 30 | Request timeout (seconds) |
| `ux.api.rate_limits.requests_per_minute` | int | spec.ux.api.rate_limits | 60 | Rate limit threshold |
| `langgraph.checkpointer_type` | enum | spec.langgraph.checkpointer_type | "cosmos" | Session backend: cosmos\|redis\|blob |
| `langgraph.state_ttl` | int | spec.langgraph.state_ttl | 86400 | Session TTL (seconds) |

### Deploy-Time Configs (from parameters.json → env vars)

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `AZURE_SUBSCRIPTION_ID` | string | parameters.json | "12345..." | Deployment target |
| `RESOURCE_GROUP` | string | parameters.json | "rg-goalgen-dev" | Resource group name |
| `CONTAINER_REGISTRY` | string | parameters.json | "acr123.azurecr.io" | ACR URL |
| `IMAGE_TAG` | string | CI/CD pipeline | "1.0.0-abc123" | Container image version |
| `KEYVAULT_URL` | string | Bicep output | "https://kv-xyz.vault.azure.net/" | Key Vault endpoint |
| `COSMOS_ENDPOINT` | string | Bicep output | "https://cosmos-xyz.documents.azure.com:443/" | Cosmos DB endpoint |
| `REDIS_HOST` | string | Bicep output | "redis-xyz.redis.cache.windows.net" | Redis cache host |
| `REDIS_PORT` | int | Bicep output | 6380 | Redis SSL port |
| `SIGNALR_CONNECTION_STRING` | string | Key Vault ref | "Endpoint=https://..." | SignalR connection |
| `APPINSIGHTS_INSTRUMENTATION_KEY` | string | Bicep output | "abc-123-..." | App Insights key |
| `MANAGED_IDENTITY_CLIENT_ID` | string | Bicep output | "guid" | User-assigned identity |
| `MIN_REPLICAS` | int | parameters.json | 1 | Initial min replicas |
| `MAX_REPLICAS` | int | parameters.json | 10 | Initial max replicas |
| `CPU_CORES` | float | parameters.json | 0.5 | CPU allocation |
| `MEMORY_GB` | string | parameters.json | "1Gi" | Memory allocation |

### Runtime Configs (from App Config / Key Vault / env overrides)

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `LOG_LEVEL` | enum | App Config | "INFO" | DEBUG\|INFO\|WARNING\|ERROR |
| `ENABLE_DEBUG_ENDPOINTS` | boolean | App Config | false | Enable /debug routes |
| `MAINTENANCE_MODE` | boolean | App Config | false | Return 503 for all requests |
| `FEATURE_FLAG_{GOAL_ID}` | boolean | App Config | true | Enable/disable specific goal |
| `CIRCUIT_BREAKER_THRESHOLD` | int | App Config | 5 | Failures before circuit opens |
| `CIRCUIT_BREAKER_TIMEOUT` | int | App Config | 60 | Seconds before retry |
| `REQUEST_TIMEOUT_OVERRIDE` | int | App Config | null | Override build-time timeout |
| `MAX_CONCURRENT_REQUESTS` | int | App Config | 100 | Concurrent request limit |
| `SCALING_CPU_THRESHOLD` | int | Container Apps | 70 | CPU % for scale-up |
| `SCALING_MEMORY_THRESHOLD` | int | Container Apps | 80 | Memory % for scale-up |
| `SCALING_HTTP_QUEUE_DEPTH` | int | Container Apps | 100 | Queue depth for scale-up |
| `CURRENT_REPLICAS` | int | Container Apps | (auto) | Current replica count |
| `LLM_RETRY_ATTEMPTS` | int | App Config | 3 | Max LLM call retries |
| `CACHE_TTL_SECONDS` | int | App Config | 300 | Response cache TTL |

---

## 2. LANGGRAPH (Quest Builder)

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `id` | string | spec.id | required | Graph identifier |
| `context_fields` | string[] | spec.context_fields | required | QuestState schema fields |
| `tasks` | object[] | spec.tasks | required | Task node definitions |
| `tasks[].id` | string | spec.tasks[].id | required | Task node name |
| `tasks[].type` | enum | spec.tasks[].type | required | evaluator\|task |
| `tasks[].tools` | string[] | spec.tasks[].tools | [] | Tool names for task |
| `tasks[].timeout` | int | spec.tasks[].timeout | 300 | Task timeout (seconds) |
| `tasks[].retry_policy.max_attempts` | int | spec.tasks[].retry_policy | 3 | Max retry attempts |
| `tasks[].retry_policy.backoff_strategy` | enum | spec.tasks[].retry_policy | "exponential" | linear\|exponential |
| `agents` | object | spec.agents | required | Agent definitions |
| `evaluators` | object[] | spec.evaluators | required | Evaluator definitions |
| `langgraph.checkpointer_type` | enum | spec.langgraph.checkpointer_type | "cosmos" | cosmos\|redis\|blob |
| `langgraph.supervisor_policy` | enum | spec.langgraph.supervisor_policy | "simple_router" | Routing strategy |
| `langgraph.max_iterations` | int | spec.langgraph.max_iterations | 20 | Max graph iterations |
| `langgraph.state_ttl` | int | spec.langgraph.state_ttl | 86400 | State TTL (seconds) |
| `langgraph.human_in_loop` | boolean | spec.langgraph.human_in_loop | false | Enable interrupts |

### Deploy-Time Configs

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `CHECKPOINTER_COSMOS_ENDPOINT` | string | Bicep output | "https://..." | Cosmos endpoint |
| `CHECKPOINTER_COSMOS_KEY` | string | Key Vault | "..." | Cosmos key (if not MI) |
| `CHECKPOINTER_DATABASE_NAME` | string | parameters.json | "goalgen" | Cosmos database |
| `CHECKPOINTER_CONTAINER_NAME` | string | parameters.json | "checkpoints" | Cosmos container |
| `CHECKPOINTER_REDIS_HOST` | string | Bicep output | "redis-xyz.redis..." | Redis host (if redis) |
| `CHECKPOINTER_REDIS_PORT` | int | Bicep output | 6380 | Redis port |
| `CHECKPOINTER_REDIS_PASSWORD` | string | Key Vault | "..." | Redis password |
| `LLM_ENDPOINT` | string | parameters.json | "https://api.openai.com/v1" | LLM API endpoint |
| `LLM_API_KEY` | string | Key Vault | "sk-..." | LLM API key |
| `LLM_API_VERSION` | string | parameters.json | "2023-12-01-preview" | Azure OpenAI API version |
| `LLM_DEPLOYMENT_NAME` | string | parameters.json | "gpt-4" | Model deployment name |

### Runtime Configs

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `CHECKPOINTER_TTL_OVERRIDE` | int | App Config | null | Override state TTL |
| `MAX_ITERATIONS_OVERRIDE` | int | App Config | null | Override max iterations |
| `ENABLE_TASK_{TASK_ID}` | boolean | App Config | true | Enable/disable specific task |
| `TASK_TIMEOUT_OVERRIDE_{TASK_ID}` | int | App Config | null | Override task timeout |
| `TASK_ROUTING_WEIGHT_{TASK_ID}` | int | App Config | 100 | A/B test routing (0-100) |
| `SUPERVISOR_POLICY_OVERRIDE` | string | App Config | null | Override routing policy |
| `GRAPH_EXECUTION_TIMEOUT` | int | App Config | 600 | Total graph timeout |

---

## 3. AGENTS

### Build-Time Configs (per agent in spec.agents)

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `agents.{name}.kind` | enum | spec.agents.{name}.kind | required | supervisor\|llm_agent\|function_agent |
| `agents.{name}.policy` | string | spec.agents.{name}.policy | null | Supervisor routing policy |
| `agents.{name}.tools` | string[] | spec.agents.{name}.tools | [] | Tool IDs available |
| `agents.{name}.max_loop` | int | spec.agents.{name}.max_loop | 3 | Max agent iterations |
| `agents.{name}.prompt_template` | string | spec.agents.{name}.prompt_template | "default" | Prompt template path |
| `agents.{name}.llm_config.model` | string | spec.agents.{name}.llm_config.model | "gpt-4" | Default model |
| `agents.{name}.llm_config.temperature` | float | spec.agents.{name}.llm_config.temperature | 0.7 | Temperature (0-2) |
| `agents.{name}.llm_config.max_tokens` | int | spec.agents.{name}.llm_config.max_tokens | 2000 | Max output tokens |
| `agents.{name}.llm_config.streaming` | boolean | spec.agents.{name}.llm_config.streaming | false | Enable streaming |

### Deploy-Time Configs

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `LLM_ENDPOINT` | string | parameters.json | "https://api.openai.com/v1" | LLM API base |
| `LLM_API_KEY` | string | Key Vault | "sk-..." | API key |
| `AGENT_PROMPT_TEMPLATE_PATH` | string | parameters.json | "/app/prompts" | Prompt directory |
| `TOOL_ENDPOINTS` | json | parameters.json | {...} | Tool endpoint map |

### Runtime Configs (per agent)

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `AGENT_{NAME}_MODEL` | string | App Config | (build default) | Model override |
| `AGENT_{NAME}_TEMPERATURE` | float | App Config | (build default) | Temperature override |
| `AGENT_{NAME}_MAX_TOKENS` | int | App Config | (build default) | Max tokens override |
| `AGENT_{NAME}_TOP_P` | float | App Config | 1.0 | Top-p sampling |
| `AGENT_{NAME}_FREQUENCY_PENALTY` | float | App Config | 0.0 | Frequency penalty |
| `AGENT_{NAME}_PRESENCE_PENALTY` | float | App Config | 0.0 | Presence penalty |
| `AGENT_{NAME}_MAX_TOOL_CALLS` | int | App Config | 5 | Max tool calls/turn |
| `AGENT_{NAME}_STREAMING` | boolean | App Config | (build default) | Streaming override |
| `AGENT_{NAME}_PROMPT_OVERRIDE` | string | App Config | null | Prompt template override |
| `AGENT_{NAME}_ENABLED` | boolean | App Config | true | Enable/disable agent |
| `AGENT_{NAME}_RETRY_ATTEMPTS` | int | App Config | 3 | LLM retry attempts |

---

## 4. EVALUATORS

### Build-Time Configs (per evaluator)

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `evaluators[].id` | string | spec.evaluators[].id | required | Evaluator identifier |
| `evaluators[].checks` | object[] | spec.evaluators[].checks | required | Validation checks |
| `evaluators[].checks[].field` | string | spec.evaluators[].checks[].field | required | Context field to check |
| `evaluators[].checks[].action` | enum | spec.evaluators[].checks[].action | required | ask_user\|set_default\|abort |
| `evaluators[].checks[].validation.type` | enum | spec.evaluators[].checks[].validation.type | "presence" | presence\|regex\|range\|enum |
| `evaluators[].checks[].validation.pattern` | string | spec.evaluators[].checks[].validation | null | Regex pattern |
| `evaluators[].checks[].validation.min` | number | spec.evaluators[].checks[].validation | null | Min value (range) |
| `evaluators[].checks[].validation.max` | number | spec.evaluators[].checks[].validation | null | Max value (range) |
| `evaluators[].checks[].validation.values` | array | spec.evaluators[].checks[].validation | null | Allowed values (enum) |
| `evaluators[].timeout` | int | spec.evaluators[].timeout | 10 | Evaluation timeout |

### Deploy-Time Configs

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `VALIDATION_SERVICE_URL` | string | parameters.json | "https://..." | External validation service |
| `REFERENCE_DATA_ENDPOINT` | string | parameters.json | "https://..." | Lookup data API |

### Runtime Configs

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `EVALUATOR_{ID}_ENABLED` | boolean | App Config | true | Enable/disable evaluator |
| `EVALUATOR_{ID}_STRICTNESS` | enum | App Config | "normal" | strict\|normal\|lenient |
| `EVALUATOR_{ID}_ERROR_THRESHOLD` | int | App Config | 3 | Errors before abort |
| `EVALUATOR_{ID}_TIMEOUT` | int | App Config | (build default) | Timeout override |
| `VALIDATION_CACHE_TTL` | int | App Config | 600 | Cache validation results |

---

## 5. TOOLS

### Build-Time Configs (per tool in spec.tools)

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `tools.{name}.type` | enum | spec.tools.{name}.type | required | http\|internal\|function |
| `tools.{name}.spec.url` | string | spec.tools.{name}.spec.url | required | Endpoint URL template |
| `tools.{name}.spec.method` | enum | spec.tools.{name}.spec.method | "POST" | GET\|POST\|PUT\|DELETE |
| `tools.{name}.spec.auth` | enum | spec.tools.{name}.spec.auth | "key" | key\|oauth\|managed_identity |
| `tools.{name}.spec.timeout` | int | spec.tools.{name}.spec.timeout | 30 | Request timeout |
| `tools.{name}.spec.retry_attempts` | int | spec.tools.{name}.spec.retry_attempts | 3 | Retry attempts |
| `tools.{name}.spec.cache_ttl` | int | spec.tools.{name}.spec.cache_ttl | 0 | Cache TTL (0=no cache) |
| `tools.{name}.spec.request_schema` | object | spec.tools.{name}.spec | null | JSON schema for request |
| `tools.{name}.spec.response_schema` | object | spec.tools.{name}.spec | null | JSON schema for response |

### Deploy-Time Configs (per tool)

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `TOOL_{NAME}_URL` | string | deployment.variables | "https://api.partner/v1" | Actual endpoint URL |
| `TOOL_{NAME}_API_KEY` | string | Key Vault | "key123..." | API key (if auth=key) |
| `TOOL_{NAME}_OAUTH_CLIENT_ID` | string | Key Vault | "client-id" | OAuth client ID |
| `TOOL_{NAME}_OAUTH_SECRET` | string | Key Vault | "secret" | OAuth secret |
| `TOOL_{NAME}_FUNCTION_URL` | string | Bicep output | "https://func.azurewebsites.net/api/tool" | Azure Function URL |
| `TOOL_{NAME}_FUNCTION_KEY` | string | Key Vault | "func-key" | Function auth key |

### Runtime Configs (per tool)

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `TOOL_{NAME}_ENABLED` | boolean | App Config | true | Enable/disable tool |
| `TOOL_{NAME}_TIMEOUT_OVERRIDE` | int | App Config | null | Override timeout |
| `TOOL_{NAME}_RETRY_OVERRIDE` | int | App Config | null | Override retry attempts |
| `TOOL_{NAME}_RATE_LIMIT` | int | App Config | 100 | Requests/minute |
| `TOOL_{NAME}_CIRCUIT_BREAKER_THRESHOLD` | int | App Config | 5 | Failures before open |
| `TOOL_{NAME}_CIRCUIT_BREAKER_TIMEOUT` | int | App Config | 60 | Circuit open seconds |
| `TOOL_{NAME}_CACHE_TTL_OVERRIDE` | int | App Config | null | Override cache TTL |
| `TOOL_{NAME}_AB_TEST_ENDPOINT` | string | App Config | null | A/B test alternate URL |
| `TOOL_{NAME}_AB_TEST_PERCENTAGE` | int | App Config | 0 | % traffic to A/B (0-100) |
| `TOOL_{NAME}_MOCK_MODE` | boolean | App Config | false | Return mock responses |

---

## 6. INFRASTRUCTURE (Bicep)

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `deployment.targets` | string[] | spec.deployment.targets | required | containerapps\|functions\|aks |
| `deployment.regions` | string[] | spec.deployment.regions | ["eastus"] | Azure regions |
| `deployment.high_availability` | boolean | spec.deployment.high_availability | false | Multi-zone deployment |
| `deployment.multi_region` | boolean | spec.deployment.multi_region | false | Multi-region deployment |
| `deployment.resources.orchestrator.cpu` | float | spec.deployment.resources | 0.5 | CPU cores |
| `deployment.resources.orchestrator.memory` | string | spec.deployment.resources | "1Gi" | Memory allocation |
| `deployment.resources.orchestrator.min_replicas` | int | spec.deployment.resources | 1 | Min replicas |
| `deployment.resources.orchestrator.max_replicas` | int | spec.deployment.resources | 10 | Max replicas |
| `deployment.resources.cosmos.throughput` | int | spec.deployment.resources | 400 | Cosmos RU/s |
| `deployment.resources.cosmos.consistency` | enum | spec.deployment.resources | "session" | Consistency level |
| `deployment.resources.redis.sku` | enum | spec.deployment.resources | "basic" | basic\|standard\|premium |
| `deployment.resources.redis.capacity` | int | spec.deployment.resources | 1 | 0-6 based on SKU |
| `deployment.security.managed_identity` | enum | spec.deployment.security | "system" | system\|user |
| `deployment.security.network.vnet_integration` | boolean | spec.deployment.security | false | VNet integration |
| `deployment.security.network.private_endpoints` | boolean | spec.deployment.security | false | Private endpoints |

### Deploy-Time Configs (per environment)

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `subscription_id` | string | deployment.environments.{env} | "guid" | Azure subscription |
| `resource_group` | string | deployment.environments.{env} | "rg-goalgen-dev" | Resource group |
| `location` | string | deployment.environments.{env} | "eastus" | Primary region |
| `environment_name` | string | deployment.environments.{env} | "dev" | Environment tag |
| `naming_prefix` | string | parameters.json | "goalgen" | Resource name prefix |
| `naming_suffix` | string | parameters.json | "xyz123" | Resource name suffix |
| `tags` | object | parameters.json | {...} | Azure tags |
| `vnet_id` | string | parameters.json | "/subscriptions/..." | VNet resource ID |
| `subnet_id` | string | parameters.json | "/subscriptions/..." | Subnet resource ID |
| `acr_name` | string | parameters.json | "acrgoalgen" | Container registry |
| `log_analytics_workspace_id` | string | parameters.json | "/subscriptions/..." | Log Analytics ID |

### Runtime Configs (Infrastructure layer)

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `cosmos_ru_s` | int | Azure Portal/CLI | (deploy value) | Cosmos throughput |
| `redis_cache_size` | enum | Azure Portal/CLI | (deploy value) | Redis tier/capacity |
| `signalr_unit_count` | int | Azure Portal/CLI | 1 | SignalR units |
| `container_apps_replicas` | int | Auto/Manual | (deploy range) | Current replicas |
| `function_app_plan_tier` | enum | Azure Portal/CLI | (deploy value) | Function plan |
| `diagnostics_log_retention` | int | Azure Portal/CLI | 30 | Log retention days |

---

## 7. SECURITY (Key Vault + Managed Identity)

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `deployment.security.managed_identity` | enum | spec.deployment.security | "system" | system\|user |
| `deployment.security.key_vault_name` | string | spec.deployment.security | "(generated)" | Key Vault name |
| `deployment.security.secrets` | object[] | spec.deployment.security.secrets | [] | Secret definitions |
| `deployment.security.secrets[].name` | string | spec.deployment.security.secrets | required | Secret name |
| `deployment.security.secrets[].source` | enum | spec.deployment.security.secrets | "manual" | manual\|reference |
| `deployment.security.network.firewall_rules` | object[] | spec.deployment.security | [] | IP allow list |

### Deploy-Time Configs

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `KEY_VAULT_NAME` | string | parameters.json | "kv-goalgen-xyz" | Key Vault name |
| `KEY_VAULT_SKU` | enum | parameters.json | "standard" | standard\|premium |
| `MANAGED_IDENTITY_NAME` | string | parameters.json | "mi-goalgen" | User-assigned MI name |
| `RBAC_ASSIGNMENTS` | object[] | Bicep | [...] | Role assignments |
| `ACCESS_POLICIES` | object[] | Bicep (legacy) | [...] | Access policies |
| `SECRET_{NAME}_VALUE` | string | Manual/Script | "..." | Secret values |
| `CERTIFICATE_NAMES` | string[] | parameters.json | [] | Cert names to provision |

### Runtime Configs

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `SECRET_ROTATION_ENABLED` | boolean | Key Vault | false | Auto-rotation |
| `SECRET_EXPIRY_DAYS` | int | Key Vault | null | Secret expiry |
| `AUDIT_LOG_ENABLED` | boolean | Diagnostic Settings | true | Audit logging |
| `ACCESS_POLICY_UPDATES` | object[] | Azure Portal/CLI | - | Runtime access changes |

---

## 8. TEAMS BOT

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `ux.teams.enabled` | boolean | spec.ux.teams.enabled | false | Generate Teams bot |
| `ux.teams.bot_name` | string | spec.ux.teams.bot_name | required | Bot display name |
| `ux.teams.message_style` | enum | spec.ux.teams.message_style | "text" | text\|adaptiveCard |
| `ux.teams.commands` | string[] | spec.ux.teams.commands | [] | Bot commands |
| `ux.teams.multi_language` | boolean | spec.ux.teams.multi_language | false | Multi-language support |
| `ux.teams.message_extensions` | boolean | spec.ux.teams | false | Enable message extensions |

### Deploy-Time Configs

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `TEAMS_APP_ID` | string | Bot Framework | "guid" | Teams app ID |
| `BOT_ID` | string | Bot Framework | "guid" | Bot Framework app ID |
| `BOT_PASSWORD` | string | Key Vault | "secret" | Bot Framework secret |
| `MESSAGING_ENDPOINT` | string | parameters.json | "https://api.../messages" | Bot endpoint |
| `TEAMS_MANIFEST_VERSION` | string | parameters.json | "1.16" | Manifest schema version |
| `VALID_DOMAINS` | string[] | parameters.json | ["api.domain.com"] | Allowed domains |

### Runtime Configs

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `TEAMS_BOT_ENABLED` | boolean | App Config | true | Enable/disable bot |
| `COMMAND_ROUTING` | object | App Config | {...} | Command routing rules |
| `ADAPTIVE_CARD_TEMPLATE_VERSION` | string | App Config | "1.5" | Card schema version |
| `RESPONSE_TIMEOUT` | int | App Config | 30 | Response timeout |
| `TYPING_INDICATOR` | boolean | App Config | true | Show typing indicator |
| `MESSAGE_THROTTLE_MS` | int | App Config | 1000 | Min ms between messages |

---

## 9. WEBCHAT SPA

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `ux.webchat.enabled` | boolean | spec.ux.webchat.enabled | false | Generate webchat |
| `ux.webchat.theme` | enum | spec.ux.webchat.theme | "light" | light\|dark\|auto |
| `ux.webchat.features.file_upload` | boolean | spec.ux.webchat.features | true | File upload |
| `ux.webchat.features.voice` | boolean | spec.ux.webchat.features | false | Voice input |
| `ux.webchat.features.video` | boolean | spec.ux.webchat.features | false | Video chat |
| `ux.webchat.markdown` | boolean | spec.ux.webchat | true | Markdown rendering |
| `ux.webchat.analytics` | string | spec.ux.webchat | null | Analytics provider |

### Deploy-Time Configs

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `VITE_API_ENDPOINT` | string | parameters.json | "https://api.../v1" | API base URL |
| `VITE_SIGNALR_URL` | string | parameters.json | "https://signalr..." | SignalR endpoint |
| `VITE_SIGNALR_HUB` | string | parameters.json | "goalgen" | Hub name |
| `VITE_AUTH_ENDPOINT` | string | parameters.json | "https://auth..." | Auth endpoint |
| `VITE_CDN_URL` | string | parameters.json | "https://cdn..." | CDN for assets |
| `VITE_ENVIRONMENT` | enum | parameters.json | "dev" | dev\|staging\|prod |
| `VITE_GA_TRACKING_ID` | string | parameters.json | "G-..." | Google Analytics |
| `VITE_APPINSIGHTS_KEY` | string | parameters.json | "key" | App Insights |

### Runtime Configs

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `FEATURE_FILE_UPLOAD` | boolean | App Config | (build) | Feature flag |
| `FEATURE_VOICE` | boolean | App Config | (build) | Feature flag |
| `THEME_MODE` | enum | User preference | (build) | Theme override |
| `MESSAGE_POLL_INTERVAL` | int | App Config | 1000 | Polling interval (ms) |
| `SIGNALR_RECONNECT_DELAY` | int | App Config | 5000 | Reconnect delay (ms) |
| `FILE_UPLOAD_MAX_SIZE` | int | App Config | 10485760 | Max file size (bytes) |
| `SESSION_TIMEOUT` | int | App Config | 1800 | Session timeout (seconds) |
| `AB_TEST_VARIANT` | string | App Config | "default" | A/B test variant |

---

## 10. CI/CD PIPELINE

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `deployment.cicd.provider` | enum | spec.deployment.cicd.provider | "github" | github\|azdo\|gitlab |
| `deployment.cicd.branch_strategy` | enum | spec.deployment.cicd.branch_strategy | "gitflow" | gitflow\|trunk |
| `deployment.cicd.auto_deploy.dev` | boolean | spec.deployment.cicd.auto_deploy | true | Auto-deploy to dev |
| `deployment.cicd.auto_deploy.staging` | boolean | spec.deployment.cicd.auto_deploy | false | Auto-deploy to staging |
| `deployment.cicd.auto_deploy.prod` | boolean | spec.deployment.cicd.auto_deploy | false | Auto-deploy to prod |
| `deployment.cicd.approval_required.staging` | boolean | spec.deployment.cicd.approval_required | true | Require approval |
| `deployment.cicd.approval_required.prod` | boolean | spec.deployment.cicd.approval_required | true | Require approval |
| `deployment.cicd.tests.unit` | boolean | spec.deployment.cicd.tests | true | Run unit tests |
| `deployment.cicd.tests.integration` | boolean | spec.deployment.cicd.tests | true | Run integration tests |
| `deployment.cicd.tests.e2e` | boolean | spec.deployment.cicd.tests | false | Run e2e tests |
| `deployment.cicd.tests.load` | boolean | spec.deployment.cicd.tests | false | Run load tests |

### Deploy-Time Configs (GitHub Secrets / Variables)

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `AZURE_CREDENTIALS` | json | GitHub Secret | {...} | Service principal JSON |
| `AZURE_SUBSCRIPTION_ID` | string | GitHub Secret | "guid" | Subscription ID |
| `ACR_USERNAME` | string | GitHub Secret | "acr" | Registry username |
| `ACR_PASSWORD` | string | GitHub Secret | "pwd" | Registry password |
| `ACR_LOGIN_SERVER` | string | GitHub Variable | "acr.azurecr.io" | Registry URL |
| `RESOURCE_GROUP_DEV` | string | GitHub Variable | "rg-dev" | Dev RG |
| `RESOURCE_GROUP_STAGING` | string | GitHub Variable | "rg-staging" | Staging RG |
| `RESOURCE_GROUP_PROD` | string | GitHub Variable | "rg-prod" | Prod RG |
| `SMOKE_TEST_URL_DEV` | string | GitHub Variable | "https://..." | Dev smoke test |
| `HEALTH_CHECK_ENDPOINT` | string | GitHub Variable | "/health" | Health check path |

### Runtime Configs

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `ENABLE_AUTO_DEPLOY` | boolean | GitHub Actions | (build) | Toggle auto-deploy |
| `APPROVAL_TIMEOUT_MINUTES` | int | GitHub Actions | 60 | Approval wait time |
| `DEPLOYMENT_SCHEDULE` | cron | GitHub Actions | null | Scheduled deployments |
| `ROLLBACK_ON_FAILURE` | boolean | GitHub Actions | true | Auto-rollback |
| `ALERT_ON_FAILURE` | boolean | GitHub Actions | true | Send alerts |

---

## 11. DEPLOYMENT SCRIPTS

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `deployment.targets` | string[] | spec.deployment.targets | required | Deployment targets |
| `deployment.environments` | object | spec.deployment.environments | required | Environment configs |

### Deploy-Time Configs (Script Parameters)

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `ENVIRONMENT` | enum | CLI arg | "dev" | dev\|staging\|prod |
| `SUBSCRIPTION_ID` | string | Env var / arg | "guid" | Azure subscription |
| `RESOURCE_GROUP` | string | Env var / arg | "rg-name" | Target RG |
| `LOCATION` | string | parameters file | "eastus" | Azure region |
| `DEPLOYMENT_NAME` | string | Generated | "deploy-20250101..." | Deployment name |
| `PARAMETER_FILE` | string | Derived | "parameters.dev.json" | Parameter file path |
| `BICEP_FILE` | string | Fixed | "infra/main.bicep" | Main Bicep file |
| `TERRAFORM_STATE_URL` | string | Env var | "https://..." | State backend (if TF) |

### Runtime Configs (Script Flags)

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `DRY_RUN` | boolean | CLI flag | false | Validate only |
| `FORCE` | boolean | CLI flag | false | Skip confirmations |
| `COMPONENT` | string | CLI flag | null | Deploy specific component |
| `SKIP_PREFLIGHT` | boolean | CLI flag | false | Skip validation |
| `HEALTH_CHECK_INTERVAL` | int | CLI flag | 30 | Seconds between checks |
| `HEALTH_CHECK_RETRIES` | int | CLI flag | 10 | Max health check attempts |
| `VERBOSE` | boolean | CLI flag | false | Verbose output |

---

## 12. TESTS

### Build-Time Configs

| Config Key | Type | Source | Default | Usage |
|------------|------|--------|---------|-------|
| `deployment.cicd.tests.unit` | boolean | spec.deployment.cicd.tests | true | Generate unit tests |
| `deployment.cicd.tests.integration` | boolean | spec.deployment.cicd.tests | true | Generate integration tests |
| `deployment.cicd.tests.e2e` | boolean | spec.deployment.cicd.tests | false | Generate e2e tests |
| `deployment.cicd.tests.load` | boolean | spec.deployment.cicd.tests | false | Generate load tests |
| `tests.framework` | enum | generator default | "pytest" | pytest\|unittest |
| `tests.coverage_threshold` | int | generator default | 80 | Min code coverage % |

### Deploy-Time Configs (Test Environment)

| Config Key | Type | Where Set | Example | Usage |
|------------|------|-----------|---------|-------|
| `TEST_DATABASE_CONNECTION` | string | .env.test | "mongodb://..." | Test DB |
| `TEST_COSMOS_ENDPOINT` | string | .env.test | "https://localhost:8081" | Cosmos emulator |
| `TEST_REDIS_HOST` | string | .env.test | "localhost" | Redis emulator |
| `TEST_SIGNALR_ENDPOINT` | string | .env.test | "http://localhost:5000" | SignalR test |
| `TEST_KEYVAULT_URL` | string | .env.test | "(mock)" | Mock Key Vault |
| `TEST_IDENTITY_CLIENT_ID` | string | .env.test | "(mock)" | Mock identity |
| `DOCKER_COMPOSE_FILE` | string | Fixed | "tests/docker-compose.yml" | Emulators config |

### Runtime Configs (Test Execution)

| Config Key | Type | Where Set | Default | Usage |
|------------|------|-----------|---------|-------|
| `PYTEST_MARKERS` | string | CLI | null | Test markers to run |
| `PYTEST_PARALLEL` | boolean | CLI | false | Parallel execution |
| `PYTEST_TIMEOUT` | int | CLI | 300 | Test timeout (seconds) |
| `PYTEST_RETRIES` | int | CLI | 0 | Retry flaky tests |
| `PYTEST_VERBOSE` | boolean | CLI | false | Verbose output |
| `COVERAGE_HTML` | boolean | CLI | false | Generate HTML report |
| `LOAD_TEST_DURATION` | int | CLI | 60 | Load test duration (sec) |
| `LOAD_TEST_USERS` | int | CLI | 10 | Concurrent users |
| `LOAD_TEST_RAMP_UP` | int | CLI | 10 | Ramp-up time (sec) |

---

## Configuration File Templates

Each generator should produce these configuration files:

### 1. infra/parameters.dev.json
```json
{
  "resourceGroupName": "rg-goalgen-dev",
  "location": "eastus",
  "orchestratorImage": "acr.azurecr.io/goalgen/orchestrator:latest",
  "orchestratorCpu": 0.5,
  "orchestratorMemory": "1Gi",
  "orchestratorMinReplicas": 1,
  "orchestratorMaxReplicas": 3,
  "cosmosAccountName": "cosmos-goalgen-dev",
  "cosmosThroughput": 400,
  "redisName": "redis-goalgen-dev",
  "redisSku": "Basic",
  "redisCapacity": 1,
  "keyVaultName": "kv-goalgen-dev",
  "signalRName": "signalr-goalgen-dev",
  "signalRSku": "Free_F1"
}
```

### 2. orchestrator/.env.sample
```bash
# Build-time defaults
GOAL_ID=travel_planning
MAX_ITERATIONS=20

# Deploy-time configs (from Bicep outputs)
KEYVAULT_URL=https://kv-goalgen-dev.vault.azure.net/
COSMOS_ENDPOINT=https://cosmos-goalgen-dev.documents.azure.com:443/
REDIS_HOST=redis-goalgen-dev.redis.cache.windows.net
REDIS_PORT=6380
SIGNALR_CONNECTION_STRING=<from-keyvault>

# Runtime configs
LOG_LEVEL=INFO
MAX_RETRIES=3
REQUEST_TIMEOUT=30
ENABLE_DEBUG_ENDPOINTS=false
```

### 3. orchestrator/app/config.py
```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Build-time
    goal_id: str
    max_iterations: int = 20

    # Deploy-time
    keyvault_url: str
    cosmos_endpoint: str
    redis_host: str
    redis_port: int = 6380

    # Runtime
    log_level: str = "INFO"
    max_retries: int = 3
    request_timeout: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False
```

### 4. config/scaling-rules.json
```json
{
  "orchestrator": {
    "rules": [
      {
        "name": "cpu-rule",
        "type": "cpu",
        "metadata": {
          "type": "Utilization",
          "value": "70"
        }
      },
      {
        "name": "http-rule",
        "type": "http",
        "metadata": {
          "concurrentRequests": "100"
        }
      }
    ]
  }
}
```
