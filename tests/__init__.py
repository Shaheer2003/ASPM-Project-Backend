"""
Tests Package

Contains all test modules for ASPM Backend API.

Test Organization:
- test_auth.py: Authentication and authorization tests
- test_admin.py: Admin endpoint tests
- test_teacher.py: Teacher endpoint tests
- test_student.py: Student endpoint tests
- test_shared.py: Shared endpoint and utility tests
- test_models.py: Database model unit tests
- test_utils.py: Utility function unit tests
- conftest.py: Pytest configuration and fixtures

Running Tests:
    pytest                          # Run all tests
    pytest -v                       # Verbose output
    pytest --cov=app               # With coverage report
    python test_runner.py          # Use test runner script
    pytest tests/test_auth.py       # Run specific file
    pytest -m auth                 # Run tests with marker
"""
