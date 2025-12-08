# Teams Generator Updates - Complete ✅

All improvements from E2E testing have been successfully backported to generator templates.

## Summary of Changes

### 1. **Versioned Adaptive Cards**
Generated bots now automatically detect channel type and use appropriate card versions:
- **v1.2** for Bot Framework Emulator (simple TextBlock-only layouts)
- **v1.4** for Microsoft Teams (rich layouts with ColumnSet, Container, FactSet)

**Files:**
- `templates/teams/adaptive_cards/v1.2/` - 3 card templates (welcome, response, error)
- `templates/teams/adaptive_cards/v1.4/` - 3 card templates (welcome, response, error)
- `generators/teams.py` - Updated to generate both versions

### 2. **Configurable API Timeout**
LangGraph API timeout is now configurable via environment variable.

**Changes:**
- `templates/teams/config.py.j2` - Added `langgraph_api_timeout` field (default: 90.0s)
- `templates/teams/bot.py.j2` - Uses `config.langgraph_api_timeout` instead of hardcoded value
- `templates/teams/.env.sample.j2` - Added `LANGGRAPH_API_TIMEOUT=90.0`

**Benefits:**
- Supports slower local LLMs (Ollama, llama.cpp) with 90s default
- Can be reduced to 30s for fast cloud LLMs (OpenAI, Azure OpenAI)

### 3. **Channel Detection & Template Loading**
Bot automatically selects correct adaptive card version based on channel.

**Bot Template Updates:**
- `_load_card_templates()` - Loads both v1.2 and v1.4 templates at startup
- `_get_card_version(activity)` - Detects channel (emulator vs msteams)
- `_substitute_template_vars()` - Replaces ${variables} in card JSON
- Updated all card creation methods to accept `activity` parameter
- Added missing imports: `json`, `CardFactory`, `Attachment`

### 4. **Local Development Server**
New optional server for local testing with Bot Framework Emulator.

**New File:**
- `templates/teams/server.py.j2` - aiohttp server for localhost:3978
- Exposes `/api/messages` endpoint for Bot Framework
- Includes health check endpoint at `/health`
- Displays connection info on startup

## Key Improvements

1. ✅ **Emulator Compatibility** - v1.2 cards render correctly in Bot Framework Emulator
2. ✅ **Production Polish** - v1.4 cards provide rich UI in Microsoft Teams
3. ✅ **Automatic Fallback** - Unknown channels default to safe v1.2 version
4. ✅ **Flexible Timeout** - Supports both local and cloud LLM backends
5. ✅ **Local Development** - server.py enables quick iteration with emulator

---

**Version**: v0.2.1
**Date**: 2025-12-05
**Status**: ✅ Complete and tested
