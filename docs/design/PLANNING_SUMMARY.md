# GoalGen Planning Summary

Comprehensive summary of the planning phase for the GoalGen project.

---

## Planning Phase Complete ✅

We have completed a comprehensive planning phase covering all aspects of the GoalGen code generator system.

---

## Documentation Created

### 1. CLAUDE.md (Main Documentation)
**Lines**: 490+
**Purpose**: Primary reference for Claude Code instances working with GoalGen
**Contains**:
- Project overview and architecture
- Running GoalGen commands
- 14 generator module descriptions
- Generated project structure (complete directory tree)
- Runtime architecture (request flow)
- Goal spec schema overview
- Key concepts (goals, supervisor, checkpointing, tool binding)
- Template architecture
- Generator → Output mapping table
- Technology stack quick reference
- Configuration management overview

### 2. CONFIGURATION_MATRIX.md
**Lines**: 350+
**Purpose**: Configuration requirements across build/deploy/runtime stages
**Contains**:
- 12 component configurations detailed
- Build-time configs (developer choices)
- Deploy-time configs (infrastructure parameters)
- Runtime configs (operational changes)
- Configuration management strategy
- Configuration precedence rules
- Generated configuration files list

### 3. COMPONENT_CONFIG_INVENTORY.md
**Lines**: 700+
**Purpose**: Complete inventory of all configuration parameters
**Contains**:
- **296 total configuration parameters** across all components
- Detailed tables for each component
- Config key, type, source, default, usage for each parameter
- Configuration file templates (parameters.json, .env.sample, config.py, scaling-rules.json)
- Per-component breakdown (Orchestrator: 42 configs, LangGraph: 28 configs, etc.)

### 4. CONFIG_SPEC_SCHEMA.md
**Lines**: 300+
**Purpose**: Enhanced goal spec JSON schema with all configuration options
**Contains**:
- Complete goal spec structure
- All sections documented (identity, triggers, context, tasks, agents, tools, evaluators, UX, assets, langgraph, deployment, runtime_config)
- Configuration extraction guide (which generator reads which spec sections)
- Generated configuration files per generator
- Validation requirements

### 5. FRAMEWORK_CHOICES.md
**Lines**: 900+
**Purpose**: Technology stack decisions for all components
**Contains**:
- 13 components with framework choices
- Dependencies tables with versions
- Alternative frameworks considered
- Pros/cons comparisons
- Testing stacks per component
- Build & package tools
- Key design decisions
- Version pinning strategy

### 6. EVALUATOR_FRAMEWORK_OPTIONS.md
**Lines**: 650+
**Purpose**: Comprehensive analysis of validation and rules engine options
**Contains**:
- 6 categories of options (schema validation, JSON schema, rules engines, expression evaluation, data quality, custom approaches)
- 15+ framework options analyzed
- Recommended hybrid approach (Pydantic + Custom Evaluators + business-rules)
- 7 evaluator types defined
- Architecture patterns with code examples
- Detailed pros/cons for each option

### 7. TESTING_FRAMEWORKS.md
**Lines**: 1000+
**Purpose**: Testing strategies and frameworks for all components
**Contains**:
- Testing pyramid strategy
- 12 components with testing approaches
- Unit, integration, E2E, load, security testing per component
- Framework choices with examples
- Testing dependencies
- Mocking strategies
- Test organization best practices
- CI integration examples
- Coverage tools and thresholds

### 8. MULTI_AGENT_PATTERNS.md
**Lines**: 1000+
**Purpose**: Documentation of 10 multi-agent patterns for LangGraph
**Contains**:
- 10 patterns: Sequential, Router, Supervisor, Collaborative, Map-Reduce, Human-in-Loop, Recursive, Ensemble, Reflection, Plan-Execute
- Complete LangGraph implementations for each pattern
- Goal spec configuration examples
- Topology diagrams and flow descriptions
- Use cases and advantages/disadvantages per pattern
- Code examples with StateGraph definitions

### 9. TOPOLOGY_INFERENCE.md
**Lines**: 720+
**Purpose**: Analysis of explicit vs inferred topology declaration
**Contains**:
- Option A: Explicit topology declaration (pros/cons)
- Option B: Inferred topology from patterns (pros/cons)
- Option C: Hybrid approach (RECOMMENDED)
- Inference algorithm with detection rules
- Validation rules for topology-spec alignment
- Complete code examples for inference logic
- Decision: Default to inference, allow explicit override

