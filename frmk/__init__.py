"""
GoalGen Framework - Core SDK for Generated Applications

Provides:
- Prompt loading from Azure AI Foundry
- Tool integration (HTTP, WebSocket, Functions)
- State management and checkpointing
- Conversation tracking and analytics
- Authentication helpers
- Logging and metrics
"""

__version__ = "0.1.0"

from .agents.base_agent import BaseAgent
from .tools.base_tool import BaseTool, ToolOutput
from .core.tool_registry import ToolRegistry, get_tool_registry
from .core.prompt_loader import PromptLoader, get_prompt_loader
from .core.ai_foundry_client import AIFoundryClient, get_ai_foundry_client
from .conversation import AzureConversationTracker, get_conversation_tracker

__all__ = [
    "BaseAgent",
    "BaseTool",
    "ToolOutput",
    "ToolRegistry",
    "get_tool_registry",
    "PromptLoader",
    "get_prompt_loader",
    "AIFoundryClient",
    "get_ai_foundry_client",
    "AzureConversationTracker",
    "get_conversation_tracker",
]
