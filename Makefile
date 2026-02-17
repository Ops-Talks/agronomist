.PHONY: help build clean build-docker run-tests lint format

help:
	@echo "Agronomist - Available targets:"
	@echo "  make build          - Build package locally with Poetry"
	@echo "  make build-docker   - Build package in Docker container"
	@echo "  make clean          - Remove dist/ and build artifacts"
	@echo "  make lint           - Run linters (ruff, black)"
	@echo "  make format         - Format code"
	@echo "  make test           - Run tests"
	@echo "  make check          - Run linters + tests"
	@echo "  make docs-serve     - Serve documentation locally"
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

pre-commit:
	poetry run task pre-commit
