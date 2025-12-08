# End-to-End Integration Test Plan

**Goal:** Generate a complete project and verify it actually works from spec → deployed → running.

**Test Spec:** `examples/travel_planning.json`

---

## Phase 1: Pre-Flight Checks ✈️

### Azure Prerequisites

**Required Azure Resources:**
```bash
# 1. Resource Group
az group create \
  --name rg-goalgen-e2e-test \
  --location eastus

# 2. OpenAI Service (for LLM)
az cognitiveservices account create \
  --name oai-goalgen-test-${RANDOM} \
  --resource-group rg-goalgen-e2e-test \
  --kind OpenAI \
  --sku S0 \
  --location eastus \
  --yes

# 3. Get OpenAI key
az cognitiveservices account keys list \
  --name oai-goalgen-test-${RANDOM} \
  --resource-group rg-goalgen-e2e-test

# 4. Deploy GPT-4 model
az cognitiveservices account deployment create \
  --name oai-goalgen-test-${RANDOM} \
  --resource-group rg-goalgen-e2e-test \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"

# 5. Cosmos DB (for checkpointing)
az cosmosdb create \
  --name cosmos-goalgen-test-${RANDOM} \
  --resource-group rg-goalgen-e2e-test \
  --locations regionName=eastus failoverPriority=0 \
  --default-consistency-level Session

# 6. Storage Account (for state)
az storage account create \
  --name stgoalgentest${RANDOM} \
  --resource-group rg-goalgen-e2e-test \
  --location eastus \
  --sku Standard_LRS
```

**Estimated Cost per Hour:**
- OpenAI GPT-4: ~$0.03/1k tokens (pay-as-you-go)
- Cosmos DB: ~$0.008/hour (serverless)
- Storage: ~$0.02/GB/month
- **Total for testing: < $1**

### Alternative: Local-First Testing

**Better Approach for Initial Validation:**

```bash
# Use local/mock services first:
# 1. Mock OpenAI with litellm
pip install litellm

# 2. Use SQLite for checkpointing (instead of Cosmos)
# 3. Use local file storage
# 4. Test everything works locally BEFORE Azure
```

---

## Phase 2: Generate Project 🏗️

### Step 1: Generate Complete Project

```bash
cd /Users/kalyan/projects/goalgen

# Generate with ALL targets
./goalgen.py \
  --spec examples/travel_planning.json \
  --out ./e2e_test_output \
  --targets scaffold,langgraph,api,agents,tools,assets,infra,deployment,tests

# Expected output structure:
e2e_test_output/
├── langgraph/
│   ├── quest_builder.py
│   ├── agents/
│   │   └── flight_agent.py
│   └── checkpointer_adapter.py
├── orchestrator/
│   └── app/
│       └── main.py
├── infra/
│   └── main.bicep
└── tests/
```

### Step 2: Validate Generated Files Exist

```bash
# Test 1: All expected files created
test -f e2e_test_output/langgraph/quest_builder.py || echo "FAIL: quest_builder.py missing"
test -f e2e_test_output/orchestrator/app/main.py || echo "FAIL: main.py missing"
test -f e2e_test_output/infra/main.bicep || echo "FAIL: main.bicep missing"
```

---

## Phase 3: Validate Generated Code 🔍

### Test 1: Python Syntax Validation

```bash
cd e2e_test_output

# Check all Python files compile
python -m py_compile langgraph/quest_builder.py
python -m py_compile langgraph/agents/*.py
python -m py_compile orchestrator/app/main.py

# Check for common issues
pylint langgraph/ --disable=all --enable=E  # Errors only
```

### Test 2: Import Validation

```python
# test_imports.py
import sys
sys.path.insert(0, '/Users/kalyan/projects/goalgen/e2e_test_output')

# Test 1: Can import langgraph module
try:
    from langgraph import quest_builder
    print("✓ quest_builder imports successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")

# Test 2: Can import agents
try:
    from langgraph.agents import flight_agent
    print("✓ flight_agent imports successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")

# Test 3: Can import orchestrator
try:
    from orchestrator.app import main
    print("✓ orchestrator imports successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
```

### Test 3: Bicep Validation

```bash
# Install bicep (if not already installed)
az bicep install

# Validate Bicep templates
az bicep build --file e2e_test_output/infra/main.bicep

# Check for common issues
az bicep lint --file e2e_test_output/infra/main.bicep
```

---

## Phase 4: Local Testing 🏃

### Setup Local Environment

```bash
cd e2e_test_output

# 1. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (we need to create these first!)
# Check what's needed:
grep -r "^import\|^from" langgraph/ orchestrator/ | \
  grep -v "from \." | \
  sort -u | \
  head -20
```

**Issue: Generated project needs requirements.txt!**
We'll need to add this to generators.

### Test 4: Run Quest Builder Locally

```python
# test_quest_builder_local.py
"""
Test that the generated LangGraph actually executes
"""
import asyncio
import sys
sys.path.insert(0, '/Users/kalyan/projects/goalgen/e2e_test_output')

# Mock dependencies for local testing
class MockCheckpointer:
    async def aget(self, thread_id): return None
    async def aput(self, thread_id, state): pass

async def test_quest_builder():
    from langgraph.quest_builder import build_graph

    # Mock spec
    spec = {
        "id": "travel_planning",
        "agents": {
            "supervisor_agent": {"kind": "supervisor"},
            "flight_agent": {"kind": "llm_agent", "tools": []}
        },
        "state_management": {
            "checkpointing": {"backend": "memory"}
        }
    }

    # Build graph
    graph = build_graph(spec)

    # Test invocation
    initial_state = {
        "messages": ["Find me flights to Paris"],
        "context": {}
    }

    try:
        # This will likely fail due to missing OpenAI key, but we can see how far it gets
        result = await graph.ainvoke(initial_state)
        print(f"✓ Graph executed: {result}")
        return True
    except Exception as e:
        print(f"✗ Graph execution failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_quest_builder())
```

