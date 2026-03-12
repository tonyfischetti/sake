#!/usr/bin/env bash
# release.sh - Sets up a release venv with twine and runs release.py
set -e

VENV_DIR=".release-venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating release venv in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate"

pip install --quiet --upgrade pip setuptools wheel twine

python release.py "$@"
