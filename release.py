#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Release script for master-sake

This script automates the release process:
1. Runs tests on multiple Python versions (using tox or manual checks)
2. Builds distribution packages
3. Uploads to PyPI (or TestPyPI for testing)

Usage:
    python release.py --test          # Run tests only
    python release.py --build         # Build packages only
    python release.py --test-pypi     # Upload to TestPyPI
    python release.py --release       # Full release to PyPI
    python release.py --help          # Show help
"""

from __future__ import print_function
import argparse
import os
import subprocess
import sys
import shutil

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Use simple ASCII for Windows compatibility
CHECK = 'OK'
CROSS = 'FAIL'
WARNING = 'WARN'

# PyPI package URL
PYPI_URL = 'https://pypi.org/project/master-sake/'


def print_step(message):
    """Print a step message"""
    print("\n" + BLUE + "=" * 70)
    print(message)
    print("=" * 70 + RESET)


def print_success(message):
    """Print a success message"""
    print(GREEN + "[" + CHECK + "] " + message + RESET)


def print_error(message):
    """Print an error message"""
    print(RED + "[" + CROSS + "] " + message + RESET, file=sys.stderr)


def print_warning(message):
    """Print a warning message"""
    print(YELLOW + "[" + WARNING + "] " + message + RESET)


def run_command(cmd, description, cwd=None, check=True):
    """Run a command and return the result"""
    print("\n" + YELLOW + "Running: " + RESET + cmd)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success(description + " succeeded")
            return True
        else:
            print_error(description + " failed")
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print_error(description + " failed with error code " + str(e.returncode))
        if e.stderr:
            print(e.stderr)
        return False
    except Exception as e:
        print_error(description + " failed: " + str(e))
        return False


def check_prerequisites():
    """Check if required tools are installed"""
    print_step("Checking Prerequisites")
    
    required_tools = {
        'python': 'Python',
        'pip': 'pip',
        'git': 'Git',
    }
    
    missing = []
    for cmd, name in required_tools.items():
        if not shutil.which(cmd):
            print_error(name + " not found")
            missing.append(name)
        else:
            print_success(name + " found")
    
    if missing:
        print_error("Missing required tools: " + ", ".join(missing))
        return False
    
    return True


def check_git_status(skip_check=False):
    """Check if git working directory is clean"""
    print_step("Checking Git Status")
    
    if skip_check:
        print_warning("Skipping git status check")
        return True
    
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print_warning("Git working directory is not clean:")
        print(result.stdout)
        try:
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != 'y':
                print_error("Aborted by user")
                return False
        except (EOFError, KeyboardInterrupt):
            print_error("\nAborted by user")
            return False
    else:
        print_success("Git working directory is clean")
    
    return True


def get_version():
    """Get the current version from constants.py"""
    from sakelib import constants
    return constants.VERSION


def check_version_updated():
    """Check if version-related files have been updated"""
    version = get_version()
    
    # Check if CHANGES file contains the current version
    if os.path.exists('CHANGES'):
        with open('CHANGES', 'r') as f:
            changes_content = f.read()
            if version not in changes_content:
                print_warning("Current version " + version + " not found in CHANGES file")
                return False
            else:
                print_success("CHANGES file contains version " + version)
    else:
        print_warning("CHANGES file not found")
        return False
    
    # Check if there are uncommitted changes to important files
    result = subprocess.run(
        ['git', 'diff', '--name-only', 'sakelib/constants.py', 'CHANGES'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        print_warning("Uncommitted changes to: " + result.stdout.strip())
        return False
    
    print_success("Version files appear to be committed")
    return True


def discover_python_versions():
    """Discover all installed Python versions"""
    python_versions = []
    
    # Check for Python 2.x versions (legacy support)
    for minor in range(4, 8):  # 2.4 to 2.7
        for cmd in ['python2.' + str(minor), 'python2' + str(minor)]:
            if shutil.which(cmd):
                python_versions.append(cmd)
                break
    
    # Check for Python 3.x versions
    for minor in range(4, 20):  # 3.4 to 3.19 (future-proof)
        for cmd in ['python3.' + str(minor), 'python3' + str(minor)]:
            if shutil.which(cmd):
                python_versions.append(cmd)
                break
    
    # Also check simple 'python', 'python2', 'python3'
    for cmd in ['python', 'python2', 'python3']:
        if shutil.which(cmd) and cmd not in python_versions:
            python_versions.append(cmd)
    
    # Remove duplicates by checking actual executable paths
    unique_versions = []
    seen_paths = set()
    
    for cmd in python_versions:
        try:
            result = subprocess.run(
                [cmd, '-c', 'import sys; print(sys.executable)'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                exe_path = result.stdout.strip()
                if exe_path not in seen_paths:
                    seen_paths.add(exe_path)
                    # Get version string
                    ver_result = subprocess.run(
                        [cmd, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    version_str = ver_result.stdout.strip() or ver_result.stderr.strip()
                    unique_versions.append((cmd, version_str, exe_path))
        except (subprocess.TimeoutExpired, Exception):
            continue
    
    return unique_versions


def save_tested_versions(tested_versions):
    """Save tested Python versions to a file for reference"""
    with open('TESTED_PYTHON_VERSIONS.txt', 'w') as f:
        f.write("# Python versions tested by release.py --test\n")
        f.write("# Generated on: " + subprocess.run(['date'], capture_output=True, text=True, shell=True).stdout.strip() + "\n")
        f.write("# This serves as the single source of truth for supported Python versions\n")
        f.write("#\n")
        f.write("# Format: command | version string | executable path | test result\n")
        f.write("#\n\n")
        
        for cmd, version_str, status in tested_versions:
            f.write(cmd + " | " + version_str + " | " + status + "\n")
    
    print_success("Tested versions saved to TESTED_PYTHON_VERSIONS.txt")


def run_unit_tests():
    """Run unit tests on all discovered Python versions"""
    print_step("Running Unit Tests")
    
    if not os.path.exists('test_sake.py'):
        print_error("test_sake.py not found")
        return False
    
    print_step("Discovering Python Versions")
    discovered = discover_python_versions()
    
    if not discovered:
        print_warning("No Python versions found in PATH, using current interpreter")
        discovered = [(sys.executable, sys.version, sys.executable)]
    
    print("\nDiscovered Python installations:")
    for cmd, version_str, exe_path in discovered:
        print("  " + cmd + " -> " + version_str)
    print()
    
    all_passed = True
    tested_versions = []
    
    for cmd, version_str, exe_path in discovered:
        result = subprocess.run(
            [cmd, 'test_sake.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Unit tests passed with " + cmd + " (" + version_str + ")")
            tested_versions.append((cmd, version_str, "PASSED"))
        else:
            print_error("Unit tests failed with " + cmd + " (" + version_str + ")")
            print(result.stdout)
            print(result.stderr)
            tested_versions.append((cmd, version_str, "FAILED"))
            all_passed = False
    
    # Save tested versions to file
    save_tested_versions(tested_versions)
    
    # Print summary
    print_step("Python Version Test Summary")
    passed = sum(1 for _, _, status in tested_versions if status == "PASSED")
    failed = sum(1 for _, _, status in tested_versions if status == "FAILED")
    
    print("Total tested: " + str(len(tested_versions)))
    print("Passed: " + str(passed))
    print("Failed: " + str(failed))
    print()
    print("Supported versions (PASSED):")
    for cmd, version_str, status in tested_versions:
        if status == "PASSED":
            # Extract version number for setup.py format
            import re
            match = re.search(r'(\d+)\.(\d+)', version_str)
            if match:
                major, minor = match.groups()
                print("  Python " + major + "." + minor)
    
    return all_passed


def run_functional_tests():
    """Run cross-platform functional tests"""
    print_step("Running Functional Tests")
    
    test_script = os.path.join('functests', 'run_cross_platform_tests.py')
    
    if not os.path.exists(test_script):
        print_warning("Cross-platform test runner not found, skipping")
        return True
    
    return run_command(
        sys.executable + ' ' + test_script,
        "Functional tests",
        cwd='functests'
    )


def clean_build_artifacts():
    """Clean build artifacts"""
    print_step("Cleaning Build Artifacts")
    
    dirs_to_remove = ['build', 'dist', '*.egg-info', 'master_sake.egg-info']
    
    for pattern in dirs_to_remove:
        if '*' in pattern:
            import glob
            for path in glob.glob(pattern):
                if os.path.isdir(path):
                    print("Removing " + path)
                    shutil.rmtree(path)
        else:
            if os.path.isdir(pattern):
                print("Removing " + pattern)
                shutil.rmtree(pattern)
    
    print_success("Build artifacts cleaned")
    return True


def build_packages():
    """Build source and wheel distributions"""
    print_step("Building Distribution Packages")
    
    # Clean first
    clean_build_artifacts()
    
    # Install build tools if needed
    print("Installing/upgrading build tools...")
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--upgrade', 'setuptools', 'wheel'],
        check=False,
        capture_output=True
    )
    
    # Build using legacy method (more reliable across environments)
    if not run_command(
        sys.executable + ' setup.py sdist',
        "Building source distribution"
    ):
        return False
    
    if not run_command(
        sys.executable + ' setup.py bdist_wheel',
        "Building wheel distribution"
    ):
        print_warning("Wheel build failed, but source distribution was created")
    
    # Check what was built
    if os.path.exists('dist'):
        files = os.listdir('dist')
        print("\nBuilt packages:")
        for f in files:
            print("  - " + f)
        print_success("Packages built successfully")
        return True
    else:
        print_error("dist/ directory not found")
        return False


def check_packages():
    """Check the built packages"""
    print_step("Checking Package Quality")
    
    if not os.path.exists('dist'):
        print_error("No dist/ directory found. Run build first.")
        return False
    
    # Try to install twine if needed
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--upgrade', 'twine'],
        check=False,
        capture_output=True
    )
    
    return run_command(
        sys.executable + ' -m twine check dist/*',
        "Package quality check"
    )


def upload_to_test_pypi():
    """Upload to TestPyPI"""
    print_step("Uploading to TestPyPI")
    
    print_warning("This will upload to TestPyPI (test.pypi.org)")
    print_warning("Make sure you have credentials configured in ~/.pypirc")
    print()
    
    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print_error("Aborted by user")
        return False
    
    return run_command(
        sys.executable + ' -m twine upload --repository testpypi dist/*',
        "Upload to TestPyPI"
    )


def upload_to_pypi():
    """Upload to PyPI"""
    print_step("Uploading to PyPI (" + PYPI_URL + ")")
    
    version = get_version()
    
    # Automated pre-release checks
    print_step("Pre-Release Verification")
    
    checks_passed = True
    
    # Check if version files are updated
    if not check_version_updated():
        checks_passed = False
    
    # Check git status
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print_warning("There are uncommitted changes in the repository")
        checks_passed = False
    else:
        print_success("No uncommitted changes")
    
    # Check if packages exist and have been checked
    if not os.path.exists('dist'):
        print_error("No dist/ directory found. Run --build first.")
        return False
    
    dist_files = os.listdir('dist')
    if not dist_files:
        print_error("No packages found in dist/. Run --build first.")
        return False
    
    print_success("Packages found: " + ", ".join(dist_files))
    
    if not checks_passed:
        print()
        print_warning("Some pre-release checks failed!")
        try:
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != 'y':
                print_error("Aborted by user")
                return False
        except (EOFError, KeyboardInterrupt):
            print_error("\nAborted by user")
            return False
    
    # Final confirmation
    print(RED + "\n*** WARNING ***" + RESET)
    print("This will upload version " + version + " to PyPI")
    print("URL: " + PYPI_URL)
    print("This action CANNOT be undone!")
    print()
    
    response = input("Type the version number to confirm: ")
    if response != version:
        print_error("Version mismatch. Aborted.")
        return False
    
    return run_command(
        sys.executable + ' -m twine upload dist/*',
        "Upload to PyPI"
    )


def create_git_tag():
    """Create a git tag for the release"""
    version = get_version()
    tag = 'v' + version
    
    print_step("Creating Git Tag")
    
    # Check if tag exists
    result = subprocess.run(
        ['git', 'tag', '-l', tag],
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print_warning("Tag " + tag + " already exists")
        response = input("Overwrite? [y/N]: ")
        if response.lower() == 'y':
            run_command(
                'git tag -d ' + tag,
                "Deleting existing tag"
            )
        else:
            return True
    
    if run_command(
        'git tag -a ' + tag + ' -m "Release version ' + version + '"',
        "Creating tag " + tag
    ):
        print()
        print("To push the tag, run:")
        print("  git push origin " + tag)
        return True
    
    return False


def main():
    parser = argparse.ArgumentParser(
        description='Release script for master-sake',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python release.py --test              Run all tests
  python release.py --build             Build packages
  python release.py --check             Check package quality
  python release.py --test-pypi         Upload to TestPyPI
  python release.py --release           Full release to PyPI
  python release.py --full              Run tests, build, and release
        """
    )
    
    parser.add_argument('--test', action='store_true',
                        help='Run tests only')
    parser.add_argument('--build', action='store_true',
                        help='Build packages only')
    parser.add_argument('--check', action='store_true',
                        help='Check package quality')
    parser.add_argument('--test-pypi', action='store_true',
                        help='Upload to TestPyPI')
    parser.add_argument('--release', action='store_true',
                        help='Upload to PyPI')
    parser.add_argument('--full', action='store_true',
                        help='Run tests, build, check, and release')
    parser.add_argument('--tag', action='store_true',
                        help='Create git tag')
    parser.add_argument('--skip-tests', action='store_true',
                        help='Skip running tests')
    parser.add_argument('--skip-git-check', action='store_true',
                        help='Skip git status check')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Answer yes to all prompts (non-interactive mode)')
    
    args = parser.parse_args()
    
    # If no args, show help
    if not any(vars(args).values()):
        parser.print_help()
        return 1
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Show current version
    version = get_version()
    print("\n" + BLUE + "Current version: " + version + RESET + "\n")
    
    # Run tests
    if args.test or args.full:
        if not check_git_status(skip_check=args.skip_git_check):
            return 1
        
        if not run_unit_tests():
            print_error("Unit tests failed")
            return 1
        
        if not run_functional_tests():
            print_error("Functional tests failed")
            return 1
    
    # Build packages
    if args.build or args.full or args.test_pypi or args.release:
        if not args.skip_tests and not args.full:
            print_warning("Building without running tests (use --test first)")
        
        if not build_packages():
            print_error("Package build failed")
            return 1
    
    # Check packages
    if args.check or args.full or args.test_pypi or args.release:
        if not check_packages():
            print_error("Package check failed")
            return 1
    
    # Upload to TestPyPI
    if args.test_pypi:
        if not upload_to_test_pypi():
            print_error("Upload to TestPyPI failed")
            return 1
    
    # Upload to PyPI
    if args.release or args.full:
        if not upload_to_pypi():
            print_error("Upload to PyPI failed")
            return 1
        
        print_success("\n*** Release successful! ***\n")
        
        # Offer to create tag
        if args.tag or args.full:
            create_git_tag()
    
    # Just create tag
    if args.tag and not (args.release or args.full):
        create_git_tag()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
