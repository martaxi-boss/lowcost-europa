#!/bin/sh
set -eu
umask 077

R2_ENV=/etc/lowcost-europa/r2.env
PASSWORD_FILE=/etc/lowcost-europa/restic-password
LOCK_FILE=/run/lock/lowcost-europa-restic.lock
MAX_SNAPSHOT_AGE_SECONDS=129600

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

snapshot_json=$(restic snapshots --json --latest 1 --tag lowcost-europa --tag offsite --no-cache)
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
echo "Offsite Restic repository health check passed"
