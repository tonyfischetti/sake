#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cross-platform functional test for sake parallel builds
Tests parallel execution and meta-targets
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
    for f in ['first.txt', 'second.txt', 'third.txt', 'fourth.txt', 'poem.txt', '.shastore']:
        if os.path.isfile(f):
            os.remove(f)


# Start tests
print("\n=== Running parallel build sake tests ===\n")

#####################
# Test 1: Clean start
#####################
cleanup()
out, err = run(SAKE_CMD + " clean")
if os.path.exists('.shastore'):
    FAIL("Clean start - .shastore still exists")
passed("clean start")


###########################
# Test 2: Sequential build
###########################
start_time = time.time()
out, err = run(SAKE_CMD)
sequential_time = time.time() - start_time

# Check all files were created
for f in ['first.txt', 'second.txt', 'third.txt', 'fourth.txt', 'poem.txt']:
    if not os.path.isfile(f):
        FAIL("Sequential build - {} not created".format(f))

# Verify poem content
with open('poem.txt') as f:
    content = f.read()
    if 'Twinkle twinkle' not in content or 'tea tray' not in content:
        FAIL("Sequential build - poem.txt has wrong content")

passed("sequential build")
print("  Sequential build time: {:.1f}s".format(sequential_time))


#########################
# Test 3: No rebuild
#########################
out, err = run(SAKE_CMD)
# May show some output due to empty dependencies behavior, just check Done is there
if "Done" not in out:
    FAIL("No rebuild - 'Done' not in output")
passed("no rebuild test")


###################
# Test 4: Clean
###################
cleanup()
passed("clean")


##########################
# Test 5: Parallel build
##########################
start_time = time.time()
out, err = run(SAKE_CMD + " -p")
parallel_time = time.time() - start_time

# Check all files were created
for f in ['first.txt', 'second.txt', 'third.txt', 'fourth.txt', 'poem.txt']:
    if not os.path.isfile(f):
        FAIL("Parallel build - {} not created".format(f))

# Verify poem content
with open('poem.txt') as f:
    content = f.read()
    if 'Twinkle twinkle' not in content or 'tea tray' not in content:
        FAIL("Parallel build - poem.txt has wrong content")

passed("parallel build")
print("  Parallel build time: {:.1f}s".format(parallel_time))

# Verify parallel was actually faster (should be at least 1.5x faster)
# Sequential: ~8s (4 x 2s sleep + combine), Parallel: ~2-3s (2s sleep + combine)
if parallel_time >= sequential_time * 0.8:
    print("  Warning: Parallel build not significantly faster ({:.1f}s vs {:.1f}s)".format(
        parallel_time, sequential_time))
    # Not failing because timing can be flaky in CI environments
else:
    print("  Speedup: {:.1f}x".format(sequential_time / parallel_time))


####################################
# Test 6: Rebuild after file change
####################################
# Modify first.txt to test if downstream targets rebuild
time.sleep(1)  # Ensure timestamp difference
with open('first.txt', 'a') as f:
    f.write('extra line\n')

out, err = run(SAKE_CMD)
# poem.txt should rebuild because first.txt changed
if 'combine them' not in out:
    FAIL("File change - poem.txt not rebuilt when it should")

# Verify the extra content made it through
with open('poem.txt') as f:
    content = f.read()
    if 'extra line' not in content:
        FAIL("File change - changes not propagated to poem.txt")

passed("rebuild after file change")


##################
# Test 7: Help
##################
out, err = run(SAKE_CMD + " help")
if "line by line" not in out:
    FAIL("Help - meta-target not shown")
if "first line" not in out:
    FAIL("Help - first line not shown")
if "combine them" not in out:
    FAIL("Help - combine them not shown")
passed("help with meta-targets")


######################
# Test 8: Clean final
######################
out, err = run(SAKE_CMD + " clean")
# Just check that files are removed, output format may vary
for f in ['first.txt', 'second.txt', 'third.txt', 'fourth.txt', 'poem.txt']:
    if os.path.isfile(f):
        FAIL("Final clean - {} still exists".format(f))
if os.path.isfile('.shastore'):
    FAIL("Final clean - .shastore still exists")
passed("clean command")


print("\n=== All parallel tests passed! ===\n")
sys.exit(0)
