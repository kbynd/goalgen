# Testing Frameworks by Component

Comprehensive testing strategy and framework choices for each GoalGen component.

---

## Testing Strategy Overview

### Testing Pyramid

```
           /\
          /E2E\          Small number, slow, expensive
         /------\
        /  Integ \       Medium number, moderate speed
       /----------\
      /   Unit     \     Large number, fast, cheap
     /--------------\
```

### Testing Levels Generated

| Level | % of Tests | Speed | Cost | Frameworks |
|-------|------------|-------|------|------------|
| **Unit** | 70% | Fast (<1s) | Low | pytest, vitest |
| **Integration** | 20% | Medium (1-10s) | Medium | pytest + Docker Compose |
| **E2E** | 10% | Slow (10s-1m) | High | Playwright, pytest |
| **Load** | Ad-hoc | Varies | High | Locust, k6 |
| **Security** | CI-only | Medium | Medium | Bandit, Trivy, OWASP ZAP |

---

## 1. ORCHESTRATOR (FastAPI API)

### Unit Testing

**Framework**: pytest ^7.4.0

```python
# tests/unit/test_orchestrator.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_message_endpoint_auth_required(client):
    response = client.post("/api/v1/goal/travel_planning/message")
    assert response.status_code == 401
```

**Dependencies**:

| Library | Version | Purpose |
|---------|---------|---------|
| pytest | ^7.4.0 | Test framework |
| pytest-asyncio | ^0.21.0 | Async test support |
| pytest-mock | ^3.12.0 | Mocking/stubbing |
| pytest-cov | ^4.1.0 | Coverage reporting |
| fastapi[test] | ^0.104.0 | TestClient |
| httpx | ^0.25.0 | Async HTTP testing |
| faker | ^20.1.0 | Test data generation |

**Mocking Strategy**:
- Mock LangGraph invocations
- Mock Cosmos DB/Redis
- Mock Key Vault
- Mock SignalR

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_langgraph():
    with patch('app.orchestrator.LangGraphHost') as mock:
        mock.return_value.invoke.return_value = {"response": "test"}
        yield mock

def test_message_with_mock_langgraph(client, mock_langgraph):
    response = client.post("/api/v1/message", json={"text": "Hello"})
    assert response.status_code == 200
    mock_langgraph.return_value.invoke.assert_called_once()
```

### Integration Testing

**Framework**: pytest + Docker Compose

**Test Containers**:
- Cosmos DB Emulator: `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`
- Redis: `redis:7-alpine`
- Azurite (Storage): `mcr.microsoft.com/azure-storage/azurite`

```python
# tests/integration/test_orchestrator_integration.py
import pytest
from testcontainers.redis import RedisContainer
from testcontainers.compose import DockerCompose

@pytest.fixture(scope="session")
def services():
    with DockerCompose("tests", compose_file_name="docker-compose.test.yml") as compose:
        compose.wait_for("http://localhost:8081/_explorer/index.html")  # Cosmos
        yield compose

def test_full_message_flow(client, services):
    # Test with real Cosmos/Redis
    response = client.post("/api/v1/message", json={"text": "Plan trip to Japan"})
    assert response.status_code == 200
    # Verify state saved to Cosmos
```

**Dependencies**:
- testcontainers ^3.7.0
- docker-py ^6.1.0

### API Testing

**Framework**: pytest + Tavern (REST API testing)

```yaml
# tests/api/test_message_api.tavern.yaml
test_name: Message API flow

stages:
  - name: Send message
    request:
      url: http://localhost:8000/api/v1/message
      method: POST
      json:
        thread_id: "test-123"
        message: "Plan trip"
    response:
      status_code: 200
      json:
        response: !anything
```

**Alternative**: Postman/Newman for contract testing

### Performance Testing

**Framework**: Locust ^2.17.0

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class OrchstratorUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def send_message(self):
        self.client.post("/api/v1/message", json={
            "thread_id": f"thread-{self.environment.runner.user_count}",
            "message": "Plan trip"
        })
```

**Alternatives**:
- k6 (Go-based, better for CI)
- Artillery (Node-based)
- Azure Load Testing (managed service)

