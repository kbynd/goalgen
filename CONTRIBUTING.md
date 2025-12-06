# Contributing to GoalGen

Thank you for your interest in contributing to GoalGen! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Generator Development](#generator-development)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/). By participating, you are expected to uphold this code.

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, GoalGen version)
- **Sample goal spec** (if applicable)
- **Generated output** (if applicable)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

- Use a clear and descriptive title
- Provide detailed explanation of the proposed feature
- Explain why this enhancement would be useful
- Include mockups or examples if applicable

### Contributing Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (follow commit message guidelines below)
6. Push to your fork
7. Open a Pull Request

---

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- Virtual environment tool (venv, conda, etc.)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/goalgen.git
cd goalgen

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Install goalgen in development mode
pip install -e .
```

### Running GoalGen Locally

```bash
# Generate a project
./goalgen.py --spec examples/travel_planning.json --out test_output

# Run specific generators
./goalgen.py --spec examples/travel_planning.json --out test_output --targets scaffold,agents
```

---

## Project Structure

```
goalgen/
├── generators/          # Code generators (one per component)
│   ├── scaffold.py      # Project structure
│   ├── agents.py        # Agent implementations
│   ├── api.py           # FastAPI orchestrator
│   ├── teams.py         # Microsoft Teams Bot
│   ├── deployment.py    # Deployment scripts
│   └── ...
├── templates/           # Jinja2 templates for code generation
│   ├── scaffold/
│   ├── agents/
│   ├── api/
│   ├── teams/
│   └── ...
├── frmk/                # Core SDK (copied to generated projects)
│   ├── agents/          # BaseAgent and utilities
│   ├── core/            # Prompt loader, tool registry
│   └── utils/           # Logging, tracing, safety
├── examples/            # Example goal specifications
├── tests/               # Test suite
└── goalgen.py           # Main CLI entry point
```

### Key Components

- **Generators**: Python modules that produce output files from goal specs
- **Templates**: Jinja2 templates with `.j2` extension
- **Framework (frmk)**: Reusable code library for generated projects
- **Template Engine**: Renders Jinja2 templates with context from goal specs

---

## Generator Development

### Creating a New Generator

1. Create `generators/your_generator.py`:

```python
"""
Your Generator

Generates XYZ from goal spec.

Creates:
- output/file1.py - Description
- output/file2.yaml - Description
"""

from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine

def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """Generate XYZ component"""

    print("[your_generator] Generating XYZ...")

    # Setup paths
    out_path = Path(out_dir)
    target_dir = out_path / "target_directory"

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Build context from spec
    context = {
        "goal_id": spec.get("id", "unknown"),
        # ... extract relevant fields from spec
    }

    # Generate files
    files = [
        ("your_generator/template1.py.j2", "output1.py"),
        ("your_generator/template2.yaml.j2", "output2.yaml"),
    ]

    for template_name, output_filename in files:
        output_path = target_dir / output_filename

        if dry_run:
            print(f"[your_generator]   Would write: {output_path}")
        else:
            engine.render_to_file(template_name, context, output_path)
            print(f"[your_generator]   ✓ {output_path}")

    print("[your_generator] ✓ Generation complete")
```

2. Create templates in `templates/your_generator/`:

```jinja2
{# templates/your_generator/template1.py.j2 #}
"""
Generated {{goal_id}} component
"""

def main():
    print("Goal: {{ goal_title }}")

if __name__ == "__main__":
    main()
```

3. Register generator in `goalgen.py`:

```python
AVAILABLE_TARGETS = [
    # ... existing targets
    'your_generator',  # Add here
]

# Import and dispatch in main()
if 'your_generator' in selected_targets:
    import generators.your_generator as your_generator
    your_generator.generate(spec, out_dir, dry_run)
```

### Generator Best Practices

- **Print progress**: Use `[generator_name]` prefix for all output
- **Support dry_run**: Print "Would write:" without creating files
- **Extract context**: Pull relevant fields from spec into template context
- **Error handling**: Validate required spec fields, provide helpful errors
- **Documentation**: Docstring should list all generated files

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_generators.py

# Run with coverage
pytest --cov=generators --cov=frmk

# Run integration tests (requires Docker)
pytest tests/integration/
```

### Writing Tests

Create tests in `tests/`:

```python
# tests/generators/test_your_generator.py
import pytest
from pathlib import Path
from generators.your_generator import generate

def test_generates_required_files(tmp_path):
    """Test that generator creates expected files"""

    spec = {
        "id": "test_goal",
        "title": "Test Goal",
        # ... minimal valid spec
    }

    generate(spec, str(tmp_path), dry_run=False)

    # Assert files exist
    assert (tmp_path / "target_directory" / "output1.py").exists()
    assert (tmp_path / "target_directory" / "output2.yaml").exists()

    # Assert content
    content = (tmp_path / "target_directory" / "output1.py").read_text()
    assert "test_goal" in content
```

### E2E Testing

```bash
# Generate and test full project
./goalgen.py --spec examples/travel_planning.json --out e2e_test
cd e2e_test/orchestrator
pip install -r requirements.txt
pip install ../frmk
uvicorn main:app --host 127.0.0.1 --port 8000
```

---

## Pull Request Process

### Before Submitting

1. **Update documentation** if you changed APIs or added features
2. **Add tests** for new functionality
3. **Run tests** locally to ensure they pass
4. **Update CHANGELOG.md** with your changes
5. **Follow commit message guidelines** (see below)

### Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(teams): Add versioned adaptive cards for emulator support

Add v1.2 and v1.4 adaptive card templates with automatic channel
detection. Emulator uses v1.2, Teams uses v1.4.
```

```
fix(agents): Pass full goal_config to prompt loader

Previously only passed prompt_repository field, causing errors when
loader needed other config fields.
```

```
docs: Update CONTRIBUTING with generator development guide
```

### Pull Request Template

When creating a PR, include:

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Testing
How you tested the changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow guidelines
```

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use docstrings for modules, classes, and functions

### Code Formatting

```bash
# Format with black
black generators/ frmk/

# Check with flake8
flake8 generators/ frmk/

# Type check with mypy
mypy generators/ frmk/
```

### Documentation

- **Docstrings**: Use Google style docstrings
- **Comments**: Explain "why", not "what"
- **Templates**: Add comments in Jinja2 templates for clarity

**Example Docstring:**

```python
def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate deployment scripts from goal specification.

    Args:
        spec: Goal specification dictionary with deployment config
        out_dir: Output directory path for generated files
        dry_run: If True, print actions without writing files

    Raises:
        ValueError: If required spec fields are missing
    """
```

---

## Questions or Need Help?

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: See CLAUDE.md for detailed project architecture

---

## Attribution

This document was adapted from open-source contribution guidelines and best practices.

**Thank you for contributing to GoalGen!** 🎉
