"""
Unit tests for spec validator
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from spec_validator import SpecValidator, Severity, validate_spec_file


class TestSpecValidator:
    """Test spec validator"""

    def test_valid_spec_passes(self, example_spec):
        """Test that valid spec passes validation"""
        validator = SpecValidator()
        is_valid, issues = validator.validate(example_spec)

        assert is_valid
        # May have INFO level suggestions, but no errors
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_minimal_spec_passes(self, minimal_spec):
        """Test that minimal valid spec passes"""
        validator = SpecValidator()
        is_valid, issues = validator.validate(minimal_spec)

        assert is_valid
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_missing_id_fails(self, invalid_spec_missing_id):
        """Test that spec without id fails"""
        validator = SpecValidator()
        is_valid, issues = validator.validate(invalid_spec_missing_id)

        assert not is_valid
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert any("id" in i.path.lower() for i in errors)

    def test_empty_agents_fails(self, invalid_spec_empty_agents):
        """Test that spec with empty agents fails"""
        validator = SpecValidator()
        is_valid, issues = validator.validate(invalid_spec_empty_agents)

        assert not is_valid
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert any("agents" in i.path for i in errors)

    def test_undefined_tool_reference_fails(self, invalid_spec_undefined_tool):
        """Test that undefined tool reference fails"""
        validator = SpecValidator()
        is_valid, issues = validator.validate(invalid_spec_undefined_tool)

        assert not is_valid
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert any("undefined_tool" in i.message for i in errors)


class TestRequiredFields:
    """Test required field validation"""

    def test_missing_id(self):
        """Test missing id field"""
        spec = {
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("id" in i.path for i in issues if i.severity == Severity.ERROR)

    def test_missing_title(self):
        """Test missing title field"""
        spec = {
            "id": "test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("title" in i.path for i in issues if i.severity == Severity.ERROR)

    def test_missing_version(self):
        """Test missing version field"""
        spec = {
            "id": "test",
            "title": "Test",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("version" in i.path for i in issues if i.severity == Severity.ERROR)

    def test_missing_agents(self):
        """Test missing agents field"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0"
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("agents" in i.path for i in issues if i.severity == Severity.ERROR)


class TestIDValidation:
    """Test ID format validation"""

    def test_valid_id(self):
        """Test valid ID format"""
        spec = {
            "id": "my_goal_123",
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        # May have other issues, but id should be ok
        id_errors = [i for i in issues if i.severity == Severity.ERROR and "id" in i.path]
        assert len(id_errors) == 0

    def test_id_with_uppercase_fails(self):
        """Test that uppercase in ID fails"""
        spec = {
            "id": "MyGoal",
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("lowercase" in i.message for i in issues if "id" in i.path)

    def test_id_with_hyphen_fails(self):
        """Test that hyphen in ID fails"""
        spec = {
            "id": "my-goal",
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("id" in i.path for i in issues if i.severity == Severity.ERROR)

    def test_id_starting_with_number_fails(self):
        """Test that ID starting with number fails"""
        spec = {
            "id": "123_goal",
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("id" in i.path for i in issues if i.severity == Severity.ERROR)


class TestVersionValidation:
    """Test version format validation"""

    def test_valid_version(self):
        """Test valid semantic version"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.2.3",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        version_errors = [i for i in issues if i.severity == Severity.ERROR and "version" in i.path]
        assert len(version_errors) == 0

    def test_version_with_prerelease(self):
        """Test version with prerelease tag"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0-alpha.1",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        version_errors = [i for i in issues if i.severity == Severity.ERROR and "version" in i.path]
        assert len(version_errors) == 0

    def test_invalid_version_format(self):
        """Test invalid version format"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0",
            "agents": {"supervisor": {"kind": "supervisor"}}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("version" in i.path and "semantic" in i.message for i in issues)


class TestAgentValidation:
    """Test agent validation"""

    def test_missing_supervisor_fails(self):
        """Test that spec without supervisor fails"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "worker": {"kind": "llm_agent"}
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("supervisor" in i.message for i in issues if i.severity == Severity.ERROR)

    def test_invalid_agent_kind(self):
        """Test invalid agent kind"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"},
                "bad_agent": {"kind": "invalid_kind"}
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("kind" in i.path and "invalid_kind" in i.message for i in issues)

    def test_agent_without_kind_fails(self):
        """Test that agent without kind fails"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"},
                "bad_agent": {"tools": []}
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("kind" in i.path for i in issues if i.severity == Severity.ERROR)


class TestToolValidation:
    """Test tool validation"""

    def test_http_tool_without_url_fails(self):
        """Test HTTP tool without URL fails"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}},
            "tools": {
                "bad_tool": {
                    "type": "http",
                    "spec": {"method": "GET"}
                }
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("url" in i.path or "url" in i.message for i in issues if i.severity == Severity.ERROR)

    def test_http_tool_without_method_fails(self):
        """Test HTTP tool without method fails"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}},
            "tools": {
                "bad_tool": {
                    "type": "http",
                    "spec": {"url": "https://example.com"}
                }
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("method" in i.path or "method" in i.message for i in issues if i.severity == Severity.ERROR)

    def test_tool_without_type_fails(self):
        """Test tool without type fails"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}},
            "tools": {
                "bad_tool": {
                    "spec": {"url": "https://example.com"}
                }
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("type" in i.path for i in issues if i.severity == Severity.ERROR)


class TestCrossReferences:
    """Test cross-reference validation"""

    def test_agent_references_undefined_tool(self):
        """Test that agent referencing undefined tool fails"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"},
                "worker": {"kind": "llm_agent", "tools": ["undefined_tool"]}
            },
            "tools": {}
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("undefined_tool" in i.message for i in issues if i.severity == Severity.ERROR)

    def test_task_references_undefined_agent(self):
        """Test that task referencing undefined agent fails"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"}
            },
            "tasks": [
                {"id": "task1", "type": "task", "agent": "undefined_agent"}
            ]
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("undefined_agent" in i.message for i in issues if i.severity == Severity.ERROR)


class TestFileValidation:
    """Test file-based validation"""

    def test_validate_valid_file(self, example_spec_path):
        """Test validating valid file"""
        is_valid, issues = validate_spec_file(str(example_spec_path))

        assert is_valid
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_validate_nonexistent_file(self):
        """Test validating nonexistent file"""
        is_valid, issues = validate_spec_file("/nonexistent/file.json")

        assert not is_valid
        assert len(issues) > 0
        assert "not found" in issues[0].message.lower()

    def test_validate_invalid_json(self, tmp_path):
        """Test validating file with invalid JSON"""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")

        is_valid, issues = validate_spec_file(str(bad_file))

        assert not is_valid
        assert any("json" in i.message.lower() for i in issues)


class TestLLMConfigValidation:
    """Test LLM config validation"""

    def test_temperature_out_of_range(self):
        """Test temperature outside typical range"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {
                    "kind": "supervisor",
                    "llm_config": {"model": "gpt-4", "temperature": 3.0}
                }
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        # Should be valid but with warning
        warnings = [i for i in issues if i.severity == Severity.WARNING and "temperature" in i.path]
        assert len(warnings) > 0

    def test_invalid_temperature_type(self):
        """Test invalid temperature type"""
        spec = {
            "id": "test",
            "title": "Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {
                    "kind": "supervisor",
                    "llm_config": {"model": "gpt-4", "temperature": "hot"}
                }
            }
        }

        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        assert not is_valid
        assert any("temperature" in i.path and "number" in i.message for i in issues)
