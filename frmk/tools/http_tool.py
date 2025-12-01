"""
HTTP-based Tool Implementation
For Azure Functions and external REST APIs
"""

from typing import Dict, Any, Optional
import httpx
import os
from .base_tool import BaseTool, ToolOutput
from frmk.utils.retry import async_retry
from frmk.utils.logging import get_logger


class HTTPTool(BaseTool):
    """
    HTTP-based tool for Azure Functions or external APIs

    Configuration from spec:
    {
      "type": "http",
      "spec": {
        "url": "${FLIGHT_API_URL}/search",
        "method": "POST",
        "auth": "key|bearer|managed_identity",
        "timeout": 30,
        "retry_attempts": 3,
        "cache_ttl": 3600,
        "headers": {...}
      }
    }
    """

    def __init__(self, name: str, description: str, tool_config: Dict[str, Any]):
        super().__init__(name, description, tool_config)

        self.logger = get_logger(f"tool.{name}")

        spec = tool_config.get("spec", {})

        # Resolve environment variables in URL
        self.url = self._resolve_env_vars(spec.get("url", ""))
        self.method = spec.get("method", "POST").upper()
        self.auth_type = spec.get("auth", "key")
        self.timeout = spec.get("timeout", 30)
        self.retry_attempts = spec.get("retry_attempts", 3)
        self.headers = spec.get("headers", {})

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._get_auth_headers(),
        )

    def _resolve_env_vars(self, value: str) -> str:
        """Resolve ${VAR} in configuration"""
        import re

        def replacer(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(r'\$\{(\w+)\}', replacer, value)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth type"""

        headers = self.headers.copy()

        if self.auth_type == "key":
            # API key from environment
            api_key_var = f"{self.name.upper()}_API_KEY"
            api_key = os.getenv(api_key_var)
            if api_key:
                headers["X-API-Key"] = api_key

        elif self.auth_type == "bearer":
            # Bearer token from environment
            token_var = f"{self.name.upper()}_TOKEN"
            token = os.getenv(token_var)
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif self.auth_type == "managed_identity":
            # Azure Managed Identity token
            from azure.identity import DefaultAzureCredential
            from azure.core.credentials import AccessToken

            credential = DefaultAzureCredential()
            # Get token for Azure Management scope
            token = credential.get_token("https://management.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"

        return headers

    @async_retry(max_attempts=3, backoff_strategy="exponential")
    async def execute(self, **kwargs) -> ToolOutput:
        """
        Execute HTTP tool call

        Args:
            **kwargs: Parameters to send in request body or query

        Returns:
            ToolOutput with API response
        """

        try:
            self.logger.info(f"Calling {self.name} at {self.url}")

            # Prepare request
            if self.method == "GET":
                response = await self.client.get(
                    self.url,
                    params=kwargs
                )
            elif self.method == "POST":
                response = await self.client.post(
                    self.url,
                    json=kwargs
                )
            elif self.method == "PUT":
                response = await self.client.put(
                    self.url,
                    json=kwargs
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {self.method}")

            # Check response
            response.raise_for_status()

            data = response.json()

            self.logger.info(f"{self.name} call successful")

            return ToolOutput(
                success=True,
                data=data,
                metadata={
                    "status_code": response.status_code,
                    "url": str(response.url),
                    "elapsed_ms": response.elapsed.total_seconds() * 1000
                }
            )

        except httpx.HTTPStatusError as e:
            self.logger.error(f"{self.name} HTTP error: {e.response.status_code}")
            return ToolOutput(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
                metadata={"status_code": e.response.status_code}
            )

        except Exception as e:
            self.logger.error(f"{self.name} execution failed: {e}")
            return ToolOutput(
                success=False,
                error=str(e)
            )

    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON schema from spec or infer from URL"""

        # If schema provided in spec, use it
        if "input_schema" in self.config.get("spec", {}):
            return self.config["spec"]["input_schema"]

        # Otherwise, generate basic schema
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": f"Query parameters for {self.name}"
                }
            },
            "required": ["query"]
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
