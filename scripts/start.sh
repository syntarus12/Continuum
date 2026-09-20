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

compose_args=( -f docker-compose.yml )
if [ -f "../backend/Dockerfile" ]; then
  compose_args+=( -f docker-compose.source.yml )
  echo "Using the sibling MemoryOS backend source for this monorepo checkout."
fi
docker compose "${compose_args[@]}" --profile ui up -d --pull missing || {
  echo "The published backend/console image could not be pulled." >&2
  echo "Make the GHCR packages public or set SYNTARUS_*_IMAGE in .env." >&2
  exit 1
}
"$PWD/scripts/doctor.sh"
echo "Continuum is ready: http://127.0.0.1:${CONSOLE_PORT:-5173}"
