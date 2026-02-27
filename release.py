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


def run_unit_tests():
    """Run unit tests"""
    print_step("Running Unit Tests")
    
    if not os.path.exists('test_sake.py'):
        print_error("test_sake.py not found")
        return False
    
    python_versions = []
    
    # Try to find multiple Python versions
    for version in ['3.12', '3.11', '3.10', '3.9', '3.8']:
        if shutil.which('python' + version):
            python_versions.append('python' + version)
    
    # Fallback to current Python
    if not python_versions:
        python_versions = [sys.executable]
    
    print("Testing with Python versions: " + ", ".join(python_versions))
    
    all_passed = True
    for python_cmd in python_versions:
        result = subprocess.run(
            [python_cmd, 'test_sake.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Unit tests passed with " + python_cmd)
        else:
            print_error("Unit tests failed with " + python_cmd)
            print(result.stdout)
            print(result.stderr)
            all_passed = False
    
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
    print_step("Uploading to PyPI")
    
    version = get_version()
    
    print(RED + "\n*** WARNING ***" + RESET)
    print("This will upload version " + version + " to PyPI (pypi.org)")
    print("This action CANNOT be undone!")
    print("Make sure you have:")
    print("  1. Updated the version in sakelib/constants.py")
    print("  2. Updated CHANGES file")
    print("  3. Committed and tagged the release")
    print("  4. Tested the packages")
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
