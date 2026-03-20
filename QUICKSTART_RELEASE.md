# Quick Start: Releasing sake to PyPI

## Prerequisites

```bash
pip install twine
```

## Option 1: Use the Release Script (Recommended)

### Test everything first:
```bash
python release.py --test
```

### Build packages:
```bash
python release.py --build
```

### Check package quality:
```bash
python release.py --check
```

### Test on TestPyPI (recommended before real release):
```bash
python release.py --test-pypi
```

Then test installing:
```bash
pip install --index-url https://test.pypi.org/simple/ master-sake
```

### Release to PyPI:
```bash
python release.py --release
```

### Or do everything in one go:
```bash
python release.py --full
```

## Option 2: Use Makefile Shortcuts

```bash
make test          # Run all tests
make build         # Build packages
make check         # Check quality
make test-release  # Upload to TestPyPI
make release       # Upload to PyPI
make quick-release # Test + build + check + release
```

## Option 3: Manual Process

```bash
# 1. Update version in sakelib/constants.py
# 2. Clean old builds
rm -rf build/ dist/ *.egg-info

# 3. Build
python setup.py sdist
python setup.py bdist_wheel  # if wheel is available

# 4. Check
python -m twine check dist/*

# 5. Upload to TestPyPI (optional)
python -m twine upload --repository testpypi dist/*

# 6. Upload to PyPI
python -m twine upload dist/*

# 7. Tag the release
git tag -a v1.3 -m "Release version 1.3"
git push origin v1.3
```

## PyPI Credentials

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

Get your tokens from:
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

## Help

For more details, see [RELEASE.md](RELEASE.md) or:
```bash
python release.py --help
```
