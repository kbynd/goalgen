# GoalGen Defects & Issues

**Generated from Test Results:** 2025-12-01
**Test Run:** 33 tests, 26 passing, 7 failing
**Priority Legend:** 🔴 High | 🟡 Medium | 🟢 Low

---

## Summary

Testing has identified **7 defects** in the GoalGen codebase, primarily related to template robustness and handling of optional spec fields.

| Priority | Count | Category |
|----------|-------|----------|
| 🔴 High | 4 | Template crashes on minimal specs |
| 🟡 Medium | 2 | Generator missing expected output |
| 🟢 Low | 1 | Documentation placeholders |

---

## 🔴 HIGH Priority Defects

### DEF-001: Scaffold Generator Crashes on Missing `deployment.environments` Field

**Status:** Open
**Priority:** 🔴 High
**Component:** generators/scaffold.py, templates/scaffold/README.md.j2
**Discovered by:** test_scaffold_creates_base_structure, test_scaffold_creates_readme, test_scaffold_creates_gitignore, test_scaffold_creates_requirements_txt

**Description:**
The scaffold generator's README.md template crashes when the spec doesn't include `deployment.environments.dev.resource_group`.

**Error:**
```
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'environments'
templates/scaffold/README.md.j2:141: in top-level template code
--resource-group {{ deployment.environments.dev.resource_group }}
```

**Impact:**
- Users cannot generate projects with minimal specs
- Scaffold generator fails completely, blocking all downstream generation
- Forces users to specify optional deployment fields even for local development

**Steps to Reproduce:**
```python
spec = {
    "id": "test_goal",
    "title": "Test Goal",
    "version": "1.0.0",
    "agents": {"supervisor": {"kind": "supervisor"}},
    "ux": {"teams": {"enabled": False}, "api": {"enabled": True}}
}

from generators.scaffold import generate
generate(spec, "./output", dry_run=False)  # Crashes
```

**Expected Behavior:**
Generator should work with minimal spec, using sensible defaults for missing deployment fields.

**Proposed Fix:**

**templates/scaffold/README.md.j2** (line 141):
```jinja2
# Before (crashes):
--resource-group {{ deployment.environments.dev.resource_group }}

# After (defensive):
{% if deployment and deployment.environments and deployment.environments.dev %}
--resource-group {{ deployment.environments.dev.resource_group }}
{% else %}
--resource-group rg-{{ spec.id }}-dev
{% endif %}
```

**Related Files:**
- `templates/scaffold/README.md.j2` (multiple locations)
- `generators/scaffold.py` (context preparation)

**Test Cases:**
- `test_scaffold_creates_base_structure` ❌
- `test_scaffold_creates_readme` ❌
- `test_scaffold_creates_gitignore` ❌
- `test_scaffold_creates_requirements_txt` ❌

---

### DEF-002: LangGraph Generator Doesn't Create `agents/` Directory

**Status:** Open
**Priority:** 🔴 High
**Component:** generators/langgraph.py
**Discovered by:** test_langgraph_creates_agents_directory

**Description:**
The LangGraph generator creates `quest_builder.py` but doesn't create the `langgraph/agents/` directory, even though the agents generator expects it to exist.

**Error:**
```
AssertionError: assert False
 +  where False = <bound method Path.exists of PosixPath('.../langgraph/agents')>()
```

**Impact:**
- Inconsistent directory structure
- Agents generator may fail if parent directory doesn't exist
- Generated project structure doesn't match documentation

**Steps to Reproduce:**
```python
from generators.langgraph import generate
spec = {"id": "test", "agents": {"supervisor": {"kind": "supervisor"}}}
generate(spec, "./output", dry_run=False)
# langgraph/agents/ directory not created
```

**Expected Behavior:**
LangGraph generator should create the full directory structure including:
- `langgraph/`
- `langgraph/agents/`
- `langgraph/evaluators/`
- `langgraph/quest_builder.py`

**Proposed Fix:**

**generators/langgraph.py**:
```python
def generate(spec, out_dir, dry_run):
    # ... existing code ...

    # Create directory structure
    langgraph_dir = Path(out_dir, "langgraph")
    agents_dir = Path(langgraph_dir, "agents")
    evaluators_dir = Path(langgraph_dir, "evaluators")

    if not dry_run:
        agents_dir.mkdir(parents=True, exist_ok=True)
        evaluators_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        (agents_dir / "__init__.py").touch()
        (evaluators_dir / "__init__.py").touch()
```

