#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Desktop/Engine is required. Install Docker, then run this command again." >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env with safe localhost defaults. Add SARVAM_API_KEY or GEMINI_API_KEY for ingestion."
fi

docker compose --profile ui up -d --pull missing
"$PWD/scripts/doctor.sh"
echo "Continuum is ready: http://127.0.0.1:${CONSOLE_PORT:-5173}"
