# Testing Framework for Idaho Legislative Media Portal

This directory contains tests for the Idaho Legislative Media Portal. The testing framework uses pytest to validate the API, database interaction, and cloud storage functionality.

## Test Structure

The tests are organized into two main categories:

- **Unit Tests**: Tests individual components in isolation using mocks
- **Integration Tests**: Tests components interacting with real external services

### Directory Structure

```
tests/
├── conftest.py          # Common fixtures and test configuration
├── unit/                # Unit tests that don't require external services
│   ├── test_api_endpoints.py      # Tests for API endpoints
│   ├── test_firestore_db.py       # Tests for Firestore database class
│   └── test_cloud_storage.py      # Tests for Cloud Storage class
└── integration/         # Integration tests that require external services
    └── test_api_integration.py    # Tests for API endpoints with real Firestore
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Unit Tests

```bash
pytest
```

### Run Unit Tests with Coverage Report

```bash
pytest --cov=src tests/unit/
```

### Run Integration Tests

Note: Integration tests require valid GCP credentials.

```bash
# Run all integration tests
pytest tests/integration/

# Or use the marker
pytest -m integration
```

### Run Specific Test File

```bash
pytest tests/unit/test_api_endpoints.py
```

### Run Specific Test Function

```bash
pytest tests/unit/test_api_endpoints.py::test_health_check
```

## Test Configuration

The pytest configuration is in the `pytest.ini` file at the project root. By default, integration tests are skipped to avoid requiring credentials for local development.

## Mocking Strategy

The unit tests use pytest fixtures to mock external services:

- `mock_firestore_db`: Mocks the Firestore database for testing the API without real database access
- `mock_db_app`: Uses the mock Firestore database to create a test client for the API
- `mock_storage_client`: Mocks the Google Cloud Storage client for testing without real storage access

## Integration Tests

The integration tests use real services and require proper credentials:

- `api_client`: A test client for the API that connects to the real Firestore database

Integration tests are automatically skipped if no credentials are available.

## Best Practices

1. Always run unit tests before committing changes
2. Make sure mocks accurately represent the real behavior
3. Validate changes with integration tests before deployment
4. Keep tests isolated from each other
5. Use markers to organize tests by category or speed
6. Create new mock data in the fixtures as needed
7. Add test coverage for new features and bug fixes