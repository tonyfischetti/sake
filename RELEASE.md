# Release Process for master-sake

This document describes how to create a new release of master-sake to PyPI.

## Prerequisites

1. **Install required tools:**
   ```bash
   pip install --upgrade build twine
   ```

2. **Configure PyPI credentials:**
   Create or edit `~/.pypirc`:
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-AgEIcHlwaS5vcmc...  # Your PyPI API token

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-AgENdGVzdC5weXBpLm9yZw...  # Your TestPyPI API token
   ```

   Or use environment variables:
   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...
   ```

## Quick Start

The easiest way to release is using the `release.py` script:

### Test Everything
```bash
python release.py --test
```

### Build Packages Only
```bash
python release.py --build
```

### Test Release on TestPyPI
```bash
python release.py --test-pypi
```

### Full Release to PyPI
```bash
python release.py --full
```

This will:
1. Run all tests
2. Build packages
3. Check package quality
4. Upload to PyPI
5. Create a git tag

## Manual Release Process

If you prefer to do it manually:

### 1. Update Version

Edit `sakelib/constants.py`:
```python
VERSION = "1.3"  # Update this
```

### 2. Update Changelog

Edit `CHANGES` file to document what's new.

### 3. Commit Changes

```bash
git add sakelib/constants.py CHANGES
git commit -m "Bump version to 1.3"
```

### 4. Run Tests

```bash
# Unit tests
python test_sake.py

# Functional tests
cd functests
python run_cross_platform_tests.py
cd ..
```

### 5. Clean Build Artifacts

```bash
rm -rf build/ dist/ *.egg-info
```

### 6. Build Distribution Packages

```bash
# Modern way (recommended)
python -m build

# Or legacy way
python setup.py sdist bdist_wheel
```

This creates:
- `dist/master-sake-1.3.tar.gz` (source distribution)
- `dist/master_sake-1.3-py3-none-any.whl` (wheel distribution)

### 7. Check Packages

```bash
python -m twine check dist/*
```

### 8. Test on TestPyPI (Optional but Recommended)

```bash
python -m twine upload --repository testpypi dist/*
```

Then test installing from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps master-sake
```

### 9. Upload to PyPI

```bash
python -m twine upload dist/*
```

### 10. Create Git Tag

```bash
git tag -a v1.3 -m "Release version 1.3"
git push origin v1.3
```

### 11. Create GitHub Release

Go to GitHub and create a release from the tag with release notes.

## Using the Release Script

The `release.py` script provides several options:

### Available Commands

```bash
# Show help
python release.py --help

# Run tests only
python release.py --test

# Build packages only
python release.py --build

# Check package quality
python release.py --check

# Upload to TestPyPI for testing
python release.py --test-pypi

# Upload to PyPI (production)
python release.py --release

# Full release workflow (test + build + release + tag)
python release.py --full

# Create git tag only
python release.py --tag

# Skip tests when building
python release.py --build --skip-tests
```

### Typical Workflow

1. **First, test everything:**
   ```bash
   python release.py --test
   ```

2. **Test on TestPyPI:**
   ```bash
   python release.py --build --test-pypi
   ```
   
   Then install and test:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ master-sake
   sake --help
   ```

3. **Release to production PyPI:**
   ```bash
   python release.py --release
   ```

4. **Create git tag:**
   ```bash
   python release.py --tag
   git push origin v1.3
   ```

Or do it all at once:
```bash
python release.py --full
git push origin v1.3
```

## CI/CD Automation

### GitHub Actions

The project includes GitHub Actions workflows:

- **`.github/workflows/tests.yml`** - Runs tests on every push/PR
- **`.github/workflows/release.yml`** - Automatically publishes to PyPI when you create a GitHub release

To use automatic releases:

1. Add your PyPI API token to GitHub Secrets:
   - Go to repository Settings → Secrets → Actions
   - Add new secret: `PYPI_API_TOKEN` with your PyPI token

2. Create a new release on GitHub:
   - Go to Releases → Draft a new release
   - Create a new tag (e.g., `v1.3`)
   - Fill in release notes
   - Publish release

The workflow will automatically build and publish to PyPI.

### Travis CI

The `.travis.yml` file is configured for Travis CI (legacy system).
It tests on Python 3.8-3.12 on Linux.

## Testing Multiple Python Versions Locally

### Using pyenv (Recommended)

```bash
# Install pyenv
curl https://pyenv.run | bash

# Install multiple Python versions
pyenv install 3.8.18
pyenv install 3.9.18
pyenv install 3.10.13
pyenv install 3.11.7
pyenv install 3.12.1

# Set local versions
pyenv local 3.8.18 3.9.18 3.10.13 3.11.7 3.12.1

# Run tests
python3.8 test_sake.py
python3.9 test_sake.py
python3.10 test_sake.py
python3.11 test_sake.py
python3.12 test_sake.py
```

### Using tox

Create a `tox.ini` file:
```ini
[tox]
envlist = py38,py39,py310,py311,py312

[testenv]
deps =
    networkx>=1.0
    PyYAML>=3.0
commands =
    python test_sake.py
    python functests/run_cross_platform_tests.py
```

Then run:
```bash
pip install tox
tox
```

## Troubleshooting

### "Upload failed: File already exists"

You can't upload the same version twice to PyPI. You need to:
1. Increment the version in `sakelib/constants.py`
2. Rebuild and re-upload

### "Invalid distribution file"

Make sure you're building with a recent version of setuptools:
```bash
pip install --upgrade setuptools wheel build
```

### "Authentication failed"

Check your PyPI credentials in `~/.pypirc` or environment variables.
Make sure you're using an API token, not a password.

## Checklist

Before releasing, make sure:

- [ ] Version updated in `sakelib/constants.py`
- [ ] `CHANGES` file updated with release notes
- [ ] All tests pass (`python release.py --test`)
- [ ] Git working directory is clean
- [ ] Changes committed to git
- [ ] Tested on TestPyPI (optional)
- [ ] Built and checked packages
- [ ] Uploaded to PyPI
- [ ] Created and pushed git tag
- [ ] Created GitHub release with notes

## Version Numbering

Follow semantic versioning (semver):
- **Major version** (X.0.0): Breaking changes
- **Minor version** (1.X.0): New features, backward compatible
- **Patch version** (1.2.X): Bug fixes

Examples:
- `1.2` → `1.3`: New features added
- `1.3` → `2.0`: Breaking API changes
- `1.3` → `1.3.1`: Bug fix only

## Links

- PyPI page: https://pypi.org/project/master-sake/
- TestPyPI page: https://test.pypi.org/project/master-sake/
- GitHub: https://github.com/tonyfischetti/sake
- Documentation: http://tonyfischetti.github.io/sake/
