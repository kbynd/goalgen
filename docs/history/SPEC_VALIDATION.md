# Goal Spec Validation

GoalGen includes comprehensive spec validation to catch errors before generation.

## Overview

The spec validator checks your goal specification for:
- **Required fields** - Ensures all mandatory fields are present
- **Format validation** - IDs, versions, and other fields follow correct formats
- **Type checking** - Values have correct types (string, dict, list, etc.)
- **Cross-references** - Tools referenced by agents exist, tasks reference valid agents
- **Best practices** - Suggestions for improving your spec

## Validation Levels

### 🔴 ERROR
Spec is invalid and generation will fail. Must be fixed.

**Examples:**
- Missing required fields (id, title, version, agents)
- Invalid ID format (uppercase, hyphens, starting with number)
- Undefined tool references
- Missing supervisor agent
- Invalid semantic version

### 🟡 WARNING
Spec may work but has issues that could cause problems.

**Examples:**
- LLM agent without llm_config
- Unknown model name
- Temperature out of typical range (0-2)
- No UX interfaces enabled

### ℹ️ INFO
Best practice suggestions to improve your spec.

**Examples:**
- Missing description field
- No monitoring configuration
- Consider adding state management

## Using the Validator

### Standalone Validation

Validate spec files before generation:

```bash
# Validate a single spec
./spec_validator.py examples/travel_planning.json

# Validate multiple specs
./spec_validator.py examples/*.json

# Show only errors
./spec_validator.py --errors-only spec.json

# Show errors and warnings (skip info)
./spec_validator.py --warnings spec.json

# JSON output for tooling
./spec_validator.py --json spec.json
```

### Integrated with GoalGen

Validation runs automatically when you use `goalgen.py`:

```bash
# Validation runs by default
./goalgen.py --spec spec.json --out ./output

# Skip validation (not recommended)
./goalgen.py --spec spec.json --out ./output --skip-validation
```

## Validation Rules

### Required Fields

**Root Level:**
- `id` (string) - Unique identifier for the goal
- `title` (string) - Human-readable title
- `version` (string) - Semantic version (x.y.z)
- `agents` (dict) - At least one agent required

**Agent Fields:**
- `kind` (string) - Must be 'supervisor', 'llm_agent', or 'evaluator'

**Tool Fields (if tools present):**
- `type` (string) - Tool type (http, sql, vectordb, function)

**HTTP Tool Fields:**
- `spec.url` (string) - API endpoint URL
- `spec.method` (string) - HTTP method

### Format Validation

**ID Format:**
```python
# Valid IDs
"travel_planning"
"my_goal_v2"
"agent_workflow_123"

# Invalid IDs
"Travel-Planning"  # Uppercase
"my-goal"          # Hyphens
"123_goal"         # Starts with number
"my goal"          # Spaces
```

Must match regex: `^[a-z][a-z0-9_]*$`

**Version Format:**
```python
# Valid versions
"1.0.0"
"2.1.3"
"1.0.0-alpha"
"1.0.0-beta.1"

# Invalid versions
"1.0"          # Missing patch version
"v1.0.0"       # Prefix not allowed
"1.0.0.0"      # Too many parts
```

Must follow semantic versioning: `x.y.z[-prerelease]`

### Cross-Reference Validation

**Tools Referenced by Agents:**
```json
{
  "agents": {
    "flight_agent": {
      "kind": "llm_agent",
      "tools": ["flight_api"]  // ← Must be defined in tools section
    }
  },
  "tools": {
    "flight_api": {  // ✓ Defined
      "type": "http",
      "spec": {"url": "...", "method": "POST"}
    }
  }
}
```

**Agents Referenced by Tasks:**
```json
{
  "agents": {
    "flight_agent": {"kind": "llm_agent"}  // ✓ Defined
  },
  "tasks": [
    {
      "id": "search_flights",
      "agent": "flight_agent"  // ← Must exist in agents section
    }
  ]
}
```

### Type Validation

**Common Type Errors:**
```json
// ❌ Wrong types
{
  "id": 123,                    // Must be string
  "agents": [],                 // Must be dict
  "tools": "flight_api",        // Must be dict
  "llm_config": {
    "temperature": "high"       // Must be number
  }
}

// ✅ Correct types
{
  "id": "my_goal",
  "agents": {"supervisor": {...}},
  "tools": {"flight_api": {...}},
  "llm_config": {
    "temperature": 0.7
  }
}
```

### Agent Validation

