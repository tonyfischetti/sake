# Test6 - Cross-Platform Advanced Features Test

This test verifies advanced sake features using only Python.

## Purpose

Tests advanced sake functionality:
- Macro definitions and substitution (#!)
- Conditional macros with ?= operator  
- Force rebuild with -f flag
- Recon with force (-f -r)
- Specific target selection
- Wildcard outputs
- Meta-targets

## Why Cross-Platform?

Uses only Python for all operations, making it work on any system with Python installed.

## Running the Test

```bash
cd functests/test6
python functest.py
```

## What It Tests

1. **Macro substitution** - Tests #! macro definitions
2. **Conditional macros** - Tests ?= operator (set if not already set)
3. **Force rebuild** - Tests -f flag forces rebuild even when up-to-date
4. **Force recon** - Tests -f -r combination
5. **Specific targets** - Tests building individual targets
6. **Wildcard outputs** - Tests output glob patterns
7. **CLI macro override** - Tests -D flag to override macros

## Files

- `input.txt` - Input file
- `Sakefile.yaml` - Build process with macros and meta-targets
- `functest.py` - Test runner
- `README.md` - This file
