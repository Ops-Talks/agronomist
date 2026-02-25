.PHONY: help build clean build-docker run-tests lint format test-workflows test-unit test-integration install-test-deps

help:
	@echo "Agronomist - Available targets:"
	@echo "  make build              - Build package locally with Poetry"
	@echo "  make build-docker       - Build package in Docker container"
	@echo "  make clean              - Remove dist/ and build artifacts"
	@echo "  make lint               - Run linters (ruff, black)"
	@echo "  make format             - Format code"
	@echo "  make test               - Run tests"
	@echo "  make test-workflows     - Run workflow tests (unit + integration)"
	@echo "  make test-unit          - Run workflow unit tests"
	@echo "  make test-integration   - Run workflow integration tests"
	@echo "  make install-test-deps  - Install workflow test dependencies"
	@echo "  make check              - Run linters + tests"
	@echo "  make docs-serve         - Serve documentation locally"
	@echo "  make release TAG=v0.3.0 - Create Git tag and trigger release"

build:
	poetry build

build-docker:
	@rm -rf dist/ 2>/dev/null || true
	docker build --no-cache -t agronomist-build .
	docker create --name agronomist-tmp agronomist-build
	docker cp agronomist-tmp:/build/dist . 
	docker rm agronomist-tmp
	@echo "✓ Build complete!"
	@ls -lh dist/

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

lint:
	poetry run task lint

format:
	poetry run task format

test:
	poetry run task test

check:
	poetry run task check

docs-serve:
	poetry run mkdocs serve

release:
	@if [ -z "$(TAG)" ]; then \
		echo "Error: TAG not specified. Use: make release TAG=v0.3.0"; \
		exit 1; \
	fi
	git tag $(TAG)
	git push origin $(TAG)
	@echo "Release $(TAG) triggered!"

install-dev:
	poetry install --with dev

install-test-deps:
	@echo "Installing workflow test dependencies..."
	@if ! command -v bats &> /dev/null; then \
		echo "Installing bats-core..."; \
		if command -v brew &> /dev/null; then \
			brew install bats-core; \
		elif command -v apt-get &> /dev/null; then \
			sudo apt-get update && sudo apt-get install -y bats; \
		else \
			echo "Please install bats-core manually: https://github.com/bats-core/bats-core"; \
			exit 1; \
		fi \
	fi
	@if ! command -v jq &> /dev/null; then \
		echo "Installing jq..."; \
		if command -v brew &> /dev/null; then \
			brew install jq; \
		elif command -v apt-get &> /dev/null; then \
			sudo apt-get update && sudo apt-get install -y jq; \
		else \
			echo "Please install jq manually"; \
			exit 1; \
		fi \
	fi
	@echo "Workflow test dependencies installed successfully!"

test-unit:
	@echo "Running workflow unit tests..."
	@bats test/unit/*.bats

test-integration:
	@echo "Running workflow integration tests..."
	@bash test/integration/test_multi_pr_flow.sh

test-workflows: test-unit test-integration
	@echo ""
	@echo "All workflow tests passed!"

pre-commit:
	poetry run task pre-commit
