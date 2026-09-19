#!/bin/sh
set -eu
umask 077

R2_ENV=/etc/lowcost-europa/r2.env
PASSWORD_FILE=/etc/lowcost-europa/restic-password
LIVE_ENV=/etc/lowcost-europa/lowcost-europa.env
LOCK_FILE=/run/lock/lowcost-europa-restic.lock

check_root_secret() {
    path=$1
    [ -f "$path" ] && [ ! -L "$path" ] || exit 1
    [ "$(stat -c '%U:%G:%a' "$path")" = "root:root:600" ] || exit 1
}

check_root_secret "$R2_ENV"
check_root_secret "$PASSWORD_FILE"
[ -f "$LIVE_ENV" ] || { echo "Live application environment is missing" >&2; exit 1; }

live_db=$(sed -n 's/^POSTGRES_DB=//p' "$LIVE_ENV" | head -n 1)
[ -n "$live_db" ] || { echo "Live PostgreSQL database name is unavailable" >&2; exit 1; }

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
temp_db="lowcost_europa_restic_restore_$(date -u +%Y%m%d%H%M%S)_$$"
[ "$temp_db" != "$live_db" ] || { echo "Temporary database name matches live database" >&2; exit 1; }

db_created=0
cleanup() {
    status=$?
    trap - EXIT HUP INT TERM
    set +e
    db_dropped=NOT_CREATED
    if [ "$db_created" -eq 1 ]; then
        if runuser -u postgres -- dropdb --if-exists "$temp_db" >/dev/null 2>&1; then
            db_dropped=YES
        else
            db_dropped=NO
            status=1
        fi
    fi
    rm -rf "$target"
    [ ! -e "$target" ] && dir_removed=YES || { dir_removed=NO; status=1; }

    echo "TEMP DATABASE DROPPED=$db_dropped"
    echo "RESTORE TEMP DIRECTORY REMOVED=$dir_removed"
    if [ "$status" -eq 0 ]; then
        echo "LIVE DATABASE MODIFIED=NO"
    fi
    exit "$status"
}
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

runuser -u postgres -- createdb "$temp_db"
db_created=1
cat "$latest_dump" | runuser -u postgres -- pg_restore     --exit-on-error     --no-owner     --no-privileges     --dbname="$temp_db"

runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -d "$temp_db" -At <<'SQL' >/dev/null
SELECT 1 WHERE to_regclass('public.django_migrations') IS NOT NULL;
SELECT 1 WHERE to_regclass('public.catalog_productfamily') IS NOT NULL;
SELECT 1 WHERE to_regclass('public.catalog_offer') IS NOT NULL;
SELECT count(*) FROM django_migrations;
SELECT count(*) FROM catalog_productfamily;
SELECT count(*) FROM catalog_offer;
SQL

echo "POSTGRES TEMP RESTORE=PASS"
echo "DJANGO_MIGRATIONS=PRESENT"
echo "CORE CATALOG READ=PASS"
