"""
Generation Manifest

Tracks generated files to enable incremental updates.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set


class GenerationManifest:
    """
    Tracks what files were generated and their content hashes

    Enables incremental generation by detecting:
    - What was generated before
    - What changed in the spec
    - What was modified by the user
    """

    def __init__(self, out_dir: str):
        self.out_dir = Path(out_dir)
        self.manifest_path = self.out_dir / ".goalgen" / "manifest.json"
        self.manifest = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load existing manifest or create new one"""
        if self.manifest_path.exists():
            try:
                return json.loads(self.manifest_path.read_text())
            except (json.JSONDecodeError, OSError):
                return self._empty_manifest()
        return self._empty_manifest()

    def _empty_manifest(self) -> Dict[str, Any]:
        """Create empty manifest structure"""
        return {
            "version": "1.0",
            "generated_at": None,
            "spec_hash": None,
            "files": {}
        }

    def save(self, spec: Dict[str, Any], generated_files: List[Path]):
        """
        Save manifest after generation

        Args:
            spec: Goal spec that was used
            generated_files: List of file paths that were generated
        """
        self.manifest = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "spec": {
                "hash": self._hash_dict(spec),
                "version": spec.get("version", "1.0.0"),
                "schema_version": spec.get("schema_version", 1),
                "agents": list(spec.get("agents", {}).keys()),
                "tools": list(spec.get("tools", {}).keys()),
            },
            "files": {}
        }

        for file_path in generated_files:
            if file_path.exists():
                rel_path = str(file_path.relative_to(self.out_dir))
                self.manifest["files"][rel_path] = {
                    "hash": self._hash_file(file_path),
                    "generated_at": datetime.now().isoformat(),
                    "size": file_path.stat().st_size
                }

        # Save manifest
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2))

    def is_modified(self, file_path: Path) -> bool:
        """
        Check if a file was modified by the user since generation

        Args:
            file_path: Absolute or relative path to check

        Returns:
            True if file exists and was modified, False otherwise
        """
        # Convert to relative path
        if file_path.is_absolute():
            try:
                rel_path = str(file_path.relative_to(self.out_dir))
            except ValueError:
                return False
        else:
            rel_path = str(file_path)

        # Check if tracked
        if rel_path not in self.manifest.get("files", {}):
            return False

        # Check if exists
        full_path = self.out_dir / rel_path
        if not full_path.exists():
            return True  # File was deleted

        # Compare hashes
        stored_hash = self.manifest["files"][rel_path]["hash"]
        current_hash = self._hash_file(full_path)

        return stored_hash != current_hash

    def get_previous_spec_info(self) -> Dict[str, Any]:
        """Get information about the spec used in previous generation"""
        return self.manifest.get("spec", {})

    def get_tracked_files(self) -> Set[str]:
        """Get set of all tracked file paths"""
        return set(self.manifest.get("files", {}).keys())

    def detect_spec_changes(self, new_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare new spec with previous spec to detect changes

        Returns:
            Dictionary with:
            - added_agents: List of new agent names
            - removed_agents: List of removed agent names
            - added_tools: List of new tool names
            - removed_tools: List of removed tool names
            - schema_version_changed: Boolean
        """
        old_spec = self.get_previous_spec_info()

        if not old_spec:
            # First generation - everything is new
            return {
                "added_agents": list(new_spec.get("agents", {}).keys()),
                "removed_agents": [],
                "added_tools": list(new_spec.get("tools", {}).keys()),
                "removed_tools": [],
                "schema_version_changed": False,
                "is_first_generation": True
            }

        # Compare agents
        old_agents = set(old_spec.get("agents", []))
        new_agents = set(new_spec.get("agents", {}).keys())

        # Compare tools
        old_tools = set(old_spec.get("tools", []))
        new_tools = set(new_spec.get("tools", {}).keys())

        # Compare schema version
        old_schema_version = old_spec.get("schema_version", 1)
        new_schema_version = new_spec.get("schema_version", 1)

        return {
            "added_agents": list(new_agents - old_agents),
            "removed_agents": list(old_agents - new_agents),
            "added_tools": list(new_tools - old_tools),
            "removed_tools": list(old_tools - new_tools),
            "schema_version_changed": old_schema_version != new_schema_version,
            "is_first_generation": False
        }

    def _hash_file(self, path: Path) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    def _hash_dict(self, d: Dict[str, Any]) -> str:
        """Calculate hash of dictionary (for spec comparison)"""
        json_str = json.dumps(d, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]


def should_regenerate_file(
    file_path: Path,
    manifest: GenerationManifest,
    incremental: bool,
    force: bool
) -> tuple[bool, str]:
    """
    Determine if a file should be regenerated

    Args:
        file_path: Path to check
        manifest: GenerationManifest instance
        incremental: If True, skip unmodified files
        force: If True, regenerate everything

    Returns:
        (should_regenerate: bool, reason: str)
    """
    if force:
        return True, "forced regeneration"

    if not file_path.exists():
        return True, "file does not exist"

    if not incremental:
        return True, "full regeneration (not incremental)"

    if manifest.is_modified(file_path):
        return False, "file was modified by user (skipping to preserve changes)"

    return False, "file unchanged (skipping)"
