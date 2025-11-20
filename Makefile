.PHONY: help setup install install-dev clean test lint format build upload docs

help:
	@echo "Available commands:"
	@echo "  make setup         - Setup venv and install package in development mode"
	@echo "  make install       - Install package in production mode"
	@echo "  make install-dev   - Install package in development mode with dev dependencies"
	@echo "  make clean         - Remove build artifacts and cache files"
	@echo "  make test          - Run tests with pytest"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make lint          - Run linters (flake8, mypy)"
	@echo "  make format        - Format code with black and isort"
	@echo "  make build         - Build distribution packages"
	@echo "  make upload        - Upload package to PyPI"
	@echo "  make upload-test   - Upload package to TestPyPI"

setup:
	@echo "Setting up virtual environment..."
	python3 -m venv venv
	@echo "Installing package in development mode..."
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -e ".[dev]"
	@echo ""
	@echo "✅ Setup complete! Activate the virtual environment with:"
	@echo "   source venv/bin/activate"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

test:
	pytest -v

test-cov:
	pytest --cov=swarm --cov-report=html --cov-report=term

lint:
	flake8 swarm/ --max-line-length=100 --exclude=__pycache__
	mypy swarm/ --ignore-missing-imports

format:
	black swarm/ examples/
	isort swarm/ examples/

build: clean
	python setup.py sdist bdist_wheel

upload: build
	twine upload dist/*

upload-test: build
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Run examples
example-market-maker:
	python examples/example_market_maker.py

example-cross-chain-access:
	python examples/example_cross_chain_access.py

example-trading:
	python examples/example_trading.py

example-errors:
	python examples/example_error_handling.py
