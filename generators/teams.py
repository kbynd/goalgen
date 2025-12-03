"""
Teams Generator

Generates Microsoft Teams Bot implementation with Bot Framework integration.

Creates:
- teams_app/bot.py - Bot Framework integration with ConversationMapper
- teams_app/config.py - Configuration management
- teams_app/requirements.txt - Teams Bot dependencies
- teams_app/manifest.json - Teams app manifest
- teams_app/adaptive_cards/*.json - Adaptive Card templates
- teams_app/.env.sample - Environment variables template
"""

import os
from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine


def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate Microsoft Teams Bot implementation

    Creates:
    - teams_app/bot.py - Main bot handler with ConversationMapper
    - teams_app/config.py - Configuration management
    - teams_app/requirements.txt - Dependencies
    - teams_app/manifest.json - Teams app manifest
    - teams_app/adaptive_cards/ - Adaptive Card templates
    - teams_app/.env.sample - Environment variables
    """

    print("[teams] Generating Microsoft Teams Bot...")

    # Check if Teams is enabled
    ux_config = spec.get("ux", {})
    teams_config = ux_config.get("teams", {})

    if not teams_config.get("enabled", False):
        print("[teams]   ⚠️  Teams not enabled in spec, skipping")
        return

    # Setup paths
    out_path = Path(out_dir)
    teams_dir = out_path / "teams_app"
    adaptive_cards_dir = teams_dir / "adaptive_cards"

    if not dry_run:
        teams_dir.mkdir(parents=True, exist_ok=True)
        adaptive_cards_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Extract context from spec
    context = _build_context(spec)

    # Generate files
    files = [
        ("teams/bot.py.j2", "bot.py"),
        ("teams/config.py.j2", "config.py"),
        ("teams/requirements.txt.j2", "requirements.txt"),
        ("teams/manifest.json.j2", "manifest.json"),
        ("teams/.env.sample.j2", ".env.sample"),
        ("teams/__init__.py.j2", "__init__.py"),
    ]

    for template_name, output_filename in files:
        output_path = teams_dir / output_filename

        if dry_run:
            print(f"[teams]   Would write: {output_path}")
        else:
            engine.render_to_file(template_name, context, output_path)
            print(f"[teams]   ✓ {output_path}")

    # Generate adaptive cards
    adaptive_card_templates = [
        ("teams/adaptive_cards/welcome.json.j2", "welcome.json"),
        ("teams/adaptive_cards/response.json.j2", "response.json"),
        ("teams/adaptive_cards/error.json.j2", "error.json"),
    ]

    for template_name, output_filename in adaptive_card_templates:
        output_path = adaptive_cards_dir / output_filename

        if dry_run:
            print(f"[teams]   Would write: {output_path}")
        else:
            engine.render_to_file(template_name, context, output_path)
            print(f"[teams]   ✓ {output_path}")

    print(f"[teams] ✓ Teams Bot generated for: {context['goal_id']}")


def _build_context(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Build template context from spec"""

    goal_id = spec.get("id", "unknown")
    goal_title = spec.get("title", goal_id)
    goal_description = spec.get("description", "")

    # UX configuration
    ux_config = spec.get("ux", {})
    teams_config = ux_config.get("teams", {})
    api_config = ux_config.get("api", {})

    # Conversation mapping configuration
    conversation_mapping = teams_config.get("conversation_mapping", {
        "strategy": "hash",
        "hash_algorithm": "sha256",
        "hash_length": 16,
        "prefix": "teams"
    })

    # LangGraph workflow endpoint
    langgraph_endpoint = api_config.get("endpoint") or f"http://localhost:8000"

    # Authentication
    auth_config = spec.get("authentication", {})
    auth_backend = auth_config.get("backend", {}).get("type", "managed_identity")

    # Bot configuration
    bot_name = teams_config.get("bot_name", f"{goal_title} Bot")
    bot_description = teams_config.get("bot_description", goal_description)
    bot_icon_color = teams_config.get("icon_color", "#4CAF50")
    bot_accent_color = teams_config.get("accent_color", "#4CAF50")

    # Adaptive Cards configuration
    use_adaptive_cards = teams_config.get("use_adaptive_cards", True)

    return {
        "goal_id": goal_id,
        "goal_title": goal_title,
        "goal_description": goal_description,
        "bot_name": bot_name,
        "bot_description": bot_description,
        "bot_icon_color": bot_icon_color,
        "bot_accent_color": bot_accent_color,
        "langgraph_endpoint": langgraph_endpoint,
        "conversation_mapping": conversation_mapping,
        "auth_backend": auth_backend,
        "use_adaptive_cards": use_adaptive_cards,
    }
