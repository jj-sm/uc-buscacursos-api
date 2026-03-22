#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${API_URL:-0.0.0.0}"
PORT="${API_PORT:-8000}"

export DEBUG=1
exec uvicorn app.main:app --reload --host "$HOST" --port "$PORT"