**Supervisor Agent Required:**
Every spec must have at least one supervisor agent:

```json
{
  "agents": {
    "supervisor_agent": {  // ✓ At least one supervisor
      "kind": "supervisor",
      "policy": "simple_router"
    }
  }
}
```

**Valid Agent Kinds:**
- `supervisor` - Routes to other agents
- `llm_agent` - LLM-powered agent with tools
- `evaluator` - Validates state/context

**LLM Agent Best Practices:**
```json
{
  "my_agent": {
    "kind": "llm_agent",
    "llm_config": {        // ⚠️ Recommended
      "model": "gpt-4",
      "temperature": 0.7,  // Optional: 0-2
      "max_tokens": 1500   // Optional: reasonable limit
    },
    "tools": ["tool1"],    // Optional: list of tool IDs
    "max_loop": 5          // Optional: loop limit
  }
}
```

### Tool Validation

**HTTP Tools:**
```json
{
  "flight_api": {
    "type": "http",
    "spec": {
      "url": "https://api.example.com/flights",     // Required
      "method": "POST",                               // Required
      "timeout": 30,                                  // Optional
      "headers": {"Authorization": "Bearer ${TOKEN}"}  // Optional
    }
  }
}
```

**SQL Tools:**
```json
{
  "customer_db": {
    "type": "sql",
    "spec": {
      "connection_string": "${DB_CONNECTION}",  // Recommended
      "database_type": "postgresql",            // Recommended
      "read_only": true                         // Optional
    }
  }
}
```

**VectorDB Tools:**
```json
{
  "knowledge_base": {
    "type": "vectordb",
    "spec": {
      "provider": "azure_ai_search",  // Recommended
      "index_name": "docs",
      "top_k": 5
    }
  }
}
```

### LLM Config Validation

**Temperature:**
- Type: number (int or float)
- Typical range: 0.0 - 2.0
- Warning if outside range

**Max Tokens:**
- Type: integer
- Info if > 4096 (may increase costs)

**Model:**
- Type: string
- Warning for unknown models
- Supported: gpt-4, gpt-4-turbo, gpt-4o, gpt-3.5-turbo, etc.

## Examples

### Valid Minimal Spec

```json
{
  "id": "minimal_goal",
  "title": "Minimal Goal",
  "version": "1.0.0",
  "agents": {
    "supervisor": {
      "kind": "supervisor",
      "policy": "simple_router"
    }
  }
}
```

**Validation Result:** ✅ Valid (with info suggestions)

### Invalid Spec - Missing Required Fields

```json
{
  "id": "test",
  "title": "Test"
  // Missing: version, agents
}
```

**Validation Result:**
```
❌ Spec validation failed with 2 errors:
  [ERROR] root.version: Required field 'version' is missing
  [ERROR] root.agents: Required field 'agents' is missing
```

### Invalid Spec - Bad ID Format

```json
{
  "id": "My-Goal-123",  // Uppercase and hyphens
  "title": "Test",
  "version": "1.0.0",
  "agents": {"supervisor": {"kind": "supervisor"}}
}
```

**Validation Result:**
```
❌ Spec validation failed with 1 errors:
  [ERROR] root.id: ID must start with lowercase letter and contain only lowercase letters, numbers, and underscores
    → Example: 'my_goal_123'
```

### Invalid Spec - Undefined Tool Reference

```json
{
  "id": "test_goal",
  "title": "Test",
  "version": "1.0.0",
  "agents": {
    "supervisor": {"kind": "supervisor"},
    "worker": {
      "kind": "llm_agent",
      "tools": ["undefined_tool"]  // ← Tool not defined
    }
  },
  "tools": {}
}
```

**Validation Result:**
```
❌ Spec validation failed with 1 errors:
  [ERROR] agents.worker.tools: Agent references undefined tool 'undefined_tool'
    → Define tool in tools section or remove reference
```

### Spec with Warnings

```json
{
  "id": "test_goal",
  "title": "Test",
  "version": "1.0.0",
  "agents": {
    "supervisor": {"kind": "supervisor"},
    "worker": {
      "kind": "llm_agent",
      "llm_config": {
        "model": "gpt-7",        // ← Unknown model
        "temperature": 3.0        // ← Out of typical range
      }
    }
  }
}
```

