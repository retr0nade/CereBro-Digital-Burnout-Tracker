# Test Suite for Mental Burnout Tracker V2

This directory contains comprehensive unit tests for the Mental Burnout Tracker V2 backend components.

## Overview

The test suite covers the following key areas:

- **Database Schema Tests**: Validate database table creation, schema, and operations
- **Idle Detection Tests**: Test idle monitoring logic and state transitions
- **Focus Timer Tests**: Test focus session management and timing logic
- **App Usage Logging Tests**: Test window tracking and app usage logging

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_database_schema.py     # Database schema and operations tests
├── test_idle_detection.py      # Idle detection logic tests
├── test_focus_timer.py         # Focus session timer tests
├── test_app_usage_logging.py   # App usage logging tests
├── pytest.ini                 # Pytest configuration
└── README.md                  # This file
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

### Running All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Running Specific Test Categories

```bash
# Database tests only
pytest tests/test_database_schema.py

# Idle detection tests only
pytest tests/test_idle_detection.py

# Focus timer tests only
pytest tests/test_focus_timer.py

# App usage logging tests only
pytest tests/test_app_usage_logging.py
```

### Running Tests with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests excluding slow ones
pytest -m "not slow"

# Run database-related tests
pytest -m database
```

## Test Categories

### Database Schema Tests (`test_database_schema.py`)

Tests database initialization, schema validation, and CRUD operations:

- **Table Creation**: Verify all required tables are created
- **Schema Validation**: Check column types and constraints
- **Data Operations**: Test insert, fetch, and query operations
- **Data Integrity**: Validate data types and constraints
- **Performance**: Test with multiple records and limits

### Idle Detection Tests (`test_idle_detection.py`)

Tests idle monitoring functionality:

- **Initialization**: Test idle monitor setup
- **Threshold Detection**: Test idle/active state transitions
- **State Management**: Test idle start/end logging
- **Error Handling**: Test exception scenarios
- **Performance**: Test rapid state changes
- **Configuration**: Test parameter validation

### Focus Timer Tests (`test_focus_timer.py`)

Tests focus session management:

- **Session Lifecycle**: Test start, stop, and status operations
- **Duration Tracking**: Test session timing calculations
- **Interruption Detection**: Test idle interruption logic
- **Statistics**: Test session statistics and history
- **Error Handling**: Test edge cases and exceptions
- **Configuration**: Test parameter validation

### App Usage Logging Tests (`test_app_usage_logging.py`)

Tests window tracking and app usage logging:

- **Window Detection**: Test active window identification
- **Switch Detection**: Test window/app switching logic
- **Data Logging**: Test activity logging to database
- **Categorization**: Test app categorization logic
- **Performance**: Test rapid window changes
- **Error Handling**: Test exception scenarios

## Test Fixtures

The test suite uses several fixtures defined in `conftest.py`:

- **`temp_db_path`**: Creates temporary database file
- **`test_db`**: Provides initialized test database instance
- **`mock_config`**: Provides mock configuration
- **`sample_*_data`**: Provides sample data for testing
- **`mock_time`**: Mocks time functions for consistent testing
- **`mock_datetime`**: Mocks datetime functions

## Coverage

The test suite aims for high code coverage:

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **Edge Cases**: Test boundary conditions and error scenarios
- **Performance Tests**: Test with high load scenarios

## Continuous Integration

The test suite is integrated with GitHub Actions:

- **Multi-platform Testing**: Runs on Ubuntu, Windows, and macOS
- **Multi-version Testing**: Tests with Python 3.9, 3.10, and 3.11
- **Code Coverage**: Generates coverage reports
- **Linting**: Runs code quality checks
- **Security Scanning**: Performs security analysis

## Test Data

Tests use mock data to ensure consistency:

- **Timestamps**: Fixed timestamps for predictable results
- **Sample Records**: Predefined data structures
- **Mock Functions**: Mocked system calls and external dependencies

## Best Practices

The test suite follows these best practices:

- **Isolation**: Each test is independent
- **Mocking**: External dependencies are mocked
- **Cleanup**: Temporary resources are cleaned up
- **Documentation**: Tests are well-documented
- **Naming**: Clear, descriptive test names
- **Assertions**: Specific, meaningful assertions

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with debug output
pytest -v -s

# Run specific test with debug
pytest tests/test_database_schema.py::TestDatabaseSchema::test_database_initialization -v -s
```

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html  # Linux
```

### Common Issues

1. **Import Errors**: Ensure the parent directory is in Python path
2. **Database Errors**: Check that SQLite is available
3. **Mock Issues**: Verify mock patches are correct
4. **Timing Issues**: Use fixed timestamps in tests

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Use appropriate fixtures
3. Add comprehensive docstrings
4. Test both success and failure cases
5. Update this README if needed

## CI/CD Integration

The test suite is automatically run on:

- **Push to main/develop**: Full test suite
- **Pull Requests**: Full test suite with coverage
- **Scheduled**: Daily security scans

Test results are available in the GitHub Actions tab.