**Test Cases:**
- `test_langgraph_creates_agents_directory` ❌

---

### DEF-003: README Template Assumes `deployment` Section Exists

**Status:** Open
**Priority:** 🔴 High
**Component:** templates/scaffold/README.md.j2
**Discovered by:** Multiple scaffold tests

**Description:**
The README template accesses `deployment.monitoring`, `deployment.environments`, and other deployment fields without checking if the `deployment` section exists in the spec.

**Error:**
```
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'monitoring'
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'environments'
```

**Impact:**
- Cannot generate README for minimal specs
- All scaffold tests fail
- Blocks initial project setup

**Affected Template Locations:**

**templates/scaffold/README.md.j2**:
- Line 141: `{{ deployment.environments.dev.resource_group }}`
- Line ~90: `{{ deployment.monitoring.app_insights }}`
- Line ~100: `{{ deployment.target }}` (assumed)
- Multiple other locations

**Expected Behavior:**
Template should provide defaults or conditionally render deployment sections.

**Proposed Fix:**

```jinja2
## Deployment

{% if deployment %}
### Environments

{% if deployment.environments %}
{% for env_name, env_config in deployment.environments.items() %}
- **{{ env_name }}**: `{{ env_config.resource_group }}`
{% endfor %}
{% else %}
- **dev**: `rg-{{ spec.id }}-dev` (default)
- **staging**: `rg-{{ spec.id }}-staging` (default)
- **prod**: `rg-{{ spec.id }}-prod` (default)
{% endif %}

### Monitoring

{% if deployment.monitoring %}
- Application Insights: {{ "enabled" if deployment.monitoring.app_insights else "disabled" }}
- Log Analytics: {{ "enabled" if deployment.monitoring.log_analytics else "disabled" }}
{% else %}
- Application Insights: enabled (default)
- Log Analytics: enabled (default)
{% endif %}

{% else %}
### Quick Start (No Deployment Config)

This project was generated without deployment configuration.
To deploy to Azure, add a `deployment` section to your spec.

See the [deployment guide](docs/DEPLOYMENT.md) for details.
{% endif %}
```

**Test Cases:**
- `test_scaffold_creates_base_structure` ❌
- `test_scaffold_creates_readme` ❌
- `test_scaffold_creates_gitignore` ❌
- `test_scaffold_creates_requirements_txt` ❌

---

### DEF-004: Manifest Generator Crashes on Missing Deployment Section

**Status:** Open
**Priority:** 🔴 High
**Component:** generators/scaffold.py or goalgen.py (manifest generation)
**Discovered by:** test_manifest_is_created

**Description:**
Manifest generation fails when spec doesn't include deployment section.

**Error:**
```
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'environments'
```

**Impact:**
- Cannot track generated files in `.goalgen/manifest.json`
- Incremental generation will not work
- No record of what was generated

**Expected Behavior:**
Manifest should be created regardless of optional spec sections. The manifest should track:
- Spec version
- Generated files list
- Generation timestamp
- GoalGen version
- Spec checksum

**Proposed Fix:**

**goalgen.py** (manifest generation):
```python
def save_manifest(spec, out_dir, generated_files):
    """Save generation manifest"""
    manifest = {
        "spec": {
            "id": spec["id"],
            "version": spec["version"],
            "checksum": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
        },
        "generated_files": generated_files,
        "timestamp": datetime.now().isoformat(),
        "goalgen_version": "0.1.0",
        "generators_run": list(set(f.split("/")[0] for f in generated_files))
    }

    manifest_path = Path(out_dir, ".goalgen", "manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
```

**Test Cases:**
- `test_manifest_is_created` ❌

---

## 🟡 MEDIUM Priority Defects

### DEF-005: Agent Files Don't Match Expected Function Signature

**Status:** Open
**Priority:** 🟡 Medium
**Component:** generators/agents.py, templates/agents/
**Discovered by:** test_agent_file_has_execute_function

**Description:**
Generated agent files don't contain the expected `execute` or `async def execute` function signature that tests are looking for.

**Error:**
```
AssertionError: assert 'def execute' in '<agent file content>' or 'async def execute' in '<agent file content>'
```

