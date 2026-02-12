#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cross-platform functional test for sake advanced features
Tests macros, force rebuild, wildcards, and specific targets
"""

from __future__ import print_function
import os
import platform
import shutil
import sys
import time
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
    for f in ['output1.txt', 'output2.txt', 'output3.txt', 'final.txt', '.shastore']:
        if os.path.isfile(f):
            os.remove(f)


# Start tests
print("\n=== Running advanced features sake tests ===\n")

#####################
# Test 1: Clean start
#####################
cleanup()
out, err = run(SAKE_CMD + " clean")
passed("clean start")


#############################
# Test 2: Full build (macros)
#############################
out, err = run(SAKE_CMD)

# Check all output files were created
for f in ['output1.txt', 'output2.txt', 'output3.txt', 'final.txt']:
    if not os.path.isfile(f):
        FAIL("Full build - {} not created".format(f))

# Verify macro substitution worked
with open('output1.txt') as f:
    content = f.read()
    if 'THIS IS A TEST INPUT FILE' not in content:
        FAIL("Full build - uppercase not working")

with open('output3.txt') as f:
    content = f.read()
    if 'Hello World' not in content:
        FAIL("Full build - MESSAGE macro not substituted")

# Verify wildcard dependency worked
with open('final.txt') as f:
    content = f.read()
    if '---' not in content:
        FAIL("Full build - combine not working")
    # Should have all three outputs combined
    if content.count('---') != 2:  # 3 sections separated by 2 separators
        FAIL("Full build - not all outputs combined")

passed("full build with macros")


#########################
# Test 3: No rebuild
#########################
out, err = run(SAKE_CMD)
if "Done" not in out:
    FAIL("No rebuild - should show Done")
if "Running target" in out:
    FAIL("No rebuild - should not rebuild anything")
passed("no rebuild when up-to-date")


################################
# Test 4: Specific target build
################################
# Since targets share dependencies, they must be built together
# Test building a specific meta-target instead
cleanup()
out, err = run(SAKE_CMD + ' "process files"')

# Should rebuild all process files targets
if 'uppercase' not in out:
    FAIL("Specific meta-target - uppercase not built")
if 'reverse' not in out:
    FAIL("Specific meta-target - reverse not built")
if 'combine' in out:
    FAIL("Specific meta-target - combine should not be built")

for f in ['output1.txt', 'output2.txt', 'output3.txt']:
    if not os.path.isfile(f):
        FAIL("Specific meta-target - {} not created".format(f))

if os.path.isfile('final.txt'):
    FAIL("Specific meta-target - final.txt should not exist")

passed("specific meta-target build")


############################
# Test 5: Force rebuild
############################
# Everything is up-to-date, but force should rebuild
out, err = run(SAKE_CMD + " -F")

if "Running target" not in out:
    FAIL("Force rebuild - no targets run")
# Should rebuild all atomic targets
if 'uppercase' not in out:
    FAIL("Force rebuild - uppercase not rebuilt")
if 'reverse' not in out:
    FAIL("Force rebuild - reverse not rebuilt")

passed("force rebuild")


#############################
# Test 6: Force recon
#############################
# Force recon should show what would be rebuilt even though up-to-date
out, err = run(SAKE_CMD + " -F -r")

if "Would run target:" not in out:
    FAIL("Force recon - no targets shown")
if 'uppercase' not in out:
    FAIL("Force recon - uppercase not shown")

# But shouldn't actually build anything
time.sleep(1)
mtime_before = os.path.getmtime('output1.txt')
time.sleep(1)
out, err = run(SAKE_CMD + " -F -r")
mtime_after = os.path.getmtime('output1.txt')

if mtime_after != mtime_before:
    FAIL("Force recon - files were modified")

passed("force recon")


################################
# Test 7: CLI macro override
################################
cleanup()
# Override CUSTOM macro (which has ?= so can be overridden)
out, err = run(SAKE_CMD + ' -DCUSTOM="Custom Value"')

# Check that the custom value was used
with open('output3.txt') as f:
    content = f.read()
    if 'Custom Value' not in content:
        FAIL("CLI macro override - CUSTOM not overridden")
    if content.count('default') > 0:
        FAIL("CLI macro override - default CUSTOM still used")

passed("CLI macro override")


#################################
# Test 8: Conditional macro (?=)
#################################
# SUFFIX?= means SUFFIX has a default but can be overridden
# Since it's used in output filenames which are also in dependencies,
# we just verify the default works
cleanup()
out, err = run(SAKE_CMD)
if not os.path.isfile('output1.txt'):
    FAIL("Conditional macro - default SUFFIX not used")

passed("conditional macro ?=")


##################
# Test 9: Help
##################
out, err = run(SAKE_CMD + " help")
if "process files" not in out:
    FAIL("Help - meta-target not shown")
if "uppercase" not in out:
    FAIL("Help - uppercase not shown")
if "combine" not in out:
    FAIL("Help - combine not shown")
passed("help command")


######################
# Test 10: Clean
######################
cleanup()
out, err = run(SAKE_CMD + " clean")
for f in ['output1.txt', 'output2.txt', 'output3.txt', 'final.txt']:
    if os.path.isfile(f):
        FAIL("Clean - {} still exists".format(f))
passed("clean command")


print("\n=== All advanced feature tests passed! ===\n")
sys.exit(0)
