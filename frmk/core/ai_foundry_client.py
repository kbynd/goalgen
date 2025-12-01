"""
Azure AI Foundry Client - Central Hub
All Core SDK bridges use this to communicate with Azure AI Foundry
"""

from azure.ai.resources import AIResourcesClient
from azure.identity import DefaultAzureCredential
from typing import Dict, Any, Optional
import uuid
import os
from frmk.utils.logging import get_logger

logger = get_logger("ai_foundry")


class AIFoundryClient:
    """
    Wrapper for Azure AI Foundry SDK

    Provides:
    - Prompt loading (via Prompt Flow)
    - Asset management (cards, images, configs)
    - Distributed tracing
    - Experiment tracking
    - Model deployment monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI Foundry client

        Args:
            config: Goal configuration with ai_foundry section
        """

        self.credential = DefaultAzureCredential()

        ai_foundry_config = config.get("ai_foundry", {})

        # AI Foundry connection
        endpoint = ai_foundry_config.get("endpoint") or os.getenv("AI_FOUNDRY_ENDPOINT")

        if endpoint:
            self.client = AIResourcesClient(
                endpoint=endpoint,
                credential=self.credential
            )
        else:
            self.client = None
            logger.warning("AI Foundry endpoint not configured - running in local mode")

        self.project_name = ai_foundry_config.get("project_name")
        self.enabled = ai_foundry_config.get("enabled", True) and self.client is not None

        # Features
        features = ai_foundry_config.get("features", {})
        self.prompt_flow_enabled = features.get("prompt_flow", True)
        self.monitoring_enabled = features.get("monitoring", True)
        self.experiments_enabled = features.get("experiments", False)
        self.asset_management_enabled = features.get("asset_management", True)

        # Tracing config
        tracing_config = ai_foundry_config.get("tracing", {})
        self.tracing_enabled = tracing_config.get("enabled", True)
        self.sample_rate = tracing_config.get("sample_rate", 1.0)

        logger.info(f"AI Foundry client initialized (enabled: {self.enabled})")

    # ==================== TRACING ====================

    def start_trace(
        self,
        operation: str,
        goal_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Start distributed trace

        Args:
            operation: Operation name (e.g., "execute_agent", "api_request")
            goal_id: Goal identifier
            metadata: Additional trace metadata

        Returns:
            Trace ID for correlation
        """

        if not self.enabled or not self.tracing_enabled:
            return str(uuid.uuid4())

        import random
        if random.random() > self.sample_rate:
            return str(uuid.uuid4())  # Sampled out

        trace_id = str(uuid.uuid4())

        try:
            # Log trace start
            logger.debug(f"[TRACE START] {trace_id}: {operation}", extra={
                "trace_id": trace_id,
                "operation": operation,
                "goal_id": goal_id,
                "metadata": metadata or {}
            })

            # TODO: Send to Azure Monitor / Application Insights
            # self.client.traces.start(trace_id, operation, metadata)

        except Exception as e:
            logger.error(f"Failed to start trace: {e}")

        return trace_id

    def end_trace(
        self,
        trace_id: str,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        End distributed trace

        Args:
            trace_id: Trace ID from start_trace
            success: Whether operation succeeded
            error: Error message if failed
            metadata: Additional metadata (duration, status code, etc.)
        """

        if not self.enabled or not self.tracing_enabled:
            return

        try:
            status = "SUCCESS" if success else "FAILURE"

            logger.debug(f"[TRACE END] {trace_id}: {status}", extra={
                "trace_id": trace_id,
                "success": success,
                "error": error,
                "metadata": metadata or {}
            })

            # TODO: Send to Azure Monitor / Application Insights
            # self.client.traces.end(trace_id, success, error, metadata)

        except Exception as e:
            logger.error(f"Failed to end trace: {e}")

    # ==================== EVALUATION TRACKING ====================

    def log_evaluation(
        self,
        evaluator_id: str,
        result: Dict,
        state_snapshot: Dict
    ):
        """
        Log evaluation result to AI Foundry

        Args:
            evaluator_id: Evaluator identifier
            result: Evaluation result (passed, missing_fields, etc.)
            state_snapshot: Current state when evaluation ran
        """

        if not self.enabled or not self.monitoring_enabled:
            return

        try:
            logger.info(f"[EVALUATION] {evaluator_id}: passed={result.get('passed')}", extra={
                "evaluator_id": evaluator_id,
                "result": result,
                "state_snapshot": state_snapshot
            })

            # TODO: Send to AI Foundry evaluation tracking
            # self.client.evaluations.log(evaluator_id, result, state_snapshot)

        except Exception as e:
            logger.error(f"Failed to log evaluation: {e}")

    # ==================== NODE REGISTRATION ====================

    def register_node(
        self,
        goal_id: str,
        node_name: str,
        node_type: str,
        metadata: Dict
    ):
        """
        Register LangGraph node in AI Foundry for monitoring

        Args:
            goal_id: Goal identifier
            node_name: Node name
            node_type: Node type (task, evaluator, supervisor)
            metadata: Node metadata from spec
        """

        if not self.enabled or not self.monitoring_enabled:
            return

        try:
            logger.debug(f"[NODE REGISTERED] {goal_id}.{node_name} ({node_type})", extra={
                "goal_id": goal_id,
                "node_name": node_name,
                "node_type": node_type,
                "metadata": metadata
            })

            # TODO: Register in AI Foundry monitoring
            # self.client.nodes.register(goal_id, node_name, node_type, metadata)

        except Exception as e:
            logger.error(f"Failed to register node: {e}")

    # ==================== ASSET MANAGEMENT ====================

    async def get_asset(
        self,
        asset_type: str,
        name: str,
        version: Optional[str] = None
    ) -> Any:
        """
        Get asset from AI Foundry

        Args:
            asset_type: Asset type (prompt, adaptive_card, image, config)
            name: Asset name
            version: Version (default: latest)

        Returns:
            Asset content (format depends on asset_type)
        """

        if not self.enabled or not self.asset_management_enabled:
            raise ValueError("Asset management not enabled")

        try:
            if asset_type == "prompt":
                # Use Prompt Flow
                asset = self.client.prompts.get(
                    project=self.project_name,
                    name=name,
                    version=version or "latest"
                )
                return asset.content

            elif asset_type == "adaptive_card":
                # Custom asset type
                asset = await self._get_custom_asset("adaptive_cards", name, version)
                return asset

            elif asset_type == "image":
                # Binary asset
                asset = await self._get_custom_asset("images", name, version)
                return asset

            elif asset_type == "config":
                # Configuration file
                asset = await self._get_custom_asset("configs", name, version)
                return asset

            else:
                raise ValueError(f"Unknown asset type: {asset_type}")

        except Exception as e:
            logger.error(f"Failed to get asset {asset_type}/{name}: {e}")
            raise

    async def _get_custom_asset(
        self,
        category: str,
        name: str,
        version: Optional[str]
    ) -> Any:
        """Get custom asset from AI Foundry asset store"""

        # TODO: Implement custom asset retrieval
        # For now, return None
        logger.warning(f"Custom asset retrieval not yet implemented: {category}/{name}")
        return None

    # ==================== EXPERIMENT TRACKING ====================

    def start_experiment(
        self,
        experiment_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Start experiment tracking

        Args:
            experiment_name: Experiment name
            parameters: Experiment parameters

        Returns:
            Experiment run ID
        """

        if not self.enabled or not self.experiments_enabled:
            return str(uuid.uuid4())

        try:
            run_id = str(uuid.uuid4())

            logger.info(f"[EXPERIMENT START] {experiment_name} (run: {run_id})", extra={
                "experiment_name": experiment_name,
                "run_id": run_id,
                "parameters": parameters
            })

            # TODO: Start experiment in AI Foundry
            # run = self.client.experiments.start(experiment_name, parameters)
            # return run.id

            return run_id

        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            return str(uuid.uuid4())

    def log_metric(
        self,
        run_id: str,
        metric_name: str,
        value: float,
        step: Optional[int] = None
    ):
        """
        Log experiment metric

        Args:
            run_id: Experiment run ID
            metric_name: Metric name
            value: Metric value
            step: Step number (for time series)
        """

        if not self.enabled or not self.experiments_enabled:
            return

        try:
            logger.debug(f"[METRIC] {metric_name}={value} (run: {run_id}, step: {step})")

            # TODO: Log to AI Foundry
            # self.client.experiments.log_metric(run_id, metric_name, value, step)

        except Exception as e:
            logger.error(f"Failed to log metric: {e}")


# Global singleton
_ai_foundry_client: Optional[AIFoundryClient] = None


def get_ai_foundry_client(config: Optional[Dict] = None) -> AIFoundryClient:
    """
    Get or create AI Foundry client singleton

    Args:
        config: Goal configuration (required on first call)

    Returns:
        AIFoundryClient instance
    """
    global _ai_foundry_client

    if _ai_foundry_client is None:
        if config is None:
            # Load from environment
            config = {
                "ai_foundry": {
                    "enabled": os.getenv("AI_FOUNDRY_ENABLED", "true").lower() == "true",
                    "endpoint": os.getenv("AI_FOUNDRY_ENDPOINT"),
                    "project_name": os.getenv("AI_FOUNDRY_PROJECT"),
                }
            }

        _ai_foundry_client = AIFoundryClient(config)

    return _ai_foundry_client


def reset_ai_foundry_client():
    """Reset global client (useful for testing)"""
    global _ai_foundry_client
    _ai_foundry_client = None