---

## Phase 5: Azure Deployment Strategy 🚀

### Option A: Minimal Azure (Recommended First)

**Deploy only what's needed to test:**

```bash
# 1. Just OpenAI + Cosmos (skip Container Apps for now)
az deployment group create \
  --resource-group rg-goalgen-e2e-test \
  --template-file e2e_test_output/infra/modules/cosmos.bicep \
  --parameters databaseName=travel-planning

# 2. Test with local orchestrator connecting to Azure resources
export COSMOS_ENDPOINT=$(az cosmosdb show -n cosmos-goalgen-test -g rg-goalgen-e2e-test --query documentEndpoint -o tsv)
export COSMOS_KEY=$(az cosmosdb keys list -n cosmos-goalgen-test -g rg-goalgen-e2e-test --query primaryMasterKey -o tsv)

# 3. Run orchestrator locally
cd e2e_test_output/orchestrator
uvicorn app.main:app --reload
```

### Option B: Full Deployment (After Local Works)

```bash
# Deploy complete infrastructure
cd e2e_test_output
./scripts/deploy.sh dev
```

---

## Phase 6: Functional Testing 🧪

### Test 5: Message Flow Test

```bash
# Send test message to orchestrator
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-123",
    "message": "Find me flights to Paris for next week"
  }'

# Expected response:
{
  "response": "I'll help you find flights to Paris...",
  "thread_id": "test-123"
}
```

### Test 6: Checkpointing Test

```bash
# Send message 1
curl -X POST http://localhost:8000/message \
  -d '{"thread_id": "test-123", "message": "Find flights to Paris"}'

# Send message 2 (should remember context)
curl -X POST http://localhost:8000/message \
  -d '{"thread_id": "test-123", "message": "Make it business class"}'

# Response should reference previous request
```

---

## Phase 7: Results & Documentation 📊

### Success Criteria

**Must Pass:**
- [ ] Generated code compiles without syntax errors
- [ ] Generated Bicep builds successfully
- [ ] LangGraph graph can be created
- [ ] Orchestrator can start locally
- [ ] Can send message and get response

**Should Pass:**
- [ ] Checkpointing persists state
- [ ] Agent routing works
- [ ] Tools can be called
- [ ] Deploys to Azure successfully

### Gap Documentation Template

For each failure, document:

```markdown
### Gap #N: [Title]

**What Failed:**
[Specific error or issue]

**Root Cause:**
[Why it failed - template issue, missing code, wrong assumption]

**Fix Required:**
[What needs to be added/changed]

**Priority:** High/Medium/Low
```

---

## Recommended Execution Order

### Phase 1: Safety First (Local Only)

```bash
# DAY 1: No Azure costs yet
1. Generate project
2. Check files exist
3. Validate Python syntax
4. Try importing modules
5. Validate Bicep builds
6. Document all gaps found
```

### Phase 2: Local Runtime

```bash
# DAY 2: Still no Azure costs
1. Fix import errors
2. Add missing requirements.txt
3. Create mock services
4. Test graph execution locally
5. Test orchestrator locally
6. Document runtime gaps
```

### Phase 3: Azure Integration

```bash
# DAY 3: Azure costs start (~$1/day)
1. Create minimal Azure resources
2. Test with real OpenAI
3. Test with real Cosmos
4. Fix Azure-specific issues
5. Document Azure gaps
```

### Phase 4: Full Deployment

```bash
# DAY 4: Full Azure costs (~$5/day)
1. Deploy complete infrastructure
2. Test end-to-end
3. Performance testing
4. Cost analysis
5. Final gap documentation
```

---

## What We'll Learn 🎓

**Expected Discoveries:**

1. **Missing Files:**
   - requirements.txt (definitely missing)
   - __init__.py files (some missing)
   - Configuration files (.env.sample)

2. **Template Issues:**
   - Import paths might be wrong
   - Some generated code might not match frmk/ API
   - Bicep parameter files might be incomplete

3. **Integration Issues:**
   - BaseAgent + LangGraph integration
   - Checkpointer adapter implementation
   - Tool registry implementation

4. **Missing Documentation:**
   - How to actually run generated code
   - Environment variable setup
   - Deployment prerequisites

---

## Cost Optimization 💰

**To Minimize Azure Costs:**

```bash
# 1. Use serverless/consumption tier
- Cosmos DB: Serverless mode
- Functions: Consumption plan
- OpenAI: Pay-per-token

# 2. Auto-shutdown after testing
az group delete --name rg-goalgen-e2e-test --yes --no-wait

# 3. Use dev quotas
az cognitiveservices account deployment create \
  --sku-capacity 1  # Minimum capacity

# 4. Monitor costs
az consumption usage list --start-date 2025-12-01
```

**Expected Total Cost for E2E Test:** $2-5

---

## Next Steps

1. **You choose:** Local-first or Azure-first?
2. **I'll help:** Guide through each phase
3. **We document:** Every gap discovered
4. **We fix:** Critical issues found
5. **We test:** Until one complete flow works

**Ready to start with Phase 1 (generation)?**
