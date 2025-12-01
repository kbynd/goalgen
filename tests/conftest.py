"""
Pytest configuration and shared fixtures
"""
import json
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def goalgen_root():
    """Path to GoalGen root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def example_spec_path(goalgen_root):
    """Path to example travel planning spec"""
    return goalgen_root / "examples" / "travel_planning.json"


@pytest.fixture
def example_spec(example_spec_path):
    """Load example spec as dict"""
    with open(example_spec_path) as f:
        return json.load(f)


@pytest.fixture
def minimal_spec():
    """Minimal valid spec for testing"""
    return {
        "id": "test_goal",
        "title": "Test Goal",
        "version": "1.0.0",
        "agents": {
            "supervisor": {"kind": "supervisor"}
        }
    }


@pytest.fixture
def complex_spec():
    """Complex spec with multiple agents and tools"""
    return {
        "id": "complex_test",
        "title": "Complex Test Goal",
        "version": "1.0.0",
        "agents": {
            "supervisor_agent": {
                "kind": "supervisor",
                "policy": "simple_router",
                "llm_config": {"model": "gpt-4"}
            },
            "flight_agent": {
                "kind": "llm_agent",
                "tools": ["flight_api"],
                "llm_config": {"model": "gpt-4", "temperature": 0.5}
            },
            "hotel_agent": {
                "kind": "llm_agent",
                "tools": ["hotel_api"],
                "llm_config": {"model": "gpt-3.5-turbo"}
            }
        },
        "tools": {
            "flight_api": {
                "type": "http",
                "spec": {
                    "url": "https://api.example.com/flights",
                    "method": "POST",
                    "timeout": 30
                }
            },
            "hotel_api": {
                "type": "http",
                "spec": {
                    "url": "https://api.example.com/hotels",
                    "method": "GET"
                }
            }
        },
        "tasks": [
            {"id": "search_flights", "type": "task", "agent": "flight_agent"},
            {"id": "search_hotels", "type": "task", "agent": "hotel_agent"}
        ],
        "state_management": {
            "checkpointing": {"backend": "cosmos"}
        }
    }


@pytest.fixture
def invalid_spec_missing_id():
    """Invalid spec - missing id field"""
    return {
        "title": "Test Goal",
        "version": "1.0.0",
        "agents": {"supervisor": {"kind": "supervisor"}}
    }


@pytest.fixture
def invalid_spec_empty_agents():
    """Invalid spec - empty agents"""
    return {
        "id": "test_goal",
        "title": "Test Goal",
        "version": "1.0.0",
        "agents": {}
    }


@pytest.fixture
def invalid_spec_undefined_tool():
    """Invalid spec - agent references undefined tool"""
    return {
        "id": "test_goal",
        "title": "Test Goal",
        "version": "1.0.0",
        "agents": {
            "agent1": {
                "kind": "llm_agent",
                "tools": ["undefined_tool"]
            }
        },
        "tools": {}
    }


def pytest_configure(config):
    """Pytest configuration hook"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for full workflows"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time to run"
    )
    config.addinivalue_line(
        "markers", "requires_azure: Tests that require Azure credentials"
    )
    config.addinivalue_line(
        "markers", "requires_network: Tests that require network access"
    )
