#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -d "$REPO_ROOT/.venv" ]]; then
  echo "Missing $REPO_ROOT/.venv" >&2
  echo "Create it with: python3.13 -m venv .venv && source .venv/bin/activate && python -m pip install -r requirements.txt" >&2
  exit 1
fi

source "$REPO_ROOT/.venv/bin/activate"

export PYTHONUNBUFFERED=1
export PYTORCH_ENABLE_MPS_FALLBACK="${PYTORCH_ENABLE_MPS_FALLBACK:-1}"

HOST="${COMFYUI_HOST:-127.0.0.1}"
PORT="${COMFYUI_PORT:-8188}"

exec python main.py \
  --listen "$HOST" \
  --port "$PORT" \
  --disable-auto-launch \
  --preview-method auto \
  --cpu-vae \
  --cache-none \
  "$@"
