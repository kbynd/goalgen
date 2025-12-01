import os
from pathlib import Path
import sys

# Add parent directory to path to import template_engine
sys.path.insert(0, str(Path(__file__).parent.parent))
from template_engine import TemplateEngine, get_context_from_spec


def generate(spec, out_dir, dry_run=False):
    """
    Generate project scaffold (README, LICENSE, .gitignore, directory structure)

    Args:
        spec: Goal specification dictionary
        out_dir: Output directory path
        dry_run: If True, print what would be generated without writing files
    """
    print(f"[scaffold] Generating project scaffold for goal: {spec.get('id', 'unknown')}")

    out_path = Path(out_dir)
    templates_dir = Path(__file__).parent.parent / 'templates'
    engine = TemplateEngine(templates_dir)
    context = get_context_from_spec(spec)

    # Add version if not in spec
    if 'version' not in context:
        context['version'] = spec.get('version', '1.0.0')

    # Files to generate
    files = [
        ('scaffold/README.md.j2', 'README.md'),
        ('scaffold/LICENSE.j2', 'LICENSE'),
        ('scaffold/.gitignore.j2', '.gitignore'),
    ]

    for template_name, output_filename in files:
        output_file = out_path / output_filename

        if dry_run:
            print(f"  [DRY RUN] Would generate: {output_file}")
        else:
            engine.render_to_file(template_name, context, output_file)
            print(f"  ✓ Generated: {output_file}")

    # Create directory structure
    directories = [
        'infra/modules',
        'orchestrator/app',
        'workflow/agents',
        'workflow/evaluators',
        'tools',
        'prompts',
        'assets/images',
        'ci/workflows',
        'scripts',
        'tests/unit',
        'tests/integration',
        'config',  # For goal_spec.json
        'frmk',    # For Core SDK
    ]

    # Add conditional directories
    if spec.get('ux', {}).get('teams', {}).get('enabled'):
        directories.append('teams_app/adaptive_cards')

    if spec.get('ux', {}).get('webchat', {}).get('enabled'):
        directories.append('webchat/src')

    for dir_path in directories:
        full_path = out_path / dir_path
        if dry_run:
            print(f"  [DRY RUN] Would create directory: {full_path}")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created directory: {full_path}")

    # Copy goal spec to config/
    import json
    import shutil

    config_file = out_path / "config" / "goal_spec.json"
    if not dry_run:
        with open(config_file, 'w') as f:
            json.dump(spec, f, indent=2)
        print(f"  ✓ Copied goal spec: {config_file}")

    # Copy Core SDK (frmk/)
    frmk_source = Path(__file__).parent.parent / "frmk"
    frmk_dest = out_path / "frmk"

    if frmk_source.exists() and not dry_run:
        shutil.copytree(frmk_source, frmk_dest, dirs_exist_ok=True,
                       ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache'))
        print(f"  ✓ Copied Core SDK: {frmk_dest}")

    # Generate frmk/setup.py and frmk/pyproject.toml
    if not dry_run:
        frmk_setup_files = [
            ("frmk/setup.py.j2", frmk_dest / "setup.py"),
            ("frmk/pyproject.toml.j2", frmk_dest / "pyproject.toml"),
        ]

        for template_name, output_file in frmk_setup_files:
            if dry_run:
                print(f"  Would generate: {output_file}")
            else:
                engine.render_to_file(template_name, context, output_file)
                print(f"  ✓ Generated: {output_file}")

    print(f"[scaffold] ✓ Scaffold generation complete")
