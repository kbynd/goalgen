"""
Assets Generator
Generates static resources including prompt templates
"""

from pathlib import Path
from template_engine import TemplateEngine, get_context_from_spec


def generate(spec, out_dir, dry_run=False):
    """
    Generate static assets

    - Prompt templates for each agent
    - Logo/images (if specified in spec)
    - Adaptive Card templates (for Teams)
    """

    goal_id = spec.get("id", "unknown")
    print(f"[assets] Generating assets for goal: {goal_id}")

    out_path = Path(out_dir)
    prompts_dir = out_path / "prompts"

    # Get template context
    context = get_context_from_spec(spec)

    # Initialize template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Generate prompt templates for each agent
    agents = spec.get("agents", {})

    for agent_name, agent_config in agents.items():
        agent_kind = agent_config.get("kind", "llm_agent")

        # Choose template based on agent kind
        if agent_kind == "supervisor":
            template_name = "prompts/supervisor_agent.md.j2"
        elif agent_kind == "llm_agent":
            template_name = "prompts/llm_agent.md.j2"
        else:
            template_name = "prompts/default_agent.md.j2"

        # Build tool descriptions
        tool_descriptions = {}
        all_tools = spec.get("tools", {})
        for tool_name in agent_config.get("tools", []):
            if tool_name in all_tools:
                tool_descriptions[tool_name] = all_tools[tool_name].get("description", f"Tool for {tool_name}")

        # Add agent-specific context
        agent_context = {
            **context,
            "agent_name": agent_name,
            "agent_config": agent_config,
            "agent_kind": agent_kind,
            "tools": agent_config.get("tools", []),
            "tool_descriptions": tool_descriptions,
            "model": agent_config.get("llm_config", {}).get("model", "gpt-4"),
        }

        output_file = prompts_dir / f"{agent_name}.md"

        if not dry_run:
            engine.render_to_file(template_name, agent_context, output_file)
            print(f"[assets]   ✓ {output_file}")
        else:
            print(f"[assets]   (dry-run) {output_file}")

    # Copy logos/images if specified
    assets_config = spec.get("assets", {})

    if "logo" in assets_config:
        logo_path = assets_config["logo"]
        print(f"[assets]   Note: Copy logo from {logo_path} to assets/logo.png")

    print(f"[assets] ✓ Generated {len(agents)} prompt templates")
