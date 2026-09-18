#!/bin/sh
set -eu
umask 077

R2_ENV=/etc/lowcost-europa/r2.env
PASSWORD_FILE=/etc/lowcost-europa/restic-password
LOCK_FILE=/run/lock/lowcost-europa-restic.lock

check_root_secret() {
    path=$1
    [ -f "$path" ] && [ ! -L "$path" ] || exit 1
    [ "$(stat -c '%U:%G:%a' "$path")" = "root:root:600" ] || exit 1
}

check_root_secret "$R2_ENV"
check_root_secret "$PASSWORD_FILE"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "Another Restic operation is already running" >&2
    exit 75
fi

set -a
. "$R2_ENV"
set +a
export RESTIC_PASSWORD_FILE="$PASSWORD_FILE"
: "${AWS_ACCESS_KEY_ID:?R2 access key is not configured}"
: "${AWS_SECRET_ACCESS_KEY:?R2 secret key is not configured}"
: "${RESTIC_REPOSITORY:?Restic repository is not configured}"

target=$(mktemp -d /tmp/lowcost-europa-restic-restore.XXXXXX)
cleanup() { rm -rf "$target"; }
trap cleanup EXIT HUP INT TERM

restic restore latest     --tag lowcost-europa     --tag offsite     --target "$target"     --no-cache >/dev/null

restored_backup_dir="$target/var/backups/lowcost-europa/daily"
restored_env="$target/etc/lowcost-europa/lowcost-europa.env"
[ -f "$restored_env" ] || { echo "Restored application environment is missing" >&2; exit 1; }

latest_dump=$(find "$restored_backup_dir" -maxdepth 1 -type f -name '*.dump' -printf '%T@ %p\n' |
    sort -nr | head -n 1 | cut -d' ' -f2-)
[ -n "$latest_dump" ] && [ -s "$latest_dump" ] || {
    echo "Restored PostgreSQL dump is missing or empty" >&2
    exit 1
}

sidecar="$latest_dump.sha256"
[ -f "$sidecar" ] || { echo "Restored checksum sidecar is missing" >&2; exit 1; }
(
    cd "$restored_backup_dir"
    sha256sum -c "$(basename "$sidecar")" >/dev/null
)
pg_restore --list "$latest_dump" >/dev/null

echo "Offsite restore drill passed without touching the live database"
