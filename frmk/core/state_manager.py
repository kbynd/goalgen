"""
State Manager - Integration Layer for LangGraph

Sits between LangGraph execution and storage, providing:
1. Checkpointer integration (Cosmos/Redis/Blob)
2. Conversation tracking (Azure Conversation API)
3. State validation
4. Metrics tracking
"""

from typing import Dict, Any, Optional, List
from langgraph.checkpoint import BaseCheckpointSaver
from langchain_core.messages import BaseMessage
import asyncio
from frmk.conversation import get_conversation_tracker
from frmk.core.ai_foundry_client import get_ai_foundry_client
from frmk.utils.logging import get_logger

logger = get_logger("state_manager")


class StateManager:
    """
    Manages state for LangGraph workflows

    Responsibilities:
    1. Save/load state via checkpointer
    2. Track conversations in Azure Conversation API (async)
    3. Track state changes in AI Foundry
    4. Validate state schema
    5. Emit metrics

    Usage:
        state_manager = StateManager(goal_config, checkpointer)

        # Save state (also tracks conversation)
        await state_manager.save_state(thread_id, state)

        # Load state
        state = await state_manager.load_state(thread_id)
    """

    def __init__(
        self,
        goal_config: Dict[str, Any],
        checkpointer: BaseCheckpointSaver
    ):
        self.goal_config = goal_config
        self.goal_id = goal_config["id"]
        self.checkpointer = checkpointer

        # Initialize AI Foundry integrations
        self.ai_foundry = get_ai_foundry_client(goal_config)
        self.conversation_tracker = get_conversation_tracker(goal_config)

        # State schema (for validation)
        self.state_schema = goal_config.get("state_management", {}).get("state", {}).get("schema", {})
        self.context_fields = self.state_schema.get("context_fields", [])

        logger.info(f"StateManager initialized for {self.goal_id}")

    async def save_state(
        self,
        thread_id: str,
        user_id: str,
        state: Dict[str, Any],
        checkpoint_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save state to checkpointer and track in Azure services

        Args:
            thread_id: Thread ID
            user_id: User ID (for conversation tracking)
            state: Current state
            checkpoint_metadata: Metadata for checkpoint

        Flow:
            1. Validate state
            2. Save to checkpointer (Cosmos/Redis/Blob)
            3. Track new messages in Conversation API (async)
            4. Track state change in AI Foundry (async)
        """

        # 1. Validate state
        self._validate_state(state)

        # 2. Save to checkpointer
        config = {"configurable": {"thread_id": thread_id}}

        checkpoint = {
            "id": self._generate_checkpoint_id(thread_id),
            "state": state,
            "metadata": checkpoint_metadata or {}
        }

        self.checkpointer.put(config, checkpoint, checkpoint_metadata or {})

        logger.debug(f"State saved to checkpointer: {thread_id}")

        # 3. Track new messages in Conversation API (async, non-blocking)
        messages = state.get("messages", [])
        if messages:
            # Track only new messages (since last save)
            # For simplicity, track the last message
            last_message = messages[-1]

            asyncio.create_task(
                self._track_message_async(
                    thread_id=thread_id,
                    user_id=user_id,
                    message=last_message
                )
            )

        # 4. Track state change in AI Foundry (async)
        asyncio.create_task(
            self._track_state_change_async(
                thread_id=thread_id,
                state=state,
                metadata=checkpoint_metadata
            )
        )

    async def load_state(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load state from checkpointer

        Args:
            thread_id: Thread ID
            checkpoint_id: Specific checkpoint (default: latest)

        Returns:
            State dict or None if not found
        """

        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            }
        }

        checkpoint = self.checkpointer.get(config)

        if checkpoint is None:
            logger.debug(f"No state found for thread: {thread_id}")
            return None

        state = checkpoint.get("state", {})

        logger.debug(f"State loaded from checkpointer: {thread_id}")

        return state

    async def list_checkpoints(
        self,
        thread_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List checkpoints for a thread

        Args:
            thread_id: Thread ID
            limit: Max number of checkpoints to return

        Returns:
            List of checkpoint metadata
        """

        config = {"configurable": {"thread_id": thread_id}}

        checkpoints = self.checkpointer.list(config)

        # Return metadata only (not full state)
        return [
            {
                "id": cp.get("id"),
                "timestamp": cp.get("metadata", {}).get("timestamp"),
                "node_name": cp.get("metadata", {}).get("node_name")
            }
            for cp in checkpoints[:limit]
        ]

    def _validate_state(self, state: Dict[str, Any]):
        """
        Validate state against schema

        Raises:
            ValueError: If state is invalid
        """

        # Check required context fields exist
        context = state.get("context", {})

        # Validation can be strict or lenient based on config
        strict = self.state_schema.get("validation", {}).get("strict", False)

        if strict:
            # All context fields must be defined (can be None)
            for field in self.context_fields:
                if field not in context:
                    raise ValueError(f"Missing context field: {field}")

        # Check no extra fields (if configured)
        allow_extra = self.state_schema.get("validation", {}).get("allow_extra_fields", True)

        if not allow_extra:
            extra_fields = set(context.keys()) - set(self.context_fields)
            if extra_fields:
                raise ValueError(f"Extra context fields not allowed: {extra_fields}")

    async def _track_message_async(
        self,
        thread_id: str,
        user_id: str,
        message: BaseMessage
    ):
        """
        Track message in Azure Conversation API (async)

        This runs in background and doesn't block state save
        """

        try:
            # Determine role from message type
            role = "user" if message.__class__.__name__ == "HumanMessage" else "assistant"

            # Track in Conversation API
            insights = await self.conversation_tracker.track_message(
                thread_id=thread_id,
                user_id=user_id,
                message=message.content,
                role=role,
                metadata={
                    "goal_id": self.goal_id,
                    "message_id": getattr(message, 'id', None)
                }
            )

            if insights:
                logger.debug(f"Message insights: {insights}")

        except Exception as e:
            # Don't fail state save if tracking fails
            logger.error(f"Failed to track message: {e}")

    async def _track_state_change_async(
        self,
        thread_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ):
        """
        Track state change in AI Foundry (async)

        Logs:
        - State transitions
        - Context field changes
        - Task progress
        """

        try:
            # Log state change
            self.ai_foundry.log_metric(
                run_id=thread_id,
                metric_name="message_count",
                value=len(state.get("messages", []))
            )

            # Log context completeness
            context = state.get("context", {})
            filled_fields = sum(1 for field in self.context_fields if context.get(field) is not None)
            completeness = filled_fields / len(self.context_fields) if self.context_fields else 1.0

            self.ai_foundry.log_metric(
                run_id=thread_id,
                metric_name="context_completeness",
                value=completeness
            )

            logger.debug(f"State change tracked: {thread_id}")

        except Exception as e:
            logger.error(f"Failed to track state change: {e}")

    def _generate_checkpoint_id(self, thread_id: str) -> str:
        """Generate unique checkpoint ID"""
        import uuid
        return f"{thread_id}_checkpoint_{uuid.uuid4().hex[:8]}"


# Factory function
def create_state_manager(
    goal_config: Dict[str, Any],
    checkpointer: BaseCheckpointSaver
) -> StateManager:
    """
    Create StateManager instance

    Args:
        goal_config: Goal configuration
        checkpointer: Checkpointer instance (Cosmos/Redis/Blob)

    Returns:
        StateManager instance
    """

    return StateManager(goal_config, checkpointer)
