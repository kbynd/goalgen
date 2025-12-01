"""
Tool Registry
Discovers and registers tools from spec
"""

from typing import Dict, Any, List, Optional
from frmk.tools.base_tool import BaseTool
from frmk.tools.http_tool import HTTPTool
from frmk.tools.websocket_tool import WebSocketTool
from frmk.utils.logging import get_logger

logger = get_logger("tool_registry")


class ToolRegistry:
    """
    Registry for all tools defined in goal spec

    Automatically instantiates tools based on type:
    - http -> HTTPTool
    - websocket -> WebSocketTool
    - function -> FunctionTool
    """

    def __init__(self, goal_config: Dict[str, Any]):
        self.goal_config = goal_config
        self.tools: Dict[str, BaseTool] = {}

        # Load tools from spec
        self._load_tools()

    def _load_tools(self):
        """Load all tools from goal spec"""

        tools_spec = self.goal_config.get("tools", {})

        for tool_name, tool_config in tools_spec.items():
            try:
                tool = self._create_tool(tool_name, tool_config)
                self.tools[tool_name] = tool
                logger.info(f"Registered tool: {tool_name} ({tool_config.get('type')})")

            except Exception as e:
                logger.error(f"Failed to register tool {tool_name}: {e}")

    def _create_tool(self, name: str, config: Dict[str, Any]) -> BaseTool:
        """
        Create tool instance based on type

        Args:
            name: Tool name
            config: Tool configuration from spec

        Returns:
            Tool instance
        """

        tool_type = config.get("type")
        description = config.get("description", f"Tool: {name}")

        if tool_type == "http":
            return HTTPTool(name, description, config)

        elif tool_type == "websocket":
            return WebSocketTool(name, description, config)

        elif tool_type == "function":
            from frmk.tools.function_tool import FunctionTool
            return FunctionTool(name, description, config)

        elif tool_type == "sql":
            from frmk.tools.sql_tool import SQLTool, AzureSQLTool
            # Use AzureSQLTool if database_type is azure_sql
            db_type = config.get("spec", {}).get("database_type", "")
            if db_type == "azure_sql":
                return AzureSQLTool(name, description, config)
            return SQLTool(name, description, config)

        elif tool_type == "vectordb":
            from frmk.tools.vectordb_tool import VectorDBTool
            return VectorDBTool(name, description, config)

        else:
            raise ValueError(f"Unknown tool type: {tool_type}")

    def get(self, tool_name: str) -> BaseTool:
        """
        Get tool by name

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance

        Raises:
            KeyError: If tool not found
        """

        if tool_name not in self.tools:
            raise KeyError(f"Tool not found: {tool_name}")

        return self.tools[tool_name]

    def get_langchain_tools(self, tool_names: List[str]) -> List:
        """
        Get LangChain tool instances for agent binding

        Args:
            tool_names: List of tool names

        Returns:
            List of LangChain Tool objects
        """

        return [
            self.tools[name].to_langchain_tool()
            for name in tool_names
            if name in self.tools
        ]

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())

    async def close_all(self):
        """Close all tools (HTTP clients, WebSocket connections)"""
        for tool in self.tools.values():
            if hasattr(tool, 'close'):
                await tool.close()


# Global singleton
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry(goal_config: Optional[Dict[str, Any]] = None) -> ToolRegistry:
    """Get or create tool registry singleton"""
    global _tool_registry

    if _tool_registry is None:
        if goal_config is None:
            raise ValueError("goal_config required for first call")
        _tool_registry = ToolRegistry(goal_config)

    return _tool_registry


def reset_tool_registry():
    """Reset global registry (useful for testing)"""
    global _tool_registry
    _tool_registry = None
