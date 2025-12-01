# E2E Testing - Gaps Discovered

**Date**: 2025-12-01  
**Phase**: Phase 1 - Generate & Validate (Local Testing)  
**Test Spec**: examples/travel_planning.json

---

## ✅ What Works

### Code Generation (100% Success)
- ✅ All files generated without errors
- ✅ Directory structure created correctly (langgraph/, orchestrator/, infra/, tools/, etc.)
- ✅ All Python files compile successfully (no syntax errors)
- ✅ Templates rendered correctly with defensive checks
- ✅ Manifest tracking works (.goalgen/manifest.json created)

### Files Generated

**Core LangGraph Files:**
- ✅ langgraph/quest_builder.py (3111 bytes)
- ✅ langgraph/state_schema.py (1146 bytes)
- ✅ langgraph/checkpointer_adapter.py (2021 bytes)
- ✅ langgraph/agents/supervisor_agent.py (3183 bytes)
- ✅ langgraph/agents/flight_agent.py (2692 bytes)

**Orchestrator Files:**
- ✅ orchestrator/main.py (3237 bytes)
- ✅ orchestrator/Dockerfile (451 bytes)
- ✅ orchestrator/requirements.txt (490 bytes)
- ✅ orchestrator/.env.sample (684 bytes)

**Infrastructure Files:**
- ✅ infra/main.bicep (2700 bytes)
- ✅ infra/modules/keyvault.bicep
- ✅ infra/modules/cosmos.bicep
- ✅ infra/modules/containerapp.bicep
- ✅ infra/modules/functionapp.bicep
- ✅ infra/modules/container-env.bicep
- ✅ infra/parameters.json

**Other Assets:**
- ✅ README.md, LICENSE, .gitignore
- ✅ prompts/supervisor_agent.md, prompts/flight_agent.md
- ✅ tools/flight_api/function_app.py
- ✅ scripts/deploy.sh, scripts/build.sh, scripts/destroy.sh
- ✅ tests/pytest.ini

---

## Gaps Discovered

### GAP #1: Missing Dependency Installation Instructions
**Severity**: HIGH
**Status**: ✅ FIXED in v0.2.0

**Problem**:
Generated project has `requirements.txt` but no guidance on how to install dependencies for local testing.

**Current Behavior**:
```bash
$ python3 -c "from langgraph.graph import StateGraph"
ModuleNotFoundError: No module named 'langgraph.graph'
```

**Missing Dependencies**:
- langgraph>=0.0.40
- langchain>=0.1.0
- langchain-core>=0.1.0
- langchain-openai>=0.0.5
- fastapi>=0.104.0
- azure-cosmos>=4.5.0
- azure-identity>=1.15.0
- And 10+ more from requirements.txt

**What Should Be Generated**:
1. Root-level requirements.txt or QUICKSTART.md with:
   ```bash
   # Setup virtual environment
   python3.11 -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r orchestrator/requirements.txt
   ```

2. Or a `setup.sh` script that does this automatically

**Impact**: Cannot test any imports or run any code locally without manual dependency setup.

**Workaround**: User must manually create venv and install deps.

**Resolution (v0.2.0)**:
- ✅ Generated `QUICKSTART.md` with complete setup instructions
- ✅ Step-by-step guide for venv creation and dependency installation
- ✅ Includes troubleshooting section for common issues
- ✅ Documents all three modes: Key Vault, direct key, memory checkpointer

---

### GAP #2: frmk/ Package Not Installable
**Severity**: HIGH
**Status**: ✅ FIXED in v0.2.0

**Problem**:
`requirements.txt` references `../frmk` as editable install:
```
-e ../frmk
```

But `frmk/` directory:
1. Has no `setup.py` or `pyproject.toml`
2. Cannot be installed as package
3. Import paths won't work

**Current State**:
```bash
$ pip install -e frmk/
ERROR: File "setup.py" not found. Directory cannot be installed in editable mode
```

**What's Missing**:
Either:
- `frmk/setup.py` with package metadata
- Or `frmk/pyproject.toml` for modern Python packaging

**Impact**:
- Cannot import `from frmk.agents.base_agent import BaseAgent`
- All agent files will fail to import
- Cannot run orchestrator or any generated code

**Resolution (v0.2.0)**:
- ✅ Auto-generate `frmk/setup.py` with complete metadata
- ✅ Auto-generate `frmk/pyproject.toml` for modern packaging
- ✅ Package includes all dependencies (langchain, langgraph, azure-sdk, etc.)
- ✅ `pip install -e frmk/` now works out of the box

---

### GAP #3: No Local Development Path
**Severity**: MEDIUM
**Status**: ✅ FIXED in v0.2.0

**Problem**:
All generated code assumes Azure resources exist:
- Cosmos DB endpoint and key
- Azure OpenAI endpoint and key
- Key Vault for secrets
- Azure AI Foundry project