### Security Testing

**Tools**:
- **bandit** ^1.7.5 - Python security linter
- **safety** ^2.3.0 - Dependency vulnerability scanner
- **OWASP ZAP** - API security scanner (Docker)

```bash
# Run security scans
bandit -r app/
safety check
docker run -t zaproxy/zap-stable zap-api-scan.py -t http://localhost:8000/openapi.json
```

---

## 2. LANGGRAPH (Quest Builder)

### Unit Testing

**Framework**: pytest ^7.4.0

```python
# tests/unit/test_quest_builder.py
import pytest
from langgraph.quest_builder import build_graph, QuestState

@pytest.fixture
def graph():
    return build_graph()

def test_supervisor_node():
    state = QuestState(context={"destination": "Japan"}, messages=[])
    result = supervisor(state)
    assert result["next"] == "run_tasks"

def test_evaluator_missing_field():
    state = QuestState(context={}, messages=[])
    result = evaluator_missing_info(state)
    assert result["next"] == "ask_missing"
    assert "destination" in result["missing"]
```

**Dependencies**:

| Library | Version | Purpose |
|---------|---------|---------|
| pytest | ^7.4.0 | Test framework |
| pytest-asyncio | ^0.21.0 | Async support |
| pytest-mock | ^3.12.0 | Mocking |
| langchain-testing | ^0.1.0 | LangChain test utils |
| faker | ^20.1.0 | Test data |

**Mocking Strategy**:
- Mock LLM calls (OpenAI)
- Mock checkpointer (Cosmos/Redis)
- Mock tool executions

```python
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage

@pytest.fixture
def mock_llm():
    with patch('langchain_openai.ChatOpenAI') as mock:
        mock.return_value.ainvoke = AsyncMock(
            return_value=AIMessage(content="Mocked response")
        )
        yield mock

async def test_agent_with_mock_llm(mock_llm):
    graph = build_graph()
    result = await graph.ainvoke({"messages": [("user", "Hello")]})
    assert "response" in result
```

### State Testing

**Custom Fixtures**:

```python
# tests/fixtures/state_fixtures.py
import pytest

@pytest.fixture
def empty_state():
    return QuestState(context={}, messages=[], next="supervisor")

@pytest.fixture
def partial_state():
    return QuestState(
        context={"destination": "Japan"},
        messages=[],
        missing=["budget", "dates"]
    )

@pytest.fixture
def complete_state():
    return QuestState(
        context={
            "destination": "Japan",
            "budget": 5000,
            "dates": "2024-06-01 to 2024-06-07"
        },
        messages=[]
    )
```

### Integration Testing

**Framework**: pytest + Real Checkpointer

```python
# tests/integration/test_langgraph_integration.py
import pytest
from azure.cosmos import CosmosClient

@pytest.fixture
def cosmos_checkpointer():
    # Use test Cosmos instance
    client = CosmosClient(TEST_COSMOS_URL, TEST_COSMOS_KEY)
    return CosmosCheckpointer(client, database="test", container="checkpoints")

async def test_conversation_persistence(cosmos_checkpointer):
    graph = build_graph(checkpointer=cosmos_checkpointer)

    # First message
    result1 = await graph.ainvoke(
        {"messages": [("user", "Plan trip")]},
        config={"configurable": {"thread_id": "test-123"}}
    )

    # Second message (should have state from first)
    result2 = await graph.ainvoke(
        {"messages": [("user", "Budget is $5000")]},
        config={"configurable": {"thread_id": "test-123"}}
    )

    # Verify state persisted
    assert result2["context"]["budget"] == 5000
```

### Graph Flow Testing

**Framework**: pytest + Graph visualization

```python
def test_graph_structure():
    graph = build_graph()

    # Verify nodes
    assert "supervisor" in graph.nodes
    assert "ask_missing" in graph.nodes
    assert all(f"run_task_{task_id}" in graph.nodes for task_id in TASK_IDS)

    # Verify edges
    edges = graph.get_edges()
    assert ("supervisor", "ask_missing") in edges
    assert ("supervisor", "run_tasks") in edges
```

---

## 3. AGENTS

