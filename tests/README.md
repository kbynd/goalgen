# GoalGen Tests

Comprehensive test suite for the GoalGen code generator.

## Test Structure

```
tests/
├── unit/                          # Unit tests for individual components
│   ├── test_spec_validation.py   # Spec validation logic tests
│   └── test_generator_outputs.py # Generator output validation tests
├── integration/                   # Integration tests
│   └── test_full_generation.py   # End-to-end generation workflow tests
├── fixtures/                      # Test fixtures and sample specs
│   └── minimal_spec.json         # Minimal valid spec for testing
├── conftest.py                   # Shared pytest fixtures and configuration
└── pytest.ini                    # Pytest configuration

```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_spec_validation.py

# Specific test function
pytest tests/unit/test_spec_validation.py::TestSpecValidation::test_valid_spec_loads_successfully
```

### Run tests with markers
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

### Run with verbose output
```bash
pytest -v tests/

# With detailed output
pytest -vv tests/

# Show print statements
pytest -s tests/
```

### Run with coverage
```bash
# Install pytest-cov first
pip install pytest-cov

# Run with coverage
pytest --cov=generators --cov=frmk --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

## Test Categories

### Unit Tests (`tests/unit/`)

**test_spec_validation.py**
- Validates goal spec structure
- Tests required fields presence
- Tests agent/tool/task validation
- Tests edge cases and invalid specs

**test_generator_outputs.py**
- Tests individual generator outputs
- Validates generated file structure
- Checks generated code quality
- Tests dry-run behavior

### Integration Tests (`tests/integration/`)

**test_full_generation.py**
- End-to-end generation workflows
- Tests complete project generation
- Tests selective generation (--targets)
- Tests incremental generation
- Tests error handling

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

- `temp_output_dir` - Temporary directory for test outputs
- `goalgen_root` - Path to GoalGen root
- `example_spec` - Loaded travel planning spec
- `minimal_spec` - Minimal valid spec
- `complex_spec` - Complex multi-agent spec
- `invalid_spec_*` - Various invalid specs for error testing

## Writing New Tests

### Unit Test Template

```python
import pytest

class TestYourFeature:
    """Test your feature"""

    def setup_method(self):
        """Setup before each test"""
        pass

    def teardown_method(self):
        """Cleanup after each test"""
        pass

    def test_something(self):
        """Test description"""
        # Arrange
        # Act
        # Assert
        assert True
```

### Integration Test Template

```python
import pytest
import subprocess
from pathlib import Path

@pytest.mark.integration
class TestYourIntegration:
    """Integration test for your feature"""

    def test_full_workflow(self, temp_output_dir, goalgen_root):
        """Test complete workflow"""
        result = subprocess.run(
            ["python", str(goalgen_root / "goalgen.py"), ...],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_unit():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.requires_azure
def test_with_azure():
    pass
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --tb=short
```

## Best Practices

1. **Isolate tests**: Use fixtures and temp directories
2. **Clean up**: Use teardown_method or fixture cleanup
3. **Clear names**: Test names should describe what they test
4. **Fast tests**: Keep unit tests fast, mark slow tests
5. **Independent**: Tests should not depend on each other
6. **Assertions**: Use clear, descriptive assertions

## Troubleshooting

### Tests not discovered
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Verify test discovery
pytest --collect-only tests/
```

### Import errors
```bash
# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Cleanup issues
```bash
# Remove test outputs
rm -rf test_output* output/

# Clear pytest cache
rm -rf .pytest_cache
```

## Future Improvements

- [ ] Add performance benchmarks
- [ ] Add mutation testing
- [ ] Add property-based testing (hypothesis)
- [ ] Add snapshot testing for generated code
- [ ] Add test coverage goals (>80%)
- [ ] Add generated code linting tests
- [ ] Add security scanning tests