**Actual Generated Code:**
```python
class FlightAgent(BaseAgent):
    def __init__(self, goal_config: Dict[str, Any]):
        # ...

    async def _process_response(self, state, response):
        # ...

# LangGraph node function
async def flight_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # ...
```

**Impact:**
- Inconsistent agent API
- Tests expect `execute()` method but code uses `flight_agent_node()` function
- May confuse users about which function to call

**Root Cause:**
Test expectation doesn't match the actual design. The current design uses:
1. Agent classes extending `BaseAgent`
2. Node functions (e.g., `flight_agent_node`) for LangGraph integration

**Options:**

**Option A: Update Test (Recommended)**
```python
def test_agent_file_has_execute_function(self):
    """Test that agent file contains node function"""
    content = agent_file.read_text()
    agent_name = "flight_agent"

    # Check for either execute method OR node function
    assert (f"def execute" in content or
            f"async def {agent_name}_node" in content), \
           f"Agent must have execute method or {agent_name}_node function"
```

**Option B: Add Execute Method to Template**
```python
class FlightAgent(BaseAgent):
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic

        This is the main entry point for the agent.
        """
        return await self.invoke(state)
```

**Recommendation:** Option A - Update test to match actual design

**Test Cases:**
- `test_agent_file_has_execute_function` ❌

---

### DEF-006: Generated Agent Files Have Missing Max Loops Value

**Status:** Open
**Priority:** 🟡 Medium
**Component:** templates/agents/llm_agent.py.j2
**Discovered by:** Visual inspection of test output

**Description:**
Generated agent docstrings show "Max Loops: " with no value.

**Actual Output:**
```python
"""
Flight Agent

Kind: llm_agent
Model: gpt-4
Max Loops:
Tools: flight_api
"""
```

**Expected Output:**
```python
"""
Flight Agent

Kind: llm_agent
Model: gpt-4
Max Loops: 3
Tools: flight_api
"""
```

**Impact:**
- Confusing documentation
- Unclear loop limit for agent
- Minor cosmetic issue

**Root Cause:**
Template doesn't handle case where `max_loop` is not specified in agent config.

**Proposed Fix:**

**templates/agents/llm_agent.py.j2**:
```jinja2
"""
{{ agent_name | title | replace("_", " ") }}

Kind: {{ agent.kind }}
Model: {{ agent.llm_config.model }}
Max Loops: {{ agent.max_loop | default(5) }}
Tools: {{ agent.tools | join(", ") if agent.tools else "none" }}

Capabilities:
{% if agent.kind == "llm_agent" %}
- Executes tasks using LLM reasoning
- Uses tools to gather information
- Provides detailed responses
{% endif %}
"""
```

**Test Cases:**
- Visual inspection ⚠️

---

## 🟢 LOW Priority Defects

### DEF-007: Manifest Test Contains Placeholder Implementation

**Status:** Open
**Priority:** 🟢 Low
**Component:** tests/unit/test_generator_outputs.py
**Discovered by:** Code review

**Description:**
Test `test_manifest_contains_spec_version` has no assertions - just a `pass` statement.

**Code:**
```python
def test_manifest_contains_spec_version(self):
    """Test that manifest tracks spec version"""
    # This test documents that manifest should contain:
    # - spec version
    # - generated files list
    # - generation timestamp
    # - goalgen version
    pass
```

**Impact:**
- Test always passes regardless of actual behavior
- No validation of manifest content
- Missed opportunity to catch manifest issues

**Expected Behavior:**
Test should validate manifest structure and content.

**Proposed Fix:**

```python
def test_manifest_contains_spec_version(self):
    """Test that manifest tracks spec version"""
    from generators.scaffold import generate

    generate(self.spec, self.temp_dir, dry_run=False)

    # Import and call manifest generation (or run full goalgen.py)
    # For now, this would require refactoring to expose manifest generation

    manifest_path = Path(self.temp_dir, ".goalgen", "manifest.json")
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Validate manifest structure
        assert "spec" in manifest
        assert "generated_files" in manifest
        assert "timestamp" in manifest
        assert "goalgen_version" in manifest

        # Validate spec info
        assert manifest["spec"]["id"] == self.spec["id"]
        assert manifest["spec"]["version"] == self.spec["version"]
```

**Note:** This test may need architectural changes to make manifest generation testable in isolation.

