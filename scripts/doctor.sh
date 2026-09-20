#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
docker compose config --quiet
docker compose ps

api_url="http://127.0.0.1:${API_PORT:-8000}"
for _ in $(seq 1 30); do
  if curl -fsS "$api_url/health" >/tmp/continuum-health.json 2>/dev/null; then
    echo "API health: $(cat /tmp/continuum-health.json)"
    if curl -fsS "$api_url/ready" >/tmp/continuum-ready.json 2>/dev/null; then
      echo "API ready: $(cat /tmp/continuum-ready.json)"
      exit 0
    fi
  fi
  sleep 2
done

echo "Continuum did not become ready. Inspect logs with: docker compose logs --tail=200 backend" >&2
exit 1