### Unit Testing

**Framework**: pytest ^7.4.0

```python
# tests/unit/test_agents.py
import pytest
from agents.flight_agent import FlightAgent

@pytest.fixture
def agent():
    return FlightAgent(tools=["flight_api"], max_loop=3)

@pytest.mark.asyncio
async def test_agent_invoke(agent, mock_llm, mock_tool):
    result = await agent.ainvoke("Find flights to Japan")
    assert "flight" in result.lower()
    assert mock_tool.called
```

**Dependencies**:
- pytest ^7.4.0
- pytest-asyncio ^0.21.0
- pytest-mock ^3.12.0
- respx ^0.20.0 (HTTP mocking for httpx)
- vcr.py ^5.1.0 (Record/replay HTTP interactions)

**Mocking Strategy**:
- Mock LLM responses
- Mock tool calls
- Mock retry logic

```python
from respx import MockRouter

@pytest.fixture
def mock_flight_api():
    with MockRouter() as router:
        router.post("https://api.flights.com/search").mock(
            return_value=httpx.Response(200, json={"flights": [...]})
        )
        yield router

async def test_agent_with_mock_tool(agent, mock_flight_api):
    result = await agent.ainvoke("Find flights")
    assert mock_flight_api.calls.called
```

### VCR Testing (Record/Replay)

**Framework**: vcrpy ^5.1.0

```python
# tests/unit/test_agents_vcr.py
import vcr

@vcr.use_cassette('tests/fixtures/vcr_cassettes/flight_search.yaml')
async def test_agent_real_api():
    # First run: records real API call
    # Subsequent runs: replays from cassette
    agent = FlightAgent()
    result = await agent.ainvoke("Find flights to Japan")
    assert "flight" in result
```

### Behavior Testing

**Framework**: pytest-bdd ^6.1.0 (Gherkin-style)

```gherkin
# tests/bdd/flight_agent.feature
Feature: Flight Agent
  Scenario: Search for flights
    Given an agent with flight_api tool
    When I ask "Find flights to Japan in June"
    Then the agent should call the flight_api
    And the response should contain flight options
```

```python
# tests/bdd/test_flight_agent.py
from pytest_bdd import scenarios, given, when, then

scenarios('flight_agent.feature')

@given('an agent with flight_api tool')
def agent():
    return FlightAgent(tools=["flight_api"])

@when(parsers.parse('I ask "{query}"'))
async def invoke_agent(agent, query):
    agent.result = await agent.ainvoke(query)

@then('the agent should call the flight_api')
def verify_tool_called(agent, mock_tool):
    assert mock_tool.called
```

---

## 4. EVALUATORS

### Unit Testing

**Framework**: pytest ^7.4.0

```python
# tests/unit/test_evaluators.py
import pytest
from evaluators.missing_info import MissingInfoEvaluator
from evaluators.budget import BudgetEvaluator

@pytest.fixture
def evaluator():
    return MissingInfoEvaluator(fields=["destination", "budget", "dates"])

async def test_evaluator_missing_field(evaluator):
    context = {"destination": "Japan"}
    is_valid, errors = await evaluator.evaluate(context)
    assert not is_valid
    assert "budget" in errors[0]
    assert "dates" in errors[1]

async def test_evaluator_all_present(evaluator):
    context = {"destination": "Japan", "budget": 5000, "dates": "2024-06-01"}
    is_valid, errors = await evaluator.evaluate(context)
    assert is_valid
    assert len(errors) == 0
```

### Parametric Testing

**Framework**: pytest.mark.parametrize

```python
@pytest.mark.parametrize("budget,expected_valid", [
    (100, False),      # Too low
    (1000, True),      # Valid
    (50000, True),     # Valid max
    (100000, False),   # Too high
])
async def test_budget_evaluator(budget, expected_valid):
    evaluator = BudgetEvaluator(min=1000, max=50000)
    context = {"budget": budget}
    is_valid, _ = await evaluator.evaluate(context)
    assert is_valid == expected_valid
```

### Property-Based Testing

**Framework**: hypothesis ^6.90.0

