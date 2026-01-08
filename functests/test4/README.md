# Test4 - Simple Cross-Platform Functional Test

This is a simple functional test for sake that works across all platforms (Windows, Linux, macOS).

## Purpose

Tests basic sake functionality:
- Building targets with dependencies
- Recon mode (`-r` flag)
- Clean operation
- Help command
- Detecting when nothing needs to be rebuilt

## Why Cross-Platform?

Unlike test1, test2, and test3 which require Unix-specific tools (gcc, bash, sed, etc.), 
test4 uses only Python for all operations, making it work on any system with Python installed.

## Running the Test

```bash
cd functests/test4
python functest.py
```

## What It Tests

1. **Clean start** - Verifies clean removes all outputs
2. **Recon mode (clean state)** - Tests that `-r` shows what would be built
3. **Full build** - Builds all three targets and verifies outputs
4. **Recon mode (no changes)** - Verifies nothing shown when up-to-date
5. **Build with no changes** - Verifies no rebuilding when nothing changed
6. **Help command** - Tests help output
7. **Clean command** - Verifies clean removes all generated files

## Files

- `input.txt` - Simple input file
- `Sakefile.yaml` - Three-step build process using only Python commands
- `functest.py` - Test runner that validates sake behavior
- `README.md` - This file

## Expected Outputs (when running sake manually)

- `output1.txt` - Uppercase version of input
- `output2.txt` - Line count from output1
- `final.txt` - Combined output
