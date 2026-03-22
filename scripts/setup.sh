#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[setup] Installing dependencies"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "[setup] Creating required directories"
mkdir -p data auth_data logs

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "[setup] Created .env from .env.example"
else
  echo "[setup] .env already exists"
fi

echo "[setup] Verifying application import"
python3 -c "from app.main import app; print('Import OK:', app.title)"

echo "[setup] Done"