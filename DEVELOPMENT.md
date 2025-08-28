# Starfish MCP Development Workflow

## 🚨 **MANDATORY TESTING REQUIREMENT**

**For every code change, you MUST:**

1. ✅ **Create/Update Tests** - Write comprehensive tests for new functionality
2. ✅ **Run All Tests** - Execute full test suite to ensure no regressions  
3. ✅ **Verify Results** - Review test output and fix any failures
4. ✅ **Check Coverage** - Ensure adequate test coverage for changes
5. ✅ **Commit Only When Green** - Never commit failing tests

## 🧪 **Test Categories**

### **Unit Tests**
- **Location**: `tests/test_*.py`
- **Purpose**: Test individual components in isolation
- **Run**: `make test` or `pytest tests/ -v`
- **Files**:
  - `test_tools_modular.py` - New modular tools architecture
  - `test_query_builder.py` - Query building logic
  - `test_models.py` - Data models
  - `test_client.py` - API client
  - `test_config.py` - Configuration

### **Integration Tests** 
- **Location**: `tests/test_integration*.py`
- **Purpose**: Test against real Starfish API
- **Run**: `make test-integration` or `pytest tests/test_integration*.py -v -m integration`
- **Requirements**: Set environment variables:
  ```bash
  export STARFISH_INTEGRATION_BASE_URL=https://sf-redashdev.sfish.dev/api
  export STARFISH_INTEGRATION_USERNAME=demo
  export STARFISH_INTEGRATION_PASSWORD=demo
  ```

### **Coverage Reports**
- **Run**: `make coverage` or `pytest --cov=starfish_mcp --cov-report=html`
- **View**: Open `htmlcov/index.html` in browser
- **Target**: >90% coverage for all new code

## 🔄 **Development Workflow**

### **Before Making Changes**
```bash
# 1. Ensure tests pass
make test

# 2. Check current coverage
make coverage

# 3. Create feature branch (if using git flow)
git checkout -b feature/new-starfish-parameter
```

### **During Development**
```bash
# 1. Write failing test first (TDD approach)
# 2. Implement minimal code to pass test  
# 3. Refactor and improve
# 4. Run tests frequently
make test-watch  # Auto-run on file changes
```

### **Before Committing**
```bash
# 1. Run full test suite
make test

# 2. Run integration tests (if possible)
make test-integration

# 3. Check linting
make lint

# 4. Generate coverage report
make coverage

# 5. Only commit if all green ✅
git add -A
git commit -m "Add feature X with comprehensive tests"
```

## 📝 **Test Writing Guidelines**

### **For New Starfish Parameters**
When adding new query parameters (e.g., `--blocks`, `--aggrs`):

1. **Update Schema** (`tools/schema.py`)
2. **Update Query Builder** (`tools/query_builder.py`) 
3. **Write Unit Tests** (`test_query_builder.py`):
   ```python
   def test_new_parameter(self):
       args = {"new_param": "test_value"}
       query = build_starfish_query(args)
       assert "new_param=test_value" in query
   ```
4. **Write Integration Tests** (`test_integration_comprehensive.py`):
   ```python
   @pytest.mark.integration
   async def test_new_parameter_integration(integration_tools):
       result = await integration_tools.handle_tool_call("starfish_query", {
           "new_param": "test_value",
           "limit": 5
       })
       assert not result.isError
   ```

### **Test Naming Conventions**
- `test_<component>_<functionality>.py` - Main test files
- `test_<specific_feature>()` - Individual test functions
- `test_<edge_case>_edge_case()` - Edge case tests
- `test_<error_condition>_error()` - Error handling tests

### **Test Structure**
```python
def test_feature_description():
    """Clear description of what this test verifies."""
    # Arrange - Set up test data
    args = {"param": "value"}
    
    # Act - Execute the functionality  
    result = function_under_test(args)
    
    # Assert - Verify expected behavior
    assert result == expected_value
```

## 🛠️ **Make Commands**

| Command | Purpose |
|---------|---------|
| `make test` | Run all unit tests |
| `make test-integration` | Run integration tests |
| `make test-watch` | Auto-run tests on file changes |
| `make coverage` | Generate coverage report |
| `make lint` | Run code linting |
| `make format` | Auto-format code |
| `make check` | Run all checks (test + lint + coverage) |

## 🐛 **Debugging Test Failures**

### **Common Issues**
1. **Import Errors**: Check module paths after refactoring
2. **Mock Setup**: Ensure mocks match actual API signatures  
3. **Async Tests**: Use `@pytest.mark.asyncio` decorator
4. **Environment**: Verify test environment variables

### **Debugging Commands**
```bash
# Run specific test with verbose output
pytest tests/test_tools_modular.py::test_starfish_query_tool -v -s

# Run with debugger on failure
pytest tests/test_tools_modular.py --pdb

# Run only failed tests from last run
pytest --lf
```

## 📊 **Current Test Status**

### **✅ Test Coverage by Module**
- `tools/` - **NEW COMPREHENSIVE TESTS**
  - `test_tools_modular.py` - Full modular architecture tests
  - `test_query_builder.py` - Comprehensive query building tests
- `test_integration_comprehensive.py` - Real API integration tests
- `test_models.py` - Data model validation
- `test_client.py` - API client functionality  
- `test_config.py` - Configuration management

### **🎯 Testing Priorities**
1. **All new parameters** must have unit + integration tests
2. **Query builder logic** must be thoroughly tested
3. **Error handling** must be tested for all edge cases
4. **API compatibility** must be verified with integration tests

## 🚀 **Continuous Integration**

When setting up CI/CD:
```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    make test
    make coverage
    make lint
    
- name: Integration Tests  
  run: make test-integration
  env:
    STARFISH_INTEGRATION_BASE_URL: ${{ secrets.STARFISH_URL }}
    STARFISH_INTEGRATION_USERNAME: ${{ secrets.STARFISH_USER }}
    STARFISH_INTEGRATION_PASSWORD: ${{ secrets.STARFISH_PASS }}
```

---

**Remember: Tests are not optional - they're part of the code!** 🧪✨
