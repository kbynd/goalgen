# GoalGen

**Code generator for multi-agent conversational AI systems**

GoalGen scaffolds complete, production-ready projects using LangGraph for workflow orchestration and Azure services for deployment. Define your conversational goals in JSON, generate enterprise-grade infrastructure and code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- 🤖 **Multi-Agent Orchestration** - LangGraph-based workflows with supervisor patterns
- 💾 **Persistent Conversations** - Cross-device resume with Cosmos DB/Redis checkpointing
- 🔄 **Schema Versioning** - Safe state evolution with automatic migrations
- 🔧 **Common Tools** - Built-in SQL, Vector DB, HTTP, and custom tool support
- 🏗️ **Infrastructure as Code** - Azure Bicep templates for complete deployments
- 🧪 **Testing Built-in** - Generated test suites for migrations and workflows
- 📊 **Production Ready** - AI Foundry integration, monitoring, RBAC, secrets management

## What's New in v0.2.0-beta

### Teams Bot Generator
- ✨ **Versioned Adaptive Cards** - Auto-detects channel (v1.2 for Emulator, v1.4 for Teams)
- 🔧 **Configurable API Timeout** - Support for slow local LLMs via `LANGGRAPH_API_TIMEOUT`
- 🖥️ **Local Development Server** - Test Teams Bots with Bot Framework Emulator
- 📱 **Channel Detection** - Automatic template selection based on conversation context

