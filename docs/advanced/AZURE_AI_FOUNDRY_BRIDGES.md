# Azure AI Foundry Bridges - Complete Core SDK Architecture

**Every component** in GoalGen needs a Core SDK bridge to Azure AI Foundry.

---

## Component-to-Bridge Mapping

| Component | Core SDK Bridge | Azure AI Foundry Integration | Purpose |
|-----------|----------------|------------------------------|---------|
| **Agents** | `frmk/agents/base_agent.py` | Prompt Flow prompts | Load agent system prompts |
| **LangGraph** | `frmk/langgraph/graph_builder.py` | Orchestration tracking | Track graph execution metrics |
| **Evaluators** | `frmk/evaluators/base_evaluator.py` | Evaluation metrics | Track validation results |
| **Tools** | `frmk/tools/base_tool.py` | Tool monitoring | Monitor tool calls & latency |
| **API** | `frmk/api/base_service.py` | Request tracing | Trace API requests end-to-end |
| **Teams** | `frmk/teams/bot_adapter.py` | Conversation analytics | Track Teams interactions |
| **Webchat** | `frmk/webchat/chat_client.ts` | User analytics | Track webchat sessions |
| **Infra** | `frmk/infra/resource_manager.py` | Resource monitoring | Monitor deployed resources |
| **Security** | `frmk/security/auth_helper.py` | Security events | Audit auth events |
| **Assets** | `frmk/assets/asset_loader.py` | Asset versioning | Version prompts, cards, images |
| **CI/CD** | `frmk/cicd/deployment_tracker.py` | Deployment tracking | Track deployments |
| **Tests** | `frmk/testing/test_harness.py` | Test results | Report test metrics |

---

## Complete Core SDK Structure

```
frmk/                                    # GoalGen Core SDK
│
├── agents/                              # AGENT BRIDGES
│   ├── base_agent.py                   # ✅ Already implemented
│   ├── supervisor_agent.py             # Supervisor pattern
│   └── llm_agent.py                    # Standard LLM agent
│
├── tools/                               # TOOL BRIDGES
│   ├── base_tool.py                    # ✅ Already implemented
│   ├── http_tool.py                    # ✅ Already implemented
│   ├── websocket_tool.py               # ✅ Already implemented
│   └── function_tool.py                # Local Python functions
│
├── langgraph/                           # LANGGRAPH BRIDGES
│   ├── graph_builder.py                # Graph construction helper
│   ├── state_schema.py                 # State schema generation
│   └── execution_tracker.py            # Track graph execution in AI Foundry
│
├── evaluators/                          # EVALUATOR BRIDGES
│   ├── base_evaluator.py               # Base evaluator class
│   ├── field_validator.py              # Pydantic field validation
│   └── rule_engine.py                  # Business rules engine
│
├── api/                                 # API BRIDGES
│   ├── base_service.py                 # FastAPI base service
│   ├── auth_middleware.py              # JWT validation
│   ├── rbac_middleware.py              # Role-based access control
│   └── request_tracer.py               # Distributed tracing to AI Foundry
│
├── teams/                               # TEAMS BRIDGES
│   ├── bot_adapter.py                  # Bot Framework adapter
│   ├── adaptive_card_builder.py        # Adaptive Card generator
│   └── conversation_tracker.py         # Track Teams conversations
│
├── webchat/                             # WEBCHAT BRIDGES (TypeScript)
│   ├── chat_client.ts                  # WebChat client SDK
│   ├── signalr_connector.ts            # SignalR connection
│   └── session_tracker.ts              # Track webchat sessions
│
├── infra/                               # INFRA BRIDGES
│   ├── resource_manager.py             # Azure resource management
│   ├── bicep_validator.py              # Validate Bicep templates
│   └── deployment_orchestrator.py      # Orchestrate deployments
│
├── security/                            # SECURITY BRIDGES
│   ├── auth_helper.py                  # Managed Identity + Entra ID
│   ├── secret_manager.py               # Key Vault integration
│   └── audit_logger.py                 # Security audit logging
│
├── assets/                              # ASSET BRIDGES
│   ├── asset_loader.py                 # Load assets from AI Foundry
│   ├── prompt_manager.py               # Prompt versioning
│   └── card_template_loader.py         # Adaptive Card templates
│
├── checkpointers/                       # CHECKPOINT BRIDGES
│   ├── base_checkpointer.py            # Base checkpointer interface
│   ├── cosmos_checkpointer.py          # Cosmos DB implementation
│   ├── redis_checkpointer.py           # Redis implementation
│   └── blob_checkpointer.py            # Blob Storage implementation
│
├── cicd/                                # CI/CD BRIDGES
│   ├── deployment_tracker.py           # Track deployments in AI Foundry
│   ├── pipeline_validator.py           # Validate CI/CD config
│   └── rollback_manager.py             # Automated rollback
│
├── testing/                             # TESTING BRIDGES
│   ├── test_harness.py                 # Test execution framework
│   ├── mock_services.py                # Mock Azure services
│   └── metrics_reporter.py             # Report test results to AI Foundry
│
├── core/                                # CORE UTILITIES
│   ├── prompt_loader.py                # ✅ Already implemented
│   ├── tool_registry.py                # ✅ Already implemented
│   ├── state_manager.py                # State management
│   ├── config.py                       # Configuration loader
│   └── ai_foundry_client.py            # AI Foundry SDK wrapper
│
└── utils/                               # SHARED UTILITIES
    ├── logging.py                      # ✅ Already implemented
    ├── retry.py                        # ✅ Already implemented
    ├── metrics.py                      # Application Insights
    ├── tracing.py                      # Distributed tracing
    └── cache.py                        # Caching utilities
```

