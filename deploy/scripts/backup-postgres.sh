#!/bin/sh
set -eu
umask 077

ENV_FILE=/srv/projects/lowcost-europa/private/systemd-env/lowcost-europa.env
BACKUP_DIR=/srv/projects/lowcost-europa/backups/daily

set -a
. "$ENV_FILE"
set +a

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
final="$BACKUP_DIR/lowcost-europa-$timestamp.dump"
tmp="$final.tmp"
tmp_sidecar="$final.sha256.tmp"
cleanup() {
    rm -f "$tmp" "$tmp_sidecar"
}
trap cleanup EXIT HUP INT TERM

runuser -u postgres -- pg_dump -Fc "$POSTGRES_DB" > "$tmp"
chmod 600 "$tmp"
mv "$tmp" "$final"
(
    cd "$BACKUP_DIR"
    sha256sum "$(basename "$final")" > "$(basename "$tmp_sidecar")"
)
chmod 600 "$tmp_sidecar"
mv "$tmp_sidecar" "$final.sha256"

trap - EXIT HUP INT TERM
find "$BACKUP_DIR" -type f \( -name '*.dump' -o -name '*.sha256' \) -mtime +6 -delete
