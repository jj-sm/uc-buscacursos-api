#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export DEBUG=1

if [[ $# -gt 0 ]]; then
  exec pytest "$@"
else
  exec pytest test/ -v
fi