#!/usr/bin/env python3
"""
Goal Spec Validator

Validates goal spec JSON files for correctness, completeness, and best practices.
"""

import json
import re
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Validation issue severity levels"""
    ERROR = "error"      # Spec is invalid, generation will fail
    WARNING = "warning"  # Spec has issues but may work
    INFO = "info"        # Best practice recommendations


@dataclass
class ValidationIssue:
    """A single validation issue"""
    severity: Severity
    path: str  # JSON path to the issue (e.g., "agents.flight_agent.tools[0]")
    message: str
    suggestion: Optional[str] = None

    def __str__(self):
        result = f"[{self.severity.value.upper()}] {self.path}: {self.message}"
        if self.suggestion:
            result += f"\n  Suggestion: {self.suggestion}"
        return result


class SpecValidator:
    """Validates goal specification files"""

    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.spec: Dict[str, Any] = {}

    def validate(self, spec: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate a goal spec

        Returns:
            Tuple of (is_valid, issues_list)
            is_valid is False if any ERROR severity issues found
        """
        self.spec = spec
        self.issues = []

        # Run all validation checks
        self._validate_required_fields()
        self._validate_id()
        self._validate_version()
        self._validate_agents()
        self._validate_tools()
        self._validate_tasks()
        self._validate_state_management()
        self._validate_ux()
        self._validate_deployment()
        self._validate_authentication()
        self._validate_cross_references()
        self._validate_best_practices()

        # Check if spec is valid (no errors)
        has_errors = any(issue.severity == Severity.ERROR for issue in self.issues)
        is_valid = not has_errors

        return is_valid, self.issues

    def _add_issue(self, severity: Severity, path: str, message: str, suggestion: str = None):
        """Add a validation issue"""
        self.issues.append(ValidationIssue(severity, path, message, suggestion))

    # ===== Required Fields =====

    def _validate_required_fields(self):
        """Validate that required top-level fields exist"""
        required_fields = ["id", "title", "version", "agents"]

        for field in required_fields:
            if field not in self.spec:
                self._add_issue(
                    Severity.ERROR,
                    f"root.{field}",
                    f"Required field '{field}' is missing",
                    f"Add '{field}' to the root of your spec"
                )

    # ===== ID Validation =====

    def _validate_id(self):
        """Validate spec ID"""
        if "id" not in self.spec:
            return  # Already reported by required fields check

        spec_id = self.spec["id"]

        # Check type
        if not isinstance(spec_id, str):
            self._add_issue(
                Severity.ERROR,
                "root.id",
                f"ID must be a string, got {type(spec_id).__name__}"
            )
            return

        # Check format (valid identifier)
        if not spec_id:
            self._add_issue(
                Severity.ERROR,
                "root.id",
                "ID cannot be empty"
            )
            return

        # Must be valid Python/filename identifier
        if not re.match(r'^[a-z][a-z0-9_]*$', spec_id):
            self._add_issue(
                Severity.ERROR,
                "root.id",
                "ID must start with lowercase letter and contain only lowercase letters, numbers, and underscores",
                f"Example: '{spec_id.lower().replace('-', '_').replace(' ', '_')}'"
            )

        # Check length
        if len(spec_id) > 50:
            self._add_issue(
                Severity.WARNING,
                "root.id",
                f"ID is very long ({len(spec_id)} chars). Consider shortening for better usability"
            )

    # ===== Version Validation =====

    def _validate_version(self):
        """Validate semantic version"""
        if "version" not in self.spec:
            return  # Already reported

        version = self.spec["version"]

        if not isinstance(version, str):
            self._add_issue(
                Severity.ERROR,
                "root.version",
                f"Version must be a string, got {type(version).__name__}"
            )
            return

        # Check semantic versioning format
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$', version):
            self._add_issue(
                Severity.ERROR,
                "root.version",
                f"Version '{version}' is not valid semantic version (x.y.z)",
                "Example: '1.0.0' or '1.0.0-alpha'"
            )

    # ===== Agents Validation =====

    def _validate_agents(self):
        """Validate agents section"""
        if "agents" not in self.spec:
            return  # Already reported

        agents = self.spec["agents"]

        if not isinstance(agents, dict):
            self._add_issue(
                Severity.ERROR,
                "agents",
                f"Agents must be a dict, got {type(agents).__name__}"
            )
            return

        if not agents:
            self._add_issue(
                Severity.ERROR,
                "agents",
                "Agents dict cannot be empty. At least one agent required."
            )
            return

        # Check for at least one supervisor
        has_supervisor = any(
            agent.get("kind") == "supervisor"
            for agent in agents.values()
        )

        if not has_supervisor:
            self._add_issue(
                Severity.ERROR,
                "agents",
                "At least one supervisor agent is required",
                "Add an agent with 'kind': 'supervisor'"
            )

        # Validate each agent
        for agent_name, agent_config in agents.items():
            self._validate_agent(agent_name, agent_config)

    def _validate_agent(self, agent_name: str, agent_config: Dict[str, Any]):
        """Validate a single agent"""
        path = f"agents.{agent_name}"

        # Check agent name format
        if not re.match(r'^[a-z][a-z0-9_]*$', agent_name):
            self._add_issue(
                Severity.WARNING,
                path,
                f"Agent name '{agent_name}' should be lowercase with underscores",
                f"Example: '{agent_name.lower().replace('-', '_')}'"
            )

        # Required: kind
        if "kind" not in agent_config:
            self._add_issue(
                Severity.ERROR,
                f"{path}.kind",
                "Agent must have 'kind' field",
                "Valid kinds: 'supervisor', 'llm_agent', 'evaluator'"
            )
            return

        kind = agent_config["kind"]
        valid_kinds = ["supervisor", "llm_agent", "evaluator"]

        if kind not in valid_kinds:
            self._add_issue(
                Severity.ERROR,
                f"{path}.kind",
                f"Invalid agent kind '{kind}'",
                f"Valid kinds: {', '.join(valid_kinds)}"
            )

        # Validate based on kind
        if kind == "supervisor":
            self._validate_supervisor_agent(agent_name, agent_config)
        elif kind == "llm_agent":
            self._validate_llm_agent(agent_name, agent_config)
        elif kind == "evaluator":
            self._validate_evaluator_agent(agent_name, agent_config)

        # Validate llm_config if present
        if "llm_config" in agent_config:
            self._validate_llm_config(f"{path}.llm_config", agent_config["llm_config"])

    def _validate_supervisor_agent(self, agent_name: str, agent_config: Dict[str, Any]):
        """Validate supervisor-specific config"""
        path = f"agents.{agent_name}"

        # Supervisors should have policy
        if "policy" not in agent_config:
            self._add_issue(
                Severity.INFO,
                f"{path}.policy",
                "Supervisor should specify routing policy",
                "Recommended: 'policy': 'simple_router'"
            )

    def _validate_llm_agent(self, agent_name: str, agent_config: Dict[str, Any]):
        """Validate LLM agent-specific config"""
        path = f"agents.{agent_name}"

        # LLM agents should have llm_config
        if "llm_config" not in agent_config:
            self._add_issue(
                Severity.WARNING,
                f"{path}.llm_config",
                "LLM agent should specify llm_config with model",
                "Example: 'llm_config': {'model': 'gpt-4'}"
            )

        # Check tools
        if "tools" in agent_config:
            tools = agent_config["tools"]
            if not isinstance(tools, list):
                self._add_issue(
                    Severity.ERROR,
                    f"{path}.tools",
                    f"Tools must be a list, got {type(tools).__name__}"
                )

    def _validate_evaluator_agent(self, agent_name: str, agent_config: Dict[str, Any]):
        """Validate evaluator-specific config"""
        path = f"agents.{agent_name}"

        # Evaluators should have checks
        if "checks" not in agent_config:
            self._add_issue(
                Severity.WARNING,
                f"{path}.checks",
                "Evaluator should specify checks to perform"
            )

    def _validate_llm_config(self, path: str, llm_config: Dict[str, Any]):
        """Validate LLM configuration"""
        if not isinstance(llm_config, dict):
            self._add_issue(
                Severity.ERROR,
                path,
                f"llm_config must be a dict, got {type(llm_config).__name__}"
            )
            return

        # Check model
        if "model" not in llm_config:
            self._add_issue(
                Severity.WARNING,
                f"{path}.model",
                "llm_config should specify model"
            )
        else:
            model = llm_config["model"]
            valid_models = ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

            if not any(valid in model for valid in valid_models):
                self._add_issue(
                    Severity.WARNING,
                    f"{path}.model",
                    f"Unknown model '{model}'. May not be supported.",
                    f"Common models: {', '.join(valid_models)}"
                )

        # Check temperature
        if "temperature" in llm_config:
            temp = llm_config["temperature"]
            if not isinstance(temp, (int, float)):
                self._add_issue(
                    Severity.ERROR,
                    f"{path}.temperature",
                    f"Temperature must be a number, got {type(temp).__name__}"
                )
            elif temp < 0 or temp > 2:
                self._add_issue(
                    Severity.WARNING,
                    f"{path}.temperature",
                    f"Temperature {temp} is outside typical range (0-2)"
                )

        # Check max_tokens
        if "max_tokens" in llm_config:
            max_tokens = llm_config["max_tokens"]
            if not isinstance(max_tokens, int):
                self._add_issue(
                    Severity.ERROR,
                    f"{path}.max_tokens",
                    f"max_tokens must be an integer, got {type(max_tokens).__name__}"
                )
            elif max_tokens > 4096:
                self._add_issue(
                    Severity.INFO,
                    f"{path}.max_tokens",
                    f"max_tokens {max_tokens} is very high. May increase costs."
                )

    # ===== Tools Validation =====

    def _validate_tools(self):
        """Validate tools section"""
        if "tools" not in self.spec:
            return  # Tools are optional

        tools = self.spec["tools"]

        if not isinstance(tools, dict):
            self._add_issue(
                Severity.ERROR,
                "tools",
                f"Tools must be a dict, got {type(tools).__name__}"
            )
            return

        for tool_name, tool_config in tools.items():
            self._validate_tool(tool_name, tool_config)

    def _validate_tool(self, tool_name: str, tool_config: Dict[str, Any]):
        """Validate a single tool"""
        path = f"tools.{tool_name}"

        if not isinstance(tool_config, dict):
            self._add_issue(
                Severity.ERROR,
                path,
                f"Tool config must be a dict, got {type(tool_config).__name__}"
            )
            return

        # Required: type
        if "type" not in tool_config:
            self._add_issue(
                Severity.ERROR,
                f"{path}.type",
                "Tool must have 'type' field",
                "Valid types: 'http', 'sql', 'vectordb', 'function'"
            )
            return

        tool_type = tool_config["type"]
        valid_types = ["http", "sql", "vectordb", "function", "internal"]

        if tool_type not in valid_types:
            self._add_issue(
                Severity.ERROR,
                f"{path}.type",
                f"Invalid tool type '{tool_type}'",
                f"Valid types: {', '.join(valid_types)}"
            )

        # Validate based on type
        if tool_type == "http":
            self._validate_http_tool(tool_name, tool_config)
        elif tool_type == "sql":
            self._validate_sql_tool(tool_name, tool_config)
        elif tool_type == "vectordb":
            self._validate_vectordb_tool(tool_name, tool_config)

    def _validate_http_tool(self, tool_name: str, tool_config: Dict[str, Any]):
        """Validate HTTP tool configuration"""
        path = f"tools.{tool_name}"

        if "spec" not in tool_config:
            self._add_issue(
                Severity.ERROR,
                f"{path}.spec",
                "HTTP tool must have 'spec' field"
            )
            return

        spec = tool_config["spec"]

        # Required: url
        if "url" not in spec:
            self._add_issue(
                Severity.ERROR,
                f"{path}.spec.url",
                "HTTP tool must specify 'url'"
            )

        # Required: method
        if "method" not in spec:
            self._add_issue(
                Severity.ERROR,
                f"{path}.spec.method",
                "HTTP tool must specify 'method'",
                "Valid methods: GET, POST, PUT, DELETE, PATCH"
            )
        else:
            method = spec["method"]
            valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
            if method.upper() not in valid_methods:
                self._add_issue(
                    Severity.WARNING,
                    f"{path}.spec.method",
                    f"Unusual HTTP method '{method}'",
                    f"Common methods: {', '.join(valid_methods)}"
                )

    def _validate_sql_tool(self, tool_name: str, tool_config: Dict[str, Any]):
        """Validate SQL tool configuration"""
        path = f"tools.{tool_name}"

        if "spec" not in tool_config:
            self._add_issue(
                Severity.ERROR,
                f"{path}.spec",
                "SQL tool must have 'spec' field"
            )
            return

        spec = tool_config["spec"]

        # Should have connection_string or database_type
        if "connection_string" not in spec and "database_type" not in spec:
            self._add_issue(
                Severity.WARNING,
                f"{path}.spec",
                "SQL tool should specify 'connection_string' or 'database_type'"
            )

    def _validate_vectordb_tool(self, tool_name: str, tool_config: Dict[str, Any]):
        """Validate VectorDB tool configuration"""
        path = f"tools.{tool_name}"

        if "spec" not in tool_config:
            self._add_issue(
                Severity.ERROR,
                f"{path}.spec",
                "VectorDB tool must have 'spec' field"
            )
            return

        spec = tool_config["spec"]

        # Should have provider
        if "provider" not in spec:
            self._add_issue(
                Severity.WARNING,
                f"{path}.spec.provider",
                "VectorDB tool should specify 'provider'",
                "Examples: 'azure_ai_search', 'pinecone', 'weaviate', 'qdrant', 'chroma'"
            )

    # ===== Tasks Validation =====

    def _validate_tasks(self):
        """Validate tasks section"""
        if "tasks" not in self.spec:
            return  # Tasks are optional

        tasks = self.spec["tasks"]

        if not isinstance(tasks, list):
            self._add_issue(
                Severity.ERROR,
                "tasks",
                f"Tasks must be a list, got {type(tasks).__name__}"
            )
            return

        for idx, task in enumerate(tasks):
            self._validate_task(idx, task)

    def _validate_task(self, idx: int, task: Dict[str, Any]):
        """Validate a single task"""
        path = f"tasks[{idx}]"

        if not isinstance(task, dict):
            self._add_issue(
                Severity.ERROR,
                path,
                f"Task must be a dict, got {type(task).__name__}"
            )
            return

        # Required: id
        if "id" not in task:
            self._add_issue(
                Severity.ERROR,
                f"{path}.id",
                "Task must have 'id' field"
            )

        # Required: type
        if "type" not in task:
            self._add_issue(
                Severity.ERROR,
                f"{path}.type",
                "Task must have 'type' field",
                "Valid types: 'task', 'evaluator'"
            )

        # Check agent reference (will be validated in cross-references)
        if "agent" in task:
            agent_name = task["agent"]
            if not isinstance(agent_name, str):
                self._add_issue(
                    Severity.ERROR,
                    f"{path}.agent",
                    f"Task agent must be a string, got {type(agent_name).__name__}"
                )

    # ===== State Management Validation =====

    def _validate_state_management(self):
        """Validate state management section"""
        if "state_management" not in self.spec:
            self._add_issue(
                Severity.INFO,
                "state_management",
                "No state management configured. Using defaults.",
                "Consider adding state_management section for checkpointing config"
            )
            return

        state_mgmt = self.spec["state_management"]

        if "checkpointing" in state_mgmt:
            checkpoint = state_mgmt["checkpointing"]

            if "backend" in checkpoint:
                backend = checkpoint["backend"]
                valid_backends = ["cosmos", "redis", "memory"]

                if backend not in valid_backends:
                    self._add_issue(
                        Severity.WARNING,
                        "state_management.checkpointing.backend",
                        f"Unknown checkpointing backend '{backend}'",
                        f"Supported: {', '.join(valid_backends)}"
                    )

    # ===== UX Validation =====

    def _validate_ux(self):
        """Validate UX section"""
        if "ux" not in self.spec:
            return  # UX is optional

        ux = self.spec["ux"]

        if not isinstance(ux, dict):
            self._add_issue(
                Severity.ERROR,
                "ux",
                f"UX must be a dict, got {type(ux).__name__}"
            )
            return

        # Check at least one UX is enabled
        has_enabled_ux = False
        for ux_type in ["teams", "webchat", "api"]:
            if ux_type in ux and isinstance(ux[ux_type], dict):
                if ux[ux_type].get("enabled", False):
                    has_enabled_ux = True

        if not has_enabled_ux:
            self._add_issue(
                Severity.WARNING,
                "ux",
                "No UX interfaces enabled. Users won't be able to interact with the system.",
                "Enable at least one: teams, webchat, or api"
            )

    # ===== Deployment Validation =====

    def _validate_deployment(self):
        """Validate deployment section"""
        if "deployment" not in self.spec:
            return  # Deployment is optional

        deployment = self.spec["deployment"]

        if not isinstance(deployment, dict):
            self._add_issue(
                Severity.ERROR,
                "deployment",
                f"Deployment must be a dict, got {type(deployment).__name__}"
            )
            return

        # Check environments
        if "environments" in deployment:
            environments = deployment["environments"]

            if not isinstance(environments, dict):
                self._add_issue(
                    Severity.ERROR,
                    "deployment.environments",
                    f"Environments must be a dict, got {type(environments).__name__}"
                )
            elif not environments:
                self._add_issue(
                    Severity.WARNING,
                    "deployment.environments",
                    "No deployment environments configured"
                )

    # ===== Authentication Validation =====

    def _validate_authentication(self):
        """Validate authentication section"""
        if "authentication" not in self.spec:
            return  # Authentication is optional

        auth = self.spec["authentication"]

        if not isinstance(auth, dict):
            self._add_issue(
                Severity.ERROR,
                "authentication",
                f"Authentication must be a dict, got {type(auth).__name__}"
            )

    # ===== Cross-References Validation =====

    def _validate_cross_references(self):
        """Validate cross-references between sections"""
        # Tools referenced by agents must be defined
        if "agents" in self.spec and "tools" in self.spec:
            defined_tools = set(self.spec["tools"].keys())

            for agent_name, agent_config in self.spec["agents"].items():
                if "tools" in agent_config:
                    agent_tools = agent_config["tools"]
                    if isinstance(agent_tools, list):
                        for tool in agent_tools:
                            if tool not in defined_tools:
                                self._add_issue(
                                    Severity.ERROR,
                                    f"agents.{agent_name}.tools",
                                    f"Agent references undefined tool '{tool}'",
                                    f"Define tool in tools section or remove reference"
                                )

        # Tasks referencing agents
        if "tasks" in self.spec and "agents" in self.spec:
            defined_agents = set(self.spec["agents"].keys())

            for idx, task in enumerate(self.spec["tasks"]):
                if isinstance(task, dict) and "agent" in task:
                    agent_name = task["agent"]
                    if agent_name not in defined_agents:
                        self._add_issue(
                            Severity.ERROR,
                            f"tasks[{idx}].agent",
                            f"Task references undefined agent '{agent_name}'",
                            f"Define agent in agents section or fix reference"
                        )

    # ===== Best Practices =====

    def _validate_best_practices(self):
        """Check for best practices"""
        # Check for description
        if "description" not in self.spec:
            self._add_issue(
                Severity.INFO,
                "root.description",
                "Consider adding a description field for documentation"
            )

        # Check agent count
        if "agents" in self.spec:
            agent_count = len(self.spec["agents"])

            if agent_count > 10:
                self._add_issue(
                    Severity.INFO,
                    "agents",
                    f"Large number of agents ({agent_count}). Consider grouping related functionality."
                )

        # Check for monitoring
        if "deployment" in self.spec:
            deployment = self.spec["deployment"]
            if "monitoring" not in deployment:
                self._add_issue(
                    Severity.INFO,
                    "deployment.monitoring",
                    "Consider enabling monitoring (Application Insights, Log Analytics)"
                )