---

## Bridge Implementation Details

### 1. **LangGraph Bridge** - `frmk/langgraph/graph_builder.py`

```python
"""
LangGraph Bridge to Azure AI Foundry
Tracks graph execution and reports to AI Foundry
"""

from langgraph.graph import StateGraph
from typing import Dict, Any
from frmk.core.ai_foundry_client import get_ai_foundry_client
from frmk.utils.logging import get_logger

logger = get_logger("graph_builder")


class GraphBuilder:
    """
    Helper to build LangGraph graphs with AI Foundry integration

    Features:
    - Auto-register nodes in AI Foundry
    - Track execution metrics
    - Report errors and bottlenecks
    """

    def __init__(self, goal_config: Dict[str, Any]):
        self.goal_config = goal_config
        self.goal_id = goal_config["id"]
        self.ai_foundry = get_ai_foundry_client(goal_config)

    def build_from_spec(self) -> StateGraph:
        """
        Build LangGraph from goal spec

        Automatically:
        - Creates nodes for each task
        - Wires edges based on topology
        - Adds execution tracking
        """

        from frmk.langgraph.state_schema import create_state_schema

        # Generate state schema from spec
        StateClass = create_state_schema(self.goal_config)

        graph = StateGraph(StateClass)

        # Add nodes from spec
        tasks = self.goal_config.get("tasks", [])
        for task in tasks:
            node_name = task["id"]
            node_fn = self._create_tracked_node(task)
            graph.add_node(node_name, node_fn)

            # Register in AI Foundry
            self._register_node_in_foundry(node_name, task)

        # Wire edges based on topology
        topology = self.goal_config.get("topology", {})
        self._wire_edges(graph, topology)

        return graph

    def _create_tracked_node(self, task: Dict):
        """Wrap node function with AI Foundry tracking"""

        async def tracked_node(state: Dict[str, Any]) -> Dict[str, Any]:
            task_id = task["id"]

            # Start tracking
            trace_id = self.ai_foundry.start_trace(
                operation=task_id,
                goal_id=self.goal_id
            )

            try:
                # Execute actual node logic
                if task["type"] == "task":
                    agent_name = task["agent"]
                    from frmk.core.tool_registry import get_tool_registry
                    # ... execute agent
                    result = {"next": "END"}

                elif task["type"] == "evaluator":
                    evaluator_id = task["evaluator"]
                    # ... execute evaluator
                    result = {"next": "END"}

                # Track success
                self.ai_foundry.end_trace(trace_id, success=True)

                return result

            except Exception as e:
                # Track failure
                self.ai_foundry.end_trace(trace_id, success=False, error=str(e))
                raise

        return tracked_node

    def _register_node_in_foundry(self, node_name: str, task: Dict):
        """Register node in AI Foundry for monitoring"""

        self.ai_foundry.register_node(
            goal_id=self.goal_id,
            node_name=node_name,
            node_type=task["type"],
            metadata=task
        )

    def _wire_edges(self, graph: StateGraph, topology: Dict):
        """Wire edges based on topology pattern"""

        topology_type = topology.get("type", "sequential")

        if topology_type == "supervisor":
            # Supervisor pattern
            supervisor = topology["supervisor_agent"]
            workers = topology["workers"]

            graph.set_entry_point(supervisor)

            # Supervisor routes to workers
            for worker in workers:
                graph.add_edge(supervisor, worker)
                graph.add_edge(worker, supervisor)  # Workers return to supervisor

        elif topology_type == "sequential":
            # Sequential chain
            tasks = self.goal_config.get("tasks", [])
            for i, task in enumerate(tasks):
                if i == 0:
                    graph.set_entry_point(task["id"])
                else:
                    graph.add_edge(tasks[i-1]["id"], task["id"])

        # ... other topologies
```

