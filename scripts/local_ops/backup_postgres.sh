#!/bin/zsh
set -euo pipefail
umask 077

PROJECT="/Users/shivamsingh1208/ Python/pulseiq"
DOCKER="/Users/shivamsingh1208/.docker/bin/docker"

cd "$PROJECT"
mkdir -p backups/postgres

echo "[$(date)] Starting PulseIQ PostgreSQL backup."

"$DOCKER" compose ps --status running -q postgres | grep -q .

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
