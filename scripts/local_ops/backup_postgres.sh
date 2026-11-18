#!/bin/zsh
set -euo pipefail
umask 077

PROJECT="/Users/shivamsingh1208/ Python/pulseiq"
DOCKER="/Users/shivamsingh1208/.docker/bin/docker"

cd "$PROJECT"
mkdir -p backups/postgres

echo "[$(date)] Starting PulseIQ PostgreSQL backup."

# Start Docker Desktop if it is not already available.
echo "[$(date)] Requesting Docker Desktop startup."
open -gj -a Docker >/dev/null 2>&1 || true

# Wait up to 10 minutes for the Docker daemon.
DOCKER_READY=0
for attempt in {1..60}; do
  if "$DOCKER" info >/dev/null 2>&1; then
    DOCKER_READY=1
    break
  fi
  echo "[$(date)] Waiting for Docker daemon ($attempt/60)..."
  sleep 10
done

if [[ "$DOCKER_READY" -ne 1 ]]; then
  echo "[$(date)] ERROR: Docker daemon unavailable after 10 minutes."
  exit 1
fi

# Wait up to 10 minutes for the PostgreSQL service.
POSTGRES_READY=0
for attempt in {1..60}; do
  if "$DOCKER" compose exec -T postgres sh -c \
    'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
    POSTGRES_READY=1
    break
  fi
  echo "[$(date)] Waiting for PostgreSQL ($attempt/60)..."
  sleep 10
done

if [[ "$POSTGRES_READY" -ne 1 ]]; then
  echo "[$(date)] ERROR: PostgreSQL unavailable after 10 minutes."
  exit 1
fi

echo "[$(date)] Docker and PostgreSQL are ready."

STAMP=$(date +%Y%m%d_%H%M%S)
FINAL="backups/postgres/pulseiq_${STAMP}.dump"
TEMP="${FINAL}.tmp"
LIST="${FINAL}.list.tmp"

cleanup() {
  rm -f "$TEMP" "$LIST"
}
trap cleanup EXIT

"$DOCKER" compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "$TEMP"

test -s "$TEMP"

"$DOCKER" compose exec -T postgres pg_restore --list \
  < "$TEMP" > "$LIST"

test -s "$LIST"
chmod 600 "$TEMP"
mv "$TEMP" "$FINAL"
rm -f "$LIST"

find backups/postgres -type f -name 'pulseiq_*.dump' -mtime +14 -delete

echo "[$(date)] Backup verified: $FINAL"
ls -lh "$FINAL"
echo "[$(date)] Backup job completed."
