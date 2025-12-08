# GoalGen Generator Updates Required

**Date**: 2025-12-02
**Based on**: E2E Runtime Testing Results
**Status**: Action Items for Generator Implementation

---

## Overview

Based on E2E testing, we discovered 4 runtime gaps that need to be fixed in the generator templates. Additionally, we need to add Bicep infrastructure templates to the generated output.

## Generator Updates by Module

### 1. **agents** Generator

**File to Update**: `generators/agents.py` (or template: `templates/agents/base_agent.py.j2`)

#### Changes Required:

**A. Fix Prompt Loader Initialization (Gap #9)**

```python
# CURRENT (BROKEN):
prompt_loader = get_prompt_loader(
    self.goal_config.get("prompt_repository")
)

# FIXED:
prompt_loader = get_prompt_loader(
    self.goal_config  # Pass full config
)
```

**B. Add OpenAI base_url Support (Gap #10)**

```python
# Add this logic to BaseAgent.__init__():

# Build LLM parameters with base_url support
llm_params = {
    "model": model_name,
    "temperature": llm_config.get("temperature", 0.7),
    "max_tokens": llm_config.get("max_tokens"),
    "streaming": llm_config.get("streaming", False),
}

# Support ollama and other OpenAI-compatible endpoints
if os.getenv("OPENAI_API_BASE"):
    llm_params["base_url"] = os.getenv("OPENAI_API_BASE")

self.llm = ChatOpenAI(**llm_params)
```

**C. Add Environment Variable Override for Model**

```python
# Add before LLM initialization:
model_name = os.getenv("OPENAI_MODEL_NAME") or llm_config.get("model", "gpt-4")
```

**Template Location**: `frmk/agents/base_agent.py` (if used as template) or `templates/agents/base_agent.py.j2`

**Generator**: `generators/agents.py` - Copy updated `frmk/agents/base_agent.py` to generated project

---

### 2. **scaffold** Generator

**File to Update**: `generators/scaffold.py`

#### Changes Required:

**A. Add build_context Directory Structure**

Update directory creation to include:
```python
directories = [
    'build_context',           # NEW
    'build_context/frmk',      # NEW
    'build_context/workflow',  # NEW
    'build_context/config',    # NEW
    'build_context/orchestrator', # NEW
    # ... existing directories ...
]
```

**B. Generate Build Context Preparation Script**

Create `scripts/prepare_build_context.sh`:
```bash
#!/bin/bash
# Prepare build context for Docker cloud builds
set -e

echo "Preparing build context for Docker cloud builds..."

# Clean existing build context
rm -rf build_context
mkdir -p build_context

# Copy source directories
echo "Copying frmk..."
cp -r frmk build_context/

echo "Copying workflow..."
cp -r workflow build_context/

echo "Copying config..."
cp -r config build_context/

echo "Copying orchestrator..."
cp -r orchestrator build_context/

# Copy Dockerfile to build context root
cp orchestrator/Dockerfile build_context/

echo "✅ Build context prepared successfully!"
echo "You can now run: az acr build --registry <acr-name> --image <image-name>:tag --file build_context/Dockerfile build_context/"
```

---

### 3. **api** Generator (Dockerfile)

**File to Update**: `generators/api.py` or `templates/api/Dockerfile.j2`

#### Changes Required:

**A. Fix COPY Paths (Gap #11)**

```dockerfile
# CURRENT (BROKEN):
FROM python:3.11-slim
WORKDIR /app
COPY ../frmk /app/frmk
COPY ../workflow /app/workflow

# FIXED (for build_context):
FROM python:3.11-slim
WORKDIR /app

# Copy frmk package first
COPY frmk /app/frmk

# Install frmk package
RUN pip install --no-cache-dir /app/frmk

# Copy workflow module
COPY workflow /app/workflow

# Copy config
COPY config /app/config

# Copy orchestrator requirements
COPY orchestrator/requirements.txt /tmp/requirements.txt

# Install orchestrator dependencies (frmk already installed)
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy orchestrator code
COPY orchestrator /app/orchestrator

# Set working directory
WORKDIR /app/orchestrator

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**B. Fix requirements.txt (Gap #12)**

Update requirements.txt generation to NOT include:
```txt
# REMOVE THIS LINE:
-e ../frmk

# REPLACE WITH COMMENT:
# GoalGen Framework (Core SDK)
# Installed separately in Dockerfile (see COPY frmk step above)
# Updated: {{ current_date }}
```

**Template Location**: `templates/api/Dockerfile.j2` and `templates/api/requirements.txt.j2`

---

### 4. **infra** Generator ⭐ NEW

**File to Create**: `generators/infra.py`

#### Purpose:
Generate Bicep templates for Azure infrastructure deployment

#### Files to Generate:

**A. `infra/modules/acr.bicep`**
- Azure Container Registry module
- Configurable SKU (Basic/Standard/Premium)
- Admin user enabled by default

**B. `infra/modules/container-apps-environment.bicep`**
- Container Apps Environment
- Log Analytics Workspace integration
- Consumption workload profile

**C. `infra/modules/container-app.bicep`**
- Container App deployment
- ACR integration with credentials
- Environment variables support
- Auto-scaling configuration

**D. `infra/main-simple.bicep`**
- Main orchestration template
- Composes all modules
- Parameters for configuration
- Outputs for app URL and resource details

**E. `infra/parameters.dev.json`**
- Development environment parameters
- Template with placeholders

**F. `infra/README.md`**
- Deployment instructions
- Prerequisites
- Cost estimates
- Troubleshooting guide

#### Template Variables:

```python
# Template context for Jinja2
context = {
    'app_name': spec['id'],
    'environment': 'dev',
    'location': 'eastus',
    'image_tag': 'v1',
    'target_port': 8000,
    'cpu': '1.0',
    'memory': '2.0Gi',
    'min_replicas': 1,
    'max_replicas': 3,
    'acr_sku': 'Basic',
    'current_date': datetime.now().strftime('%Y-%m-%d'),
}
```

---

### 5. **deployment** Generator

**File to Update**: `generators/deployment.py`

#### Changes Required:

**A. Add Bicep Deployment Script**

Generate `scripts/deploy-azure.sh`:
```bash
#!/bin/bash
# Azure deployment script using Bicep

set -e

RESOURCE_GROUP="${RESOURCE_GROUP:-goalgen-rg}"
LOCATION="${LOCATION:-eastus}"
OPENAI_API_KEY="${OPENAI_API_KEY}"
IMAGE_TAG="${IMAGE_TAG:-v1}"

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is required"
    exit 1
fi

echo "🚀 Deploying to Azure..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Image Tag: $IMAGE_TAG"

# Create resource group if it doesn't exist
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy infrastructure
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infra/main-simple.bicep \
    --parameters \
        environment=dev \
        imageTag=$IMAGE_TAG \
        openAiApiKey="$OPENAI_API_KEY"

# Get app URL
APP_URL=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main-simple \
    --query properties.outputs.appUrl.value -o tsv)

echo ""
echo "✅ Deployment complete!"
echo "App URL: $APP_URL"
echo ""
echo "Test with:"
echo "  curl $APP_URL/health"
```

**B. Add ACR Build Script**

Generate `scripts/build-and-push.sh`:
```bash
#!/bin/bash
# Build Docker image and push to ACR

set -e

ACR_NAME="${ACR_NAME}"
IMAGE_TAG="${IMAGE_TAG:-v1}"

if [ -z "$ACR_NAME" ]; then
    echo "Error: ACR_NAME environment variable is required"
    exit 1
fi

echo "🔨 Building and pushing Docker image..."
echo "ACR: $ACR_NAME"
echo "Image Tag: $IMAGE_TAG"

# Prepare build context
./scripts/prepare_build_context.sh

# Build on ACR
az acr build \
    --registry $ACR_NAME \
    --image goalgen:$IMAGE_TAG \
    --file build_context/Dockerfile \
    build_context/

echo ""
echo "✅ Image built and pushed successfully!"
echo "Image: $ACR_NAME.azurecr.io/goalgen:$IMAGE_TAG"
```

---

## Implementation Checklist

### Phase 1: Fix Existing Generators
- [ ] Update `agents` generator - Fix BaseAgent template
  - [ ] Fix prompt loader config (Gap #9)
  - [ ] Add base_url support (Gap #10)
  - [ ] Add OPENAI_MODEL_NAME override
- [ ] Update `api` generator - Fix Dockerfile
  - [ ] Fix COPY paths (Gap #11)
  - [ ] Separate frmk installation
- [ ] Update `api` generator - Fix requirements.txt
  - [ ] Remove editable install (Gap #12)
  - [ ] Add documentation comment
- [ ] Update `scaffold` generator
  - [ ] Add build_context directory structure
  - [ ] Generate prepare_build_context.sh

### Phase 2: Add New Generator
- [ ] Create `infra` generator
  - [ ] Generate acr.bicep module
  - [ ] Generate container-apps-environment.bicep module
  - [ ] Generate container-app.bicep module
  - [ ] Generate main-simple.bicep orchestration
  - [ ] Generate parameters.dev.json
  - [ ] Generate infra/README.md

### Phase 3: Update Deployment Scripts
- [ ] Update `deployment` generator
  - [ ] Generate deploy-azure.sh
  - [ ] Generate build-and-push.sh
  - [ ] Update main deploy.sh to call these scripts

### Phase 4: Testing
- [ ] Generate new project with updated generators
- [ ] Test local deployment with ollama
- [ ] Test Azure deployment with OpenAI
- [ ] Verify all gaps are fixed
- [ ] Verify Bicep deployment works

---

## Template File Locations

### Existing Templates to Update:
```
templates/
├── agents/
│   └── base_agent.py.j2          # Update: Gaps #9, #10
├── api/
│   ├── Dockerfile.j2              # Update: Gap #11
│   └── requirements.txt.j2        # Update: Gap #12
└── scaffold/
    └── scripts/
        └── prepare_build_context.sh.j2  # NEW
```

### New Templates to Create:
```
templates/
└── infra/
    ├── modules/
    │   ├── acr.bicep.j2
    │   ├── container-apps-environment.bicep.j2
    │   └── container-app.bicep.j2
    ├── main-simple.bicep.j2
    ├── parameters.dev.json.j2
    └── README.md.j2
```

---

## Generator Target Selection

Update `goalgen.py` to include the new `infra` target:

```python
AVAILABLE_TARGETS = [
    'scaffold',
    'langgraph',
    'api',
    'teams',
    'webchat',
    'tools',
    'agents',
    'evaluators',
    'infra',        # NEW
    'security',
    'assets',
    'cicd',
    'deployment',
    'tests'
]
```

---

## Testing the Updated Generators

### Test Command:
```bash
./goalgen.py \
    --spec examples/travel_planning.json \
    --out test_generated \
    --targets scaffold,agents,api,infra,deployment
```

### Expected Generated Structure:
```
test_generated/
├── build_context/                   # NEW from scaffold
│   ├── Dockerfile
│   ├── frmk/
│   ├── workflow/
│   ├── config/
│   └── orchestrator/
├── frmk/
│   └── agents/
│       └── base_agent.py            # FIXED: Gaps #9, #10
├── orchestrator/
│   ├── Dockerfile                   # FIXED: Gap #11
│   └── requirements.txt             # FIXED: Gap #12
├── infra/                           # NEW from infra generator
│   ├── modules/
│   │   ├── acr.bicep
│   │   ├── container-apps-environment.bicep
│   │   └── container-app.bicep
│   ├── main-simple.bicep
│   ├── parameters.dev.json
│   └── README.md
└── scripts/                         # UPDATED from deployment
    ├── prepare_build_context.sh     # NEW
    ├── build-and-push.sh            # NEW
    └── deploy-azure.sh              # NEW
```

---

## Priority Order

1. **HIGH**: Fix agents generator (Gaps #9, #10) - Blocks all runtime testing
2. **HIGH**: Fix api generator (Gaps #11, #12) - Blocks cloud builds
3. **MEDIUM**: Add infra generator - Enables automated deployments
4. **MEDIUM**: Update deployment scripts - Improves DX
5. **LOW**: Add prepare_build_context.sh - Nice to have

---

## Success Criteria

✅ Generate new project with: `./goalgen.py --spec examples/travel_planning.json --out test_gen --targets all`

✅ Local test succeeds:
```bash
cd test_gen/orchestrator
uvicorn main:app --host 127.0.0.1 --port 8000 --env-file .env
curl -X POST http://127.0.0.1:8000/api/v1/message -d '{"thread_id":"t1","message":"test","user_id":"u1"}'
```

✅ Azure deployment succeeds:
```bash
cd test_gen
./scripts/prepare_build_context.sh
export ACR_NAME=myacr
./scripts/build-and-push.sh
export OPENAI_API_KEY=sk-...
./scripts/deploy-azure.sh
```

✅ All 4 gaps fixed in generated code

✅ Infrastructure deployable with one command

---

*Document Generated: 2025-12-02*
*Based on: E2E Runtime Testing (travel_planning example)*
*GoalGen Version: 0.2.0 → 0.3.0 (post-gap-fixes)*
