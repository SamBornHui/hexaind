# Makefile for hexaind_backend testing

# Python interpreter
PYTHON := python3

# Test directories
TEST_DIR := app/tests
UNIT_TEST_DIRS := app/tests/core app/tests/services app/tests/utils app/tests/workers
API_TEST_DIR := app/tests/api
APPHUB_TEST_DIR := app/tests/api/v1/apphub

# Test commands
PYTEST := pytest
PYTEST_OPTS := --verbose

# Backend URL
BACKEND_URL := http://localhost:8080

.PHONY: all test unit-test integration-test apphub-test clean swagger

# Default target
all: test

# Run all tests
test:
	$(PYTEST) $(PYTEST_OPTS) $(TEST_DIR)

# Run only unit tests
unit-test:
	$(PYTEST) $(PYTEST_OPTS) $(UNIT_TEST_DIRS)

# Run only API/integration tests
integration-test:
	$(PYTEST) $(PYTEST_OPTS) $(API_TEST_DIR)

# Run only AppHub tests
apphub-test:
	$(PYTEST) $(PYTEST_OPTS) $(APPHUB_TEST_DIR)

# Run tests with coverage report
test-coverage:
	$(PYTEST) $(PYTEST_OPTS) --cov=app --cov-report=html --cov-report=term $(TEST_DIR)

# Run tests with HTML report
test-report:
	$(PYTEST) $(PYTEST_OPTS) --html=app/tests/report.html $(TEST_DIR)

# Open Swagger UI in default browser
swagger:
	open $(BACKEND_URL)/docs

# Clean up
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	# Clean up test-generated JSON files
	find app/tests -name "*_preview.json" -delete
	find app/tests -name "*_column_metadata.json" -delete
	find app/tests -name "*_categorical_stats.json" -delete
	find app/tests -name "*_numerical_stats.json" -delete 