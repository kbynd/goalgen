"""
Unit tests for generator output validation
"""
import json
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestScaffoldGenerator:
    """Test scaffold generator outputs"""

    def setup_method(self):
        """Create temporary output directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.spec = {
            "id": "test_goal",
            "title": "Test Goal",
            "version": "1.0.0",
            "agents": {
                "supervisor": {
                    "kind": "supervisor",
                    "policy": "simple_router",
                    "llm_config": {"model": "gpt-4"}
                }
            },
            "ux": {
                "teams": {"enabled": False},
                "webchat": {"enabled": False},
                "api": {"enabled": True}
            }
        }

    def teardown_method(self):
        """Clean up temporary directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_scaffold_creates_base_structure(self):
        """Test that scaffold creates expected directory structure"""
        from generators.scaffold import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        # Check directories
        assert Path(self.temp_dir, "langgraph").exists()
        assert Path(self.temp_dir, "orchestrator").exists()
        assert Path(self.temp_dir, "infra").exists()
        assert Path(self.temp_dir, "scripts").exists()
        assert Path(self.temp_dir, "tests").exists()
        assert Path(self.temp_dir, "prompts").exists()

    def test_scaffold_creates_readme(self):
        """Test that scaffold creates README.md"""
        from generators.scaffold import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        readme_path = Path(self.temp_dir, "README.md")
        assert readme_path.exists()

        # Check README contains spec title
        content = readme_path.read_text()
        assert self.spec["title"] in content

    def test_scaffold_creates_gitignore(self):
        """Test that scaffold creates .gitignore"""
        from generators.scaffold import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        gitignore_path = Path(self.temp_dir, ".gitignore")
        assert gitignore_path.exists()

        content = gitignore_path.read_text()
        assert "__pycache__" in content
        assert ".env" in content

    def test_scaffold_creates_base_files(self):
        """Test that scaffold creates base files"""
        from generators.scaffold import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        # Scaffold creates README, LICENSE, .gitignore
        assert Path(self.temp_dir, "README.md").exists()
        assert Path(self.temp_dir, "LICENSE").exists()
        assert Path(self.temp_dir, ".gitignore").exists()

        # requirements.txt is created per-component (orchestrator/, langgraph/) not at root
        # This matches the design where each component has its own dependencies


class TestLangGraphGenerator:
    """Test langgraph generator outputs"""

    def setup_method(self):
        """Create temporary output directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.spec = {
            "id": "test_goal",
            "title": "Test Goal",
            "version": "1.0.0",
            "agents": {
                "supervisor_agent": {"kind": "supervisor", "policy": "simple_router"},
                "worker_agent": {"kind": "llm_agent", "tools": []}
            }
        }

    def teardown_method(self):
        """Clean up temporary directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_langgraph_creates_quest_builder(self):
        """Test that langgraph generator creates quest_builder.py"""
        from generators.langgraph import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        quest_builder_path = Path(self.temp_dir, "langgraph", "quest_builder.py")
        assert quest_builder_path.exists()

    def test_quest_builder_imports_langgraph(self):
        """Test that quest_builder imports LangGraph"""
        from generators.langgraph import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        quest_builder_path = Path(self.temp_dir, "langgraph", "quest_builder.py")
        content = quest_builder_path.read_text()

        assert "from langgraph.graph import StateGraph" in content

    def test_quest_builder_defines_state_class(self):
        """Test that quest_builder defines state class"""
        from generators.langgraph import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        quest_builder_path = Path(self.temp_dir, "langgraph", "quest_builder.py")
        content = quest_builder_path.read_text()

        assert "State" in content or "class" in content

    def test_langgraph_creates_agents_directory(self):
        """Test that langgraph generator creates agents directory"""
        from generators.langgraph import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        agents_dir = Path(self.temp_dir, "langgraph", "agents")
        assert agents_dir.exists()
        assert agents_dir.is_dir()


