"""Notify only verified public sitemap changes; no cookies, credentials or click routes."""

import fcntl
import hashlib
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

ENDPOINT = "https://api.indexnow.org/indexnow"
PUBLIC_PATH = re.compile(
    r"^/(?:|como-funciona/|afiliados/|privacidade/|termos/|contacto/|products/[a-z0-9-]+/)$"
)
CSRF_INPUT = re.compile(r'<input\b[^>]*\bname=[\"\']csrfmiddlewaretoken[\"\'][^>]*>', re.I)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url, payload=None):
    request = Request(url, data=payload, headers={
        "User-Agent": "LowcostEuropa-IndexNow/1.0",
        "Accept-Language": "en",
        **({"Content-Type": "application/json; charset=utf-8"} if payload else {}),
    })
    # Do not follow a poisoned sitemap or a changed endpoint to another host.
    with build_opener(NoRedirect).open(request, timeout=15) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise CommandError("IndexNow response exceeds safety limit")
        return response.status, response.headers, body


class PageMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href"))
        if tag == "meta" and attrs.get("name", "").lower() in ("robots", "bingbot"):
            self.noindex |= "noindex" in attrs.get("content", "").lower()


def valid_url(url, base):
    parsed = urlsplit(url)
    return bool(
        url.startswith(base + "/") and not parsed.query and not parsed.fragment
        and PUBLIC_PATH.fullmatch(parsed.path)
    )


def snapshot(base):
    status, _, xml = fetch(base + "/sitemap.xml")
    if status != 200:
        raise CommandError("Sitemap is not available")
    urls = [node.text for node in ElementTree.fromstring(xml).findall(
        "{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
    )]
    if not urls or len(urls) > 100 or len(urls) != len(set(urls)):
        raise CommandError("Invalid sitemap size or duplicate URLs")
    result = {}
    for url in urls:
        if not isinstance(url, str) or not valid_url(url, base):
            raise CommandError("Sitemap contains a non-public or noncanonical URL")
        status, headers, html = fetch(url)
        page = PageMetadata()
        text = html.decode("utf-8")
        page.feed(text)
        if (status != 200 or page.noindex or "noindex" in headers.get("X-Robots-Tag", "").lower()
                or page.canonicals != [url]):
            raise CommandError("Public page failed indexing checks")
        # Django masks this token differently on every anonymous render.
        result[url] = hashlib.sha256(CSRF_INPUT.sub("", text).encode()).hexdigest()
    return result


class Command(BaseCommand):
    help = "Submit new/changed/removed public pages to IndexNow; accepted is not indexed."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        base = settings.PUBLIC_SITE_URL
        public = urlsplit(base)
        if (not settings.PUBLIC_INDEXING_ENABLED or public.scheme != "https"
                or not public.hostname or public.netloc != public.hostname or public.path
                or not all(settings.PUBLIC_OPERATOR.get(k) for k in ("name", "address", "tax_id"))
                or not re.fullmatch(r"[a-f0-9]{32}", settings.INDEXNOW_KEY)):
            raise CommandError("Public indexing and private IndexNow configuration required")
        directory = Path(settings.BASE_DIR) / ".indexnow"
        directory.mkdir(mode=0o700, exist_ok=True)
        with (directory / "notify.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self.stdout.write("INDEXNOW_BUSY")
                return
            try:
                self.notify(base, directory, options["dry_run"])
            except (HTTPError, URLError, OSError, ValueError, ElementTree.ParseError,
                    DefusedXmlException) as error:
                # Exception URLs can contain the verification key; never log them.
                code = getattr(error, "code", "network_or_state")
                raise CommandError(f"IndexNow failed ({code}); accepted state preserved") from None

    def notify(self, base, directory, dry_run):
        state = directory / "accepted.json"
        previous = json.loads(state.read_text()) if state.exists() else {}
        if not isinstance(previous, dict) or any(not valid_url(url, base) for url in previous):
            raise CommandError("Invalid previous state; refusing submission")
        current = snapshot(base)
        changed = sorted(url for url in current if current[url] != previous.get(url))
        removed = sorted(set(previous) - set(current))
        urls = changed + removed
        if not urls or dry_run:
            self.stdout.write(f"INDEXNOW_{'DRY_RUN' if dry_run else 'UNCHANGED'} "
                              f"public={len(current)} changed={len(changed)} "
                              f"removed={len(removed)}")
            return
        key = settings.INDEXNOW_KEY
        status, _, proof = fetch(base + f"/indexnow-{key}.txt")
        if status != 200 or proof.decode("utf-8").strip() != key:
            raise CommandError("IndexNow proof file is not available")
        status, _, _ = fetch(ENDPOINT, json.dumps({
            "host": urlsplit(base).hostname,
            "key": key,
            "keyLocation": base + f"/indexnow-{key}.txt",
            "urlList": urls,
        }).encode())
        if status not in (200, 202):
            raise CommandError(f"IndexNow unexpected response ({status}); state preserved")
        if status == 200:
            temporary = directory / "accepted.next"
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as output:
                json.dump(current, output, sort_keys=True)
            temporary.replace(state)
        self.stdout.write(f"INDEXNOW_RECEIVED http={status} urls={len(urls)} "
                          f"key_verification={'pending' if status == 202 else 'accepted'} "
                          "index_inclusion=unconfirmed")
