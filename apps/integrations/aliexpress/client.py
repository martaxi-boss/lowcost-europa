import errno
import fcntl
import json
import logging
import os
import random
import stat
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from urllib import error, parse, request

from .config import AliExpressConfig
from .exceptions import (
    AliExpressAPIError,
    AliExpressAuthenticationError,
    AliExpressRateLimitError,
    AliExpressResponseError,
    AliExpressRuntimeStateError,
    AliExpressTransportError,
)
from .normalizers import normalize_category, normalize_product
from .signing import sign_hmac_sha256
from .types import AliExpressSearchResult

logger = logging.getLogger(__name__)

SUPPORTED_DELIVERY_DAYS = frozenset({3, 5, 7, 10})
MAX_SEARCH_PAGE_SIZE = 25
DEFAULT_LOCK_PATH = "/run/lowcost-europa/aliexpress.lock"
DEFAULT_CADENCE_PATH = "/run/lowcost-europa/aliexpress.last-start"


def _secure_state_open(path: str, flags: int, mode: int = 0o600):
    secure_flags = flags | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        secure_flags |= os.O_NOFOLLOW
    fd = os.open(path, secure_flags, mode)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise AliExpressRuntimeStateError("AliExpress runtime state is not a regular file")
        if info.st_uid != os.geteuid():
            raise AliExpressRuntimeStateError("AliExpress runtime state ownership mismatch")
        os.fchmod(fd, mode)
        return fd
    except Exception:
        os.close(fd)
        raise


@dataclass
class AliExpressCallMetrics:
    logical_operations: int = 0
    attempts: int = 0
    successful: int = 0
    retries: int = 0
    http_429: int = 0
    http_5xx: int = 0
    transport_failures: int = 0
    rate_limit_abort: bool = False
    duration_ms: int = 0
    lock_wait_ms: int = 0


def format_execution_metrics(metrics: AliExpressCallMetrics) -> list[str]:
    return [
        f"Logical operations: {metrics.logical_operations}",
        f"HTTP attempts: {metrics.attempts}",
        f"Retries: {metrics.retries}",
        f"429 responses: {metrics.http_429}",
        f"5xx responses: {metrics.http_5xx}",
        f"Transport failures: {metrics.transport_failures}",
        f"Rate-limit abort: {'YES' if metrics.rate_limit_abort else 'NO'}",
        f"Total duration ms: {metrics.duration_ms}",
        f"Lock wait ms: {metrics.lock_wait_ms}",
    ]


class _LocalOperationLock:
    def __init__(self, path, timeout, monotonic, sleeper):
        self.path = path
        self.timeout = timeout
        self.monotonic = monotonic
        self.sleeper = sleeper
        self.handle = None
        self.wait_ms = 0

    def __enter__(self):
        started = self.monotonic()
        try:
            fd = _secure_state_open(self.path, os.O_RDWR | os.O_CREAT)
            self.handle = os.fdopen(fd, "a+", encoding="utf-8")
        except OSError as exc:
            raise AliExpressRuntimeStateError("AliExpress operation lock unavailable") from exc
        while True:
            try:
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.wait_ms = int((self.monotonic() - started) * 1000)
                return self
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise AliExpressRuntimeStateError(
                        "AliExpress operation lock unavailable"
                    ) from exc
                if self.monotonic() - started >= self.timeout:
                    self.handle.close()
                    self.handle = None
                    raise AliExpressRuntimeStateError(
                        "AliExpress operation lock timeout"
                    ) from exc
                self.sleeper(min(0.05, self.timeout))

    def __exit__(self, *_args):
        if self.handle is not None:
            try:
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            finally:
                self.handle.close()
                self.handle = None
        return False


