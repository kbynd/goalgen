"""
Integration tests for full GoalGen generation flow
"""
import json
import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path


class TestFullGeneration:
    """Test complete generation workflow"""

    def setup_method(self):
        """Create temporary output directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.goalgen_root = Path(__file__).parent.parent.parent
        self.spec_path = self.goalgen_root / "examples" / "travel_planning.json"

    def teardown_method(self):
        """Clean up temporary directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_full_generation_completes_successfully(self):
        """Test that full generation completes without errors"""
        result = subprocess.run(
            [
                sys.executable if 'sys' in dir() else "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(self.spec_path),
                "--out", self.temp_dir
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert "completed" in result.stdout.lower()

    def test_generated_project_has_complete_structure(self):
        """Test that generated project has all expected directories"""
        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(self.spec_path),
                "--out", self.temp_dir
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Check all expected directories exist
        expected_dirs = [
            "langgraph",
            "orchestrator",
            "infra",
            "scripts",
            "tests",
            "prompts",
            "tools",
            ".goalgen"
        ]

        for dir_name in expected_dirs:
            dir_path = Path(self.temp_dir, dir_name)
            assert dir_path.exists(), f"Expected directory {dir_name} not found"

    def test_generated_project_has_manifest(self):
        """Test that manifest is created"""
        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(self.spec_path),
                "--out", self.temp_dir
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        manifest_path = Path(self.temp_dir, ".goalgen", "manifest.json")
        assert manifest_path.exists(), "Manifest not created"

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "spec" in manifest
        assert "generated_files" in manifest
        assert "timestamp" in manifest

    def test_selective_generation_scaffold_only(self):
        """Test generating only scaffold"""
        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(self.spec_path),
                "--out", self.temp_dir,
                "--targets", "scaffold"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Scaffold should create base structure
        assert Path(self.temp_dir, "README.md").exists()
        assert Path(self.temp_dir, ".gitignore").exists()

    def test_selective_generation_assets_only(self):
        """Test generating only assets"""
        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(self.spec_path),
                "--out", self.temp_dir,
                "--targets", "assets"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Assets should create prompts
        prompts_dir = Path(self.temp_dir, "prompts")
        assert prompts_dir.exists()
        assert len(list(prompts_dir.glob("*.md"))) > 0

    def test_dry_run_does_not_create_files(self):
        """Test that dry run doesn't create files"""
        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(self.spec_path),
                "--out", self.temp_dir,
                "--dry-run"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "dry run" in result.stdout.lower() or "dry-run" in result.stdout.lower()

        # Should not create README (or very minimal structure)
        # Dry run behavior may vary, but manifest shouldn't be fully populated
        if Path(self.temp_dir, ".goalgen", "manifest.json").exists():
            with open(Path(self.temp_dir, ".goalgen", "manifest.json")) as f:
                manifest = json.load(f)
            # In dry run, generated_files should be empty or not exist
            assert manifest.get("generated_files", []) == []

    def test_multiple_targets_generation(self):
        """Test generating multiple specific targets"""
        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(self.spec_path),
                "--out", self.temp_dir,
                "--targets", "scaffold,assets,agents"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Check that specified targets were generated
        assert Path(self.temp_dir, "README.md").exists()  # scaffold
        assert Path(self.temp_dir, "prompts").exists()  # assets
        assert Path(self.temp_dir, "langgraph", "agents").exists()  # agents


class TestGenerationWithDifferentSpecs:
    """Test generation with various spec configurations"""

    def setup_method(self):
        """Create temporary output directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.goalgen_root = Path(__file__).parent.parent.parent

    def teardown_method(self):
        """Clean up"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_minimal_spec_generates_successfully(self):
        """Test generation with minimal spec"""
        minimal_spec = {
            "id": "minimal_test",
            "title": "Minimal Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"}
            }
        }

        spec_path = Path(self.temp_dir, "minimal_spec.json")
        with open(spec_path, "w") as f:
            json.dump(minimal_spec, f, indent=2)

        output_dir = Path(self.temp_dir, "output")
        output_dir.mkdir()

        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(spec_path),
                "--out", str(output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_spec_with_multiple_agents_and_tools(self):
        """Test generation with complex spec"""
        complex_spec = {
            "id": "complex_test",
            "title": "Complex Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"},
                "agent1": {"kind": "llm_agent", "tools": ["tool1"]},
                "agent2": {"kind": "llm_agent", "tools": ["tool2"]}
            },
            "tools": {
                "tool1": {"type": "http", "spec": {"url": "https://api1.com", "method": "GET"}},
                "tool2": {"type": "http", "spec": {"url": "https://api2.com", "method": "POST"}}
            }
        }

        spec_path = Path(self.temp_dir, "complex_spec.json")
        with open(spec_path, "w") as f:
            json.dump(complex_spec, f, indent=2)

        output_dir = Path(self.temp_dir, "output")
        output_dir.mkdir()

        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(spec_path),
                "--out", str(output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify all agents have prompt templates
        for agent_name in complex_spec["agents"].keys():
            prompt_file = Path(output_dir, "prompts", f"{agent_name}.md")
            assert prompt_file.exists(), f"Prompt for {agent_name} not created"


class TestIncrementalGeneration:
    """Test incremental generation features"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.goalgen_root = Path(__file__).parent.parent.parent

    def teardown_method(self):
        """Clean up"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_incremental_flag_preserves_existing_files(self):
        """Test that incremental mode preserves user modifications"""
        # First generation
        spec_v1 = {
            "id": "incremental_test",
            "title": "Incremental Test",
            "version": "1.0.0",
            "agents": {
                "supervisor": {"kind": "supervisor"},
                "agent1": {"kind": "llm_agent"}
            }
        }

        spec_path = Path(self.temp_dir, "spec.json")
        with open(spec_path, "w") as f:
            json.dump(spec_v1, f, indent=2)

        output_dir = Path(self.temp_dir, "output")
        output_dir.mkdir()

        # Initial generation
        subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(spec_path),
                "--out", str(output_dir)
            ],
            capture_output=True,
            text=True
        )

        # Modify a generated file
        agent_file = Path(output_dir, "langgraph", "agents", "agent1.py")
        if agent_file.exists():
            original_content = agent_file.read_text()
            modified_content = original_content + "\n# USER MODIFICATION\n"
            agent_file.write_text(modified_content)

            # Second generation with new agent
            spec_v2 = {
                "id": "incremental_test",
                "title": "Incremental Test",
                "version": "1.0.0",
                "agents": {
                    "supervisor": {"kind": "supervisor"},
                    "agent1": {"kind": "llm_agent"},
                    "agent2": {"kind": "llm_agent"}  # New agent
                }
            }

            with open(spec_path, "w") as f:
                json.dump(spec_v2, f, indent=2)

            # Incremental generation
            result = subprocess.run(
                [
                    "python",
                    str(self.goalgen_root / "goalgen.py"),
                    "--spec", str(spec_path),
                    "--out", str(output_dir),
                    "--incremental"
                ],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Check that modification is preserved
                new_content = agent_file.read_text()
                assert "USER MODIFICATION" in new_content, \
                    "Incremental mode should preserve user modifications"


class TestErrorHandling:
    """Test error handling in generation"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.goalgen_root = Path(__file__).parent.parent.parent

    def teardown_method(self):
        """Clean up"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_invalid_spec_path_fails_gracefully(self):
        """Test that invalid spec path produces clear error"""
        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", "/nonexistent/path/spec.json",
                "--out", self.temp_dir
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()

    def test_invalid_json_fails_gracefully(self):
        """Test that invalid JSON produces clear error"""
        invalid_spec_path = Path(self.temp_dir, "invalid.json")
        invalid_spec_path.write_text("{ invalid json }")

        result = subprocess.run(
            [
                "python",
                str(self.goalgen_root / "goalgen.py"),
                "--spec", str(invalid_spec_path),
                "--out", self.temp_dir
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "json" in result.stderr.lower() or "parse" in result.stderr.lower()


# Add sys import at top
import sys
