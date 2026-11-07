#!/usr/bin/env python3
"""Refresh DB-IP Country Lite (CC BY 4.0) inside this project, not system-wide."""

import gzip
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import maxminddb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = PROJECT_ROOT / ".geoip"
DESTINATION = DB_DIR / "dbip-country-lite.mmdb"
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_DATABASE_BYTES = 64 * 1024 * 1024


def release_months():
    now = datetime.now(UTC)
    previous_year = now.year if now.month > 1 else now.year - 1
    previous_month = now.month - 1 if now.month > 1 else 12
    return (f"{now.year}-{now.month:02d}", f"{previous_year}-{previous_month:02d}")


def download_release(release, archive):
    url = f"https://download.db-ip.com/free/dbip-country-lite-{release}.mmdb.gz"
    request = Request(url, headers={"User-Agent": "Lowcost-Europa-country-db/1"})
    count = 0
    with urlopen(request, timeout=60) as source, archive.open("wb") as target:
        while block := source.read(1024 * 1024):
            count += len(block)
            if count > MAX_ARCHIVE_BYTES:
                raise ValueError("Country MMDB archive exceeds safety limit")
            target.write(block)


def decompress_and_verify(archive, database):
    count = 0
    with gzip.open(archive, "rb") as source, database.open("wb") as target:
        while block := source.read(1024 * 1024):
            count += len(block)
            if count > MAX_DATABASE_BYTES:
                raise ValueError("Country MMDB exceeds safety limit")
            target.write(block)

    with maxminddb.open_database(str(database)) as reader:
        record = reader.get("8.8.8.8") or {}
        if record.get("country", {}).get("iso_code") != "US":
            raise ValueError("Unexpected country database schema or invalid contents")


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".dbip-update-", dir=DB_DIR) as name:
        folder = Path(name)
        last_error = None
        for release in release_months():
            archive = folder / "source.mmdb.gz"
            database = folder / "dbip-country-lite.mmdb"
            try:
                download_release(release, archive)
                decompress_and_verify(archive, database)
            except (HTTPError, URLError, OSError, ValueError, EOFError) as exc:
                last_error = f"{release}: {type(exc).__name__}"
                continue
            database.chmod(0o644)
            os.replace(database, DESTINATION)
            print(f"COUNTRY_DB_READY release={release} path={DESTINATION}")
            return
    raise SystemExit(f"Country database update failed ({last_error})")


if __name__ == "__main__":
    main()