**What's Missing**:
1. Mock/local alternatives for development
2. Feature flags to run without Azure (e.g., using in-memory checkpointer)
3. Clear documentation on minimum Azure setup required

**Example Code Expecting Azure**:
```python
# checkpointer_adapter.py
from azure.cosmos import CosmosClient

def create_checkpointer(goal_config):
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")  # ← Must exist
    cosmos_key = os.getenv("COSMOS_KEY")            # ← Must exist
    client = CosmosClient(cosmos_endpoint, cosmos_key)  # ← Fails if not set
```

**Impact**: Cannot run generated code without Azure resources deployed first.

**Resolution (v0.2.0)**:
- ✅ Added `MemorySaver` fallback in checkpointer_adapter.py
- ✅ Added `USE_MEMORY_CHECKPOINTER` environment variable support
- ✅ Try/except around frmk imports with graceful fallback
- ✅ Updated `.env.sample` with all three options documented
- ✅ Can now test locally without any Azure resources

---

### GAP #4: Azure CLI Not Detected (Bicep Validation Skipped)
**Severity**: LOW
**Status**: ✅ RESOLVED (Tested 2025-12-01)

**Problem**:
Cannot validate Bicep templates because Azure CLI not installed.

**Command Attempted**:
```bash
$ az bicep build --file infra/main.bicep
az: command not found
```

**Resolution**:
- Azure CLI is now available
- All 6 Bicep files validated successfully ✅
- 0 errors, 2 non-blocking warnings found

**Validation Results**:
```
✅ main.bicep - Valid (1 warning: unused parameter)
✅ cosmos.bicep - Valid (1 warning: secret in output)
✅ container-env.bicep - Valid
✅ containerapp.bicep - Valid
✅ functionapp.bicep - Valid
✅ keyvault.bicep - Valid
```

**Warnings Found (Original)**:
1. `subscriptionId` parameter unused in main.bicep
2. ~~Cosmos DB primary key exposed in output~~ ✅ **FIXED**

**Security Fix Applied**:
- ✅ Cosmos key now stored in Key Vault (not in Bicep outputs)
- ✅ Runtime retrieval using DefaultAzureCredential
- ✅ Falls back to COSMOS_KEY env var for local dev
- ✅ Removed cosmos-key from Container App secrets
- ✅ Bicep linter warning eliminated

**Conclusion**:
- This was an **environment issue**, not a code generation bug
- Generated Bicep is syntactically correct and deployable
- ✅ Security warning fixed (Cosmos key to Key Vault)
- ⚠️ 1 minor warning remains: unused `subscriptionId` parameter

**Details**: See `GAP4_BICEP_VALIDATION_RESULTS.md`

**Remaining Work**:
1. Remove unused `subscriptionId` parameter from main.bicep template (cosmetic only)

---

### GAP #5: No Unit Tests for Generated Code
**Severity**: MEDIUM  
**Status**: NOT TESTED

**Problem**:
`tests/` directory created but only contains:
- `pytest.ini` (config file)
- `__init__.py` (empty)

**What's Missing**:
1. Unit tests for each agent
2. Tests for quest_builder graph construction
3. Tests for state schema validation
4. Mock-based tests for orchestrator endpoints

**Expected Files**:
```
tests/
├── unit/
│   ├── test_supervisor_agent.py
│   ├── test_flight_agent.py
│   ├── test_quest_builder.py
│   └── test_state_schema.py
└── integration/
    └── test_full_workflow.py
```

**Impact**: No automated way to verify generated code behavior without manual testing.

**Suggested Fix**:
Add test generator that creates basic unit tests:
```python
# tests/unit/test_flight_agent.py (should be generated)
def test_flight_agent_init():
    config = load_test_config()
    agent = FlightAgent(config)
    assert agent.agent_name == "flight_agent"
```

---

### GAP #6: README Deployment Instructions Reference Non-Existent Files
**Severity**: LOW  
**Status**: DOCUMENTATION

**Problem**:
README.md contains deployment instructions referencing:
```bash
./scripts/deploy.sh dev
```

But doesn't mention prerequisites:
- Azure CLI must be installed
- Must be logged in (`az login`)
- Subscription must be set
- Resource group must be created first
- Container image must be built and pushed

**What's Missing**:
Pre-flight checklist section in README.

**Suggested Fix**:
Add "Prerequisites" section:
```markdown
## Prerequisites

Before deployment:
1. Install Azure CLI: https://...
2. Login: `az login`
3. Create resource group: `az group create ...`
4. Build container: `./scripts/build.sh`
```

---

## 📊 Summary

### Statistics
- **Files Generated**: 56
- **Python Files**: 20+
- **Bicep Files**: 7
- **Scripts**: 5
- **Total Size**: ~90KB