### 2. **Evaluator Bridge** - `frmk/evaluators/base_evaluator.py`

```python
"""
Evaluator Bridge to Azure AI Foundry
Tracks validation results and reports to AI Foundry
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError
from frmk.core.ai_foundry_client import get_ai_foundry_client
from frmk.utils.logging import get_logger


class EvaluationResult(BaseModel):
    """Evaluation result"""
    passed: bool
    missing_fields: List[str] = []
    validation_errors: List[str] = []
    actions: List[str] = []  # ask_user, set_default, etc.


class BaseEvaluator(ABC):
    """
    Base class for all evaluators

    Features:
    - Pydantic validation
    - AI Foundry reporting
    - Action recommendations
    """

    def __init__(
        self,
        evaluator_id: str,
        evaluator_config: Dict[str, Any],
        goal_config: Dict[str, Any]
    ):
        self.evaluator_id = evaluator_id
        self.config = evaluator_config
        self.goal_config = goal_config

        self.logger = get_logger(f"evaluator.{evaluator_id}")
        self.ai_foundry = get_ai_foundry_client(goal_config)

        # Load checks from config
        self.checks = evaluator_config.get("checks", [])

    async def evaluate(self, state: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate state against checks

        Reports results to AI Foundry
        """

        # Start evaluation trace
        trace_id = self.ai_foundry.start_trace(
            operation=f"evaluate_{self.evaluator_id}",
            goal_id=self.goal_config["id"]
        )

        try:
            result = await self._run_checks(state)

            # Report to AI Foundry
            self.ai_foundry.log_evaluation(
                evaluator_id=self.evaluator_id,
                result=result.dict(),
                state_snapshot=state.get("context", {})
            )

            self.ai_foundry.end_trace(trace_id, success=True)

            return result

        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            self.ai_foundry.end_trace(trace_id, success=False, error=str(e))
            raise

    async def _run_checks(self, state: Dict[str, Any]) -> EvaluationResult:
        """Run all configured checks"""

        context = state.get("context", {})
        missing_fields = []
        validation_errors = []
        actions = []

        for check in self.checks:
            field = check["field"]
            action = check["action"]
            validation = check.get("validation", {})

            # Check presence
            if validation.get("type") == "presence":
                if field not in context or context[field] is None:
                    missing_fields.append(field)
                    actions.append(f"{action}:{field}")

            # Check range
            elif validation.get("type") == "range":
                if field in context:
                    value = context[field]
                    if value < validation.get("min", float('-inf')):
                        validation_errors.append(f"{field} below minimum")
                    if value > validation.get("max", float('inf')):
                        validation_errors.append(f"{field} above maximum")

            # ... other validation types

        passed = len(missing_fields) == 0 and len(validation_errors) == 0

        return EvaluationResult(
            passed=passed,
            missing_fields=missing_fields,
            validation_errors=validation_errors,
            actions=actions
        )
```

