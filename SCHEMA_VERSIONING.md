# Schema Versioning & Migration Guide

Guide for evolving state schemas safely in production systems.

## The Problem

When you enhance agents and add new context fields, you need to handle:

- ✅ **Existing conversations** with old schema (in Cosmos DB checkpoints)
- ✅ **New conversations** with new schema
- ✅ **Migration** of old state to new format
- ✅ **Backward compatibility** during deployments
- ✅ **Schema validation** to catch errors early

## Solution: Schema Versioning

GoalGen uses a **versioned schema migration system** that allows safe schema evolution.

### Schema Version in Goal Spec

```json
{
  "id": "travel_planning",
  "version": "1.0.0",
  "schema_version": 2,  // ← Schema version number
  "context_fields": {
    "destination": {"type": "str"},
    "departure_date": {"type": "str"}
  },
  "schema_migrations": {
    "1_to_2": {
      "description": "Added departure_date field",
      "migration": "set_default",
      "added_fields": ["departure_date"],
      "default_values": {
        "departure_date": null
      }
    }
  }
}
```

## Generated State Schema with Versioning

### Enhanced State Schema Template

The generated state schema includes version tracking:

```python
class TravelPlanningState(TypedDict):
    """
    State schema for travel_planning workflow

    Schema Version: 2
    Last Updated: 2025-01-15
    """

    # Schema metadata
    schema_version: int  # Current schema version (2)

    # Messages
    messages: Annotated[List[BaseMessage], add_messages]

    # Context fields (v2)
    destination: Optional[str]
    departure_date: Optional[str]  # Added in v2

    # Standard fields
    next: Optional[str]
    completed_tasks: List[str]
    thread_id: Optional[str]
    user_id: Optional[str]
    conversation_insights: Optional[Dict[str, Any]]
```

### Migration Handler

Generated migration code handles schema upgrades automatically:

```python
# Generated in langgraph/schema_migrations.py

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 2

def migrate_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate state from any version to current version

    Args:
        state: State dictionary (may be old version)

    Returns:
        Migrated state at current version
    """

    # Get current state version (default to 1 if not set)
    state_version = state.get("schema_version", 1)

    if state_version == CURRENT_SCHEMA_VERSION:
        # Already at current version
        return state

    logger.info(f"Migrating state from v{state_version} to v{CURRENT_SCHEMA_VERSION}")

    # Apply migrations sequentially
    migrated_state = state.copy()

    while state_version < CURRENT_SCHEMA_VERSION:
        next_version = state_version + 1
        migration_fn = MIGRATIONS.get(f"{state_version}_to_{next_version}")

        if migration_fn:
            migrated_state = migration_fn(migrated_state)
            migrated_state["schema_version"] = next_version
            logger.info(f"Applied migration {state_version} → {next_version}")
        else:
            logger.error(f"Missing migration {state_version} → {next_version}")
            break

        state_version = next_version

    return migrated_state


# Migration functions

def migrate_1_to_2(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migration v1 → v2: Added departure_date field
    """

    # Add new field with default value
    if "departure_date" not in state:
        state["departure_date"] = None

    return state


# Migration registry
MIGRATIONS = {
    "1_to_2": migrate_1_to_2,
}
```

## Evolution Scenarios

### Scenario 1: Adding a New Field

**v1 Schema:**
```json
{
  "schema_version": 1,
  "context_fields": {
    "destination": {"type": "str"}
  }
}
```

**v2 Schema (add field):**
```json
{
  "schema_version": 2,
  "context_fields": {
    "destination": {"type": "str"},
    "travelers": {"type": "int"}  // ← New field
  },
  "schema_migrations": {
    "1_to_2": {
      "description": "Added travelers field for multi-person trips",
      "migration": "set_default",
      "added_fields": ["travelers"],
      "default_values": {
        "travelers": 1  // ← Default for existing conversations
      }
    }
  }
}
```

**Generated Migration:**
```python
def migrate_1_to_2(state: Dict[str, Any]) -> Dict[str, Any]:
    """Add travelers field with default value 1"""
    if "travelers" not in state:
        state["travelers"] = 1
    return state
```

**Behavior:**
- Old conversations: `{"destination": "Paris"}` → `{"destination": "Paris", "travelers": 1}`
- New conversations: Start with v2 schema directly

### Scenario 2: Renaming a Field

**v2 → v3: Rename `destination` to `destination_city`**

```json
{
  "schema_version": 3,
  "context_fields": {
    "destination_city": {"type": "str"}  // Renamed from destination
  },
  "schema_migrations": {
    "2_to_3": {
      "description": "Renamed destination to destination_city",
      "migration": "rename_field",
      "renamed_fields": {
        "destination": "destination_city"
      }
    }
  }
}
```

**Generated Migration:**
```python
def migrate_2_to_3(state: Dict[str, Any]) -> Dict[str, Any]:
    """Rename destination to destination_city"""
    if "destination" in state:
        state["destination_city"] = state.pop("destination")
    return state
```

