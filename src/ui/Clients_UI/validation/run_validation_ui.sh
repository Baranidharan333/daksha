#!/usr/bin/env bash
# Dataset validation UI — type a dataset path, press Run, read which episodes
# are wrong and why, with joint traces and the videos for any episode.
#
#   bash /home/physicalai/Desktop/I/ui/run_validation_ui.sh
#   PORT=9000 bash .../run_validation_ui.sh
#   TOKEN=mysecret bash .../run_validation_ui.sh      # require ?token=mysecret
#   HOST=127.0.0.1 bash .../run_validation_ui.sh      # this machine only
#   DATASET_PATH=/data/ds bash .../run_validation_ui.sh
#
# It binds every interface by default so you can open it from another machine;
# the script prints the exact URLs. Anyone who can reach the port can read any
# dataset under ALLOW_ROOT, so set TOKEN on a shared network.
set -euo pipefail

UI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${VENV:-$HOME/Desktop/I/grootn1.7/Isaac-GR00T/.venv}"

PORT="${PORT:-8124}"
HOST="${HOST:-0.0.0.0}"
TOKEN="${TOKEN:-}"
ALLOW_ROOT="${ALLOW_ROOT:-$HOME}"
DATASET_PATH="${DATASET_PATH:-/home/physicalai/Desktop/I/barani/pick_place_brown_300}"

# pyarrow/numpy live in the GR00T venv; fall back to whatever python is active.
if [ -f "$VENV/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
fi

# Free the port if a previous UI server is still holding it.
fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 1

exec python "$UI_DIR/validation_ui.py" \
  --host "$HOST" --port "$PORT" \
  --allow-root "$ALLOW_ROOT" \
  --dataset "$DATASET_PATH" \
  ${TOKEN:+--token "$TOKEN"}