def validate_spec_file(spec_path: str) -> Tuple[bool, List[ValidationIssue]]:
    """
    Validate a spec file

    Args:
        spec_path: Path to JSON spec file

    Returns:
        Tuple of (is_valid, issues_list)
    """
    try:
        with open(spec_path) as f:
            spec = json.load(f)
    except FileNotFoundError:
        return False, [ValidationIssue(
            Severity.ERROR,
            "file",
            f"File not found: {spec_path}"
        )]
    except json.JSONDecodeError as e:
        return False, [ValidationIssue(
            Severity.ERROR,
            "file",
            f"Invalid JSON: {str(e)}"
        )]

    validator = SpecValidator()
    return validator.validate(spec)


def main():
    """CLI entry point"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate GoalGen spec files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a spec file
  ./spec_validator.py examples/travel_planning.json

  # Validate and show only errors
  ./spec_validator.py --errors-only examples/travel_planning.json

  # Validate multiple files
  ./spec_validator.py examples/*.json
        """
    )
    parser.add_argument(
        "spec_files",
        nargs="+",
        help="Spec file(s) to validate"
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Show only errors, not warnings or info"
    )
    parser.add_argument(
        "--warnings",
        action="store_true",
        help="Show errors and warnings, but not info"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    all_valid = True
    results = {}

    for spec_file in args.spec_files:
        is_valid, issues = validate_spec_file(spec_file)
        all_valid = all_valid and is_valid
        results[spec_file] = {"valid": is_valid, "issues": issues}

        if args.json:
            continue

        # Text output
        print(f"\n{'='*70}")
        print(f"Validating: {spec_file}")
        print(f"{'='*70}")

        if not issues:
            print("✅ Spec is valid! No issues found.")
            continue

        # Filter issues based on flags
        filtered_issues = issues
        if args.errors_only:
            filtered_issues = [i for i in issues if i.severity == Severity.ERROR]
        elif args.warnings:
            filtered_issues = [i for i in issues if i.severity in (Severity.ERROR, Severity.WARNING)]

        # Count by severity
        errors = sum(1 for i in issues if i.severity == Severity.ERROR)
        warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
        infos = sum(1 for i in issues if i.severity == Severity.INFO)

        print(f"\nSummary: {errors} errors, {warnings} warnings, {infos} info")
        print()

        # Print issues
        for issue in filtered_issues:
            print(issue)
            print()

        # Overall verdict
        if is_valid:
            print("✅ Spec is valid (but has warnings/suggestions)")
        else:
            print("❌ Spec is INVALID - fix errors before generating")

    # JSON output
    if args.json:
        output = {}
        for spec_file, result in results.items():
            output[spec_file] = {
                "valid": result["valid"],
                "issues": [
                    {
                        "severity": i.severity.value,
                        "path": i.path,
                        "message": i.message,
                        "suggestion": i.suggestion
                    }
                    for i in result["issues"]
                ]
            }
        print(json.dumps(output, indent=2))

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
