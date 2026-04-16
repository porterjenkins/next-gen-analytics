#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
NAME=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --name)
      NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [ -z "$NAME" ]; then
  echo "Usage: $0 --name <migration_name>"
  exit 1
fi

DEV_CONTAINER="atlas-dev-db"
DEV_PORT=15432

# Start a temporary pgvector container for diffing
docker run --rm -d \
  --name "$DEV_CONTAINER" \
  -e POSTGRES_USER=dev \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=dev \
  -p "${DEV_PORT}:5432" \
  pgvector/pgvector:pg16 > /dev/null

# Wait for Postgres to be ready
until docker exec "$DEV_CONTAINER" pg_isready -U dev -q 2>/dev/null; do
  sleep 0.5
done

# Enable vector extension on dev DB
docker exec "$DEV_CONTAINER" psql -U dev -d dev -c "CREATE EXTENSION IF NOT EXISTS vector;" > /dev/null

cleanup() {
  docker stop "$DEV_CONTAINER" > /dev/null 2>&1 || true
}
trap cleanup EXIT

atlas migrate diff "$NAME" \
  --dir "file://${DB_DIR}/migrations" \
  --to "file://${DB_DIR}/schema.pg.hcl" \
  --dev-url "postgresql://dev:dev@localhost:${DEV_PORT}/dev?search_path=public&sslmode=disable"

echo "Migration generated: $NAME"
