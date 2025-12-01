#!/usr/bin/env python3
"""
GoalGen - Code generator for multi-agent conversational AI systems

Generates production-ready LangGraph projects with Azure deployment infrastructure.
"""
import argparse, os, json, sys
from pathlib import Path
from generators import (
    scaffold, langgraph, api, teams, webchat,
    tools, agents, evaluators, infra, security, assets,
    cicd, deployment, tests
)
from manifest import GenerationManifest
from spec_validator import SpecValidator, Severity

__version__ = "0.1.0"

SUB_GENERATORS = {
    "scaffold": scaffold.generate,
    "langgraph": langgraph.generate,
    "api": api.generate,
    "teams": teams.generate,
    "webchat": webchat.generate,
    "tools": tools.generate,
    "agents": agents.generate,
    "evaluators": evaluators.generate,
    "infra": infra.generate,
    "security": security.generate,
    "assets": assets.generate,
    "cicd": cicd.generate,
    "deployment": deployment.generate,
    "tests": tests.generate
}

def load_spec(path):
    with open(path) as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(
        description="GoalGen - Code generator for multi-agent conversational AI systems",
        epilog="For more information: https://github.com/yourorg/goalgen"
    )
    parser.add_argument("--spec", required=True, help="Path to goal spec JSON")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--targets", default="scaffold,langgraph,api,teams,webchat,tools,agents,evaluators,infra,security,assets,cicd,deployment,tests",
                        help="Comma-separated list of targets to generate")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be generated")
    parser.add_argument("--incremental", action="store_true",
                       help="Incremental mode: preserve existing files, only add/update changed components")
    parser.add_argument("--force", action="store_true",
                       help="Force regeneration of all files (ignores user modifications)")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip spec validation (not recommended)")
    parser.add_argument("--version", action="version", version=f"GoalGen {__version__}")
    args = parser.parse_args()

    spec = load_spec(args.spec)

    # Validate spec before generation
    if not args.skip_validation:
        print("[goalgen] Validating spec...")
        validator = SpecValidator()
        is_valid, issues = validator.validate(spec)

        # Print issues
        errors = [i for i in issues if i.severity == Severity.ERROR]
        warnings = [i for i in issues if i.severity == Severity.WARNING]
        infos = [i for i in issues if i.severity == Severity.INFO]

        if errors:
            print(f"[goalgen] ❌ Spec validation failed with {len(errors)} errors:")
            for issue in errors:
                print(f"  [ERROR] {issue.path}: {issue.message}")
                if issue.suggestion:
                    print(f"    → {issue.suggestion}")
            print("\n[goalgen] Fix the errors above and try again.")
            print("[goalgen] Use --skip-validation to bypass (not recommended)")
            sys.exit(1)

        if warnings:
            print(f"[goalgen] ⚠️  Spec has {len(warnings)} warnings:")
            for issue in warnings:
                print(f"  [WARN] {issue.path}: {issue.message}")
                if issue.suggestion:
                    print(f"    → {issue.suggestion}")

        if infos:
            print(f"[goalgen] ℹ️  {len(infos)} suggestions:")
            for issue in infos[:3]:  # Only show first 3 info messages
                print(f"  [INFO] {issue.path}: {issue.message}")
            if len(infos) > 3:
                print(f"  ... and {len(infos) - 3} more suggestions")

        if is_valid and not warnings:
            print("[goalgen] ✅ Spec is valid!")
        elif is_valid:
            print("[goalgen] ✅ Spec is valid (with warnings)")
        print()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    # Load or create manifest
    manifest = GenerationManifest(out_dir)

    # Detect what changed if in incremental mode
    if args.incremental:
        changes = manifest.detect_spec_changes(spec)

        if changes["is_first_generation"]:
            print("[goalgen] First generation - creating all files")
        else:
            print("[goalgen] Incremental mode - analyzing changes...")
            if changes["added_agents"]:
                print(f"[goalgen]   New agents: {', '.join(changes['added_agents'])}")
            if changes["removed_agents"]:
                print(f"[goalgen]   Removed agents: {', '.join(changes['removed_agents'])}")
            if changes["added_tools"]:
                print(f"[goalgen]   New tools: {', '.join(changes['added_tools'])}")
            if changes["removed_tools"]:
                print(f"[goalgen]   Removed tools: {', '.join(changes['removed_tools'])}")
            if changes["schema_version_changed"]:
                print(f"[goalgen]   Schema version changed")

            if not any([
                changes["added_agents"],
                changes["removed_agents"],
                changes["added_tools"],
                changes["removed_tools"],
                changes["schema_version_changed"]
            ]):
                print("[goalgen]   No significant changes detected")

    elif args.force:
        print("[goalgen] Force mode - regenerating all files")

    targets = [t.strip() for t in args.targets.split(",")]

    # Track generated files for manifest
    generated_files = []

    for t in targets:
        if t not in SUB_GENERATORS:
            print(f"Unknown generator target: {t}")
            continue
        print(f"Running generator: {t}")

        # TODO: Pass incremental/force flags to generators
        # For now, generators still run in full mode
        SUB_GENERATORS[t](spec, out_dir, dry_run=args.dry_run)

    # Save manifest after successful generation
    if not args.dry_run:
        # Collect all generated files
        generated_files = list(Path(out_dir).rglob("*.py")) + \
                         list(Path(out_dir).rglob("*.bicep")) + \
                         list(Path(out_dir).rglob("*.json")) + \
                         list(Path(out_dir).rglob("*.sh")) + \
                         list(Path(out_dir).rglob("*.md"))

        manifest.save(spec, generated_files)
        print(f"[goalgen] Saved manifest: {manifest.manifest_path}")

    print(f"Goal generation completed at {out_dir}")

if __name__ == "__main__":
    main()
