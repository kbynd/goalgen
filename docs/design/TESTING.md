# GoalGen Testing Infrastructure

This document describes the testing infrastructure added to GoalGen for validation and quality assurance.

## Overview

A comprehensive test suite has been added to validate:
- Goal spec structure and semantics
- Generator outputs and file generation
- End-to-end generation workflows
- Error handling and edge cases

## Test Organization

```
tests/
├── unit/                          # Unit tests (fast, isolated)
│   ├── test_spec_validation.py   # 18 tests - Spec structure validation
│   └── test_generator_outputs.py # 15 tests - Generator output validation
├── integration/                   # Integration tests (slower, full workflows)
│   └── test_full_generation.py   # End-to-end generation tests
├── fixtures/                      # Test data and fixtures
│   └── minimal_spec.json         # Minimal valid spec for testing
├── conftest.py                   # Shared pytest fixtures
├── pytest.ini                    # Pytest configuration
└── README.md                     # Testing documentation
```

## Test Results

### Current Status (Unit Tests)

```
Total: 33 tests
Passed: 26 tests (79%)
Failed: 7 tests (21%)
```

**Passing Tests:**
- ✅ All 18 spec validation tests
- ✅ 8 generator output tests (LangGraph, agents, tools, assets)

**Failing Tests (Expected - Template Robustness Issues):**
- ❌ 4 scaffold tests - Missing deployment.environments section
- ❌ 2 agent tests - Missing agents directory / execute function patterns
- ❌ 1 manifest test - Missing deployment.environments section

**Note:** The failing tests are identifying real issues where templates assume optional fields exist. These failures are valuable for improving template robustness.

## Test Categories

### 1. Spec Validation Tests (test_spec_validation.py)

Validates goal spec structure and semantics:

- **Basic Structure:** Required fields (id, title, agents, version)
- **Agent Validation:** Kind, tools references, supervisor existence
- **Tool Validation:** HTTP tool structure, undefined tool detection
- **Task Validation:** Agent references, valid task structure
- **Edge Cases:** Optional fields, multiple supervisors, minimal specs

**Sample Tests:**
```python
def test_supervisor_agent_exists()
def test_tools_referenced_by_agents_are_defined()
def test_http_tools_have_required_fields()
def test_version_is_semantic()
```

### 2. Generator Output Tests (test_generator_outputs.py)

Validates generator outputs:

- **Scaffold Generator:** Directory structure, README, .gitignore, requirements.txt
- **LangGraph Generator:** quest_builder.py, state definitions, imports
- **Agents Generator:** Agent files created, function signatures
- **Tools Generator:** Tool directory structure
- **Assets Generator:** Prompt templates created and populated

**Sample Tests:**
```python
def test_scaffold_creates_base_structure()
def test_quest_builder_imports_langgraph()
def test_agents_generator_creates_agent_files()
def test_assets_creates_prompt_templates()
```

### 3. Integration Tests (test_full_generation.py)

End-to-end workflows:

- **Full Generation:** Complete project generation from spec
- **Selective Generation:** --targets flag functionality
- **Incremental Generation:** --incremental flag preservation of user changes
- **Error Handling:** Invalid specs, missing files, JSON parsing
- **Dry Run:** --dry-run flag behavior

**Sample Tests:**
```python
def test_full_generation_completes_successfully()
def test_selective_generation_scaffold_only()
def test_incremental_flag_preserves_existing_files()
def test_invalid_spec_path_fails_gracefully()
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific category
pytest tests/unit/
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_spec_validation.py

# Run specific test
pytest tests/unit/test_spec_validation.py::TestSpecValidation::test_supervisor_agent_exists
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Skip tests requiring Azure
pytest -m "not requires_azure"
```

### Coverage

```bash
# Install pytest-cov
pip install pytest-cov

# Run with coverage
pytest --cov=generators --cov=frmk --cov-report=html tests/

# View report
open htmlcov/index.html
```

## Pytest Configuration

**pytest.ini** includes:
- Test discovery patterns
- Output verbosity settings
- Test markers for categorization
- Coverage configuration (optional)