### Pass Rate (Updated v0.2.0)
- ✅ Code Generation: 100%
- ✅ Syntax Validation: 100% (all .py files compile)
- ✅ Import Validation: 100% (dependencies installable, frmk package works)
- ✅ Bicep Validation: 100% (0 errors, 1 minor warning)
- 🔄 Runtime Testing: READY (all blockers removed)

### Status Update: All Critical Blockers Removed! ✅

**v0.2.0 Resolved**:
1. ✅ GAP #1 resolved (QUICKSTART.md generated)
2. ✅ GAP #2 resolved (frmk/setup.py auto-generated)
3. ✅ GAP #3 resolved (memory checkpointer fallback)
4. ✅ GAP #7 resolved (workflow/ instead of langgraph/)
5. ✅ GAP #4 Warning 2 resolved (Cosmos key to Key Vault)

**Ready for**:
- Local development testing with memory checkpointer
- Azure deployment with proper security (Key Vault)
- E2E Phase 2: Runtime message flow testing

---

## 🎯 Next Steps (Post v0.2.0)

### ✅ Critical Fixes Complete (v0.2.0)

All blocking issues resolved:
1. ✅ **frmk/setup.py** - Auto-generated with complete metadata
2. ✅ **QUICKSTART.md** - Complete setup guide with troubleshooting
3. ✅ **Memory Checkpointer** - USE_MEMORY_CHECKPOINTER flag implemented
4. ✅ **workflow/ directory** - No more import shadowing
5. ✅ **Key Vault security** - Cosmos key properly secured

### 🔄 Ready for Phase 2: Runtime Testing

**Goal**: Get ONE complete message flow working

**Next Steps**:
1. Test local message flow with memory checkpointer
2. Validate LangGraph workflow execution
3. Test agent invocation and tool calling
4. Verify state persistence
5. Test Azure deployment end-to-end

### 📋 Remaining Nice-to-Have Improvements

**GAP #5**: Generate Basic Unit Tests (future enhancement)
- Create test stubs for each agent
- Add tests for graph construction
- Provide test data fixtures

**GAP #6**: Enhanced README Prerequisites (minor documentation)
- Add pre-flight checklist
- Document Azure CLI requirements
- Add troubleshooting section

**Minor**: Remove unused `subscriptionId` parameter (cosmetic only)

---

## 🔥 Critical Path: UNBLOCKED ✅

**Status**: All blockers removed in v0.2.0

**Why This Matters**:
- ✅ Generated code structure proven correct
- ✅ Can test LangGraph workflow locally
- ✅ No Azure resources required for basic testing
- ✅ Fast iteration on generated code possible
- ✅ Production deployment uses proper security (Key Vault)

---

### GAP #7: Generated langgraph/ Directory Shadows Installed Package
**Severity**: CRITICAL
**Status**: ✅ FIXED in v0.2.0

**Problem**:
Generated project creates a directory called `langgraph/` which shadows the installed `langgraph` Python package.

**Current Behavior**:
```python
# In generated code:
from langgraph.graph import StateGraph  # Tries to import from installed package

# But Python finds:
./langgraph/__init__.py  # Local directory found first!

# Which tries to import:
from .quest_builder import graph  # Which itself tries:
from langgraph.graph import StateGraph  # Infinite loop!
```

**Error**:
```
ModuleNotFoundError: No module named 'langgraph.graph'
```

**Root Cause**:
Python's import system searches current working directory FIRST, before site-packages.
Our `langgraph/` directory is found before the installed `langgraph` package.

**Impact**:
- ❌ Cannot import ANY generated code
- ❌ Cannot run quest_builder
- ❌ Cannot test workflow
- ❌ **BLOCKS ALL EXECUTION**

**Suggested Fixes**:

### Option 1: Rename Generated Directory (RECOMMENDED)
```
langgraph/           →  workflow/
├── quest_builder.py →  ├── quest_builder.py
├── state_schema.py  →  ├── state_schema.py
└── agents/          →  └── agents/
```

Then update imports:
```python
# Before:
from langgraph.state_schema import TravelPlanningState
from langgraph.agents import supervisor_agent_node

# After:
from workflow.state_schema import TravelPlanningState
from workflow.agents import supervisor_agent_node
```

### Option 2: Add Package Prefix
Rename to:
- `travel_planning_workflow/`
- `{goal_id}_graph/`

### Option 3: Move to Subdirectory
```
src/
└── langgraph/
    ├── quest_builder.py
    └── ...
```

Then add `src/` to PYTHONPATH.

**Recommended Fix**: Option 1 - rename to `workflow/`
- Simple and clear
- No confusion with installed packages
- Standard naming convention

**Resolution (v0.2.0)**:
- ✅ Renamed all occurrences of `langgraph/` to `workflow/` in generators
- ✅ Updated `generators/langgraph.py` to output to `workflow/`
- ✅ Updated `generators/agents.py` to use `workflow/agents/`
- ✅ Updated `generators/scaffold.py` directory list
- ✅ All imports now work correctly without shadowing

---
