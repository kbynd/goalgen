"""
Tools Generator

Generates Azure Function implementations for tools from goal spec.

Creates:
- tools/<tool_name>/function_app.py - Azure Function handler
- tools/<tool_name>/host.json - Function configuration
- tools/<tool_name>/requirements.txt - Dependencies
"""

import os
from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine


def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate tool implementations

    Creates:
    - tools/<tool_name>/function_app.py for each tool
    - tools/<tool_name>/host.json
    - tools/<tool_name>/requirements.txt
    """

    print("[tools] Generating tool implementations...")

    # Setup paths
    out_path = Path(out_dir)
    tools_dir = out_path / "tools"

    if not dry_run:
        tools_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Get tools from spec
    tools = spec.get("tools", {})

    if not tools:
        print("[tools] Warning: No tools defined in spec")
        return

    generated_tools = []

    # Generate each tool
    for tool_name, tool_config in tools.items():
        print(f"[tools]   Generating {tool_name} ({tool_config.get('type', 'unknown')})...")

        tool_dir = tools_dir / tool_name

        if not dry_run:
            tool_dir.mkdir(parents=True, exist_ok=True)

        # Prepare context for template
        context = {
            "tool_name": tool_name,
            "tool": tool_config,
        }

        # Generate files
        files = [
            ("tools/function_app.py.j2", "function_app.py"),
            ("tools/host.json.j2", "host.json"),
            ("tools/requirements.txt.j2", "requirements.txt"),
        ]

        for template_name, output_filename in files:
            output_path = tool_dir / output_filename

            if dry_run:
                print(f"[tools]     Would write: {output_path}")
            else:
                engine.render_to_file(template_name, context, output_path)
                print(f"[tools]     ✓ {output_path}")

        generated_tools.append(tool_name)

    print(f"[tools] ✓ Generated {len(generated_tools)} tools")