### 3. **API Bridge** - `frmk/api/base_service.py`

```python
"""
API Bridge to Azure AI Foundry
Traces API requests end-to-end
"""

from fastapi import FastAPI, Request, Response
from typing import Callable
import time
from frmk.core.ai_foundry_client import get_ai_foundry_client
from frmk.utils.logging import get_logger

logger = get_logger("api_service")


class BaseAPIService:
    """
    Base class for FastAPI services

    Features:
    - Request tracing to AI Foundry
    - Performance monitoring
    - Error tracking
    """

    def __init__(self, goal_config: Dict):
        self.app = FastAPI(
            title=goal_config.get("title", "GoalGen API"),
            version=goal_config.get("version", "1.0.0")
        )

        self.goal_config = goal_config
        self.ai_foundry = get_ai_foundry_client(goal_config)

        # Add middleware
        self.app.middleware("http")(self.trace_requests)

    async def trace_requests(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Middleware to trace all API requests"""

        # Start trace
        trace_id = self.ai_foundry.start_trace(
            operation=f"{request.method} {request.url.path}",
            goal_id=self.goal_config["id"],
            metadata={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host
            }
        )

        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # End trace
            self.ai_foundry.end_trace(
                trace_id,
                success=response.status_code < 400,
                metadata={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            self.ai_foundry.end_trace(
                trace_id,
                success=False,
                error=str(e),
                metadata={"duration_ms": duration_ms}
            )

            raise
```

### 4. **Asset Bridge** - `frmk/assets/asset_loader.py`

```python
"""
Asset Bridge to Azure AI Foundry
Load versioned assets (prompts, cards, images)
"""

from typing import Optional, Dict, Any
from frmk.core.ai_foundry_client import get_ai_foundry_client


class AssetLoader:
    """
    Load assets from Azure AI Foundry

    Asset types:
    - Prompts (Prompt Flow)
    - Adaptive Cards
    - Images/logos
    - Configuration files
    """

    def __init__(self, goal_config: Dict[str, Any]):
        self.goal_config = goal_config
        self.ai_foundry = get_ai_foundry_client(goal_config)
        self.cache = {}

    async def load_prompt(
        self,
        name: str,
        version: Optional[str] = None
    ) -> str:
        """Load prompt from AI Foundry"""

        # Use PromptLoader (already implemented)
        from frmk.core.prompt_loader import get_prompt_loader
        loader = get_prompt_loader(self.goal_config.get("prompt_repository"))
        return loader.load(name, version)

    async def load_adaptive_card(
        self,
        card_name: str,
        version: Optional[str] = None
    ) -> Dict:
        """Load Adaptive Card template from AI Foundry"""

        cache_key = f"card:{card_name}:{version or 'latest'}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Load from AI Foundry
        card_template = await self.ai_foundry.get_asset(
            asset_type="adaptive_card",
            name=card_name,
            version=version
        )

        self.cache[cache_key] = card_template
        return card_template

    async def load_image(
        self,
        image_name: str,
        version: Optional[str] = None
    ) -> bytes:
        """Load image from AI Foundry asset store"""

        return await self.ai_foundry.get_asset(
            asset_type="image",
            name=image_name,
            version=version
        )
```

