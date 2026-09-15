import os
from dataclasses import dataclass

from .exceptions import AliExpressConfigurationError


@dataclass(frozen=True)
class AliExpressConfig:
    app_key: str
    app_secret: str
    tracking_id: str
    gateway: str = "https://api-sg.aliexpress.com/sync"
    timeout_seconds: float = 10.0
    max_retries: int = 2
    min_interval_seconds: float = 1.0
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 30.0
    jitter_max_seconds: float = 0.5
    max_retry_after_seconds: float = 60.0
    max_consecutive_429: int = 3
    lock_timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> "AliExpressConfig":
        required = {
            "app_key": os.environ.get("ALIEXPRESS_APP_KEY"),
            "app_secret": os.environ.get("ALIEXPRESS_APP_SECRET"),
            "tracking_id": os.environ.get("ALIEXPRESS_TRACKING_ID"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise AliExpressConfigurationError(
                "Missing required AliExpress configuration: " + ", ".join(missing)
            )
        values = {
            "gateway": os.environ.get("ALIEXPRESS_GATEWAY", "https://api-sg.aliexpress.com/sync"),
            "timeout_seconds": _float_env("ALIEXPRESS_TIMEOUT_SECONDS", 10.0),
            "max_retries": _int_env("ALIEXPRESS_MAX_RETRIES", 2),
            "min_interval_seconds": _float_env("ALIEXPRESS_MIN_INTERVAL_SECONDS", 1.0),
            "backoff_base_seconds": _float_env("ALIEXPRESS_BACKOFF_BASE_SECONDS", 1.0),
            "backoff_max_seconds": _float_env("ALIEXPRESS_BACKOFF_MAX_SECONDS", 30.0),
            "jitter_max_seconds": _float_env("ALIEXPRESS_JITTER_MAX_SECONDS", 0.5),
            "max_retry_after_seconds": _float_env("ALIEXPRESS_MAX_RETRY_AFTER_SECONDS", 60.0),
            "max_consecutive_429": _int_env("ALIEXPRESS_MAX_CONSECUTIVE_429", 3),
            "lock_timeout_seconds": _float_env("ALIEXPRESS_LOCK_TIMEOUT_SECONDS", 15.0),
        }
        _validate(values)
        return cls(
            app_key=required["app_key"],
            app_secret=required["app_secret"],
            tracking_id=required["tracking_id"],
            **values,
        )


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise AliExpressConfigurationError(
            f"Invalid numeric AliExpress configuration: {name}"
        ) from exc


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise AliExpressConfigurationError(
            f"Invalid integer AliExpress configuration: {name}"
        ) from exc


def _validate(values: dict[str, object]) -> None:
    if values["timeout_seconds"] <= 0:
        raise AliExpressConfigurationError("ALIEXPRESS_TIMEOUT_SECONDS must be > 0")
    if not 0 <= values["max_retries"] <= 5:
        raise AliExpressConfigurationError("ALIEXPRESS_MAX_RETRIES must be between 0 and 5")
    for name in (
        "min_interval_seconds",
        "backoff_base_seconds",
        "backoff_max_seconds",
        "jitter_max_seconds",
        "max_retry_after_seconds",
    ):
        if values[name] < 0:
            raise AliExpressConfigurationError(f"{name} must be >= 0")
    if values["backoff_max_seconds"] < values["backoff_base_seconds"]:
        raise AliExpressConfigurationError("ALIEXPRESS_BACKOFF_MAX_SECONDS must be >= base")
    if not 1 <= values["max_consecutive_429"] <= 10:
        raise AliExpressConfigurationError(
            "ALIEXPRESS_MAX_CONSECUTIVE_429 must be between 1 and 10"
        )
    if values["lock_timeout_seconds"] <= 0:
        raise AliExpressConfigurationError("ALIEXPRESS_LOCK_TIMEOUT_SECONDS must be > 0")
