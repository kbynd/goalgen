"""
Function-based Tool Implementation
For local Python functions
"""

from typing import Dict, Any, Callable, Optional
import importlib
import inspect
from .base_tool import BaseTool, ToolOutput
from frmk.utils.logging import get_logger


class FunctionTool(BaseTool):
    """
    Function-based tool for local Python functions

    Configuration from spec:
    {
      "type": "function",
      "spec": {
        "module": "tools.calculator",
        "function": "calculate",
        "input_schema": {...},  // Optional: JSON schema for parameters
        "timeout": 10
      }
    }
    """

    def __init__(self, name: str, description: str, tool_config: Dict[str, Any]):
        super().__init__(name, description, tool_config)

        self.logger = get_logger(f"tool.{name}")

        spec = tool_config.get("spec", {})

        # Import the function
        module_path = spec.get("module")
        function_name = spec.get("function")

        if not module_path or not function_name:
            raise ValueError(f"FunctionTool {name} requires 'module' and 'function' in spec")

        try:
            module = importlib.import_module(module_path)
            self.func = getattr(module, function_name)

            if not callable(self.func):
                raise ValueError(f"{module_path}.{function_name} is not callable")

        except ImportError as e:
            raise ImportError(f"Failed to import {module_path}: {e}")
        except AttributeError:
            raise AttributeError(f"Function {function_name} not found in {module_path}")

        # Store configuration
        self.timeout = spec.get("timeout", 10)
        self.input_schema = spec.get("input_schema")

    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute the Python function

        Args:
            **kwargs: Parameters to pass to the function

        Returns:
            ToolOutput with function result
        """

        try:
            self.logger.info(f"Calling function {self.name} with args: {kwargs}")

            # Check if function is async or sync
            if inspect.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)

            self.logger.info(f"{self.name} call successful")

            return ToolOutput(
                success=True,
                data=result,
                metadata={
                    "function": self.func.__name__,
                    "module": self.func.__module__
                }
            )

        except TypeError as e:
            # Invalid arguments
            self.logger.error(f"{self.name} invalid arguments: {e}")
            return ToolOutput(
                success=False,
                error=f"Invalid arguments: {e}"
            )

        except Exception as e:
            self.logger.error(f"{self.name} execution failed: {e}")
            return ToolOutput(
                success=False,
                error=str(e)
            )

    def get_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for function parameters

        Returns:
            JSON Schema derived from function signature or spec
        """

        # If schema provided in spec, use it
        if self.input_schema:
            return self.input_schema

        # Otherwise, infer from function signature
        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            # Skip self/cls parameters
            if param_name in ('self', 'cls'):
                continue

            param_type = "string"  # Default
            param_desc = f"Parameter: {param_name}"

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                annotation = param.annotation
                if annotation == int:
                    param_type = "integer"
                elif annotation == float:
                    param_type = "number"
                elif annotation == bool:
                    param_type = "boolean"
                elif annotation == list:
                    param_type = "array"
                elif annotation == dict:
                    param_type = "object"

            properties[param_name] = {
                "type": param_type,
                "description": param_desc
            }

            # Required if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
