# Schema Versioning Implementation Guide

Complete implementation of schema versioning and migration system for GoalGen.

## Overview

The schema versioning system enables safe evolution of LangGraph state schemas in production without breaking existing conversations stored in Cosmos DB or Redis.

## Generated Components

When you define `schema_version` and `schema_migrations` in your goal spec, GoalGen generates:

### 1. Schema Migration Module

**File**: `langgraph/schema_migrations.py`

Generated from: `templates/langgraph/schema_migrations.py.j2`

**Contents**:
- `CURRENT_SCHEMA_VERSION` - Current schema version from spec
- `migrate_state(state)` - Main migration function (v1 → current)
- `migrate_X_to_Y(state)` - Per-migration functions
- `MIGRATIONS` - Registry mapping migration keys to functions
- `get_migration_path(from, to)` - Calculate migration sequence
- `validate_migration_chain()` - Verify all migrations exist

**Example**:
```python
from langgraph.schema_migrations import migrate_state

# Automatically migrate old state to current version
old_state = {"schema_version": 1, ...}
new_state = migrate_state(old_state)
assert new_state["schema_version"] == CURRENT_SCHEMA_VERSION
```

### 2. Migrating Checkpointer

**File**: `langgraph/checkpointer_adapter.py`

**Added**:
- `MigratingCheckpointer` class that wraps base checkpointer
- Intercepts `aget()` to migrate state on load
- Implements lazy migration strategy
- Optionally saves migrated state back to storage

**Flow**:
```
User resumes conversation
  → LangGraph calls checkpointer.aget(config)
    → MigratingCheckpointer.aget()
      → Load checkpoint from Cosmos/Redis
      → Check schema_version
      → If old version: migrate_state()
      → Save migrated checkpoint (optional)
      → Return to LangGraph
```

### 3. Batch Migration Script

**File**: `scripts/migrate_checkpoints.py`

Generated from: `templates/scripts/migrate_checkpoints.py.j2`

**Purpose**: Background job to migrate all existing checkpoints

**Usage**:
```bash
# Dry run (no changes)
python scripts/migrate_checkpoints.py --dry-run

# Migrate all checkpoints
python scripts/migrate_checkpoints.py

# Custom batch size
python scripts/migrate_checkpoints.py --batch-size 50
```

**Supports**:
- Cosmos DB backend
- Redis backend
- Managed Identity authentication
- Progress logging
- Error handling

### 4. Migration Tests

**File**: `tests/test_schema_migrations.py`

Generated from: `templates/tests/test_schema_migrations.py.j2`

**Test Coverage**:
- Schema version matches spec
- Migration chain completeness
- Individual migration functions
- Full migration chain (v1 → current)
- Partial migrations (intermediate → current)
- Data preservation during migration

**Run Tests**:
```bash
cd test_output
pytest tests/test_schema_migrations.py -v
```

## Goal Spec Configuration

### Basic Schema Version

```json
{
  "id": "my_goal",
  "schema_version": 1,
  "state_management": {
    "state": {
      "schema": {
        "context_fields": ["destination", "dates"]
      }
    }
  }
}
```

### With Migrations (v2)

```json
{
  "schema_version": 2,
  "schema_migrations": {
    "1_to_2": {
      "description": "Added budget field",
      "migration": "set_default",
      "added_fields": ["budget"],
      "default_values": {
        "budget": null
      }
    }
  }
}
```

## Supported Migration Types

### 1. Add Field (`set_default`)

Add new fields with default values:

```json
{
  "migration": "set_default",
  "added_fields": ["new_field"],
  "default_values": {
    "new_field": null
  }
}
```

Generated code:
```python
def migrate_1_to_2(state):
    if "new_field" not in state:
        state["new_field"] = None
    return state
```

### 2. Rename Field (`rename_field`)

Rename existing fields:

```json
{
  "migration": "rename_field",
  "renamed_fields": {
    "old_name": "new_name"
  }
}
```

Generated code:
```python
def migrate_2_to_3(state):
    if "old_name" in state:
        state["new_name"] = state.pop("old_name")
    return state
```

### 3. Remove Field (`remove_field`)

Remove deprecated fields:

```json
{
  "migration": "remove_field",
  "removed_fields": ["deprecated_field"]
}
```

