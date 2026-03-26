.PHONY: help test clean build check release install dev-install

help:
	@echo "Sake Release Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make test          - Run all tests"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make build         - Build distribution packages"
	@echo "  make check         - Check package quality"
	@echo "  make test-release  - Upload to TestPyPI"
	@echo "  make release       - Upload to PyPI"
	@echo "  make install       - Install sake locally"
	@echo "  make dev-install   - Install in development mode"
	@echo ""
	@echo "Or use the release.py script for more control:"
	@echo "  python release.py --help"

test:
	@echo "Running unit tests..."
	python test_sake.py
	@echo "Running functional tests..."
	cd functests && python run_cross_platform_tests.py

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info master_sake.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	@echo "Building distribution packages..."
	python -m build

check: build
	@echo "Checking package quality..."
	python -m twine check dist/*

test-release: check
	@echo "Uploading to TestPyPI..."
	python -m twine upload --repository testpypi dist/*

release: check
	@echo "Uploading to PyPI..."
	python -m twine upload dist/*

install:
	@echo "Installing sake..."
	pip install .

dev-install:
	@echo "Installing sake in development mode..."
	pip install -e .

# Quick release workflow
quick-release: test build check release
	@echo "Release complete!"