### 10. STATE_MANAGEMENT_DESIGN.md
**Lines**: 800+
**Purpose**: Explicit state management design (never inferred)
**Contains**:
- 5 layers: State Schema, Checkpointing Backend, Thread Management, Serialization, Checkpoint Strategy
- Why state management must be EXPLICIT (production reliability, performance, cost, compliance)
- Complete implementations: Cosmos DB, Redis, Blob, PostgreSQL, SQLite checkpointers
- Thread manager with ID generation patterns
- Session store integration
- spec.state_management schema definition
- Testing strategies for state management

### 11. API_VERSIONING_DESIGN.md
**Lines**: 1000+
**Purpose**: OpenAPI compliance and explicit API versioning
**Contains**:
- URL path versioning strategy (RECOMMENDED)
- Complete OpenAPI 3.1 specification
- Versioned FastAPI routers (v1, v2, etc.)
- Pydantic request/response schemas with validation
- API evolution strategy with deprecation headers
- Breaking vs non-breaking changes guidelines
- Complete code examples for all endpoints
- Testing strategy for API version compatibility

### 12. AUTHENTICATION_AUTHORIZATION_DESIGN.md
**Lines**: 1100+
**Purpose**: Dual identity model for backend and frontend authentication
**Contains**:
- Backend: Managed Identity (Service Principal) architecture
- Frontend: Microsoft Entra ID + RBAC per goal
- Complete Bicep RBAC role assignments
- FastAPI token validation and permission enforcement
- Teams SSO integration
- Webchat MSAL.js authentication flow
- Goal spec authentication section
- Testing strategies for auth/authz

### 13. PLANNING_SUMMARY.md
**Lines**: 690+
**Purpose**: Comprehensive overview of planning phase
**Contains**:
- Summary of all planning documentation
- Key achievements and decisions
- Architecture summary with all 14 generators
- Technology stack details
- Configuration summary (3-stage model)
- Testing strategy overview
- Implementation checklist and estimated effort
- Success criteria and risk mitigation
- Critical design decisions with rationale

---

## Key Achievements

### ✅ Complete Architecture Definition
- 14 generator modules designed
- Request flow documented
- Generated project structure defined
- Runtime architecture explained

### ✅ Configuration Management Designed
- **296 configuration parameters** identified across all components
- Three-stage configuration model (build/deploy/runtime)
- Configuration precedence defined
- Configuration files specified

### ✅ Technology Stack Finalized
- **Backend**: Python 3.11+, FastAPI, LangChain/LangGraph
- **Frontend**: TypeScript 5.2+, React 18, Vite 5
- **Infrastructure**: Bicep, Azure Container Apps, Azure Functions
- **Testing**: pytest, Vitest, Playwright, Locust
- **Code Gen**: Python 3.11+, Jinja2

### ✅ Testing Strategy Established
- Testing pyramid defined (70% unit, 20% integration, 10% E2E)
- Frameworks selected per component
- Mocking strategies defined
- CI/CD integration planned

### ✅ Evaluator Design Completed
- Hybrid approach: Pydantic + Custom Classes + business-rules
- 7 evaluator types defined
- 15+ validation frameworks evaluated
- Architecture pattern established

### ✅ Multi-Agent Patterns Documented
- 10 LangGraph topologies analyzed
- Complete implementations for each pattern
- Goal spec integration for all patterns
- Use case guidance established

### ✅ Topology Strategy Decided
- Hybrid approach: infer with explicit override
- Inference rules for common patterns (sequential, supervisor, router)
- Explicit declaration for complex patterns (ensemble, plan-execute, recursive)
- Validation to ensure topology-spec alignment

### ✅ State Management Architecture Finalized
- Explicit declaration (never inferred) for production reliability
- 5-layer design: Schema, Checkpointing, Threads, Serialization, Strategy
- Multiple backend implementations (Cosmos, Redis, Blob, PostgreSQL, SQLite)
- Thread persistence with configurable serialization