Generated code:
```python
def migrate_3_to_4(state):
    state.pop("deprecated_field", None)
    return state
```

### 4. Transform Field (`transform`)

Change field type (requires custom logic):

```json
{
  "migration": "transform",
  "transformed_fields": {
    "travelers": {
      "from_type": "int",
      "to_type": "Dict[str, int]",
      "transform_fn": "travelers_to_dict"
    }
  }
}
```

Generated code:
```python
def migrate_4_to_5(state):
    if "travelers" in state:
        # TODO: Implement custom transformation
        # Transform from int to Dict[str, int]
        pass
    return state
```

**Note**: Transform migrations generate placeholder code that you must customize.

## Migration Strategies

### 1. Lazy Migration (Default)

- State migrated when conversation resumed
- No upfront batch processing
- Gradual rollout
- Old checkpoints remain until accessed

**When to use**:
- Most deployments
- Active conversations migrated automatically
- Low risk, no downtime

### 2. Background Migration

- Batch migrate all checkpoints upfront
- Use `scripts/migrate_checkpoints.py`
- Can run as Azure Function or Container Job

**When to use**:
- Large checkpoint databases
- Want all data at current version
- Scheduled maintenance window

### 3. Dual-Write (For Breaking Changes)

- Support both old and new schema during transition
- Requires custom adapter code
- Gradual migration with rollback capability

**When to use**:
- Major breaking changes
- Need rollback capability
- Extended migration period

## Deployment Workflow

### Step 1: Update Goal Spec

```json
{
  "schema_version": 2,
  "schema_migrations": {
    "1_to_2": {
      "description": "Added departure_date field",
      "migration": "set_default",
      "added_fields": ["departure_date"],
      "default_values": {
        "departure_date": null
      }
    }
  },
  "state_management": {
    "state": {
      "schema": {
        "context_fields": [
          "destination",
          "departure_date"  // New field
        ]
      }
    }
  }
}
```

### Step 2: Regenerate Project

```bash
./goalgen.py --spec goal_spec.json --out ./output --targets langgraph,tests
```

**Generated files**:
- `langgraph/schema_migrations.py` - Migration logic
- `langgraph/checkpointer_adapter.py` - Updated with MigratingCheckpointer
- `tests/test_schema_migrations.py` - Test suite
- `scripts/migrate_checkpoints.py` - Batch migration script

### Step 3: Test Migrations Locally

```bash
cd output
pytest tests/test_schema_migrations.py -v
```

**Verify**:
- All tests pass
- Migration functions work correctly
- Data preserved during migration

### Step 4: Deploy to Azure

```bash
./scripts/deploy.sh
```

**What happens**:
- New code deployed with MigratingCheckpointer
- Existing conversations use lazy migration on first access
- New conversations start with schema v2

### Step 5: Monitor Migration

Check Application Insights for migration logs:

```kusto
traces
| where message contains "Migrating state from v1 to v2"
| summarize count() by bin(timestamp, 1h)
```

### Step 6 (Optional): Background Migration

Migrate all checkpoints in batch:

```bash
# From Azure Cloud Shell or local with Azure credentials
python scripts/migrate_checkpoints.py --dry-run  # Preview
python scripts/migrate_checkpoints.py            # Execute
```

## Testing Strategy

### Unit Tests

Test individual migration functions:

```python
def test_migration_1_to_2():
    old_state = {"schema_version": 1, "destination": "Paris"}
    new_state = MIGRATIONS["1_to_2"](old_state)

    assert new_state["schema_version"] == 1  # Not updated yet
    assert "departure_date" in new_state
    assert new_state["departure_date"] is None
```

### Integration Tests

Test full migration chain:

```python
def test_full_migration():
    v1_state = {
        "schema_version": 1,
        "destination": "Paris",
        "messages": [...]
    }

    migrated = migrate_state(v1_state)

    assert migrated["schema_version"] == CURRENT_SCHEMA_VERSION
    assert migrated["destination"] == "Paris"  # Preserved
    assert "departure_date" in migrated  # Added
```

### Local Testing with Sample Data

