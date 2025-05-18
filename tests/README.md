# Test Suite

This directory contains the comprehensive test suite for the Satoshi AI application, following industry best practices for testing in Python.

## Test Structure

```
tests/
├── conftest.py         # Global pytest configuration and shared fixtures
├── utils.py            # Test utilities and helper functions
├── test_data/          # Test data files (JSON, CSVs, etc.)
│   └── fixtures/       # Reusable test data fixtures
│
├── api/               # API endpoint tests
│   ├── conftest.py     # API-specific fixtures
│   ├── middleware/     # Middleware tests
│   └── routes/         # Route-specific tests
│
├── database/          # Database tests
│   ├── conftest.py     # Database fixtures and utilities
│   ├── core/           # Core database operations
│   ├── migrations/     # Migration testing
│   └── security/       # Security and RLS tests
│
├── integration/       # Integration tests
│   ├── conftest.py     # Integration test fixtures
│   ├── e2e/            # End-to-end tests
│   └── workflows/      # Workflow tests
│
├── services/          # Service layer tests
│   ├── conftest.py     # Service layer fixtures
│   ├── ai/             # AI agent tests
│   ├── discord/        # Discord service tests
│   ├── meet/           # Google Meet service tests
│   └── twitter/        # Twitter service tests
│
└── unit/              # Unit tests
```

## Test Conventions

### Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`
- Fixtures: Lowercase with underscores (e.g., `test_user`, `mock_client`)

### Test Organization

- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test interactions between components
- **E2E Tests**: Test complete user flows

### Fixture Usage

- Use fixtures for common test data and setup/teardown
- Prefer function-scoped fixtures by default
- Use session-scoped fixtures for expensive setup
- Document fixture purposes and return values

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.

# Show missing lines in coverage
pytest --cov=. --cov-report=term-missing
```

### Running Tests with Docker

For integration tests that require external services, you can use the test Docker Compose configuration:

```bash
# Start test services in detached mode
docker-compose -f ../infra/docker-compose.yml -f docker-compose.test.yml up -d

# Run tests (in another terminal)
pytest tests/

# Stop and remove containers when done
docker-compose -f ../infra/docker-compose.yml -f docker-compose.test.yml down
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/api/test_endpoints.py

# Run tests by marker
pytest -m unit             # Unit tests only
pytest -m integration      # Integration tests only
pytest -m database         # Database tests only
pytest -m api              # API tests only
pytest -m "not slow"       # Skip slow tests

# Run tests matching a pattern
pytest -k "test_user"      # Run tests with 'test_user' in the name
```

### Test Coverage

We use `pytest-cov` for test coverage reporting. To generate a coverage report:

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open the HTML report (on macOS)
open htmlcov/index.html
```

## Writing Tests

### Example Unit Test

```python
import pytest

from myapp.services.user import create_user

class TestUserCreation:
    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        user = create_user(
            session=db_session,
            username="testuser",
            email="test@example.com"
        )
        assert user.id is not None
        assert user.username == "testuser"

    def test_create_user_duplicate_username(self, db_session, test_user):
        """Test user creation with duplicate username fails."""
        with pytest.raises(ValueError):
            create_user(
                session=db_session,
                username=test_user.username,
                email="new@example.com"
            )
```

### Example Integration Test

```python
import pytest
from fastapi.testclient import TestClient

from myapp.main import app

class TestUserAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(app)

    def test_create_user(self):
        """Test user creation via API."""
        response = self.client.post(
            "/users/",
            json={"username": "testuser", "email": "test@example.com"}
        )
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Deterministic**: Tests should produce the same results every time
3. **Fast**: Keep tests fast to encourage frequent running
4. **Clear Naming**: Test names should describe what's being tested
5. **Minimal Fixtures**: Only include necessary setup in fixtures
6. **Mock External Services**: Use mocks for external API calls
7. **Test Edge Cases**: Include tests for error conditions and edge cases
8. **Documentation**: Add docstrings explaining test purpose

## Debugging Tests

To debug a failing test:

```bash
# Drop to PDB on failure
pytest --pdb

# Print detailed logs
pytest -v -s

# Run with specific log level
pytest --log-cli-level=DEBUG
```

## CI/CD Integration

Tests are automatically run on pull requests and merges to main. The CI pipeline includes:

1. Unit tests
2. Integration tests
3. Code coverage checks
4. Linting and type checking

## Common Issues

### Database Connection Issues

- Ensure test database is running
- Check environment variables for database connection
- Verify migrations have been applied

### Test Isolation Issues

- Use `autouse=False` for fixtures when possible
- Clean up test data in fixture teardown
- Use transaction rollbacks where appropriate

### Slow Tests

- Mark slow tests with `@pytest.mark.slow`
- Use `pytest -m "not slow"` to skip them during development
- Consider using mocks for external API calls

## Contributing

1. Write tests for new features
2. Ensure all tests pass before opening a PR
3. Update documentation when adding new test utilities
4. Follow the existing test patterns and conventions

```

## Test Conventions

### Test Naming
- Test files should be named `test_*.py` or `*_test.py`
- Test classes should be prefixed with `Test` (e.g., `TestUserService`)
- Test methods should start with `test_` (e.g., `test_create_user`)

### Test Organization
- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test interactions between components
- **API Tests**: Test API endpoints
- **Database Tests**: Test database operations and RLS policies

### Fixtures
- Common fixtures are defined in `conftest.py`
- Use appropriate fixture scopes (`function`, `class`, `module`, `session`)
- Prefer dependency injection over global state

### Assertions
- Use Python's built-in `assert` statement
- For more complex assertions, use `pytest`'s assertion introspection
- Use descriptive assertion messages

### Test Data
- Store test data in JSON files in the `test_data` directory
- Use the `load_test_data` utility to load and validate test data
- Keep test data minimal and focused

### Logging
- Use the configured `loguru` logger
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include relevant context in log messages

## Best Practices

1. **Isolation**: Each test should be independent and not rely on state from other tests
2. **Deterministic**: Tests should produce the same results every time they're run
3. **Fast**: Keep tests fast to enable quick feedback
4. **Readable**: Write clear, descriptive test names and assertions
5. **Maintainable**: Structure tests to be easy to understand and modify
```
