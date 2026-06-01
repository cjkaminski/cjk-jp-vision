#!/usr/bin/env bash
# Start the server. Reads .env if present.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "Creating virtualenv (.venv)…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q -r requirements.txt

echo "Starting cjk-jp-vision…"
python -m app.main
