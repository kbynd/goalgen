"""
Base Agent Class - All generated agents inherit from this
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from frmk.core.prompt_loader import get_prompt_loader
from frmk.core.tool_registry import get_tool_registry
from frmk.utils.logging import get_logger


class BaseAgent(ABC):
    """
    Base class for all agents

    Provides:
    - Prompt loading from Azure AI Foundry
    - LLM initialization
    - Tool binding
    - Metrics tracking
    - Error handling
    """

    def __init__(
        self,
        agent_name: str,
        agent_config: Dict,
        goal_config: Dict
    ):
        self.agent_name = agent_name
        self.agent_config = agent_config
        self.goal_config = goal_config

        self.logger = get_logger(agent_name)

        # Initialize LLM
        llm_config = agent_config.get("llm_config", {})
        self.llm = ChatOpenAI(
            model=llm_config.get("model", "gpt-4"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens"),
            streaming=llm_config.get("streaming", False),
        )

        # Load tools from registry
        tool_names = agent_config.get("tools", [])
        if tool_names:
            tool_registry = get_tool_registry(goal_config)
            self.tools = tool_registry.get_langchain_tools(tool_names)
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.tools = []
            self.llm_with_tools = None

        # Load prompt from Azure AI Foundry
        self.system_prompt = self._load_prompt()

        # Tracking
        self.loop_count = 0
        self.max_loop = agent_config.get("max_loop", 10)

    def _load_prompt(self) -> str:
        """Load prompt from Azure AI Foundry or local"""

        prompt_loader = get_prompt_loader(
            self.goal_config.get("prompt_repository")
        )

        # Get version for this agent
        versioning = self.goal_config.get("prompt_repository", {}).get("versioning", {})
        version = versioning.get("agent_versions", {}).get(self.agent_name, "latest")

        # Build prompt variables
        variables = {
            "agent_name": self.agent_name,
            "goal_id": self.goal_config.get("id"),
            "tools": self._get_tool_descriptions(),
        }
        variables.update(
            self.agent_config.get("prompt_variables", {})
        )

        return prompt_loader.load(
            agent_name=self.agent_name,
            version=version,
            variables=variables
        )

    def _get_tool_descriptions(self) -> str:
        """Format tool descriptions for prompt"""

        if not self.tools:
            return "No tools available"

        return "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])

    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main invocation method

        Subclasses can override for custom logic
        """

        self.loop_count += 1

        # Check max loops
        if self.loop_count > self.max_loop:
            self.logger.warning(f"Max iterations reached: {self.max_loop}")
            return self._max_loop_response(state)

        # Build messages
        messages = self._build_messages(state)

        # Invoke LLM
        if self.llm_with_tools:
            response = await self.llm_with_tools.ainvoke(messages)
        else:
            response = await self.llm.ainvoke(messages)

        # Process response
        return await self._process_response(state, response)

    def _build_messages(self, state: Dict[str, Any]) -> List:
        """Build message list with system prompt"""

        # Format system prompt with context
        system_content = self._format_system_prompt(state)

        return [
            SystemMessage(content=system_content)
        ] + state.get("messages", [])

    def _format_system_prompt(self, state: Dict[str, Any]) -> str:
        """Format system prompt with runtime context"""

        prompt = self.system_prompt

        # Inject runtime context
        context = state.get("context", {})
        prompt = prompt.replace("{{context}}", str(context))

        # Inject history if needed
        if "{{history}}" in prompt:
            history = self._format_history(state.get("messages", []))
            prompt = prompt.replace("{{history}}", history)

        return prompt

    def _format_history(self, messages: List) -> str:
        """Format conversation history"""

        history_lines = []
        for msg in messages[-10:]:  # Last 10 messages
            role = msg.__class__.__name__.replace("Message", "")
            history_lines.append(f"{role}: {msg.content}")

        return "\n".join(history_lines)

    @abstractmethod
    async def _process_response(
        self,
        state: Dict[str, Any],
        response: AIMessage
    ) -> Dict[str, Any]:
        """
        Process LLM response

        Must be implemented by subclasses
        """
        pass

    def _max_loop_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Response when max loops reached"""
        return {
            "messages": state["messages"] + [
                AIMessage(content="Maximum iterations reached. Please refine your request.")
            ],
            "next": "END"
        }

    def reset(self):
        """Reset agent state"""
        self.loop_count = 0