class AliExpressClient:
    CATEGORY_METHOD = "aliexpress.affiliate.category.get"
    SEARCH_METHOD = "aliexpress.affiliate.product.query"
    DETAIL_METHOD = "aliexpress.affiliate.productdetail.get"
    LINK_METHOD = "aliexpress.affiliate.link.generate"

    def __init__(
        self,
        config: AliExpressConfig | None = None,
        opener=None,
        *,
        sleeper=time.sleep,
        monotonic=time.monotonic,
        wall_clock=time.time,
        jitter_source=random.uniform,
        lock_path: str = DEFAULT_LOCK_PATH,
        cadence_path: str = DEFAULT_CADENCE_PATH,
    ):
        self.config = config or AliExpressConfig.from_env()
        self._opener = opener or request.urlopen
        self._sleeper = sleeper
        self._monotonic = monotonic
        self._wall_clock = wall_clock
        self._jitter_source = jitter_source
        self._lock_path = lock_path
        self._cadence_path = cadence_path
        self.last_call_metrics = AliExpressCallMetrics()
        self.execution_metrics = AliExpressCallMetrics()

    def _accumulate_metrics(self, metrics: AliExpressCallMetrics) -> None:
        total = self.execution_metrics
        total.logical_operations += metrics.logical_operations
        total.attempts += metrics.attempts
        total.successful += metrics.successful
        total.retries += metrics.retries
        total.http_429 += metrics.http_429
        total.http_5xx += metrics.http_5xx
        total.transport_failures += metrics.transport_failures
        total.rate_limit_abort = total.rate_limit_abort or metrics.rate_limit_abort
        total.duration_ms += metrics.duration_ms
        total.lock_wait_ms += metrics.lock_wait_ms

    def _base_params(self, method: str) -> dict[str, object]:
        return {
            "app_key": self.config.app_key,
            "timestamp": str(int(self._wall_clock() * 1000)),
            "sign_method": "sha256",
            "method": method,
            "format": "json",
            "v": "2.0",
        }

    def _build_request(self, method: str, business_params: dict[str, object] | None):
        params = self._base_params(method)
        params.update({k: v for k, v in (business_params or {}).items() if v is not None})
        params["sign"] = sign_hmac_sha256(params, self.config.app_secret)
        encoded = parse.urlencode(params).encode("utf-8")
        return request.Request(self.config.gateway, data=encoded, method="POST")

    def _pace(self) -> None:
        now = self._wall_clock()
        last = None
        try:
            fd = _secure_state_open(self._cadence_path, os.O_RDONLY)
            with os.fdopen(fd, encoding="utf-8") as handle:
                last = float(handle.read().strip())
        except FileNotFoundError:
            last = None
        except ValueError:
            last = None
        except OSError as exc:
            raise AliExpressRuntimeStateError("AliExpress cadence state unavailable") from exc
        if last is not None:
            remaining = self.config.min_interval_seconds - (now - last)
            if remaining > 0:
                self._sleeper(remaining)
        started = self._wall_clock()
        try:
            fd = _secure_state_open(
                self._cadence_path,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            )
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(f"{started:.6f}")
        except OSError as exc:
            raise AliExpressRuntimeStateError("AliExpress cadence state unavailable") from exc

    def _retry_after_seconds(self, exc: error.HTTPError) -> float | None:
        raw = exc.headers.get("Retry-After") if exc.headers else None
        if not raw:
            return None
        try:
            delay = float(raw)
        except ValueError:
            try:
                dt = parsedate_to_datetime(raw)
                delay = dt.timestamp() - self._wall_clock()
            except (TypeError, ValueError, OverflowError):
                return None
        if delay < 0:
            delay = 0.0
        capped = min(delay, self.config.max_retry_after_seconds)
        if delay > capped:
            logger.warning(
                "AliExpress retry_after capped retry_after_seconds=%.3f",
                capped,
            )
        return capped

    def _backoff_seconds(self, retry_number: int) -> float:
        base = self.config.backoff_base_seconds * (2 ** (retry_number - 1))
        delay = min(base, self.config.backoff_max_seconds)
        jitter = self._jitter_source(0.0, self.config.jitter_max_seconds)
        return delay + jitter

    def _sleep_before_retry(self, retry_number: int, retry_after: float | None) -> float:
        delay = retry_after if retry_after is not None else self._backoff_seconds(retry_number)
        if delay > 0:
            self._sleeper(delay)
        return delay

    def _call(self, method: str, business_params: dict[str, object] | None = None) -> dict:
        metrics = AliExpressCallMetrics(logical_operations=1)
        self.last_call_metrics = metrics
        started = self._monotonic()
        consecutive_429 = 0
        attempts = self.config.max_retries + 1
        operation_lock = _LocalOperationLock(
            self._lock_path,
            self.config.lock_timeout_seconds,
            self._monotonic,
            self._sleeper,
        )
        try:
            with operation_lock:
                metrics.lock_wait_ms = operation_lock.wait_ms
                for attempt in range(1, attempts + 1):
                    self._pace()
                    req = self._build_request(method, business_params)
                    metrics.attempts += 1
                    try:
                        with self._opener(req, timeout=self.config.timeout_seconds) as response:
                            payload = json.loads(response.read().decode("utf-8"))
                        result = self._validate_response(payload)
                        metrics.successful = 1
                        logger.info(
                            (
                                "AliExpress operation=%s success attempt=%d "
                                "duration_ms=%d lock_wait_ms=%d"
                            ),
                            method,
                            attempt,
                            int((self._monotonic() - started) * 1000),
                            metrics.lock_wait_ms,
                        )
                        return result
                    except error.HTTPError as exc:
                        status = exc.code
                        if status == 429:
                            metrics.http_429 += 1
                            consecutive_429 += 1
                            if (
                                consecutive_429 >= self.config.max_consecutive_429
                                or attempt >= attempts
                            ):
                                metrics.rate_limit_abort = True
                                raise AliExpressRateLimitError(
                                    "AliExpress rate limit reached"
                                ) from exc
                            retry_after = self._retry_after_seconds(exc)
                            delay = self._sleep_before_retry(attempt, retry_after)
                            metrics.retries += 1
                            logger.warning(
                                (
                                    "AliExpress operation=%s retry=%d http_status=429 "
                                    "rate_limited=yes retry_after_seconds=%s "
                                    "backoff_seconds=%.3f"
                                ),
                                method,
                                attempt,
                                f"{retry_after:.3f}" if retry_after is not None else "none",
                                delay,
                            )
                            continue
                        consecutive_429 = 0
                        if status in {500, 502, 503, 504}:
                            metrics.http_5xx += 1
                            if attempt < attempts:
                                delay = self._sleep_before_retry(attempt, None)
                                metrics.retries += 1
                                logger.warning(
                                    (
                                        "AliExpress operation=%s retry=%d http_status=%d "
                                        "rate_limited=no backoff_seconds=%.3f"
                                    ),
                                    method,
                                    attempt,
                                    status,
                                    delay,
                                )
                                continue
                        raise AliExpressTransportError(f"AliExpress HTTP error {status}") from exc
                    except (error.URLError, TimeoutError) as exc:
                        consecutive_429 = 0
                        metrics.transport_failures += 1
                        if attempt < attempts:
                            delay = self._sleep_before_retry(attempt, None)
                            metrics.retries += 1
                            logger.warning(
                                (
                                    "AliExpress operation=%s retry=%d transport_error "
                                    "backoff_seconds=%.3f"
                                ),
                                method,
                                attempt,
                                delay,
                            )
                            continue
                        raise AliExpressTransportError("AliExpress transport error") from exc
                    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                        raise AliExpressResponseError(
                            "Invalid AliExpress response payload"
                        ) from exc
        finally:
            metrics.lock_wait_ms = operation_lock.wait_ms
            metrics.duration_ms = int((self._monotonic() - started) * 1000)
            self._accumulate_metrics(metrics)
        raise AliExpressTransportError("AliExpress request failed")

    @staticmethod
    def _validate_response(payload: dict) -> dict:
        if "error_response" in payload:
            err = payload["error_response"] or {}
            code = str(err.get("code", ""))
            sub_code = str(err.get("sub_code", ""))
            message = str(err.get("msg", "AliExpress API error"))
            if (
                code in {"27", "29"}
                or "appkey" in sub_code.lower()
                or "signature" in sub_code.lower()
            ):
                raise AliExpressAuthenticationError(f"AliExpress authentication error: {message}")
            raise AliExpressAPIError(f"AliExpress API error {code}: {message}")
        return payload

    @staticmethod
    def _result(payload: dict, method: str):
        key = method.replace(".", "_") + "_response"
        response = payload.get(key)
        if response is None:
            raise AliExpressResponseError(f"Missing response wrapper for {method}")
        result = response.get("resp_result", {}).get("result")
        if result is None:
            result = response.get("result")
        if result is None:
            raise AliExpressResponseError(f"Missing result for {method}")
        return result

    def get_categories(self):
        result = self._result(self._call(self.CATEGORY_METHOD), self.CATEGORY_METHOD)
        categories = result.get("categories", {}).get("category", [])
        return [normalize_category(item) for item in categories]

    def search_products_diagnostic(
        self,
        keyword: str,
        country: str = "PT",
        currency: str = "EUR",
        page_no: int = 1,
        page_size: int = 20,
        target_language: str | None = None,
        delivery_days: int | None = None,
    ) -> AliExpressSearchResult:
        if delivery_days is not None and delivery_days not in SUPPORTED_DELIVERY_DAYS:
            allowed = ", ".join(str(value) for value in sorted(SUPPORTED_DELIVERY_DAYS))
            raise ValueError(f"delivery_days must be one of: {allowed}")
        if page_no < 1:
            raise ValueError("page_no must be >= 1")
        if not 1 <= page_size <= MAX_SEARCH_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {MAX_SEARCH_PAGE_SIZE}")
        result = self._result(
            self._call(
                self.SEARCH_METHOD,
                {
                    "keywords": keyword,
                    "ship_to_country": country,
                    "target_currency": currency,
                    "page_no": page_no,
                    "page_size": page_size,
                    "target_language": target_language,
                    "delivery_days": delivery_days,
                    "tracking_id": self.config.tracking_id,
                },
            ),
            self.SEARCH_METHOD,
        )
        if not isinstance(result, dict):
            raise AliExpressResponseError("Unexpected product search response")
        raw_products = result.get("products", {}).get("product", [])
        if not isinstance(raw_products, list):
            raise AliExpressResponseError("Unexpected product search list")

        products = []
        invalid_items = 0
        for item in raw_products:
            if not isinstance(item, dict):
                invalid_items += 1
                continue
            try:
                products.append(normalize_product(item, country))
            except AliExpressResponseError:
                invalid_items += 1
        return AliExpressSearchResult(products=products, invalid_items=invalid_items)

    def search_products(
        self,
        keyword: str,
        country: str = "PT",
        currency: str = "EUR",
        page_no: int = 1,
        page_size: int = 20,
        target_language: str | None = None,
        delivery_days: int | None = None,
    ):
        return self.search_products_diagnostic(
            keyword,
            country,
            currency,
            page_no,
            page_size,
            target_language,
            delivery_days,
        ).products

    def get_product_detail(self, product_id: str, country: str = "PT", currency: str = "EUR"):
        result = self._result(
            self._call(
                self.DETAIL_METHOD,
                {
                    "product_ids": product_id,
                    # Unlike affiliate search (ship_to_country), the official
                    # affiliate product-detail endpoint calls this field country.
                    "country": country,
                    "target_currency": currency,
                    "tracking_id": self.config.tracking_id,
                },
            ),
            self.DETAIL_METHOD,
        )
        products = result.get("products", {}).get("product", []) if isinstance(result, dict) else []
        item = products[0] if products else result
        if not isinstance(item, dict):
            raise AliExpressResponseError("Unexpected product detail response")
        return normalize_product(item, country)

    def generate_affiliate_link(self, source_url: str):
        result = self._result(
            self._call(
                self.LINK_METHOD,
                {
                    "source_values": source_url,
                    "tracking_id": self.config.tracking_id,
                    "promotion_link_type": "0",
                },
            ),
            self.LINK_METHOD,
        )
        links = result.get("promotion_links", {}).get("promotion_link", [])
        if not links:
            raise AliExpressResponseError("No affiliate link returned")
        first = links[0]
        message = str(first.get("message", "") or "").strip()
        if message:
            raise AliExpressAPIError(f"AliExpress API error: {message}")
        affiliate_url = first.get("promotion_link") or first.get("promotion_url")
        if not affiliate_url:
            raise AliExpressResponseError("No affiliate link returned")
        return affiliate_url