### ✅ API Design Standardized
- OpenAPI 3.1 compliance required
- URL path versioning strategy
- Explicit version evolution with deprecation
- Pydantic schemas with validation

### ✅ Authentication & Authorization Architecture Defined
- Backend: Managed Identity (Service Principal) for Azure resource access
- Frontend: Microsoft Entra ID for user authentication
- RBAC: Custom roles per goal with permission enforcement
- Zero-trust: Separate identity planes for services and users
- Complete Bicep RBAC assignments and FastAPI validation

---

## Architecture Summary

### 14 Generator Modules

1. **scaffold** - Repository skeleton (README, LICENSE, .gitignore, directory structure)
2. **langgraph** - Quest builder with state machine, nodes, checkpointer
3. **api** - FastAPI orchestrator with /message endpoint
4. **teams** - Microsoft Teams Bot (manifest, adaptive cards, deploy script)
5. **webchat** - React/Vite SPA with SignalR
6. **tools** - Azure Function wrappers per tool
7. **agents** - Agent implementation stubs per spec
8. **evaluators** - Validation logic and test cases
9. **infra** - Bicep modules (Container Apps, Functions, Cosmos, Redis, Key Vault, SignalR)
10. **security** - Key Vault, Managed Identity configs
11. **assets** - Prompts, images, templates
12. **cicd** - GitHub Actions workflow
13. **deployment** - Deploy scripts (deploy.sh, destroy.sh, local_run.sh)
14. **tests** - pytest config, unit/integration stubs, docker-compose

### Generated Project Structure

```
{goal_id}/
├── README.md, LICENSE, .gitignore
├── orchestrator/          # FastAPI Bot Orchestrator
│   ├── Dockerfile, requirements.txt
│   ├── app/              # main.py, orchestrator.py, session_store.py, secure_config.py
│   └── tests/
├── langgraph/            # LangGraph workflow
│   ├── quest_builder.py
│   ├── agents/           # Per-agent implementations
│   ├── evaluators/       # Validation logic
│   └── checkpointer_adapter.py
├── teams_app/            # Microsoft Teams Bot
│   ├── manifest.json
│   ├── adaptive_cards/
│   └── deploy_team.sh
├── webchat/              # React SPA
│   ├── package.json, vite.config.js
│   └── src/              # App.tsx, signalr-client.ts
├── tools/                # Tool implementations
│   └── {tool_name}/      # function_app/ or http_wrapper
├── infra/                # Bicep infrastructure
│   ├── main.bicep
│   ├── modules/          # Per-service Bicep files
│   └── parameters.{env}.json
├── prompts/              # Prompt templates
├── assets/               # Images, logos
├── ci/                   # GitHub Actions workflow
├── scripts/              # Deployment scripts
└── tests/                # Test infrastructure
    ├── pytest.ini, unit/, integration/, e2e/
    └── docker-compose.yml
```

### Runtime Architecture

```
User (Teams/Webchat)
    ↓
FastAPI /message endpoint
    ↓
LangGraph Quest Builder
    ├── Load state from checkpointer (Cosmos/Redis)
    ├── Supervisor routes to agents/evaluators
    ├── Agents invoke LLMs + Tools
    ├── Evaluators validate context
    └── Save state to checkpointer
    ↓
Response via SignalR
    ↓
User receives message
```

---

## Technology Stack Details

### Backend Stack
```python
# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0

# LLM & Orchestration
langgraph>=0.0.35
langchain>=0.1.0
langchain-openai>=0.0.5

# Azure SDKs
azure-identity>=1.14.0
azure-keyvault-secrets>=4.7.0
azure-cosmos>=4.5.0
redis[asyncio]>=5.0.0

# Utilities
httpx>=0.25.0
structlog>=23.2.0
tenacity>=8.2.0
```

### Frontend Stack
```json
{
  "react": "^18.2.0",
  "typescript": "^5.2.0",
  "vite": "^5.0.0",
  "@microsoft/signalr": "^8.0.0",
  "zustand": "^4.4.0",
  "tailwindcss": "^3.3.0",
  "axios": "^1.6.0",
  "react-markdown": "^9.0.0"
}
```

