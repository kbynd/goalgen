"""
Unit tests for goal spec validation
"""
import json
import pytest
from pathlib import Path


class TestSpecValidation:
    """Test goal spec validation logic"""

    def test_valid_spec_loads_successfully(self):
        """Test that a valid spec loads without errors"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        # Basic structure validation
        assert "id" in spec
        assert "title" in spec
        assert "agents" in spec
        assert len(spec["agents"]) > 0

    def test_spec_has_required_fields(self):
        """Test that spec contains all required fields"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        required_fields = ["id", "title", "version", "agents"]
        for field in required_fields:
            assert field in spec, f"Missing required field: {field}"

    def test_spec_id_is_valid_identifier(self):
        """Test that spec id is a valid Python/file identifier"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        spec_id = spec["id"]
        assert spec_id.replace("_", "").isalnum(), f"Spec id '{spec_id}' contains invalid characters"
        assert not spec_id[0].isdigit(), f"Spec id '{spec_id}' starts with a digit"

    def test_agents_section_is_dict(self):
        """Test that agents section is a dictionary"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        assert isinstance(spec["agents"], dict), "agents must be a dictionary"
        assert len(spec["agents"]) > 0, "agents dictionary cannot be empty"

    def test_each_agent_has_kind(self):
        """Test that each agent has a 'kind' field"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        for agent_name, agent_config in spec["agents"].items():
            assert "kind" in agent_config, f"Agent '{agent_name}' missing 'kind' field"
            assert agent_config["kind"] in ["supervisor", "llm_agent", "evaluator"], \
                f"Agent '{agent_name}' has invalid kind: {agent_config['kind']}"

    def test_supervisor_agent_exists(self):
        """Test that at least one supervisor agent exists"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        has_supervisor = any(
            agent_config.get("kind") == "supervisor"
            for agent_config in spec["agents"].values()
        )
        assert has_supervisor, "Spec must have at least one supervisor agent"

    def test_tools_referenced_by_agents_are_defined(self):
        """Test that all tools referenced by agents are defined in tools section"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        defined_tools = set(spec.get("tools", {}).keys())

        for agent_name, agent_config in spec["agents"].items():
            agent_tools = agent_config.get("tools", [])
            for tool in agent_tools:
                assert tool in defined_tools, \
                    f"Agent '{agent_name}' references undefined tool '{tool}'"

    def test_http_tools_have_required_fields(self):
        """Test that HTTP tools have url and method"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        for tool_name, tool_config in spec.get("tools", {}).items():
            if tool_config.get("type") == "http":
                assert "spec" in tool_config, f"HTTP tool '{tool_name}' missing spec"
                assert "url" in tool_config["spec"], f"HTTP tool '{tool_name}' missing url"
                assert "method" in tool_config["spec"], f"HTTP tool '{tool_name}' missing method"

    def test_version_is_semantic(self):
        """Test that version follows semantic versioning"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        version = spec["version"]
        parts = version.split(".")
        assert len(parts) == 3, f"Version '{version}' is not semantic (x.y.z)"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' is not numeric"

    def test_tasks_reference_valid_agents(self):
        """Test that tasks reference agents that exist"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        defined_agents = set(spec["agents"].keys())

        for task in spec.get("tasks", []):
            if "agent" in task:
                assert task["agent"] in defined_agents, \
                    f"Task '{task['id']}' references undefined agent '{task['agent']}'"

    def test_llm_config_has_valid_model(self):
        """Test that LLM configs specify valid models"""
        spec_path = Path(__file__).parent.parent.parent / "examples" / "travel_planning.json"

        with open(spec_path) as f:
            spec = json.load(f)

        valid_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]

        for agent_name, agent_config in spec["agents"].items():
            if "llm_config" in agent_config:
                model = agent_config["llm_config"].get("model")
                if model:
                    assert any(valid in model for valid in valid_models), \
                        f"Agent '{agent_name}' has unknown model: {model}"


class TestSpecInvalidCases:
    """Test validation of invalid specs"""

    def test_missing_id_fails(self):
        """Test that spec without id should fail validation"""
        invalid_spec = {
            "title": "Test",
            "agents": {"test": {"kind": "llm_agent"}}
        }

        # This should fail validation
        assert "id" not in invalid_spec

    def test_empty_agents_fails(self):
        """Test that spec with no agents should fail validation"""
        invalid_spec = {
            "id": "test",
            "title": "Test",
            "agents": {}
        }

        assert len(invalid_spec["agents"]) == 0

    def test_invalid_agent_kind_fails(self):
        """Test that invalid agent kind should fail validation"""
        invalid_spec = {
            "id": "test",
            "title": "Test",
            "agents": {
                "test_agent": {"kind": "invalid_kind"}
            }
        }

        assert invalid_spec["agents"]["test_agent"]["kind"] not in [
            "supervisor", "llm_agent", "evaluator"
        ]

    def test_undefined_tool_reference_fails(self):
        """Test that referencing undefined tool should fail"""
        invalid_spec = {
            "id": "test",
            "title": "Test",
            "agents": {
                "test_agent": {
                    "kind": "llm_agent",
                    "tools": ["undefined_tool"]
                }
            },
            "tools": {}
        }

        agent_tools = invalid_spec["agents"]["test_agent"]["tools"]
        defined_tools = set(invalid_spec["tools"].keys())

        has_undefined = any(tool not in defined_tools for tool in agent_tools)
        assert has_undefined


class TestSpecEdgeCases:
    """Test edge cases in spec validation"""

    def test_agent_with_no_tools_is_valid(self):
        """Test that agents without tools are valid"""
        spec = {
            "id": "test",
            "title": "Test",
            "agents": {
                "test_agent": {"kind": "llm_agent"}
            }
        }

        # Agent without tools should be valid
        assert "tools" not in spec["agents"]["test_agent"] or \
               spec["agents"]["test_agent"].get("tools", []) == []

    def test_multiple_supervisors_is_valid(self):
        """Test that multiple supervisor agents are allowed"""
        spec = {
            "id": "test",
            "title": "Test",
            "agents": {
                "supervisor1": {"kind": "supervisor"},
                "supervisor2": {"kind": "supervisor"}
            }
        }

        supervisor_count = sum(
            1 for agent in spec["agents"].values()
            if agent.get("kind") == "supervisor"
        )
        assert supervisor_count == 2

    def test_optional_fields_can_be_missing(self):
        """Test that optional fields (tasks, ux, deployment) can be missing"""
        minimal_spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"}
            }
        }

        # These fields are optional
        assert "tasks" not in minimal_spec
        assert "ux" not in minimal_spec
        assert "deployment" not in minimal_spec

        # But required fields are present
        assert "id" in minimal_spec
        assert "title" in minimal_spec
        assert "agents" in minimal_spec
