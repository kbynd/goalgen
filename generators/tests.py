"""
Tests Generator

Generates test infrastructure and test cases.

Creates:
- tests/pytest.ini
- tests/test_schema_migrations.py (if schema_migrations defined)
"""

import os
from pathlib import Path
from typing import Dict, Any
from template_engine import TemplateEngine


def generate(spec: Dict[str, Any], out_dir: str, dry_run: bool = False):
    """
    Generate test infrastructure

    Creates:
    - tests/pytest.ini
    - tests/test_schema_migrations.py
    """

    print("[tests] Generating test infrastructure...")

    # Setup paths
    out_path = Path(out_dir)
    tests_dir = out_path / "tests"

    if not dry_run:
        tests_dir.mkdir(parents=True, exist_ok=True)

    # Setup template engine
    templates_dir = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_dir)

    # Extract context from spec
    context = {
        "goal_id": spec.get("id", "unknown"),
        "schema_version": spec.get("schema_version", 1),
        "schema_migrations": spec.get("schema_migrations", {}),
    }

    # Generate test files
    test_files = []

    # Always generate pytest.ini
    test_files.append(("tests/pytest.ini.j2", "pytest.ini"))

    # Generate schema migration tests if migrations defined
    if context.get("schema_migrations"):
        test_files.append(("tests/test_schema_migrations.py.j2", "test_schema_migrations.py"))

    for template_name, output_filename in test_files:
        output_path = tests_dir / output_filename

        if dry_run:
            print(f"[tests]   Would write: {output_path}")
        else:
            engine.render_to_file(template_name, context, output_path)
            print(f"[tests]   ✓ {output_path}")

    # Generate __init__.py
    init_file = tests_dir / "__init__.py"
    if not dry_run:
        init_file.write_text('"""Test suite"""\n')
        print(f"[tests]   ✓ {init_file}")

    print("[tests] ✓ Test infrastructure generated")
