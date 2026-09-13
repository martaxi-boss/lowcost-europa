import hashlib
import hmac


def canonicalize(params: dict[str, object]) -> str:
    return "".join(f"{key}{params[key]}" for key in sorted(params) if params[key] is not None)


def sign_hmac_sha256(params: dict[str, object], app_secret: str) -> str:
    payload = canonicalize(params).encode("utf-8")
    return hmac.new(app_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest().upper()
