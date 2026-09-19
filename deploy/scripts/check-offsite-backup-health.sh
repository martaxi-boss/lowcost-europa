#!/bin/sh
set -eu
umask 077

R2_ENV=/etc/lowcost-europa/r2.env
PASSWORD_FILE=/etc/lowcost-europa/restic-password
LOCK_FILE=/run/lock/lowcost-europa-restic.lock
SUCCESS_MARKER=/var/lib/lowcost-europa/offsite-backup.last-success
MAX_SNAPSHOT_AGE_SECONDS=129600
MAX_MARKER_AGE_SECONDS=129600

check_root_secret() {
    path=$1
    [ -f "$path" ] && [ ! -L "$path" ] || exit 1
    [ "$(stat -c '%U:%G:%a' "$path")" = "root:root:600" ] || exit 1
}

check_root_secret "$R2_ENV"
check_root_secret "$PASSWORD_FILE"
[ -f "$SUCCESS_MARKER" ] && [ ! -L "$SUCCESS_MARKER" ] || {
    echo "Offsite success marker is missing or unsafe" >&2
    exit 1
}
[ "$(stat -c '%U:%G:%a' "$SUCCESS_MARKER")" = "root:root:600" ] || {
    echo "Offsite success marker permissions are invalid" >&2
    exit 1
}

python3 - "$SUCCESS_MARKER" "$MAX_MARKER_AGE_SECONDS" <<'PY'
import datetime
import sys

marker, max_age = sys.argv[1], int(sys.argv[2])
values = {}
with open(marker, encoding="utf-8") as handle:
    for line in handle:
        key, _, value = line.strip().partition("=")
        if key and value:
            values[key] = value
stamp = values.get("timestamp")
if not stamp:
    raise SystemExit("Offsite success marker has no timestamp")
created = datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
age = (datetime.datetime.now(datetime.timezone.utc) - created).total_seconds()
if age < 0 or age > max_age:
    raise SystemExit("Offsite success marker is outside the 36-hour health window")
PY

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

snapshot_json=$(restic snapshots --json --latest 1     --tag lowcost-europa --tag offsite --host lowcost-europa-droplet --no-cache)
printf '%s' "$snapshot_json" | python3 -c '
import datetime, json, sys
max_age = int(sys.argv[1])
data = json.load(sys.stdin)
if not data:
    raise SystemExit("No offsite snapshot found")
created = datetime.datetime.fromisoformat(data[-1]["time"].replace("Z", "+00:00"))
age = (datetime.datetime.now(datetime.timezone.utc) - created).total_seconds()
if age < 0 or age > max_age:
    raise SystemExit("Latest offsite snapshot is outside the 36-hour health window")
' "$MAX_SNAPSHOT_AGE_SECONDS"

restic check --no-cache >/dev/null
echo "Offsite Restic marker, snapshot and repository health check passed"