---

## AI Foundry Client - Central Hub

```python
# frmk/core/ai_foundry_client.py

"""
Central Azure AI Foundry client
All bridges use this to communicate with AI Foundry
"""

from azure.ai.resources import AIResourcesClient
from azure.identity import DefaultAzureCredential
from typing import Dict, Any, Optional
import uuid


class AIFoundryClient:
    """
    Wrapper for Azure AI Foundry SDK

    Provides:
    - Prompt loading
    - Asset management
    - Tracing/monitoring
    - Experiment tracking
    """

    def __init__(self, config: Dict[str, Any]):
        self.credential = DefaultAzureCredential()

        ai_foundry_config = config.get("ai_foundry", {})

        self.client = AIResourcesClient(
            endpoint=ai_foundry_config.get("endpoint"),
            credential=self.credential
        )

        self.project_name = ai_foundry_config.get("project_name")
        self.enabled = ai_foundry_config.get("enabled", True)

    def start_trace(
        self,
        operation: str,
        goal_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Start distributed trace"""

        if not self.enabled:
            return str(uuid.uuid4())

        trace_id = str(uuid.uuid4())

        # TODO: Integrate with Azure Monitor / App Insights
        # For now, just log
        print(f"[TRACE START] {trace_id}: {operation}")

        return trace_id

    def end_trace(
        self,
        trace_id: str,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """End distributed trace"""

        if not self.enabled:
            return

        status = "SUCCESS" if success else "FAILURE"
        print(f"[TRACE END] {trace_id}: {status}")

        if error:
            print(f"  Error: {error}")

    def log_evaluation(
        self,
        evaluator_id: str,
        result: Dict,
        state_snapshot: Dict
    ):
        """Log evaluation result to AI Foundry"""

        if not self.enabled:
            return

        # TODO: Send to AI Foundry evaluation tracking
        print(f"[EVALUATION] {evaluator_id}: {result}")

    def register_node(
        self,
        goal_id: str,
        node_name: str,
        node_type: str,
        metadata: Dict
    ):
        """Register LangGraph node in AI Foundry"""

        if not self.enabled:
            return

        print(f"[NODE REGISTERED] {goal_id}.{node_name} ({node_type})")

    async def get_asset(
        self,
        asset_type: str,
        name: str,
        version: Optional[str] = None
    ) -> Any:
        """Get asset from AI Foundry"""

        # TODO: Implement asset retrieval
        pass


# Global singleton
_ai_foundry_client: Optional[AIFoundryClient] = None


def get_ai_foundry_client(config: Optional[Dict] = None) -> AIFoundryClient:
    """Get or create AI Foundry client"""
    global _ai_foundry_client

    if _ai_foundry_client is None:
        if config is None:
            raise ValueError("config required for first call")
        _ai_foundry_client = AIFoundryClient(config)

    return _ai_foundry_client
```

---

## Spec Configuration for AI Foundry

```json
{
  "id": "travel_planning",
  "title": "Travel Planning Assistant",

  "ai_foundry": {
    "enabled": true,
    "endpoint": "${AI_FOUNDRY_ENDPOINT}",
    "project_name": "travel-planning",
    "subscription_id": "${AZURE_SUBSCRIPTION_ID}",
    "resource_group": "rg-ai-foundry",

    "features": {
      "prompt_flow": true,
      "monitoring": true,
      "experiments": true,
      "asset_management": true
    },

    "tracing": {
      "enabled": true,
      "sample_rate": 1.0,
      "export_to": "application_insights"
    }
  }
}
```

---

## Summary

✅ **Every component has a Core SDK bridge**
✅ **All bridges communicate with Azure AI Foundry**
✅ **Central `AIFoundryClient` manages all interactions**
✅ **Tracing, monitoring, and asset management unified**
✅ **Spec-driven configuration for all bridges**

**Next: Implement remaining generators using these bridges!**
