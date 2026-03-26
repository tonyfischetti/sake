# Test5 - Cross-Platform Parallel Build Test

This test verifies parallel build functionality using only Python.

## Purpose

Tests sake's parallel build features:
- Parallel execution with `-p` flag
- Meta-targets with multiple atomic targets
- Empty dependencies field behavior (not rebuilding every time)
- Combining multiple outputs
- Speed improvement with parallel builds

## Why Cross-Platform?

Uses Python's time.sleep() instead of Unix sleep command, making it work on all platforms.

## Running the Test

```bash
cd functests/test5
python functest.py
```

## What It Tests

1. **Sequential build** - Builds all targets sequentially, measures time
2. **Parallel build** - Builds with -p flag, should be faster
3. **No rebuild** - Verifies targets with empty dependencies don't rebuild
4. **Combined output** - Tests combining multiple input files
5. **Help for meta-targets** - Verifies help works with grouped targets

## Files

- `Sakefile.yaml` - Four parallel tasks that can be run simultaneously
- `functest.py` - Test runner that validates sake parallel behavior
- `README.md` - This file