```python
from hypothesis import given, strategies as st

@given(st.floats(min_value=0, max_value=1000000))
async def test_budget_evaluator_property(budget):
    evaluator = BudgetEvaluator(min=1000, max=50000)
    context = {"budget": budget}
    is_valid, errors = await evaluator.evaluate(context)

    # Property: if budget in range, must be valid
    if 1000 <= budget <= 50000:
        assert is_valid
    else:
        assert not is_valid
```

---

## 5. TOOLS (Azure Functions / HTTP Wrappers)

### Unit Testing - HTTP Tools

**Framework**: pytest + respx

```python
# tests/unit/test_flight_tool.py
import pytest
import respx
from tools.flight_api import FlightTool

@pytest.fixture
def tool():
    return FlightTool(api_url="https://api.flights.com", api_key="test-key")

@respx.mock
async def test_flight_search(tool):
    respx.post("https://api.flights.com/search").mock(
        return_value=httpx.Response(200, json={"flights": [{"id": 1}]})
    )

    result = await tool.search(origin="NYC", destination="TYO")
    assert len(result["flights"]) == 1
```

**Dependencies**:
- pytest ^7.4.0
- pytest-asyncio ^0.21.0
- respx ^0.20.0 (httpx mocking)
- responses ^0.24.0 (requests mocking, if using requests)

### Unit Testing - Azure Functions

**Framework**: pytest + azure-functions-testing

```python
# tests/unit/test_flight_function.py
import pytest
import azure.functions as func
from function_app import main

def test_flight_function_http_trigger():
    # Create test request
    req = func.HttpRequest(
        method='POST',
        body=b'{"origin": "NYC", "destination": "TYO"}',
        url='/api/flight/search'
    )

    # Call function
    resp = main(req)

    assert resp.status_code == 200
    assert "flights" in resp.get_body().decode()
```

**Dependencies**:
- pytest ^7.4.0
- azure-functions ^1.17.0
- azure-functions-testing ^1.0.0

### Integration Testing - Real APIs

**Framework**: pytest + VCR

```python
import vcr

@vcr.use_cassette('tests/fixtures/flight_api_real.yaml')
async def test_flight_tool_integration():
    tool = FlightTool(api_url=REAL_API_URL, api_key=REAL_API_KEY)
    result = await tool.search(origin="NYC", destination="TYO")
    assert len(result["flights"]) > 0
```

### Contract Testing

**Framework**: pact-python ^2.1.0

```python
from pact import Consumer, Provider

pact = Consumer('OrchestatorAPI').has_pact_with(Provider('FlightAPI'))

def test_flight_search_contract():
    (pact
     .given('flights exist for NYC to TYO')
     .upon_receiving('a search request')
     .with_request('POST', '/search', body={"origin": "NYC", "destination": "TYO"})
     .will_respond_with(200, body={"flights": [...]})
    )

    with pact:
        # Run test
        pass
```

### Retry/Circuit Breaker Testing

```python
@pytest.mark.asyncio
async def test_tool_retry_on_failure():
    with respx.mock:
        route = respx.post("https://api.flights.com/search")
        route.side_effect = [
            httpx.Response(500),  # First call fails
            httpx.Response(500),  # Second call fails
            httpx.Response(200, json={"flights": []})  # Third succeeds
        ]

        tool = FlightTool(max_retries=3)
        result = await tool.search(origin="NYC", destination="TYO")
        assert result is not None
        assert route.call_count == 3
```

---

## 6. INFRASTRUCTURE (Bicep)

### Validation Testing

**Framework**: Bicep CLI + PSRule

```bash
# Validate Bicep syntax
bicep build infra/main.bicep

# Lint Bicep
bicep lint infra/main.bicep

# Test with PSRule
Install-Module -Name PSRule.Rules.Azure
Assert-PSRule -InputPath infra/ -Module PSRule.Rules.Azure
```

### What-If Testing

```bash
# Test deployment (dry-run)
az deployment group what-if \
  --resource-group rg-goalgen-dev \
  --template-file infra/main.bicep \
  --parameters infra/parameters.dev.json
```

### Infrastructure Testing

**Framework**: pytest + Azure SDK