### Scenario 3: Changing Field Type

**v3 → v4: Change `travelers` from `int` to `Dict[str, int]`**

```json
{
  "schema_version": 4,
  "context_fields": {
    "travelers": {
      "type": "Dict[str, int]",
      "description": "Breakdown by age group: {adults: 2, children: 1}"
    }
  },
  "schema_migrations": {
    "3_to_4": {
      "description": "Travelers now supports age breakdown",
      "migration": "transform",
      "transformed_fields": {
        "travelers": {
          "from_type": "int",
          "to_type": "Dict[str, int]",
          "transform_fn": "travelers_to_dict"
        }
      }
    }
  }
}
```

**Generated Migration:**
```python
def migrate_3_to_4(state: Dict[str, Any]) -> Dict[str, Any]:
    """Transform travelers from int to dict"""
    if "travelers" in state and isinstance(state["travelers"], int):
        # Convert single number to dict format
        count = state["travelers"]
        state["travelers"] = {
            "adults": count,
            "children": 0,
            "infants": 0
        }
    return state
```

### Scenario 4: Removing a Deprecated Field

**v4 → v5: Remove deprecated `old_field`**

```json
{
  "schema_version": 5,
  "schema_migrations": {
    "4_to_5": {
      "description": "Removed deprecated old_field",
      "migration": "remove_field",
      "removed_fields": ["old_field"]
    }
  }
}
```

**Generated Migration:**
```python
def migrate_4_to_5(state: Dict[str, Any]) -> Dict[str, Any]:
    """Remove deprecated old_field"""
    state.pop("old_field", None)  # Safe removal
    return state
```

## Integration with Checkpointing

### Loading State from Checkpoint

Automatically migrate when resuming conversations:

```python
# Generated in langgraph/checkpointer_adapter.py

from .schema_migrations import migrate_state, CURRENT_SCHEMA_VERSION

class MigratingCheckpointer:
    """Checkpointer with automatic schema migration"""

    def __init__(self, base_checkpointer):
        self.base_checkpointer = base_checkpointer

    async def aget(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """Load checkpoint and migrate if needed"""

        checkpoint = await self.base_checkpointer.aget(config)

        if checkpoint is None:
            return None

        # Get state from checkpoint
        state = checkpoint.get("state", {})
        state_version = state.get("schema_version", 1)

        # Migrate if needed
        if state_version < CURRENT_SCHEMA_VERSION:
            logger.info(
                f"Migrating checkpoint {config.get('thread_id')} "
                f"from v{state_version} to v{CURRENT_SCHEMA_VERSION}"
            )

            migrated_state = migrate_state(state)
            checkpoint["state"] = migrated_state

            # Optionally: Save migrated checkpoint
            await self.aput(config, checkpoint)

        return checkpoint
```

### Creating New Checkpoints

New conversations start with current schema:

```python
async def create_new_state(thread_id: str, user_id: str) -> Dict[str, Any]:
    """Create initial state with current schema version"""

    return {
        "schema_version": CURRENT_SCHEMA_VERSION,  # Set to current
        "messages": [],
        "destination": None,
        "travelers": 1,  # v2+ field with default
        "next": None,
        "completed_tasks": [],
        "thread_id": thread_id,
        "user_id": user_id
    }
```

## Migration Strategies

### Strategy 1: Lazy Migration (Recommended)

Migrate on first access:

```python
# Don't migrate all checkpoints upfront
# Migrate each conversation when user resumes it

# Pros:
# - No downtime
# - Gradual rollout
# - Only active conversations migrated

# Cons:
# - Old schema persists in inactive conversations
```

### Strategy 2: Background Migration

Batch migrate all checkpoints:

```python
# scripts/migrate_checkpoints.py

async def migrate_all_checkpoints():
    """Background job to migrate all existing checkpoints"""

    from azure.cosmos import CosmosClient
    from langgraph.schema_migrations import migrate_state

    client = CosmosClient(endpoint, key)
    container = client.get_database_client("db").get_container_client("checkpoints")

    # Query all checkpoints
    query = "SELECT * FROM c WHERE c.schema_version < @current_version"
    params = [{"name": "@current_version", "value": CURRENT_SCHEMA_VERSION}]

    items = container.query_items(query=query, parameters=params)

    migrated_count = 0

    for item in items:
        # Migrate state
        old_state = item.get("state", {})
        new_state = migrate_state(old_state)

        # Update in Cosmos
        item["state"] = new_state
        container.upsert_item(item)

        migrated_count += 1

        if migrated_count % 100 == 0:
            logger.info(f"Migrated {migrated_count} checkpoints...")

    logger.info(f"Migration complete: {migrated_count} total")
```

Run as Azure Function or Container Job:

```bash
# Deploy as scheduled job
python scripts/migrate_checkpoints.py
```