**Validation Result:**
```
✅ Spec is valid (with warnings)

⚠️  Spec has 2 warnings:
  [WARN] agents.worker.llm_config.model: Unknown model 'gpt-7'. May not be supported.
    → Common models: gpt-4, gpt-4-turbo, gpt-3.5-turbo, gpt-4o
  [WARN] agents.worker.llm_config.temperature: Temperature 3.0 is outside typical range (0-2)
```

## Programmatic Usage

### Python API

```python
from spec_validator import SpecValidator, Severity

# Load spec
with open("spec.json") as f:
    spec = json.load(f)

# Validate
validator = SpecValidator()
is_valid, issues = validator.validate(spec)

# Check result
if not is_valid:
    errors = [i for i in issues if i.severity == Severity.ERROR]
    for error in errors:
        print(f"ERROR: {error.path} - {error.message}")
    sys.exit(1)

# Filter warnings
warnings = [i for i in issues if i.severity == Severity.WARNING]
for warning in warnings:
    print(f"WARN: {warning.path} - {warning.message}")

# Proceed with generation
generate_project(spec)
```

### File Validation

```python
from spec_validator import validate_spec_file

is_valid, issues = validate_spec_file("spec.json")

if not is_valid:
    print("Spec is invalid!")
    for issue in issues:
        print(f"[{issue.severity.value.upper()}] {issue.path}: {issue.message}")
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Validate Spec

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install GoalGen
        run: pip install -r requirements.txt
      - name: Validate spec
        run: |
          ./spec_validator.py specs/*.json
          if [ $? -ne 0 ]; then
            echo "Spec validation failed!"
            exit 1
          fi
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Validate all spec files
./spec_validator.py specs/*.json --errors-only

if [ $? -ne 0 ]; then
  echo "❌ Spec validation failed. Fix errors before committing."
  exit 1
fi

echo "✅ Spec validation passed"
```

## Common Issues and Fixes

### Issue: "ID must start with lowercase letter"

**Problem:**
```json
{"id": "My-Goal"}
```

**Fix:**
```json
{"id": "my_goal"}
```

### Issue: "Required field 'version' is missing"

**Problem:**
```json
{
  "id": "test",
  "title": "Test"
}
```

**Fix:**
```json
{
  "id": "test",
  "title": "Test",
  "version": "1.0.0"
}
```

### Issue: "At least one supervisor agent is required"

**Problem:**
```json
{
  "agents": {
    "worker": {"kind": "llm_agent"}
  }
}
```

**Fix:**
```json
{
  "agents": {
    "supervisor": {"kind": "supervisor"},
    "worker": {"kind": "llm_agent"}
  }
}
```

### Issue: "Agent references undefined tool"

**Problem:**
```json
{
  "agents": {
    "worker": {"kind": "llm_agent", "tools": ["my_tool"]}
  },
  "tools": {}
}
```

**Fix:**
```json
{
  "agents": {
    "worker": {"kind": "llm_agent", "tools": ["my_tool"]}
  },
  "tools": {
    "my_tool": {
      "type": "http",
      "spec": {"url": "...", "method": "GET"}
    }
  }
}
```

## Testing Your Spec

1. **Validate first:** Always run the validator before generation
   ```bash
   ./spec_validator.py my_spec.json
   ```

2. **Fix errors:** Address all ERROR level issues

3. **Review warnings:** Consider fixing WARNING issues

4. **Apply suggestions:** Optionally apply INFO suggestions

5. **Generate:** Run GoalGen with validated spec
   ```bash
   ./goalgen.py --spec my_spec.json --out ./output
   ```

## Best Practices

1. ✅ **Always validate before committing** - Catch issues early
2. ✅ **Fix all errors** - Don't skip validation in production
3. ✅ **Address warnings** - They often indicate real issues
4. ✅ **Use semantic versioning** - Track spec changes properly
5. ✅ **Name IDs consistently** - Use lowercase with underscores
6. ✅ **Document your spec** - Add description field
7. ✅ **Test incrementally** - Validate after each change

## Extending the Validator

To add custom validation rules, extend `SpecValidator`:

```python
class CustomSpecValidator(SpecValidator):
    def validate(self, spec):
        is_valid, issues = super().validate(spec)

        # Add custom validation
        self._validate_custom_rules()

        return not any(i.severity == Severity.ERROR for i in self.issues), self.issues

    def _validate_custom_rules(self):
        # Your custom validation logic
        if some_condition:
            self._add_issue(
                Severity.WARNING,
                "custom.field",
                "Custom validation message"
            )
```

---

**Status:** Production Ready
**Version:** 1.0.0
**Last Updated:** 2025-12-01
