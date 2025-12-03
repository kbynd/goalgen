"""
API Generator

Generates FastAPI orchestrator from goal spec.

Creates:
- orchestrator/main.py - FastAPI app with /message endpoint
- orchestrator/Dockerfile - Container image
- orchestrator/.env.sample - Environment variables template
"""

import os
from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine


def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate FastAPI orchestrator

    Creates:
    - orchestrator/main.py
    - orchestrator/Dockerfile
    - orchestrator/.env.sample
    """

    print("[api] Generating FastAPI orchestrator...")

    # Setup paths
    out_path = Path(out_dir)
    orchestrator_dir = out_path / "orchestrator"

    if not dry_run:
        orchestrator_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Extract context from spec
    context = _build_context(spec)

    # Generate files
    files = [
        ("api/main.py.j2", "main.py"),
        ("api/Dockerfile-cloud.j2", "Dockerfile"),  # Updated to use cloud-compatible Dockerfile
        ("api/.env.sample.j2", ".env.sample"),
        ("api/requirements.txt.j2", "requirements.txt"),
        ("api/.dockerignore.j2", ".dockerignore"),
    ]

    for template_name, output_filename in files:
        output_path = orchestrator_dir / output_filename

        if dry_run:
            print(f"[api]   Would write: {output_path}")
        else:
            engine.render_to_file(template_name, context, output_path)
            print(f"[api]   ✓ {output_path}")

    # Generate __init__.py
    init_file = orchestrator_dir / "__init__.py"
    if not dry_run:
        init_file.write_text('"""Orchestrator module"""\n')
        print(f"[api]   ✓ {init_file}")

    print("[api] ✓ FastAPI orchestrator generated")


def _build_context(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Build template context from spec"""

    goal_id = spec.get("id", "unknown")
    goal_title = spec.get("title", goal_id)
    goal_description = spec.get("description", "")

    agents = spec.get("agents", {})
    tools = spec.get("tools", {})
    ux = spec.get("ux", {})

    # State management
    state_config = spec.get("state_management", {}).get("state", {}).get("schema", {})
    context_fields = state_config.get("context_fields", [])

    # Checkpointing
    checkpointing_config = spec.get("state_management", {}).get("checkpointing", {})
    checkpointing_backend = checkpointing_config.get("backend", "memory")

    return {
        "goal_id": goal_id,
        "goal_title": goal_title,
        "goal_description": goal_description,
        "agents": agents,
        "tools": tools,
        "ux": ux,
        "context_fields": context_fields,
        "checkpointing_backend": checkpointing_backend,
    }