### Testing Stack
```python
# Backend Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
pytest-cov>=4.1.0
respx>=0.20.0
hypothesis>=6.90.0
locust>=2.17.0

# Frontend Testing
vitest>=1.0.0
@testing-library/react>=14.1.0
@playwright/test>=1.40.0
```

### Infrastructure
```bash
# IaC
bicep>=0.23.0
az-cli>=2.54.0

# Containers
docker>=24.0.0

# CI/CD
github-actions
azure-container-registry
```

---

## Configuration Summary

### Three-Stage Configuration Model

**Build Time** → Spec JSON + Generator Defaults
- Token limits, graph structure, agent types
- Task definitions, evaluator rules
- UI framework choices

**Deploy Time** → parameters.{env}.json + Bicep
- Resource names, URLs, regions
- CPU/memory allocations
- Initial scaling parameters

**Runtime** → Azure App Config / Key Vault / Env Vars
- Scaling rules, feature flags
- Model selection, temperatures
- Rate limits, timeouts

### Configuration Precedence
```
Runtime Override > Deploy Time > Build Time (Spec) > Generator Defaults
```

### Key Configuration Files Generated
- `infra/parameters.dev.json` - Dev environment Bicep parameters
- `infra/parameters.staging.json` - Staging environment
- `infra/parameters.prod.json` - Production environment
- `orchestrator/.env.sample` - Local development template
- `orchestrator/app/config.py` - Application config loader (Pydantic)
- `config/scaling-rules.json` - Container Apps autoscaling

---

## Testing Strategy

### Testing Pyramid

| Level | % | Speed | Frameworks |
|-------|---|-------|------------|
| Unit | 70% | <1s | pytest, vitest |
| Integration | 20% | 1-10s | pytest + Docker Compose |
| E2E | 10% | 10s-1m | Playwright |

### Testing Coverage by Component

| Component | Unit | Integration | E2E | Load |
|-----------|------|-------------|-----|------|
| Orchestrator | pytest + FastAPI TestClient | Docker Compose | Playwright | Locust |
| LangGraph | pytest + mocks | Real checkpointer | - | - |
| Agents | pytest + respx | VCR cassettes | - | - |
| Evaluators | pytest + hypothesis | - | - | - |
| Tools | pytest + respx | VCR cassettes | - | - |
| Webchat | Vitest + Testing Library | - | Playwright | - |
| Infra | Bicep lint + PSRule | What-if | pytest + Azure SDK | - |

### Code Coverage Thresholds
- **Backend**: 80% minimum
- **Frontend**: 80% minimum
- **Critical paths**: 95% minimum

---

## Next Steps: Implementation Phase

### Phase 1: Foundation (Tasks 7-8)
✅ **Completed**: Planning and architecture
🔄 **Next**:
1. Set up Jinja2 template infrastructure
2. Create comprehensive `travel_planning.json` example spec

### Phase 2: Core Generators (Tasks 9-14)
Implement generators in priority order:
1. **scaffold** - Directory structure, base files
2. **langgraph** - Quest builder with nodes
3. **agents** - Agent stubs
4. **evaluators** - Validation logic
5. **tools** - Azure Function wrappers
6. **api** - FastAPI orchestrator

### Phase 3: Infrastructure (Tasks 15-16)
7. **infra** - Bicep modules
8. **security** - Key Vault, Managed Identity

### Phase 4: UX (Tasks 17-18)
9. **teams** - Bot manifest, adaptive cards
10. **webchat** - React SPA

### Phase 5: Supporting (Tasks 19-22)
11. **assets** - Prompts, images
12. **cicd** - GitHub Actions
13. **deployment** - Deploy scripts
14. **tests** - Test infrastructure

### Phase 6: Validation & Testing (Tasks 23-25)
15. Spec validation (JSON schema)
16. Full test with travel_planning.json
17. Documentation for generated output

---

## Implementation Checklist

### Prerequisites
- [ ] Install Python 3.11+
- [ ] Install Node.js 18+
- [ ] Install Azure CLI
- [ ] Install Bicep CLI
- [ ] Install Docker

### Template Setup
- [ ] Create `templates/` directory structure
- [ ] Set up Jinja2 environment
- [ ] Create base templates for each generator
- [ ] Set up template testing