**conftest.py** provides shared fixtures:
- `temp_output_dir` - Temporary directory for outputs
- `goalgen_root` - Path to GoalGen root
- `example_spec` - Loaded travel_planning.json
- `minimal_spec` - Minimal valid spec
- `complex_spec` - Multi-agent/tool spec
- `invalid_spec_*` - Various invalid specs for testing

## Test Fixtures

### Minimal Spec (tests/fixtures/minimal_spec.json)

```json
{
  "id": "minimal_test",
  "title": "Minimal Test Goal",
  "version": "1.0.0",
  "agents": {
    "supervisor": {
      "kind": "supervisor",
      "policy": "simple_router"
    }
  }
}
```

### Complex Spec Fixture (in conftest.py)

Includes multiple agents, tools, tasks, state management, etc. for comprehensive testing.

## Known Issues and Improvements Needed

### Template Robustness
The failing tests highlight areas where templates need to be more defensive:

1. **Optional Field Handling:** Templates should use Jinja2 `{% if field is defined %}` checks
2. **Default Values:** Provide sensible defaults for optional sections
3. **Nested Attributes:** Safe navigation for deeply nested optional fields

### Example Template Fix

**Before (causes failures):**
```jinja2
--resource-group {{ deployment.environments.dev.resource_group }}
```

**After (defensive):**
```jinja2
{% if deployment and deployment.environments and deployment.environments.dev %}
--resource-group {{ deployment.environments.dev.resource_group }}
{% else %}
--resource-group rg-{{ spec.id }}-dev
{% endif %}
```

### Recommended Next Steps

1. **Fix Template Issues:** Make templates defensive for optional fields
2. **Add More Integration Tests:** Test incremental generation, error scenarios
3. **Add Property-Based Tests:** Use Hypothesis for spec fuzzing
4. **Add Performance Tests:** Benchmark generation time
5. **Add Generated Code Tests:** Lint and validate generated code
6. **Increase Coverage:** Aim for >80% code coverage
7. **CI/CD Integration:** Run tests in GitHub Actions

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ -v --cov=generators --cov=frmk
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Writing Guidelines

### Unit Test Template

```python
class TestYourFeature:
    """Test your feature"""

    def setup_method(self):
        """Setup before each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_something(self):
        """Test description"""
        # Arrange
        spec = {"id": "test"}

        # Act
        result = function_under_test(spec)

        # Assert
        assert result == expected
```

### Integration Test Template

```python
@pytest.mark.integration
def test_full_workflow(temp_output_dir, goalgen_root):
    """Test complete workflow"""
    result = subprocess.run(
        ["python", str(goalgen_root / "goalgen.py"), ...],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert Path(temp_output_dir, "expected_file").exists()
```

## Benefits of Testing Infrastructure

1. **Quality Assurance:** Catch regressions before deployment
2. **Documentation:** Tests document expected behavior
3. **Refactoring Safety:** Change code with confidence
4. **Bug Detection:** Found real template issues
5. **Spec Validation:** Ensures valid goal specs
6. **Developer Velocity:** Fast feedback on changes

## Metrics

- **Test Coverage:** 26/33 tests passing (79%)
- **Test Execution Time:** ~0.6s for unit tests
- **Lines of Test Code:** ~700+ lines
- **Test Files:** 4 files (validation, generator, integration, fixtures)
- **Test Fixtures:** 7 shared fixtures in conftest.py

## Conclusion

A solid testing foundation has been established for GoalGen. The tests are:
- **Comprehensive:** Cover spec validation, generation, and workflows
- **Fast:** Unit tests run in < 1 second
- **Maintainable:** Clear structure, good documentation
- **Valuable:** Already finding real issues in templates

**Next Steps:**
1. Fix template robustness issues identified by failing tests
2. Add more integration tests
3. Set up CI/CD pipeline
4. Increase test coverage to >80%

---

**Generated:** 2025-12-01
**Test Framework:** pytest 9.0.1
**Python:** 3.13.5
**Status:** ✅ Testing infrastructure complete and operational
