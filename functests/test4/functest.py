#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple cross-platform functional test for sake
Tests basic build, recon, and clean functionality
"""

from __future__ import print_function
import os
import platform
import shutil
import sys
from subprocess import Popen, PIPE
import locale

# Change to test directory
here = os.path.dirname(__file__)
if here:
    os.chdir(here)

# Determine sake command based on platform
if platform.system() == 'Windows':
    SAKE_CMD = 'python ../../sake'
else:
    SAKE_CMD = '../../sake'


def run(command):
    """Run a command and return stdout, stderr"""
    encoding = locale.getpreferredencoding()
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    # Normalize line endings for cross-platform compatibility
    out_str = out.decode(encoding).replace('\r\n', '\n')
    err_str = err.decode(encoding).replace('\r\n', '\n')
    return out_str, err_str


def FAIL(message):
    """Print failure message and exit"""
    sys.stderr.write("\033[91mFAILED: " + message + "\033[0m\n")
    sys.exit(1)


def passed(test_name):
    """Print success message"""
    print("{:>45} {:>15}".format(test_name, "\033[92mpassed\033[0m"))


def cleanup():
    """Remove all generated files"""
    for f in ['output1.txt', 'output2.txt', 'final.txt', '.shastore']:
        if os.path.isfile(f):
            os.remove(f)


# Start tests
print("\n=== Running simple cross-platform sake tests ===\n")

#####################
# Test 1: Clean start
#####################
cleanup()
out, err = run(SAKE_CMD + " clean")
if os.path.exists('.shastore'):
    FAIL("Clean start - .shastore still exists")
passed("clean start")


#####################
# Test 2: Recon mode
#####################
out, err = run(SAKE_CMD + " -r")
expected = """Would run target: step1
Would run target: step2
Would run target: step3
"""
if out != expected:
    print("Expected:")
    print(repr(expected))
    print("\nGot:")
    print(repr(out))
    FAIL("recon mode output mismatch")
# Verify no files were created during recon
if os.path.isfile('output1.txt') or os.path.isfile('output2.txt') or os.path.isfile('final.txt'):
    FAIL("recon mode created files")
passed("recon mode (clean state)")


#########################
# Test 3: Full build
#########################
out, err = run(SAKE_CMD)
if "Running target step1" not in out:
    FAIL("full build - step1 not run")
if "Running target step2" not in out:
    FAIL("full build - step2 not run")
if "Running target step3" not in out:
    FAIL("full build - step3 not run")
if "Done" not in out:
    FAIL("full build - did not complete")

# Verify outputs were created
if not os.path.isfile('output1.txt'):
    FAIL("full build - output1.txt not created")
if not os.path.isfile('output2.txt'):
    FAIL("full build - output2.txt not created")
if not os.path.isfile('final.txt'):
    FAIL("full build - final.txt not created")

# Verify output1.txt content
with open('output1.txt') as f:
    content = f.read()
    if "HELLO WORLD" not in content:
        FAIL("full build - output1.txt has wrong content")

# Verify output2.txt content
with open('output2.txt') as f:
    content = f.read()
    if "Lines: 2" not in content:
        FAIL("full build - output2.txt has wrong content")

# Verify final.txt combines both
with open('final.txt') as f:
    content = f.read()
    if "Lines: 2" not in content or "HELLO WORLD" not in content:
        FAIL("full build - final.txt has wrong content")

passed("full build")


##############################
# Test 4: Recon after build
##############################
out, err = run(SAKE_CMD + " -r")
# Should show nothing needs to be built
if out.strip():
    FAIL("recon after build - should be empty but got: " + repr(out))
passed("recon mode (no changes)")


#################################
# Test 5: Build with no changes
#################################
out, err = run(SAKE_CMD)
if out != "Done\n":
    FAIL("build with no changes - should only show 'Done'")
passed("build with no changes")


######################
# Test 6: Help
######################
out, err = run(SAKE_CMD + " help")
if "step1" not in out:
    FAIL("help - step1 not shown")
if "step2" not in out:
    FAIL("help - step2 not shown")
if "step3" not in out:
    FAIL("help - step3 not shown")
if "create a simple output file from input" not in out:
    FAIL("help - step1 help text not shown")
passed("help command")


######################
# Test 7: Clean
######################
out, err = run(SAKE_CMD + " clean")
if out != "All clean\n":
    FAIL("clean - unexpected output: " + repr(out))
if os.path.isfile('output1.txt') or os.path.isfile('output2.txt') or os.path.isfile('final.txt'):
    FAIL("clean - output files still exist")
if os.path.isfile('.shastore'):
    FAIL("clean - .shastore still exists")
passed("clean command")


print("\n=== All tests passed! ===\n")
sys.exit(0)