### Generator Implementation
- [ ] scaffold generator
- [ ] langgraph generator
- [ ] api generator
- [ ] teams generator
- [ ] webchat generator
- [ ] tools generator
- [ ] agents generator
- [ ] evaluators generator
- [ ] infra generator
- [ ] security generator
- [ ] assets generator
- [ ] cicd generator
- [ ] deployment generator
- [ ] tests generator

### Validation & Testing
- [ ] JSON schema validation for goal specs
- [ ] Unit tests for each generator
- [ ] Integration test: full generation
- [ ] Golden file tests
- [ ] Documentation generation

---

## Estimated Effort

### Generator Implementation Complexity

| Generator | Complexity | Est. Days | Templates |
|-----------|------------|-----------|-----------|
| scaffold | Low | 1 | 5 |
| langgraph | High | 3-4 | 8 |
| api | Medium | 2 | 6 |
| agents | Medium | 2 | 5 |
| evaluators | Medium | 2 | 4 |
| tools | Medium | 2 | 6 |
| infra | High | 3 | 10 |
| security | Medium | 1-2 | 3 |
| teams | Medium | 2 | 5 |
| webchat | Medium | 2-3 | 8 |
| assets | Low | 1 | 4 |
| cicd | Medium | 1-2 | 2 |
| deployment | Low | 1 | 3 |
| tests | Medium | 2 | 6 |

**Total Estimated**: 25-30 development days

### Breakdown
- **Foundation & Setup**: 2 days
- **Core Generators (6)**: 13-15 days
- **Infrastructure (2)**: 4-5 days
- **UX (2)**: 4-5 days
- **Supporting (4)**: 5-6 days
- **Testing & Validation**: 3 days

---

## Success Criteria

### For GoalGen Tool
- ✅ All 14 generators implemented
- ✅ Templates for all components
- ✅ Spec validation working
- ✅ Unit tests for generators (80%+ coverage)
- ✅ Integration test: generate complete project
- ✅ Documentation complete

### For Generated Projects
- ✅ Project structure matches specification
- ✅ All configuration files generated correctly
- ✅ Code compiles/runs without errors
- ✅ Tests pass (unit, integration)
- ✅ Bicep validates and deploys successfully
- ✅ Docker containers build successfully
- ✅ CI/CD pipeline runs end-to-end

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LangGraph API changes** | High | Pin versions, test with specific releases |
| **Azure SDK compatibility** | Medium | Use stable SDK versions, test deployments |
| **Template complexity** | Medium | Start simple, iterate, extensive testing |
| **Bicep generation errors** | High | Validate with what-if, test deployments |
| **Cross-platform issues** | Medium | Test on Linux, macOS, Windows |

### Process Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Scope creep** | Medium | Stick to defined 14 generators, defer enhancements |
| **Template maintenance** | Medium | Clear documentation, version control |
| **Testing gaps** | High | Comprehensive test strategy, golden files |

---

## Documentation Deliverables

### Planning Phase (Complete) ✅
1. ✅ CLAUDE.md - Main documentation (490 lines)
2. ✅ CONFIGURATION_MATRIX.md - Config requirements (350 lines)
3. ✅ COMPONENT_CONFIG_INVENTORY.md - Complete config inventory (700 lines)
4. ✅ CONFIG_SPEC_SCHEMA.md - Enhanced spec schema (300 lines)
5. ✅ FRAMEWORK_CHOICES.md - Technology decisions (900 lines)
6. ✅ EVALUATOR_FRAMEWORK_OPTIONS.md - Evaluator analysis (650 lines)
7. ✅ TESTING_FRAMEWORKS.md - Testing strategies (1000 lines)
8. ✅ MULTI_AGENT_PATTERNS.md - LangGraph topologies (1000 lines)
9. ✅ TOPOLOGY_INFERENCE.md - Explicit vs inferred analysis (720 lines)
10. ✅ STATE_MANAGEMENT_DESIGN.md - Explicit state architecture (800 lines)
11. ✅ API_VERSIONING_DESIGN.md - OpenAPI & versioning (1000 lines)
12. ✅ AUTHENTICATION_AUTHORIZATION_DESIGN.md - Dual identity model (1100 lines)
13. ✅ PLANNING_SUMMARY.md - This document (690 lines)

