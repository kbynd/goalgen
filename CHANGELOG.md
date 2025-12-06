# Changelog

All notable changes to GoalGen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Webchat generator with React SPA template
- Additional example goal specs (expense_reporting, customer_support)
- Video tutorials and demo recordings
- Infrastructure generator for Azure Bicep templates

---

## [0.2.0-beta] - 2025-12-06

### Added - Teams Bot Generator

- **Versioned Adaptive Cards** for cross-platform compatibility
  - v1.2 cards for Bot Framework Emulator (simple TextBlock layouts)
  - v1.4 cards for Microsoft Teams (rich ColumnSet, Container, FactSet)
  - Automatic channel detection (`emulator` vs `msteams`)
  - Template variable substitution with `${variable}` syntax

- **Configurable API Timeout** via environment variable
  - `LANGGRAPH_API_TIMEOUT` defaults to 90.0s (supports slow local LLMs)
  - Can be reduced to 30s for fast cloud LLMs (OpenAI, Azure OpenAI)

- **Local Development Server** (`server.py`)
  - aiohttp server on `localhost:3978` for Bot Framework Emulator
  - Health check endpoint at `/health`
  - Displays connection info and configuration on startup

- **Channel-Specific Template Loading**
  - `_load_card_templates()` - Loads both v1.2 and v1.4 at startup
  - `_get_card_version(activity)` - Detects channel and returns appropriate version
  - `_substitute_template_vars()` - Replaces template variables in card JSON

### Added - Runtime Gap Fixes

All runtime gaps from E2E testing have been fixed:

- **Gap #9: Prompt Loader Configuration**
  - `frmk/agents/base_agent.py` now passes full `goal_config` to `get_prompt_loader()`
  - Previously only passed `prompt_repository` field, causing errors

- **Gap #10: OpenAI base_url Support**
  - Added `OPENAI_API_BASE` environment variable support for Ollama/llama.cpp
  - Added `OPENAI_MODEL_NAME` environment variable to override model selection
  - Enables use of local LLMs and OpenAI-compatible endpoints

- **Gap #11: Dockerfile COPY Paths**
  - `Dockerfile-cloud.j2` template for cloud builds (ACR, GitHub Actions)
  - Correct COPY paths for `build_context/` directory structure
  - Separate frmk package installation step

- **Gap #12: requirements.txt Editable Install**
  - Removed `-e ../frmk` editable install from generated requirements.txt
  - Added documentation comments explaining frmk installation approach
  - Cloud builds: frmk installed via `pip install /app/frmk` in Dockerfile
  - Local dev: Manual editable install instructions in comments

### Added - Build and Deployment Scripts

- **prepare_build_context.sh** - Prepares build context for cloud Docker builds
  - Copies frmk, workflow, config, orchestrator to `build_context/`
  - Copies Dockerfile to build context root
  - Supports ACR builds and GitHub Actions workflows

### Added - Documentation

- **RUNTIME_GAPS_STATUS.md** - Comprehensive verification of all runtime gap fixes
- **TEAMS_GENERATOR_COMPLETE.md** - Full documentation of Teams generator improvements
- **CONTRIBUTING.md** - Open source contribution guidelines
  - Development setup instructions
  - Generator development guide
  - Testing guidelines
  - Pull request process
  - Coding standards

### Changed

- **API Generator** now uses `Dockerfile-cloud.j2` by default (`generators/api.py:47`)
- **Deployment Generator** includes `prepare_build_context.sh` in generated scripts
- **Scaffold Generator** creates `build_context/` directory for cloud builds

### Fixed

- BaseAgent prompt loader initialization (Gap #9)
- OpenAI-compatible endpoint support for Ollama (Gap #10)
- Dockerfile COPY paths for cloud builds (Gap #11)
- requirements.txt editable install removal (Gap #12)
- Teams Bot adaptive card rendering in Bot Framework Emulator
- Teams Bot API timeout for slow local LLMs

---

## [0.1.0] - 2024-12-01

### Added

- **Core Generator System**
  - CLI entry point (`goalgen.py`)
  - Template engine with Jinja2 support
  - Modular generator architecture

- **Generators**
  - `scaffold` - Project structure and base files
  - `agents` - Agent implementations
  - `langgraph` - LangGraph workflow orchestration
  - `api` - FastAPI orchestrator
  - `teams` - Microsoft Teams Bot (basic)
  - `tools` - Tool implementations
  - `deployment` - Deployment scripts
  - `security` - Security configuration

- **Framework Package (frmk)**
  - `BaseAgent` class with LLM initialization
  - Prompt loader with Azure AI Foundry support
  - Tool registry for LangChain tool binding
  - Logging and tracing utilities
  - Safety guard system

- **Example Specifications**
  - `travel_planning.json` - Multi-agent travel planning system

- **Documentation**
  - README.md with quickstart guide
  - CLAUDE.md with detailed architecture
  - CONFIG_SPEC_SCHEMA.md with full specification schema

### Known Limitations

- No webchat generator (planned for 0.3.0)
- No infrastructure generator (planned for 0.3.0)
- Limited example goal specifications
- Manual Azure deployment required

---

## Versioning Strategy

- **Major version (X.0.0)**: Breaking changes to goal spec schema or generator API
- **Minor version (0.X.0)**: New generators, features, or significant improvements
- **Patch version (0.0.X)**: Bug fixes and minor improvements

---

## Links

- [GoalGen Repository](https://github.com/anthropics/goalgen) (placeholder)
- [Documentation](./README.md)
- [Contributing Guide](./CONTRIBUTING.md)
- [License](./LICENSE)

---

**Legend**:
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes
