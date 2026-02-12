#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run all cross-platform sake tests
This script runs all OS-independent tests
"""

from __future__ import print_function
import os
import sys
import subprocess
import platform

# Test directories (OS-independent only)
TESTS = [
    ('test4', 'Simple cross-platform functional test'),
    ('test5', 'Parallel build testing'),
    ('test6', 'Advanced features testing'),
]

def run_test(test_dir, description):
    """Run a test and return True if it passes"""
    print("\n" + "="*70)
    print("Running: {} - {}".format(test_dir, description))
    print("="*70)
    
    test_path = os.path.join(os.path.dirname(__file__), test_dir)
    functest = os.path.join(test_path, 'functest.py')
    
    if not os.path.exists(functest):
        print("SKIP: {} does not exist".format(functest))
        return None
    
    try:
        result = subprocess.call([sys.executable, functest], cwd=test_path)
        return result == 0
    except Exception as e:
        print("ERROR: Failed to run test: {}".format(e))
        return False


def main():
    print("\n" + "="*70)
    print("Cross-Platform Sake Test Suite")
    print("Platform: {}".format(platform.platform()))
    print("Python: {}".format(sys.version))
    print("="*70)
    
    results = {}
    for test_dir, description in TESTS:
        result = run_test(test_dir, description)
        results[test_dir] = result
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    for test_dir, result in results.items():
        if result is True:
            status = "\033[92mPASSED\033[0m"
        elif result is False:
            status = "\033[91mFAILED\033[0m"
        else:
            status = "\033[93mSKIPPED\033[0m"
        print("{:20} {}".format(test_dir, status))
    
    print("\nTotal: {} passed, {} failed, {} skipped".format(passed, failed, skipped))
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n\033[92mAll tests passed!\033[0m\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