**Total Planning Documentation**: ~9,700 lines

### Implementation Phase (Pending)
1. Template documentation (per generator)
2. Generator implementation guides
3. Testing documentation
4. Deployment guides
5. Troubleshooting guides

---

## Key Design Decisions

Throughout the planning phase, several critical design decisions were made:

### 1. Topology: Hybrid Approach ✅
**Decision**: Default to inference, allow explicit override
**Rationale**: Balance simplicity for common cases with control for advanced patterns
- **Simple patterns** (sequential, supervisor, router) → Auto-inferred from task structure
- **Complex patterns** (ensemble, plan-execute, recursive) → Require explicit declaration
- **Override capability** → Always honor explicit `topology.type` field

### 2. State Management: Explicit Only ✅
**Decision**: State management must ALWAYS be explicitly declared (never inferred)
**Rationale**: Production-critical with significant implications
- **Reliability**: Different backends have different guarantees
- **Performance**: Cosmos vs Redis vs SQLite have vastly different latency
- **Cost**: Pricing varies significantly across backends
- **Compliance**: Data residency and retention requirements
- **Recovery**: Backup and restore strategies differ

### 3. API Versioning: OpenAPI + URL Path ✅
**Decision**: URL path versioning with OpenAPI 3.1 compliance
**Rationale**: Industry standard, explicit, predictable
- **URL pattern**: `/api/v{major}.{minor}/goal/{goal_id}/endpoint`
- **OpenAPI spec**: Auto-generated from Pydantic schemas
- **Deprecation**: Sunset headers with clear migration path
- **Evolution**: Semantic versioning with backward compatibility guarantees

### 4. Configuration: Three-Stage Model ✅
**Decision**: Build → Deploy → Runtime with clear precedence
**Rationale**: Separation of concerns across lifecycle
- **Build**: Developer choices baked into code
- **Deploy**: Infrastructure parameters in Bicep
- **Runtime**: Operational overrides via App Config/Key Vault

### 5. Evaluators: Hybrid Framework ✅
**Decision**: Pydantic + Custom Classes + business-rules
**Rationale**: Leverage strengths of multiple approaches
- **Pydantic**: Fast schema validation
- **Custom Classes**: Complex business logic
- **business-rules**: Declarative rules engine

### 6. Authentication: Dual Identity Model ✅
**Decision**: Managed Identity for backend, Entra ID + RBAC for frontend
**Rationale**: Separate identity planes for zero-trust architecture
- **Backend Services**: Managed Identity (Service Principal) for Azure resource access
- **Frontend Users**: Microsoft Entra ID authentication + custom RBAC per goal
- **Security**: No credentials in code, least-privilege RBAC, user context auditing
- **Integration**: Teams SSO, Webchat MSAL.js, FastAPI token validation

---

## Conclusion

The planning phase is **complete** with comprehensive documentation covering:

- ✅ **Architecture**: 14 generators, runtime flow, generated structure
- ✅ **Configuration**: 296 parameters across 12 components, 3-stage model
- ✅ **Technology**: Complete stack (backend, frontend, infra, testing)
- ✅ **Testing**: Strategies for unit, integration, E2E, load, security
- ✅ **Evaluators**: Hybrid approach with multiple framework options
- ✅ **Multi-Agent Patterns**: 10 LangGraph topologies documented
- ✅ **Topology Strategy**: Hybrid inference with explicit override
- ✅ **State Management**: Explicit 5-layer architecture
- ✅ **API Design**: OpenAPI 3.1 with URL path versioning
- ✅ **Authentication & Authorization**: Dual identity model with zero-trust

### Documentation Stats
- **13 planning documents** created
- **~9,700 lines** of comprehensive documentation
- **6 critical design decisions** documented with rationale
- **296 configuration parameters** inventoried
- **10 multi-agent patterns** analyzed and implemented
- **14 generator modules** designed
- **Dual identity model**: Backend (Managed Identity) + Frontend (Entra ID + RBAC)

We are now ready to proceed to the **implementation phase**, starting with:
1. Template infrastructure setup (Jinja2)
2. Example goal spec creation (travel_planning.json)
3. Generator implementation (scaffold → langgraph → api → ...)

The foundation is solid, well-documented, and ready for execution.
