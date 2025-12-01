"""
Base Tool Interface
All tools (HTTP, WebSocket, Function) implement this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Base tool input schema"""
    pass


class ToolOutput(BaseModel):
    """Base tool output schema"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """
    Base class for all tools

    Tools can be:
    - HTTP-based (Azure Functions, external APIs)
    - WebSocket-based (real-time services)
    - Function-based (local Python functions)
    """

    def __init__(
        self,
        name: str,
        description: str,
        tool_config: Dict[str, Any]
    ):
        self.name = name
        self.description = description
        self.config = tool_config

        # LangChain tool metadata
        self.metadata = {
            "name": name,
            "description": description,
            "type": tool_config.get("type"),
        }

    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the tool

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolOutput with results
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool input schema for LLM

        Returns:
            JSON Schema for tool parameters
        """
        pass

    def to_langchain_tool(self):
        """
        Convert to LangChain tool format

        Returns:
            LangChain Tool object
        """
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            func=self._sync_wrapper,
            coroutine=self.execute,
            name=self.name,
            description=self.description,
            args_schema=self.get_schema(),
        )

    def _sync_wrapper(self, **kwargs):
        """Sync wrapper for async execute"""
        import asyncio
        return asyncio.run(self.execute(**kwargs))