```python
# tests/infra/test_bicep_deployment.py
import pytest
from azure.mgmt.resource import ResourceManagementClient
from azure.identity import DefaultAzureCredential

@pytest.fixture
def resource_client():
    credential = DefaultAzureCredential()
    return ResourceManagementClient(credential, SUBSCRIPTION_ID)

def test_container_app_exists(resource_client):
    resources = resource_client.resources.list_by_resource_group(
        "rg-goalgen-test"
    )
    container_apps = [r for r in resources if r.type == "Microsoft.App/containerApps"]
    assert len(container_apps) > 0
    assert container_apps[0].name.startswith("ca-goalgen")
```

### Terraform Testing (Alternative)

**Framework**: Terratest (Go)

```go
// tests/infra/terraform_test.go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/azure"
    "github.com/gruntwork-io/terratest/modules/terraform"
)

func TestTerraformInfra(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../../infra",
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Verify resources
    resourceGroupName := terraform.Output(t, terraformOptions, "resource_group_name")
    azure.ResourceGroupExists(t, resourceGroupName, "")
}
```

---

## 7. SECURITY

### Static Analysis

**Tools**:
- bandit ^1.7.5 - Python security linter
- safety ^2.3.0 - Dependency scanner
- semgrep ^1.45.0 - Multi-language SAST

```bash
# Python security scan
bandit -r app/ -f json -o bandit-report.json

# Dependency vulnerabilities
safety check --json

# SAST
semgrep --config=auto app/
```

### Container Scanning

**Tools**:
- Trivy ^0.48.0 - Container vulnerability scanner
- Grype - Alternative scanner

```bash
# Scan container image
trivy image acr.azurecr.io/goalgen/orchestrator:latest

# Scan IaC
trivy config infra/
```

### Dynamic Application Security Testing (DAST)

**Tools**:
- OWASP ZAP - API security scanner
- Burp Suite - Manual testing

```bash
# ZAP API scan
docker run -t zaproxy/zap-stable zap-api-scan.py \
  -t http://localhost:8000/openapi.json \
  -f openapi
```

### Secret Scanning

**Tools**:
- gitleaks ^8.18.0 - Secret scanner
- trufflehog - Alternative

```bash
# Scan for secrets in repo
gitleaks detect --source . --verbose

# Scan git history
trufflehog git file://. --json
```

---

## 8. TEAMS BOT

### Unit Testing

**Framework**: pytest + botbuilder-testing

```python
# tests/unit/test_teams_bot.py
import pytest
from botbuilder.testing import DialogTestClient
from bots.teams_bot import TeamsBot

@pytest.fixture
def bot():
    return TeamsBot()

async def test_bot_welcome_message(bot):
    client = DialogTestClient("test", bot.on_turn)

    reply = await client.send_activity("Hello")
    assert "Welcome" in reply.text
```

### Adaptive Card Testing

**Framework**: AdaptiveCards Validator

```python
# tests/unit/test_adaptive_cards.py
import json
from adaptivecards import AdaptiveCard

def test_travel_card_valid():
    with open("teams_app/adaptive_cards/travel_response.json") as f:
        card_json = json.load(f)

    # Validate schema
    card = AdaptiveCard.from_json(card_json)
    assert card.validate()
```

### Teams Manifest Testing

```python
def test_teams_manifest_valid():
    with open("teams_app/manifest.json") as f:
        manifest = json.load(f)

    assert manifest["manifestVersion"] == "1.16"
    assert len(manifest["bots"]) > 0
    assert "botId" in manifest["bots"][0]
```

---

## 9. WEBCHAT SPA

### Unit Testing

**Framework**: Vitest ^1.0.0

```typescript
// tests/unit/ChatMessage.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ChatMessage from '@/components/ChatMessage'

describe('ChatMessage', () => {
  it('renders user message', () => {
    render(<ChatMessage role="user" content="Hello" />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders bot message with markdown', () => {
    render(<ChatMessage role="assistant" content="**Bold** text" />)
    expect(screen.getByText('Bold')).toHaveStyle({ fontWeight: 'bold' })
  })
})
```

**Dependencies**:

