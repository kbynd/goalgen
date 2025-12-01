"""
Prompt Loader - Azure AI Foundry Integration

Loads prompts from Azure AI Foundry Prompt Flow with:
- Version management
- Caching (TTL)
- Fallback to local files
- Variable substitution
"""

from typing import Dict, Any, Optional
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Load prompts from Azure AI Foundry or local fallback

    Features:
    - Loads from AI Foundry Prompt Flow (if enabled)
    - Falls back to local prompt files
    - Caches prompts with TTL
    - Supports versioning
    - Variable substitution
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PromptLoader

        Args:
            config: Goal configuration with ai_foundry settings
        """
        self.config = config
        ai_foundry_config = config.get("ai_foundry", {})
        prompt_config = ai_foundry_config.get("features", {}).get("prompt_flow", {})

        self.enabled = prompt_config.get("enabled", False)
        self.project_name = ai_foundry_config.get("project_name", config.get("id", "unknown"))

        # Cache configuration
        self.cache_ttl = prompt_config.get("cache_ttl_seconds", 3600)  # 1 hour default
        self.cache: Dict[str, tuple] = {}  # {key: (prompt, timestamp)}

        # AI Foundry client (lazy initialization)
        self._client = None

        # Fallback to local prompts directory
        self.prompts_dir = Path(config.get("prompts_directory", "prompts"))

        logger.info(f"PromptLoader initialized (AI Foundry enabled: {self.enabled})")

    def load(
        self,
        agent_name: str,
        version: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Load prompt for an agent

        Args:
            agent_name: Name of the agent (e.g., "supervisor_agent")
            version: Prompt version (default: latest)
            variables: Variables for substitution

        Returns:
            Prompt string with variables substituted
        """
        cache_key = f"{agent_name}:{version or 'latest'}"

        # Check cache
        if cache_key in self.cache:
            prompt, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Prompt cache hit: {cache_key}")
                return self._substitute_variables(prompt, variables or {})

        # Load from AI Foundry or local
        if self.enabled:
            prompt = self._load_from_ai_foundry(agent_name, version)
        else:
            prompt = self._load_from_local(agent_name)

        # Cache the prompt
        self.cache[cache_key] = (prompt, datetime.now())

        # Substitute variables
        return self._substitute_variables(prompt, variables or {})

    def _load_from_ai_foundry(self, agent_name: str, version: Optional[str]) -> str:
        """
        Load prompt from Azure AI Foundry Prompt Flow

        Args:
            agent_name: Agent name
            version: Version (optional, defaults to "latest")

        Returns:
            Prompt content
        """
        try:
            # Lazy initialize AI Foundry client
            if self._client is None:
                from frmk.core.ai_foundry_client import get_ai_foundry_client
                self._client = get_ai_foundry_client(self.config)

            # Load prompt from AI Foundry using Azure ML SDK
            try:
                from azure.ai.ml import MLClient
                from azure.identity import DefaultAzureCredential

                # Get AI Foundry configuration
                ai_foundry_config = self.config.get("ai_foundry", {})
                subscription_id = ai_foundry_config.get("subscription_id")
                resource_group = ai_foundry_config.get("resource_group")
                workspace_name = ai_foundry_config.get("workspace_name")

                if not all([subscription_id, resource_group, workspace_name]):
                    logger.warning(
                        "AI Foundry configuration incomplete (need subscription_id, resource_group, workspace_name), "
                        "falling back to local"
                    )
                    return self._load_from_local(agent_name)

                # Create ML client
                credential = DefaultAzureCredential()
                ml_client = MLClient(
                    credential=credential,
                    subscription_id=subscription_id,
                    resource_group_name=resource_group,
                    workspace_name=workspace_name
                )

                # Load prompt asset
                version_str = version or "latest"
                logger.info(f"Loading prompt '{agent_name}' version '{version_str}' from AI Foundry")

                # Get prompt from AI Foundry
                prompt_asset = ml_client.prompts.get(name=agent_name, version=version_str)

                # Return content
                logger.info(f"Successfully loaded prompt '{agent_name}:{version_str}' from AI Foundry")
                return prompt_asset.content

            except ImportError:
                logger.warning("Azure ML SDK not installed, falling back to local prompts")
                logger.info("Install with: pip install azure-ai-ml")
                return self._load_from_local(agent_name)

            except Exception as sdk_error:
                logger.warning(f"AI Foundry SDK error: {sdk_error}, falling back to local")
                return self._load_from_local(agent_name)

        except Exception as e:
            logger.error(f"Failed to load prompt from AI Foundry: {e}, falling back to local")
            return self._load_from_local(agent_name)

    def _load_from_local(self, agent_name: str) -> str:
        """
        Load prompt from local file

        Args:
            agent_name: Agent name

        Returns:
            Prompt content

        Raises:
            FileNotFoundError: If prompt file not found
        """
        # Try multiple possible filenames
        possible_files = [
            self.prompts_dir / f"{agent_name}.md",
            self.prompts_dir / f"{agent_name}.txt",
            self.prompts_dir / f"{agent_name}_prompt.md",
        ]

        for prompt_file in possible_files:
            if prompt_file.exists():
                logger.debug(f"Loading prompt from: {prompt_file}")
                return prompt_file.read_text()

        # If no local file found, return a default prompt
        logger.warning(f"No prompt file found for {agent_name}, using default")
        return self._get_default_prompt(agent_name)

    def _get_default_prompt(self, agent_name: str) -> str:
        """
        Get default prompt template when no custom prompt is available

        Args:
            agent_name: Agent name

        Returns:
            Default prompt string
        """
        return f"""You are {agent_name.replace('_', ' ')}.

Your task is to assist the user with their request.

Current context:
{{context}}

Recent conversation:
{{history}}

User message:
{{user_message}}

Respond helpfully and professionally."""

    def _substitute_variables(self, prompt: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in prompt template

        Args:
            prompt: Prompt template with {variable} placeholders
            variables: Dictionary of variable values

        Returns:
            Prompt with variables substituted
        """
        try:
            # Simple string formatting
            # Use safe_substitute to avoid KeyError on missing variables
            from string import Template
            template = Template(prompt)
            return template.safe_substitute(variables)

        except Exception as e:
            logger.error(f"Error substituting variables: {e}")
            return prompt

    def clear_cache(self):
        """Clear the prompt cache"""
        self.cache.clear()
        logger.info("Prompt cache cleared")


# Global singleton
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader(config: Optional[Dict[str, Any]] = None) -> PromptLoader:
    """
    Get or create prompt loader singleton

    Args:
        config: Goal configuration (required on first call)

    Returns:
        PromptLoader instance
    """
    global _prompt_loader

    if _prompt_loader is None:
        if config is None:
            raise ValueError("Config required for first call to get_prompt_loader")
        _prompt_loader = PromptLoader(config)

    return _prompt_loader


def reset_prompt_loader():
    """Reset global prompt loader (useful for testing)"""
    global _prompt_loader
    _prompt_loader = None
