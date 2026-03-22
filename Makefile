SHELL := /bin/bash

.PHONY: help chmod-scripts setup run run-dev verify test test-health test-coverage docker-build docker-up docker-down clean

help:
	@echo "Available targets:"
	@echo "  make chmod-scripts   - Make all scripts executable"
	@echo "  make setup           - Install dependencies and initialize environment"
	@echo "  make run             - Run API in normal mode"
	@echo "  make run-dev         - Run API in development mode with reload"
	@echo "  make verify          - Verify API health and endpoints (requires running server)"
	@echo "  make test            - Run full test suite"
	@echo "  make test-health     - Run only health tests"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make docker-build    - Build local Docker image"
	@echo "  make docker-up       - Start containers with docker compose"
	@echo "  make docker-down     - Stop containers"
	@echo "  make clean           - Remove generated test and cache artifacts"

chmod-scripts:
	chmod +x scripts/*.sh

setup: chmod-scripts
	./scripts/setup.sh

run: chmod-scripts
	./scripts/run.sh

run-dev: chmod-scripts
	./scripts/run-dev.sh

verify: chmod-scripts
	./scripts/verify.sh

test: chmod-scripts
	./scripts/test.sh

test-health: chmod-scripts
	./scripts/test.sh -m health -v

test-coverage: chmod-scripts
	./scripts/test-coverage.sh

docker-build: chmod-scripts
	./scripts/docker-build.sh universal-api:local

docker-up: chmod-scripts
	./scripts/docker-up.sh

docker-down: chmod-scripts
	./scripts/docker-down.sh

clean:
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
