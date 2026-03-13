#!/usr/bin/env bash
set -euo pipefail

NAME=${1:-SafeNote}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller \
  --windowed \
  --name "$NAME" \
  --noconsole \
  --clean \
  safenote.py

echo ""
echo "Built: dist/$NAME.app"

