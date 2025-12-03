"""
Deployment Generator

Generates deployment scripts for local and CI/CD execution.

Creates:
- scripts/build.sh - Build Docker images and package functions
- scripts/deploy.sh - Deploy infrastructure and application to Azure
- scripts/destroy.sh - Teardown all Azure resources
- scripts/publish_prompts.py - Publish prompts to Azure AI Foundry
"""

import os
from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine


def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate deployment scripts

    Creates:
    - scripts/build.sh
    - scripts/deploy.sh
    - scripts/destroy.sh
    """

    print("[deployment] Generating deployment scripts...")

    # Setup paths
    out_path = Path(out_dir)
    scripts_dir = out_path / "scripts"

    if not dry_run:
        scripts_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Extract context from spec
    context = {
        "goal_id": spec.get("id", "unknown"),
        "tools": spec.get("tools", {}),
        "schema_migrations": spec.get("schema_migrations", {}),
        "checkpointing_backend": spec.get("state_management", {}).get("checkpointing", {}).get("backend", "memory"),
    }

    # Generate scripts
    scripts = [
        ("scripts/build.sh.j2", "build.sh"),
        ("scripts/deploy.sh.j2", "deploy.sh"),
        ("scripts/destroy.sh.j2", "destroy.sh"),
        ("scripts/publish_prompts.py.j2", "publish_prompts.py"),
        ("scripts/test_prompts.py.j2", "test_prompts.py"),
        ("scripts/prepare_build_context.sh.j2", "prepare_build_context.sh"),  # For cloud builds
    ]

    # Add migration script if schema_migrations defined
    if context.get("schema_migrations"):
        scripts.append(("scripts/migrate_checkpoints.py.j2", "migrate_checkpoints.py"))

    for template_name, output_filename in scripts:
        output_path = scripts_dir / output_filename

        if dry_run:
            print(f"[deployment]   Would write: {output_path}")
        else:
            engine.render_to_file(template_name, context, output_path)
            # Make scripts executable
            output_path.chmod(0o755)
            print(f"[deployment]   ✓ {output_path}")

    print("[deployment] ✓ Deployment scripts generated")