| Library | Version | Purpose |
|---------|---------|---------|
| vitest | ^1.0.0 | Test framework (fast, Vite-native) |
| @testing-library/react | ^14.1.0 | React component testing |
| @testing-library/user-event | ^14.5.0 | User interaction simulation |
| @testing-library/jest-dom | ^6.1.0 | DOM matchers |
| jsdom | ^23.0.0 | DOM implementation |
| @vitest/ui | ^1.0.0 | UI test runner |

### Component Testing

```typescript
// tests/unit/ChatInput.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatInput from '@/components/ChatInput'

describe('ChatInput', () => {
  it('calls onSend when message submitted', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()

    render(<ChatInput onSend={onSend} />)

    await user.type(screen.getByRole('textbox'), 'Hello')
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(onSend).toHaveBeenCalledWith('Hello')
  })
})
```

### Integration Testing - SignalR

```typescript
// tests/integration/signalr.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HubConnectionBuilder } from '@microsoft/signalr'

vi.mock('@microsoft/signalr')

describe('SignalR Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('connects to SignalR hub on mount', async () => {
    const mockStart = vi.fn().mockResolvedValue(undefined)
    HubConnectionBuilder.mockImplementation(() => ({
      withUrl: vi.fn().mockReturnThis(),
      build: vi.fn().mockReturnValue({
        start: mockStart,
        on: vi.fn()
      })
    }))

    render(<ChatApp />)
    await waitFor(() => expect(mockStart).toHaveBeenCalled())
  })
})
```

### E2E Testing

**Framework**: Playwright ^1.40.0

```typescript
// tests/e2e/chat.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Webchat E2E', () => {
  test('send message and receive response', async ({ page }) => {
    await page.goto('http://localhost:5173')

    // Send message
    await page.fill('[data-testid="chat-input"]', 'Plan a trip to Japan')
    await page.click('[data-testid="send-button"]')

    // Wait for response
    await expect(page.locator('[data-testid="message"]').last()).toContainText('Japan')
  })

  test('displays error on connection failure', async ({ page }) => {
    await page.route('**/signalr/**', route => route.abort())
    await page.goto('http://localhost:5173')

    await expect(page.locator('[data-testid="error"]')).toBeVisible()
  })
})
```

**Playwright Configuration**:

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: true
  }
})
```

### Visual Regression Testing

**Framework**: Playwright + Percy/Chromatic

```typescript
// tests/visual/chat.spec.ts
import { test } from '@playwright/test'
import percySnapshot from '@percy/playwright'

