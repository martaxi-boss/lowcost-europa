"""Strictly structural HTTPS checks; source identity comes from AliExpress API."""

from urllib.parse import urlsplit


def is_https_affiliate_url(value):
    """Allow only ordinary HTTPS destinations, never URL credentials or odd ports."""
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if len(value) > 1000 or any(character.isspace() or ord(character) < 32 for character in value):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and parsed.netloc
        and host
        and host.isascii()
        and "." in host
        and not host.startswith(".")
        and not host.endswith(".")
        and parsed.username is None
        and parsed.password is None
        and port in (None, 443)
    )