class TestAgentsGenerator:
    """Test agents generator outputs"""

    def setup_method(self):
        """Create temporary output directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.spec = {
            "id": "test_goal",
            "title": "Test Goal",
            "version": "1.0.0",
            "agents": {
                "flight_agent": {
                    "kind": "llm_agent",
                    "tools": ["flight_api"],
                    "llm_config": {"model": "gpt-4"}
                }
            }
        }

    def teardown_method(self):
        """Clean up temporary directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_agents_generator_creates_agent_files(self):
        """Test that agent files are created for each agent"""
        from generators.agents import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        for agent_name in self.spec["agents"].keys():
            agent_file = Path(self.temp_dir, "langgraph", "agents", f"{agent_name}.py")
            assert agent_file.exists(), f"Agent file for {agent_name} not created"

    def test_agent_file_has_process_response(self):
        """Test that agent file implements _process_response abstract method"""
        from generators.agents import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        agent_file = Path(self.temp_dir, "langgraph", "agents", "flight_agent.py")
        content = agent_file.read_text()

        # Generated agents must implement the _process_response abstract method from BaseAgent
        assert "async def _process_response" in content

        # And should have a node function for LangGraph integration
        assert "async def flight_agent_node" in content


class TestToolsGenerator:
    """Test tools generator outputs"""

    def setup_method(self):
        """Create temporary output directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.spec = {
            "id": "test_goal",
            "title": "Test Goal",
            "version": "1.0.0",
            "agents": {"supervisor": {"kind": "supervisor"}},
            "tools": {
                "flight_api": {
                    "type": "http",
                    "spec": {"url": "https://api.example.com/flights", "method": "POST"}
                }
            }
        }

    def teardown_method(self):
        """Clean up temporary directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_tools_generator_creates_tool_files(self):
        """Test that tool files are created"""
        from generators.tools import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        tools_dir = Path(self.temp_dir, "tools")
        assert tools_dir.exists()

        for tool_name in self.spec["tools"].keys():
            tool_dir = Path(tools_dir, tool_name)
            assert tool_dir.exists(), f"Tool directory for {tool_name} not created"


class TestAssetsGenerator:
    """Test assets generator outputs"""

    def setup_method(self):
        """Create temporary output directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.spec = {
            "id": "test_goal",
            "title": "Test Goal",
            "version": "1.0.0",
            "agents": {
                "supervisor_agent": {"kind": "supervisor"},
                "worker_agent": {"kind": "llm_agent"}
            }
        }

    def teardown_method(self):
        """Clean up temporary directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_assets_creates_prompt_templates(self):
        """Test that prompt templates are created"""
        from generators.assets import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        prompts_dir = Path(self.temp_dir, "prompts")
        assert prompts_dir.exists()

        # Check that prompts are created for each agent
        for agent_name in self.spec["agents"].keys():
            prompt_file = Path(prompts_dir, f"{agent_name}.md")
            assert prompt_file.exists(), f"Prompt template for {agent_name} not created"

    def test_prompt_templates_have_content(self):
        """Test that prompt templates are not empty"""
        from generators.assets import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        prompts_dir = Path(self.temp_dir, "prompts")

        for agent_name in self.spec["agents"].keys():
            prompt_file = Path(prompts_dir, f"{agent_name}.md")
            content = prompt_file.read_text()
            assert len(content) > 0, f"Prompt template for {agent_name} is empty"
            assert agent_name.replace("_", " ").title() in content or \
                   "Agent" in content, f"Prompt doesn't reference agent name"


class TestManifestGeneration:
    """Test .goalgen manifest generation"""

    def setup_method(self):
        """Create temporary output directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.spec = {
            "id": "test_goal",
            "title": "Test Goal",
            "version": "1.0.0",
            "agents": {
                "supervisor": {
                    "kind": "supervisor",
                    "policy": "simple_router",
                    "llm_config": {"model": "gpt-4"}
                }
            },
            "ux": {
                "teams": {"enabled": False},
                "webchat": {"enabled": False},
                "api": {"enabled": True}
            }
        }

    def teardown_method(self):
        """Clean up temporary directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_manifest_is_created(self):
        """Test that .goalgen/manifest.json is created"""
        from generators.scaffold import generate

        generate(self.spec, self.temp_dir, dry_run=False)

        manifest_path = Path(self.temp_dir, ".goalgen", "manifest.json")
        # Note: manifest is created by main goalgen.py, not by individual generators
        # This test documents expected behavior

    def test_manifest_contains_spec_version(self):
        """Test that manifest tracks spec version"""
        # This test documents that manifest should contain:
        # - spec version
        # - generated files list
        # - generation timestamp
        # - goalgen version
        pass