test('chat UI visual regression', async ({ page }) => {
  await page.goto('http://localhost:5173')
  await percySnapshot(page, 'Empty Chat')

  // Add messages
  await page.fill('[data-testid="chat-input"]', 'Hello')
  await page.click('[data-testid="send-button"]')
  await page.waitForTimeout(1000)

  await percySnapshot(page, 'Chat with Messages')
})
```

### Accessibility Testing

**Framework**: axe-core + @axe-core/playwright

```typescript
// tests/a11y/chat.spec.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('chat should not have accessibility violations', async ({ page }) => {
  await page.goto('http://localhost:5173')

  const accessibilityScanResults = await new AxeBuilder({ page }).analyze()

  expect(accessibilityScanResults.violations).toEqual([])
})
```

---

## 10. CI/CD PIPELINE

### Pipeline Testing

**Framework**: act (local GitHub Actions)

```bash
# Test GitHub Actions locally
act -j test
act -j build
act -j deploy --secret-file .secrets
```

### Workflow Validation

```bash
# Validate workflow syntax
actionlint .github/workflows/*.yml

# Validate with GitHub API
gh api repos/:owner/:repo/actions/workflows/:workflow_id/syntax
```

---

## 11. DEPLOYMENT SCRIPTS

### Shell Script Testing

**Framework**: bats (Bash Automated Testing System)

```bash
# tests/deployment/deploy.bats
#!/usr/bin/env bats

@test "deploy.sh requires environment parameter" {
  run ./scripts/deploy.sh
  [ "$status" -eq 1 ]
  [[ "$output" =~ "Environment required" ]]
}

@test "deploy.sh validates environment value" {
  run ./scripts/deploy.sh invalid-env
  [ "$status" -eq 1 ]
  [[ "$output" =~ "Invalid environment" ]]
}

@test "deploy.sh dry-run mode works" {
  run ./scripts/deploy.sh dev --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" =~ "DRY RUN" ]]
}
```

**Dependencies**:
- bats ^1.10.0
- shellcheck ^0.9.0 (linting)

### PowerShell Testing

**Framework**: Pester ^5.5.0

```powershell
# tests/deployment/Deploy.Tests.ps1
Describe "Deploy Script" {
    It "Requires Environment parameter" {
        { ./scripts/Deploy.ps1 } | Should -Throw
    }

    It "Validates environment value" {
        { ./scripts/Deploy.ps1 -Environment "invalid" } | Should -Throw
    }

    It "Dry run mode works" {
        $result = ./scripts/Deploy.ps1 -Environment "dev" -DryRun
        $result | Should -Contain "DRY RUN"
    }
}
```

---

## 12. GOALGEN CLI (Generator Itself)

### Unit Testing - Template Rendering

```python
# tests/unit/test_generators.py
import pytest
from generators.scaffold import generate as scaffold_gen

def test_scaffold_generator(tmp_path):
    spec = {"id": "test_goal", "title": "Test Goal"}
    scaffold_gen(spec, str(tmp_path), dry_run=False)

    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "LICENSE").exists()

    # Verify README content
    readme_content = (tmp_path / "README.md").read_text()
    assert "Test Goal" in readme_content
```

### Integration Testing - Full Generation

```python
# tests/integration/test_full_generation.py
import pytest
import subprocess

def test_full_goal_generation(tmp_path):
    spec_file = "tests/fixtures/travel_planning.json"
    output_dir = tmp_path / "generated"

    # Run goalgen
    result = subprocess.run(
        ["python", "goalgen.py", "--spec", spec_file, "--out", str(output_dir)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert (output_dir / "orchestrator" / "app" / "main.py").exists()
    assert (output_dir / "infra" / "main.bicep").exists()
    assert (output_dir / "langgraph" / "quest_builder.py").exists()
```

### Golden File Testing

```python
# tests/golden/test_generated_output.py
import pytest
import difflib

def test_scaffold_readme_matches_golden(tmp_path):
    spec = load_fixture("travel_planning.json")
    scaffold_gen(spec, str(tmp_path))

    generated = (tmp_path / "README.md").read_text()
    golden = (Path("tests/golden") / "README.md").read_text()

    diff = list(difflib.unified_diff(golden.splitlines(), generated.splitlines()))
    assert len(diff) == 0, f"Generated README differs from golden:\n{'\n'.join(diff)}"
```

---

## Testing Infrastructure

### Test Fixtures & Data

**Structure**:
```
tests/
├── fixtures/
│   ├── specs/
│   │   ├── travel_planning.json
│   │   └── expense_reporting.json
│   ├── vcr_cassettes/
│   │   └── flight_api.yaml
│   ├── responses/
│   │   └── mock_llm_responses.json
│   └── data/
│       └── sample_contexts.py
├── conftest.py              # Shared pytest fixtures
└── factories/               # Factory pattern for test data
    ├── context_factory.py
    └── message_factory.py
```

**Example conftest.py**:
```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def travel_spec(fixtures_dir):
    with open(fixtures_dir / "specs" / "travel_planning.json") as f:
        return json.load(f)

@pytest.fixture
def mock_cosmos():
    # Return mock Cosmos client
    pass

@pytest.fixture(autouse=True)
def reset_state():
    # Reset any global state before each test
    yield
    # Cleanup after test
```

### Test Data Factories

**Framework**: factory_boy ^3.3.0

```python
# tests/factories/context_factory.py
import factory
from faker import Faker

fake = Faker()

class TravelContextFactory(factory.Factory):
    class Meta:
        model = dict

    destination = factory.LazyFunction(lambda: fake.city())
    budget = factory.LazyFunction(lambda: fake.random_int(min=1000, max=50000))
    dates = factory.LazyFunction(
        lambda: f"{fake.date_between('+1d', '+30d')} to {fake.date_between('+31d', '+60d')}"
    )
    num_travelers = factory.LazyFunction(lambda: fake.random_int(min=1, max=10))

# Usage
def test_with_factory():
    context = TravelContextFactory()
    # context = {"destination": "Paris", "budget": 5000, ...}
```

---

## Code Coverage

### Backend Coverage

**Tools**:
- pytest-cov ^4.1.0
- coverage.py ^7.3.0

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Coverage thresholds
pytest --cov=app --cov-fail-under=80
```

**Configuration** (pyproject.toml):
```toml
[tool.coverage.run]
source = ["app", "langgraph", "agents"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### Frontend Coverage

**Tools**:
- Vitest coverage (via c8 or istanbul)

```bash
# Run with coverage
vitest run --coverage

# View HTML report
open coverage/index.html
```

**Configuration** (vite.config.ts):
```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: 'c8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['**/*.spec.ts', '**/node_modules/**']
    }
  }
})
```

---

## CI Integration

### GitHub Actions Test Workflow

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/unit --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      cosmos:
        image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
        ports:
          - 8081:8081
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r app/
      - run: safety check
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
```

---

## Test Organization Best Practices

### Directory Structure

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_agents.py
│   ├── test_evaluators.py
│   ├── test_orchestrator.py
│   └── test_tools.py
├── integration/            # Service integration tests
│   ├── test_api_integration.py
│   ├── test_langgraph_flow.py
│   └── test_cosmos_persistence.py
├── e2e/                    # End-to-end scenarios
│   ├── test_goal_workflow.py
│   └── playwright/
│       ├── chat.spec.ts
│       └── teams.spec.ts
├── performance/            # Load tests
│   └── locustfile.py
├── security/               # Security tests
│   └── test_security.py
├── fixtures/               # Test data
│   ├── specs/
│   ├── vcr_cassettes/
│   └── responses/
├── factories/              # Test data factories
├── golden/                 # Golden file tests
├── conftest.py            # Shared fixtures
└── pytest.ini             # Pytest config
```

### Test Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast)
    integration: Integration tests (medium)
    e2e: End-to-end tests (slow)
    slow: Slow tests
    smoke: Smoke tests
    security: Security tests
    load: Load tests

# Run specific markers
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Skip slow tests
pytest -m "unit or integration"  # Unit and integration
```

---

## Summary: Recommended Testing Stack

| Component | Unit | Integration | E2E | Load | Security |
|-----------|------|-------------|-----|------|----------|
| **Orchestrator** | pytest + FastAPI TestClient | pytest + Docker Compose | Playwright | Locust | Bandit, ZAP |
| **LangGraph** | pytest + mocks | pytest + real checkpointer | - | - | - |
| **Agents** | pytest + respx | pytest + VCR | - | - | - |
| **Evaluators** | pytest + hypothesis | - | - | - | - |
| **Tools** | pytest + respx | pytest + VCR | - | - | - |
| **Infra** | Bicep lint | What-if | pytest + Azure SDK | - | Trivy |
| **Teams Bot** | pytest + botbuilder-testing | Manual | - | - | - |
| **Webchat** | Vitest + Testing Library | - | Playwright | - | - |
| **Scripts** | bats / Pester | - | - | - | shellcheck |
| **GoalGen** | pytest | pytest (full gen) | - | - | - |

### Key Dependencies Summary

**Python Testing**:
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
pytest-cov>=4.1.0
respx>=0.20.0
hypothesis>=6.90.0
faker>=20.1.0
factory-boy>=3.3.0
vcrpy>=5.1.0
locust>=2.17.0
bandit>=1.7.5
safety>=2.3.0
```

**TypeScript Testing**:
```
vitest@^1.0.0
@testing-library/react@^14.1.0
@testing-library/user-event@^14.5.0
@playwright/test@^1.40.0
@axe-core/playwright@^4.8.0
```

**Tools**:
```
Docker Compose (integration tests)
Bicep CLI (infra validation)
actionlint (CI/CD validation)
shellcheck (script linting)
Trivy (container scanning)
```
