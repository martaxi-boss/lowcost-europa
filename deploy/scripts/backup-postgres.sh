#!/bin/sh
set -eu

ENV_FILE=/etc/lowcost-europa/lowcost-europa.env
BACKUP_DIR=/var/backups/lowcost-europa/daily

set -a
. "$ENV_FILE"
set +a

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
final="$BACKUP_DIR/lowcost-europa-$timestamp.dump"
tmp="$final.tmp"

runuser -u postgres -- pg_dump -Fc "$POSTGRES_DB" > "$tmp"
chmod 600 "$tmp"
sha256sum "$tmp" > "$tmp.sha256"
chmod 600 "$tmp.sha256"
mv "$tmp" "$final"
mv "$tmp.sha256" "$final.sha256"

find "$BACKUP_DIR" -type f \( -name '*.dump' -o -name '*.sha256' \) -mtime +6 -delete