### Strategy 3: Dual-Write (For Breaking Changes)

Support both old and new schema during transition:

```python
class DualSchemaAdapter:
    """Support both v2 and v3 schemas during migration period"""

    def normalize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any version to internal format"""

        version = state.get("schema_version", 1)

        if version == 2:
            # Old schema: destination (str)
            return {
                "destination_city": state.get("destination"),
                "destination_country": None  # Unknown in v2
            }
        elif version >= 3:
            # New schema: destination_city, destination_country
            return {
                "destination_city": state.get("destination_city"),
                "destination_country": state.get("destination_country")
            }
```

## Validation

### Runtime Validation

Validate state matches schema:

```python
# Generated in langgraph/state_validator.py

from typing import Dict, Any, List
from pydantic import BaseModel, ValidationError

class TravelPlanningStateValidator(BaseModel):
    """Pydantic model for runtime validation"""

    schema_version: int
    destination: Optional[str] = None
    travelers: Optional[int] = None
    messages: List[Any]
    # ... other fields

    class Config:
        extra = "allow"  # Allow additional fields for forward compatibility


def validate_state(state: Dict[str, Any]) -> List[str]:
    """
    Validate state against schema

    Returns:
        List of validation errors (empty if valid)
    """

    try:
        TravelPlanningStateValidator(**state)
        return []
    except ValidationError as e:
        return [str(err) for err in e.errors()]
```

### Pre-Deployment Testing

Test migrations before deploying:

```python
# tests/test_schema_migrations.py

import pytest
from langgraph.schema_migrations import migrate_state

def test_migration_1_to_2():
    """Test v1 → v2 migration adds travelers field"""

    # Old state (v1)
    old_state = {
        "schema_version": 1,
        "destination": "Paris",
        "messages": []
    }

    # Migrate
    new_state = migrate_state(old_state)

    # Assert
    assert new_state["schema_version"] == 2
    assert new_state["destination"] == "Paris"
    assert new_state["travelers"] == 1  # Default value
    assert "messages" in new_state

def test_migration_2_to_3_rename():
    """Test v2 → v3 migration renames destination"""

    old_state = {
        "schema_version": 2,
        "destination": "Tokyo",
        "travelers": 2
    }

    new_state = migrate_state(old_state)

    assert new_state["schema_version"] == 3
    assert new_state["destination_city"] == "Tokyo"
    assert "destination" not in new_state  # Old field removed
```

## Best Practices

### 1. Always Increment Schema Version

```json
// ✅ Good
{"schema_version": 3}  // Incremented from 2

// ❌ Bad
{"schema_version": 2}  // Same as before, but fields changed
```

### 2. Provide Migration for Every Version Change

```json
{
  "schema_version": 3,
  "schema_migrations": {
    "1_to_2": { /* migration */ },
    "2_to_3": { /* migration */ }  // ← Don't skip
  }
}
```

### 3. Use Descriptive Migration Messages

```json
{
  "description": "Added travelers field for multi-person trip support"  // ✅ Clear
}
```

Not:
```json
{
  "description": "Updated schema"  // ❌ Vague
}
```

### 4. Test Migrations with Real Data

```bash
# Export production checkpoint samples
az cosmosdb sql container query \
  --query "SELECT TOP 100 * FROM c" \
  > sample_checkpoints.json

# Test migration locally
python test_migration.py sample_checkpoints.json
```

### 5. Keep Migration History

Never delete old migrations - they're needed to migrate very old checkpoints:

```python
# Keep all migrations even after all checkpoints are migrated
MIGRATIONS = {
    "1_to_2": migrate_1_to_2,  # ← Keep even if all checkpoints are v2+
    "2_to_3": migrate_2_to_3,
    "3_to_4": migrate_3_to_4,
}
```

## Deployment Checklist

When deploying schema changes:

- [ ] Increment `schema_version` in goal_spec.json
- [ ] Add migration in `schema_migrations`
- [ ] Write migration test
- [ ] Test with sample production data
- [ ] Deploy new version (lazy migration)
- [ ] Monitor migration logs
- [ ] (Optional) Run background migration job
- [ ] Verify old conversations still work

## Monitoring

Track migration metrics:

```python
from frmk.core.ai_foundry_client import get_ai_foundry_client

async def log_migration_metric(from_version: int, to_version: int, success: bool):
    """Log migration to AI Foundry"""

    ai_foundry = get_ai_foundry_client(config)

    await ai_foundry.log_metric(
        metric_name="schema_migration",
        value=1,
        properties={
            "from_version": from_version,
            "to_version": to_version,
            "success": success,
            "migration_name": f"{from_version}_to_{to_version}"
        }
    )
```

Query in AI Foundry:
```kusto
customMetrics
| where name == "schema_migration"
| summarize count() by tostring(customDimensions.migration_name), tostring(customDimensions.success)
```

---

**Generated by GoalGen** | [Documentation](https://github.com/yourorg/goalgen)
