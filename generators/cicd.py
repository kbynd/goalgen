"""
CI/CD Generator

Generates GitHub Actions workflow for build and deployment.

Creates:
- .github/workflows/deploy.yml - GitHub Actions workflow
"""

import os
from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine


def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate CI/CD workflow

    Creates:
    - .github/workflows/deploy.yml
    """

    print("[cicd] Generating CI/CD workflow...")

    # Setup paths
    out_path = Path(out_dir)
    workflows_dir = out_path / ".github" / "workflows"

    if not dry_run:
        workflows_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Extract context from spec
    context = {
        "goal_id": spec.get("id", "unknown"),
        "tools": spec.get("tools", {}),
    }

    # Generate GitHub Actions workflow
    workflow_file = workflows_dir / "deploy.yml"

    if dry_run:
        print(f"[cicd]   Would write: {workflow_file}")
    else:
        engine.render_to_file("cicd/deploy.yml.j2", context, workflow_file)
        print(f"[cicd]   ✓ {workflow_file}")

    print("[cicd] ✓ CI/CD workflow generated")
