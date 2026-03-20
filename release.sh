#!/usr/bin/env bash
# release.sh - Sets up a release venv with twine and runs release.py
set -e

VENV_DIR=".release-venv"
PYTHON="${PYTHON:-python}"

# Determine activate script path (Windows uses Scripts/, Unix uses bin/)
ACTIVATE="$VENV_DIR/bin/activate"
[ -f "$VENV_DIR/Scripts/activate" ] && ACTIVATE="$VENV_DIR/Scripts/activate"

if [ ! -f "$ACTIVATE" ]; then
    echo "Creating release venv in $VENV_DIR ..."
    rm -rf "$VENV_DIR"
    "$PYTHON" -m venv --without-pip --system-site-packages "$VENV_DIR"
    # Refresh activate path after creation
    ACTIVATE="$VENV_DIR/bin/activate"
    [ -f "$VENV_DIR/Scripts/activate" ] && ACTIVATE="$VENV_DIR/Scripts/activate"
    # shellcheck disable=SC1090
    source "$ACTIVATE"
    python -m ensurepip --upgrade
else
    # shellcheck disable=SC1090
    source "$ACTIVATE"
fi

pip install --quiet --upgrade pip setuptools wheel twine
pip install --quiet -r requirements.txt

python release.py "$@"