**Test Cases:**
- `test_manifest_contains_spec_version` ⚠️ (passes but doesn't validate)

---

## Defect Statistics

### By Priority
- 🔴 High: 4 defects (57%)
- 🟡 Medium: 2 defects (29%)
- 🟢 Low: 1 defect (14%)

### By Category
- **Template Robustness:** 4 defects (DEF-001, DEF-003, DEF-004, DEF-006)
- **Generator Logic:** 1 defect (DEF-002)
- **API Design:** 1 defect (DEF-005)
- **Test Quality:** 1 defect (DEF-007)

### By Component
- `templates/scaffold/README.md.j2`: 2 defects
- `generators/scaffold.py`: 1 defect
- `generators/langgraph.py`: 1 defect
- `generators/agents.py`: 1 defect
- `templates/agents/*.j2`: 1 defect
- `tests/`: 1 defect

---

## Recommended Fix Priority

### Sprint 1 (Critical Path)
1. **DEF-001** 🔴 - Fix README template deployment section (blocks all scaffold tests)
2. **DEF-003** 🔴 - Make templates defensive for optional fields (same root cause as DEF-001)
3. **DEF-004** 🔴 - Fix manifest generation (blocks incremental generation)

### Sprint 2 (Quality)
4. **DEF-002** 🔴 - Create agents directory structure (consistency)
5. **DEF-005** 🟡 - Clarify agent function naming (documentation/tests)
6. **DEF-006** 🟡 - Fix max_loop default value (cosmetic)

### Sprint 3 (Polish)
7. **DEF-007** 🟢 - Implement manifest validation test

---

## Root Cause Analysis

### Primary Root Cause: Insufficient Template Null Checking

**Defects:** DEF-001, DEF-003, DEF-004, DEF-006

**Problem:**
Jinja2 templates assume all optional fields exist in the spec, causing crashes when users provide minimal specs.

**Examples:**
- `{{ deployment.environments.dev.resource_group }}` - assumes 3 levels of nesting
- `{{ agent.max_loop }}` - assumes field exists

**Solution Pattern:**

```jinja2
{# Bad - crashes if field missing #}
{{ deployment.environments.dev.resource_group }}

{# Good - defensive with default #}
{% if deployment and deployment.environments and deployment.environments.dev %}
{{ deployment.environments.dev.resource_group }}
{% else %}
rg-{{ spec.id }}-dev
{% endif %}

{# Better - using Jinja2 filters #}
{{ deployment.environments.dev.resource_group | default("rg-" + spec.id + "-dev") }}
```

**Recommended Actions:**
1. Audit all templates for optional field access
2. Add default values for all optional fields
3. Use Jinja2 `default()` filter consistently
4. Add template linting to CI/CD
5. Create template testing guidelines

### Secondary Root Cause: Incomplete Directory Structure Creation

**Defects:** DEF-002

**Problem:**
Generators create files but don't always create parent directory structures, relying on other generators to do it.

**Solution:**
- Each generator should create its full directory structure
- Use `Path.mkdir(parents=True, exist_ok=True)`
- Don't assume other generators have run first

---

## Impact on Users

### Current Impact
- ❌ **Cannot generate projects with minimal specs** - Forces users to specify optional fields
- ❌ **Confusing error messages** - Jinja2 errors don't clearly explain what's missing
- ❌ **Documentation mismatch** - README says optional fields are optional, but they're required
- ⚠️ **Workaround exists** - Users can copy full example spec and modify it

### After Fixes
- ✅ Minimal specs work out of the box
- ✅ Clear defaults for all optional fields
- ✅ Better error messages if required fields are missing
- ✅ Consistent directory structure

---

## Testing Improvements Needed

Based on defect discoveries:

1. **Add template-specific tests**
   ```python
   def test_template_handles_missing_optional_fields()
   def test_template_provides_sensible_defaults()
   ```

2. **Add spec variation tests**
   ```python
   def test_minimal_spec_generation()
   def test_maximal_spec_generation()
   def test_partial_spec_variations()
   ```

3. **Add directory structure tests**
   ```python
   def test_all_expected_directories_created()
   def test_generator_creates_own_directories()
   ```

4. **Add generated code validation tests**
   ```python
   def test_generated_python_code_is_valid()
   def test_generated_bicep_is_valid()
   ```

---

## Metrics

- **Test Coverage:** 79% (26/33 tests passing)
- **Defect Detection Rate:** 7 defects found
- **Critical Path Blockers:** 4 defects
- **Time to Fix (Estimated):**
  - High Priority: 4-6 hours
  - Medium Priority: 2-3 hours
  - Low Priority: 1 hour
  - **Total:** 7-10 hours

---

## Appendix: Full Test Output

```
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.0.1, pluggy-1.6.0
collecting ... collected 33 items

tests/unit/test_generator_outputs.py::TestScaffoldGenerator::test_scaffold_creates_base_structure FAILED [  3%]
tests/unit/test_generator_outputs.py::TestScaffoldGenerator::test_scaffold_creates_readme FAILED [  6%]
tests/unit/test_generator_outputs.py::TestScaffoldGenerator::test_scaffold_creates_gitignore FAILED [  9%]
tests/unit/test_generator_outputs.py::TestScaffoldGenerator::test_scaffold_creates_requirements_txt FAILED [ 12%]
tests/unit/test_generator_outputs.py::TestLangGraphGenerator::test_langgraph_creates_quest_builder PASSED [ 15%]
tests/unit/test_generator_outputs.py::TestLangGraphGenerator::test_quest_builder_imports_langgraph PASSED [ 18%]
tests/unit/test_generator_outputs.py::TestLangGraphGenerator::test_quest_builder_defines_state_class PASSED [ 21%]
tests/unit/test_generator_outputs.py::TestLangGraphGenerator::test_langgraph_creates_agents_directory FAILED [ 24%]
tests/unit/test_generator_outputs.py::TestAgentsGenerator::test_agents_generator_creates_agent_files PASSED [ 27%]
tests/unit/test_generator_outputs.py::TestAgentsGenerator::test_agent_file_has_execute_function FAILED [ 30%]
tests/unit/test_generator_outputs.py::TestToolsGenerator::test_tools_generator_creates_tool_files PASSED [ 33%]
tests/unit/test_generator_outputs.py::TestAssetsGenerator::test_assets_creates_prompt_templates PASSED [ 36%]
tests/unit/test_generator_outputs.py::TestAssetsGenerator::test_prompt_templates_have_content PASSED [ 39%]
tests/unit/test_generator_outputs.py::TestManifestGeneration::test_manifest_is_created FAILED [ 42%]
tests/unit/test_generator_outputs.py::TestManifestGeneration::test_manifest_contains_spec_version PASSED [ 45%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_valid_spec_loads_successfully PASSED [ 48%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_spec_has_required_fields PASSED [ 51%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_spec_id_is_valid_identifier PASSED [ 54%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_agents_section_is_dict PASSED [ 57%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_each_agent_has_kind PASSED [ 60%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_supervisor_agent_exists PASSED [ 63%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_tools_referenced_by_agents_are_defined PASSED [ 66%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_http_tools_have_required_fields PASSED [ 69%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_version_is_semantic PASSED [ 72%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_tasks_reference_valid_agents PASSED [ 75%]
tests/unit/test_spec_validation.py::TestSpecValidation::test_llm_config_has_valid_model PASSED [ 78%]
tests/unit/test_spec_validation.py::TestSpecInvalidCases::test_missing_id_fails PASSED [ 81%]
tests/unit/test_spec_validation.py::TestSpecInvalidCases::test_empty_agents_fails PASSED [ 84%]
tests/unit/test_spec_validation.py::TestSpecInvalidCases::test_invalid_agent_kind_fails PASSED [ 87%]
tests/unit/test_spec_validation.py::TestSpecInvalidCases::test_undefined_tool_reference_fails PASSED [ 90%]
tests/unit/test_spec_validation.py::TestSpecEdgeCases::test_agent_with_no_tools_is_valid PASSED [ 93%]
tests/unit/test_spec_validation.py::TestSpecEdgeCases::test_multiple_supervisors_is_valid PASSED [ 96%]
tests/unit/test_spec_validation.py::TestSpecEdgeCases::test_optional_fields_can_be_missing PASSED [100%]

========================= 7 failed, 26 passed in 0.59s ==========================
```

---

**Document Status:** Current as of test run 2025-12-01
**Next Review:** After fixing high-priority defects
**Owner:** GoalGen Development Team