```python
# Create sample v1 checkpoint
import json

v1_checkpoint = {
    "channel_values": {
        "schema_version": 1,
        "destination": "Tokyo",
        "messages": [],
        "next": None,
        "completed_tasks": []
    }
}

# Test migration
from langgraph.schema_migrations import migrate_state
migrated = migrate_state(v1_checkpoint["channel_values"])

print(json.dumps(migrated, indent=2))
```

## Best Practices

### 1. Always Increment Schema Version

```json
// ✅ Good
{"schema_version": 3}  // Incremented from 2

// ❌ Bad
{"schema_version": 2}  // Same as before, but fields changed
```

### 2. Provide Clear Migration Descriptions

```json
{
  "description": "Added departure_date field for trip planning"  // ✅ Clear
}
```

Not:
```json
{
  "description": "Updated schema"  // ❌ Vague
}
```

### 3. Test with Real Data

```bash
# Export sample production checkpoints
az cosmosdb sql container query \
  --query "SELECT TOP 10 * FROM c" \
  > sample_checkpoints.json

# Test migration locally
python test_migration.py sample_checkpoints.json
```

### 4. Use Default Values for New Fields

```json
{
  "default_values": {
    "new_field": null,  // Safe default
    "count": 0,         // Sensible default
    "enabled": false    // Conservative default
  }
}
```

### 5. Keep Migration History

Never delete old migrations - needed for very old checkpoints:

```python
MIGRATIONS = {
    "1_to_2": migrate_1_to_2,  # ← Keep forever
    "2_to_3": migrate_2_to_3,
    "3_to_4": migrate_3_to_4,
}
```

## Monitoring & Debugging

### Application Insights Queries

**Migration activity**:
```kusto
traces
| where message contains "Migrating state"
| project timestamp, message
| order by timestamp desc
```

**Migration errors**:
```kusto
traces
| where severityLevel >= 3
  and message contains "migration"
| project timestamp, message, severityLevel
```

**Migration duration**:
```kusto
dependencies
| where name == "migrate_state"
| summarize avg(duration), max(duration) by bin(timestamp, 1h)
```

### Debugging Failed Migrations

Enable debug logging:

```python
import logging
logging.getLogger("langgraph.schema_migrations").setLevel(logging.DEBUG)
```

Check logs:
```bash
docker logs <container-id> | grep migration
```

## Rollback Strategy

If migration causes issues:

### Option 1: Hotfix Migration Code

```python
# Fix migration function
def migrate_1_to_2(state):
    if "new_field" not in state:
        state["new_field"] = "corrected_default"  # Fixed
    return state
```

Redeploy with fix.

### Option 2: Revert Schema Version

```json
{
  "schema_version": 1  // Temporarily revert
}
```

**Warning**: Only works if no v2 checkpoints exist yet.

### Option 3: Forward Migration

Add new migration to fix:

```json
{
  "schema_version": 3,
  "schema_migrations": {
    "2_to_3": {
      "description": "Fix incorrect migration from v1→v2",
      "migration": "set_default",
      ...
    }
  }
}
```

## Example: Complete Evolution

### Version 1 (Initial)

```json
{
  "schema_version": 1,
  "state_management": {
    "state": {
      "schema": {
        "context_fields": ["destination"]
      }
    }
  }
}
```

### Version 2 (Add Field)

```json
{
  "schema_version": 2,
  "schema_migrations": {
    "1_to_2": {
      "description": "Added travelers field",
      "migration": "set_default",
      "added_fields": ["travelers"],
      "default_values": {"travelers": 1}
    }
  }
}
```

### Version 3 (Rename Field)

```json
{
  "schema_version": 3,
  "schema_migrations": {
    "1_to_2": { ... },
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

### Version 4 (Transform Field)

```json
{
  "schema_version": 4,
  "schema_migrations": {
    "1_to_2": { ... },
    "2_to_3": { ... },
    "3_to_4": {
      "description": "Transform travelers to breakdown by type",
      "migration": "transform",
      "transformed_fields": {
        "travelers": {
          "from_type": "int",
          "to_type": "Dict[str, int]"
        }
      }
    }
  }
}
```

Custom migration code:
```python
def migrate_3_to_4(state):
    if "travelers" in state and isinstance(state["travelers"], int):
        count = state["travelers"]
        state["travelers"] = {
            "adults": count,
            "children": 0,
            "infants": 0
        }
    return state
```

---

**Generated by GoalGen** | Schema Versioning System v1.0