### Runtime & Deployment
- 🐳 **Cloud Build Support** - New `Dockerfile-cloud.j2` for ACR and GitHub Actions
- 🔌 **OpenAI-Compatible Endpoints** - Use Ollama, llama.cpp via `OPENAI_API_BASE`
- 🏗️ **Build Context Scripts** - `prepare_build_context.sh` for streamlined deployments
- ✅ **Runtime Gap Fixes** - All E2E runtime gaps resolved (Gap #9-12)

### Documentation & Community
- 📚 **CONTRIBUTING.md** - Open source contribution guidelines
- 📝 **CHANGELOG.md** - Complete version history
- 🐛 **GitHub Issue Templates** - Bug reports, feature requests, questions
- 🚀 **Production Ready** - Tested end-to-end with both cloud and local LLMs

See [CHANGELOG.md](CHANGELOG.md) for full release notes.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/kbynd/goalgen.git
cd goalgen

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Generate Your First Project

```bash
# Generate a travel planning assistant
./goalgen.py --spec examples/travel_planning.json --out ./my_travel_agent

# See what was generated
cd my_travel_agent
ls -la
```

**Generated structure:**
```
my_travel_agent/
├── langgraph/           # LangGraph workflow with agents
├── orchestrator/        # FastAPI bot orchestrator
├── infra/              # Azure Bicep infrastructure
├── scripts/            # Deployment scripts
├── tests/              # Test suite
└── README.md           # Project-specific docs
```

### Deploy to Azure

```bash
cd my_travel_agent

# Set up Azure resources
./scripts/deploy.sh

# Test locally first
python -m pytest tests/
```

## Example Goal Spec

Define your conversational AI system in JSON:

```json
{
  "id": "travel_planning",
  "title": "Travel Planning Assistant",
  "version": "1.0.0",

  "agents": {
    "supervisor_agent": {
      "kind": "supervisor",
      "policy": "simple_router",
      "llm_config": {"model": "gpt-4"}
    },
    "flight_agent": {
      "kind": "llm_agent",
      "tools": ["flight_api"],
      "llm_config": {"model": "gpt-4"}
    }
  },

  "tools": {
    "flight_api": {
      "type": "http",
      "spec": {
        "url": "${FLIGHT_API_URL}/search",
        "method": "POST"
      }
    }
  },

  "state_management": {
    "checkpointing": {"backend": "cosmos"},
    "state": {
      "schema": {
        "context_fields": ["destination", "dates", "budget"]
      }
    }
  }
}
```

Run `goalgen.py` and get a complete, deployable project.

## What Gets Generated

### LangGraph Workflow

- **State schema** - TypedDict with your context fields
- **Agent implementations** - Supervisor, LLM agents, evaluators
- **Checkpointing** - Cosmos DB/Redis integration
- **Schema migrations** - Version tracking and automatic upgrades

### Azure Infrastructure

- **Bicep templates** - Container Apps, Functions, Cosmos DB, Key Vault
- **RBAC** - Managed Identity assignments
- **Networking** - VNets, private endpoints (optional)
- **Monitoring** - Application Insights integration

### API & UX

- **FastAPI orchestrator** - `/message` endpoint with auth
- **Teams Bot** - Manifest, adaptive cards, local dev server
- **Webchat SPA** - React/SignalR interface (coming soon)

### DevOps

- **GitHub Actions** - Complete CI/CD pipeline
- **Deploy scripts** - `build.sh`, `deploy.sh`, `destroy.sh`
- **Testing** - pytest suite with migration tests

## Advanced Features

### Schema Versioning

Add fields safely without breaking existing conversations:

```json
{
  "schema_version": 2,
  "schema_migrations": {
    "1_to_2": {
      "description": "Added budget field",
      "migration": "set_default",
      "added_fields": ["budget"],
      "default_values": {"budget": null}
    }
  }
}
```

GoalGen generates:
- Migration functions
- Automatic upgrading on conversation resume
- Batch migration scripts
- Complete test suite

See [SCHEMA_VERSIONING.md](SCHEMA_VERSIONING.md) for details.

### Incremental Generation (NEW in v0.1.0)

Add new agents/tools without regenerating everything:

```bash
# Initial generation
./goalgen.py --spec v1_spec.json --out ./my_project

# Customize agents
vim my_project/langgraph/agents/flight_agent.py

# Add hotel_agent to spec
vim v2_spec.json

# Incremental update - preserves your changes
./goalgen.py --spec v2_spec.json --out ./my_project --incremental
```

**Output:**
```
[goalgen] Incremental mode - analyzing changes...
[goalgen]   New agents: hotel_agent
[goalgen]   New tools: hotel_api
Running generator: agents
[agents] ✓ Generated hotel_agent.py
[agents] ✓ Preserved flight_agent.py (user modified)
```

GoalGen tracks what was generated in `.goalgen/manifest.json` and detects:
- What changed in your spec
- Which files you modified
- What needs to be regenerated

See [INCREMENTAL_GENERATION.md](INCREMENTAL_GENERATION.md) for details.

### Common Tools

Built-in tool implementations:

```json
{
  "tools": {
    "customer_db": {
      "type": "sql",
      "spec": {
        "connection_string": "${DB_CONNECTION}",
        "database_type": "postgresql",
        "read_only": true
      }
    },
    "knowledge_base": {
      "type": "vectordb",
      "spec": {
        "provider": "azure_ai_search",
        "index_name": "docs",
        "top_k": 5
      }
    }
  }
}
```

Supports:
- **SQL**: Azure SQL, PostgreSQL, MySQL, SQLite
- **Vector DBs**: Azure AI Search, Pinecone, Weaviate, Qdrant, Chroma
- **HTTP**: REST APIs with auth and retry
- **Functions**: Custom Python functions

See [COMMON_TOOLS.md](COMMON_TOOLS.md) for full reference.

## Selective Generation

Generate only what you need:

```bash
# Only infrastructure
./goalgen.py --spec spec.json --out ./output --targets infra

# Only LangGraph workflow
./goalgen.py --spec spec.json --out ./output --targets langgraph

# Multiple targets
./goalgen.py --spec spec.json --out ./output --targets langgraph,api,infra,cicd

# Preview without writing files
./goalgen.py --spec spec.json --out ./output --dry-run
```

**Available targets:**
- `scaffold` - Project structure
- `langgraph` - LangGraph workflow
- `api` - FastAPI orchestrator
- `agents` - Agent implementations
- `tools` - Tool scaffolding
- `infra` - Bicep templates
- `cicd` - GitHub Actions
- `deployment` - Deploy scripts
- `tests` - Test infrastructure
- `assets` - Prompts and static files
- `teams` - Teams Bot with adaptive cards
- `security` - Key Vault (coming soon)
- `webchat` - Web chat (coming soon)
- `evaluators` - Validation logic (coming soon)

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Architecture and development guide
- **[SCHEMA_VERSIONING.md](SCHEMA_VERSIONING.md)** - Schema evolution patterns
- **[COMMON_TOOLS.md](COMMON_TOOLS.md)** - Built-in tool reference
- **[STATE_SCHEMA.md](STATE_SCHEMA.md)** - State design guide
- **[CONFIG_SPEC_SCHEMA.md](CONFIG_SPEC_SCHEMA.md)** - Full spec reference
- **[MULTI_INSTANCE_TOOLS.md](MULTI_INSTANCE_TOOLS.md)** - Multiple tool instances

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Goal Spec (JSON)                              │
│  - Agents, Tools, Tasks, Context Fields        │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  GoalGen CLI                                    │
│  - Parse spec                                   │
│  - Invoke generators                            │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Generators  │  │  Templates   │
│  - scaffold  │  │  (Jinja2)    │
│  - langgraph │  │              │
│  - api       │  │              │
│  - infra     │  │              │
│  - cicd      │  │              │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
┌─────────────────────────────────────────────────┐
│  Generated Project                              │
│  - LangGraph workflow                          │
│  - FastAPI service                             │
│  - Bicep infrastructure                        │
│  - Deployment automation                       │
└─────────────────────────────────────────────────┘
```

## Requirements

- **Python**: 3.11 or higher
- **Azure**: Subscription for deployment (optional for local dev)
- **Node.js**: 18+ for webchat (when implemented)

## Development Status

**Current Version**: 0.2.0-beta

**Generator Status:**
- ✅ Fully Implemented: scaffold, langgraph, agents, tools, api, teams, infra, cicd, deployment, tests, assets
- 🚧 Coming Soon: security, webchat, evaluators

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for your changes
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Roadmap

**v0.3.0** (Next Release):
- [ ] Implement security generator (Key Vault, RBAC)
- [ ] Implement webchat generator (React SPA)
- [ ] Implement evaluators generator
- [ ] Add unit tests for generators
- [ ] Infrastructure generator with full Bicep templates
- [ ] Add CI/CD for GoalGen itself

**v1.0.0** (Production Ready):
- [ ] Complete documentation
- [ ] Video tutorials
- [ ] More example specs
- [ ] Performance optimizations
- [ ] Multi-cloud support (AWS, GCP)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- Inspired by enterprise conversational AI patterns
- Azure-native design patterns

## Support

- **Issues**: [GitHub Issues](https://github.com/kbynd/goalgen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kbynd/goalgen/discussions)
- **Documentation**: [Full Docs](CLAUDE.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

**Generated with GoalGen** - From spec to production-ready AI agents in minutes.
