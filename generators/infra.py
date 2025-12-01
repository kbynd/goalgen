"""
Infrastructure Generator

Generates Bicep templates for Azure deployment from goal spec.

Creates:
- infra/main.bicep - Main orchestration template
- infra/modules/*.bicep - Resource modules
- infra/parameters.json - Deployment parameters
"""

import os
from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine


def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate Bicep infrastructure templates

    Creates:
    - infra/main.bicep
    - infra/modules/keyvault.bicep
    - infra/modules/cosmos.bicep (if cosmos checkpointing)
    - infra/modules/redis.bicep (if redis checkpointing)
    - infra/modules/container-env.bicep
    - infra/modules/containerapp.bicep
    - infra/modules/functionapp.bicep (if tools exist)
    - infra/parameters.json
    """

    print("[infra] Generating Bicep infrastructure templates...")

    # Setup paths
    out_path = Path(out_dir)
    infra_dir = out_path / "infra"
    modules_dir = infra_dir / "modules"

    if not dry_run:
        infra_dir.mkdir(parents=True, exist_ok=True)
        modules_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Extract context from spec
    context = _build_context(spec)

    # Generate main.bicep
    main_bicep = infra_dir / "main.bicep"
    if dry_run:
        print(f"[infra]   Would write: {main_bicep}")
    else:
        engine.render_to_file("infra/main.bicep.j2", context, main_bicep)
        print(f"[infra]   ✓ {main_bicep}")

    # Generate modules
    modules = [
        "keyvault.bicep",
        "container-env.bicep",
        "containerapp.bicep",
    ]

    # Add checkpointing backend module
    checkpointing_backend = context.get("checkpointing_backend", "memory")
    if checkpointing_backend == "cosmos":
        modules.append("cosmos.bicep")
    elif checkpointing_backend == "redis":
        modules.append("redis.bicep")

    # Add function app if tools exist
    if context.get("tools"):
        modules.append("functionapp.bicep")

    for module in modules:
        module_path = modules_dir / module
        template_name = f"infra/modules/{module}.j2"

        if dry_run:
            print(f"[infra]   Would write: {module_path}")
        else:
            engine.render_to_file(template_name, context, module_path)
            print(f"[infra]   ✓ {module_path}")

    # Generate parameters.json
    params_file = infra_dir / "parameters.json"
    if dry_run:
        print(f"[infra]   Would write: {params_file}")
    else:
        engine.render_to_file("infra/parameters.json.j2", context, params_file)
        print(f"[infra]   ✓ {params_file}")

    print(f"[infra] ✓ Generated {len(modules) + 2} infrastructure files")


def _build_context(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Build template context from spec"""

    goal_id = spec.get("id", "unknown")
    tools = spec.get("tools", {})

    # Checkpointing backend
    checkpointing_config = spec.get("state_management", {}).get("checkpointing", {})
    checkpointing_backend = checkpointing_config.get("backend", "memory")

    return {
        "goal_id": goal_id,
        "tools": tools,
        "checkpointing_backend": checkpointing_backend,
    }
