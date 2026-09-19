#!/bin/sh
set -eu
umask 077

R2_ENV=/etc/lowcost-europa/r2.env
PASSWORD_FILE=/etc/lowcost-europa/restic-password
APP_ENV=/etc/lowcost-europa/lowcost-europa.env
BACKUP_DIR=/var/backups/lowcost-europa/daily
LOCK_FILE=/run/lock/lowcost-europa-restic.lock
STATE_DIR=/var/lib/lowcost-europa
SUCCESS_MARKER=$STATE_DIR/offsite-backup.last-success
MAX_DUMP_AGE_SECONDS=21600

check_root_secret() {
    path=$1
    [ -f "$path" ] && [ ! -L "$path" ] || {
        echo "Required secret file is missing or unsafe: $path" >&2
        exit 1
    }
    [ "$(stat -c '%U:%G:%a' "$path")" = "root:root:600" ] || {
        echo "Secret file permissions invalid: $path" >&2
        exit 1
    }
}

check_root_secret "$R2_ENV"
check_root_secret "$PASSWORD_FILE"
[ -f "$APP_ENV" ] || { echo "Application environment file missing" >&2; exit 1; }
[ -d "$BACKUP_DIR" ] || { echo "Local backup directory missing" >&2; exit 1; }

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

latest_dump=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.dump' -printf '%T@ %p\n' |
    sort -nr | head -n 1 | cut -d' ' -f2-)
[ -n "$latest_dump" ] || { echo "No local PostgreSQL dump found" >&2; exit 1; }
[ -s "$latest_dump" ] || { echo "Latest PostgreSQL dump is empty" >&2; exit 1; }

sidecar="$latest_dump.sha256"
[ -f "$sidecar" ] || { echo "Checksum sidecar missing for latest dump" >&2; exit 1; }
(
    cd "$BACKUP_DIR"
    sha256sum -c "$(basename "$sidecar")" >/dev/null
) || { echo "Latest PostgreSQL dump checksum failed" >&2; exit 1; }

now=$(date +%s)
dump_mtime=$(stat -c '%Y' "$latest_dump")
dump_age=$((now - dump_mtime))
[ "$dump_age" -ge 0 ] || { echo "Latest dump timestamp is in the future" >&2; exit 1; }
[ "$dump_age" -le "$MAX_DUMP_AGE_SECONDS" ] || {
    echo "Latest PostgreSQL dump is older than the 6-hour freshness window" >&2
    exit 1
}

restic backup     "$BACKUP_DIR"     "$APP_ENV"     --tag lowcost-europa     --tag offsite     --tag disaster-recovery     --host lowcost-europa-droplet     --no-cache

snapshot_json=$(restic snapshots --json --latest 1     --tag lowcost-europa,offsite --host lowcost-europa-droplet --no-cache)
snapshot_id=$(printf '%s' "$snapshot_json" | python3 -c '
import json, sys
data = json.load(sys.stdin)
if not data:
    raise SystemExit("No matching offsite snapshot found after backup")
print(data[-1]["short_id"])
')
restic check --no-cache >/dev/null

restic forget     --tag lowcost-europa,offsite     --group-by host,paths     --keep-daily 7     --keep-weekly 4     --keep-monthly 3     --no-cache

restic check --no-cache >/dev/null
restic prune --no-cache
restic check --no-cache >/dev/null

install -d -o root -g root -m 0700 "$STATE_DIR"
timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - "$SUCCESS_MARKER" "$timestamp" "$snapshot_id" <<'PY'
import os
import sys
import tempfile

marker, timestamp, snapshot_id = sys.argv[1:]
directory = os.path.dirname(marker)
fd, tmp = tempfile.mkstemp(prefix=".offsite-backup.last-success.", dir=directory)
try:
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f"timestamp={timestamp}\nsnapshot={snapshot_id}\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, marker)
    dirfd = os.open(directory, os.O_DIRECTORY)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)
finally:
    if os.path.exists(tmp):
        os.unlink(tmp)
PY

echo "Offsite Restic backup, retention and prune completed successfully"
