# GoalGen v0.2.0-beta Release Notes

**Release Date**: December 6, 2025

We're excited to announce GoalGen v0.2.0-beta! This release brings major improvements to the Teams Bot generator, comprehensive runtime fixes, and enhanced deployment support.

## 🎉 What's New

### Teams Bot Generator

The Teams Bot generator is now fully implemented with production-ready features:

- **✨ Versioned Adaptive Cards**
  - Automatic channel detection (`emulator` vs `msteams`)
  - v1.2 cards for Bot Framework Emulator (simple TextBlock layouts)
  - v1.4 cards for Microsoft Teams (rich ColumnSet, Container, FactSet)
  - Template variable substitution with `${variable}` syntax

- **🔧 Configurable API Timeout**
  - `LANGGRAPH_API_TIMEOUT` environment variable support
  - Defaults to 90.0s for slow local LLMs (Ollama, llama.cpp)
  - Can be reduced to 30s for fast cloud LLMs (OpenAI, Azure OpenAI)

- **🖥️ Local Development Server**
  - aiohttp server on `localhost:3978` for Bot Framework Emulator
  - Health check endpoint at `/health`
  - Connection info and configuration displayed on startup

### Runtime Gap Fixes

All runtime gaps identified during E2E testing have been resolved:

- **Gap #9: Prompt Loader Configuration**
  - `frmk/agents/base_agent.py` now passes full `goal_config` to `get_prompt_loader()`
  - Previously only passed `prompt_repository` field, causing initialization errors

- **Gap #10: OpenAI base_url Support**
  - Added `OPENAI_API_BASE` environment variable for Ollama/llama.cpp
  - Added `OPENAI_MODEL_NAME` environment variable for model override
  - Enables use of local LLMs and OpenAI-compatible endpoints

- **Gap #11: Dockerfile COPY Paths**
  - New `Dockerfile-cloud.j2` template for cloud builds (ACR, GitHub Actions)
  - Correct COPY paths for `build_context/` directory structure
  - Separate frmk package installation step

- **Gap #12: requirements.txt Editable Install**
  - Removed `-e ../frmk` editable install from generated requirements.txt
  - Cloud builds: frmk installed via `pip install /app/frmk` in Dockerfile
  - Local dev: Manual editable install instructions in comments

### Build & Deployment

- **🐳 prepare_build_context.sh**
  - Prepares build context for cloud Docker builds
  - Copies frmk, workflow, config, orchestrator to `build_context/`
  - Supports ACR builds and GitHub Actions workflows

- **📦 Cloud Build Support**
  - API Generator now uses `Dockerfile-cloud.j2` by default
  - Deployment Generator includes `prepare_build_context.sh`
  - Scaffold Generator creates `build_context/` directory

### Documentation & Community

- **📚 CONTRIBUTING.md** - Open source contribution guidelines with development setup
- **📝 CHANGELOG.md** - Complete version history following Keep a Changelog format
- **🐛 GitHub Issue Templates** - Templates for bug reports, feature requests, and questions
- **📖 Enhanced README** - Updated with v0.2.0 features and corrected repository URLs

## 📊 Generator Status

- ✅ **Fully Implemented**: scaffold, langgraph, agents, tools, api, teams, infra, cicd, deployment, tests, assets
- 🚧 **Coming Soon**: security, webchat, evaluators

## 🔧 Installation

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

## 🚀 Quick Start

```bash
# Generate a travel planning assistant
./goalgen.py --spec examples/travel_planning.json --out ./my_travel_agent

# Generate with Teams Bot support
./goalgen.py --spec examples/travel_planning.json --out ./my_travel_agent --targets scaffold,langgraph,api,teams
```

## 📋 What's Changed Since v0.1.0

### Added
- Teams Bot generator with full adaptive card support
- Configurable API timeout for local LLM compatibility
- Local development server for Teams Bot testing
- OpenAI-compatible endpoint support (Ollama, llama.cpp)
- Cloud build support with dedicated Dockerfile template
- Build context preparation scripts
- Open source contribution guidelines
- GitHub issue templates
- Comprehensive CHANGELOG

### Fixed
- BaseAgent prompt loader initialization (Gap #9)
- OpenAI base_url configuration (Gap #10)
- Dockerfile COPY paths for cloud builds (Gap #11)
- requirements.txt editable install conflicts (Gap #12)
- Teams Bot adaptive card rendering in Bot Framework Emulator
- API timeout handling for slow local LLMs

### Changed
- API Generator defaults to `Dockerfile-cloud.j2`
- Deployment Generator includes build context scripts
- Scaffold Generator creates cloud build directories
- README updated with v0.2.0 features and repository URLs
- Version bumped to 0.2.0-beta across all files

## 🐛 Known Issues

None at this time. Please report issues at [GitHub Issues](https://github.com/kbynd/goalgen/issues).

## 🛣️ Roadmap

### v0.3.0 (Next Release)
- Security generator (Key Vault, RBAC)
- Webchat generator (React SPA)
- Evaluators generator
- Unit tests for generators
- Full Infrastructure generator with Bicep templates

### v1.0.0 (Production Ready)
- Complete documentation
- Video tutorials
- More example specifications
- Performance optimizations
- Multi-cloud support (AWS, GCP)

## 📖 Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[CLAUDE.md](CLAUDE.md)** - Architecture and development guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Full version history

## 💬 Community & Support

- **Issues**: [GitHub Issues](https://github.com/kbynd/goalgen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kbynd/goalgen/discussions)
- **Bug Reports**: Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- **Feature Requests**: Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)

## 🙏 Acknowledgments

- Built on [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- Inspired by enterprise conversational AI patterns
- Azure-native design principles

---

**Full Changelog**: https://github.com/kbynd/goalgen/blob/main/CHANGELOG.md

🤖 **Generated with GoalGen** - From spec to production-ready AI agents in minutes.
