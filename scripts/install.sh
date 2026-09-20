#!/usr/bin/env bash
set -euo pipefail

repo_url="${CONTINUUM_REPO_URL:-https://github.com/syntarus12/Continuum.git}"
target_dir="${1:-continuum}"

if [ -e "$target_dir" ]; then
  echo "Target already exists: $target_dir" >&2
  exit 1
fi

git clone --depth 1 "$repo_url" "$target_dir"
cd "$target_dir"
./scripts/start.sh
