#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_DIR="$(cd "$DB_DIR/.." && pwd)"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

DATABASE_URL="${DATABASE_URL:?DATABASE_URL is not set}"

atlas migrate apply \
  --dir "file://${DB_DIR}/migrations" \
  --url "$DATABASE_URL"

echo "Migrations applied successfully."
