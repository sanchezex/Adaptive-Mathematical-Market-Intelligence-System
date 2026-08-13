#!/usr/bin/env bash
set -euo pipefail

# Minimal helper to install Kronos into the current Python environment.
# Usage: source .venv/bin/activate && bash scripts/install_kronos.sh

echo "Installing Kronos from GitHub (this may take a while)..."
pip install --upgrade pip
pip install git+https://github.com/shiyu-coder/Kronos.git

echo "Kronos installed. You can now use ammis.engines.kronos_adapter.KronosAdapter.load()"
