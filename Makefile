.PHONY: help install install-dev clean test lint format build upload docs

help:
	@echo "Available commands:"
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
	pytest --cov=shared --cov=market_maker_sdk --cov=cross_chain_access_sdk --cov=trading_sdk --cov-report=html --cov-report=term

lint:
	flake8 shared/ market_maker_sdk/ cross_chain_access_sdk/ trading_sdk/ --max-line-length=100 --exclude=__pycache__
	mypy shared/ market_maker_sdk/ cross_chain_access_sdk/ trading_sdk/ --ignore-missing-imports

format:
	black shared/ market_maker_sdk/ cross_chain_access_sdk/ trading_sdk/ examples/
	isort shared/ market_maker_sdk/ cross_chain_access_sdk/ trading_sdk/ examples/

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
