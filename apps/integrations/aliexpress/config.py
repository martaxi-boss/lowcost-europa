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
        return cls(
            app_key=required["app_key"],
            app_secret=required["app_secret"],
            tracking_id=required["tracking_id"],
            gateway=os.environ.get(
                "ALIEXPRESS_GATEWAY", "https://api-sg.aliexpress.com/sync"
            ),
            timeout_seconds=float(
                os.environ.get("ALIEXPRESS_TIMEOUT_SECONDS", "10")
            ),
            max_retries=int(os.environ.get("ALIEXPRESS_MAX_RETRIES", "2")),
        )
