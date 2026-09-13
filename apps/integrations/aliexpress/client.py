import json
import logging
import time
from urllib import error, parse, request

from .config import AliExpressConfig
from .exceptions import (
    AliExpressAPIError,
    AliExpressAuthenticationError,
    AliExpressResponseError,
    AliExpressTransportError,
)
from .normalizers import normalize_category, normalize_product
from .signing import sign_hmac_sha256

logger = logging.getLogger(__name__)


class AliExpressClient:
    CATEGORY_METHOD = "aliexpress.affiliate.category.get"
    SEARCH_METHOD = "aliexpress.affiliate.product.query"
    DETAIL_METHOD = "aliexpress.affiliate.productdetail.get"
    LINK_METHOD = "aliexpress.affiliate.link.generate"

    def __init__(self, config: AliExpressConfig | None = None, opener=None):
        self.config = config or AliExpressConfig.from_env()
        self._opener = opener or request.urlopen

    def _base_params(self, method: str) -> dict[str, object]:
        return {
            "app_key": self.config.app_key,
            "timestamp": str(int(time.time() * 1000)),
            "sign_method": "sha256",
            "method": method,
            "format": "json",
            "v": "2.0",
        }

    def _call(
        self, method: str, business_params: dict[str, object] | None = None
    ) -> dict:
        params = self._base_params(method)
        params.update(
            {k: v for k, v in (business_params or {}).items() if v is not None}
        )
        params["sign"] = sign_hmac_sha256(params, self.config.app_secret)
        encoded = parse.urlencode(params).encode("utf-8")
        req = request.Request(self.config.gateway, data=encoded, method="POST")
        started = time.monotonic()
        attempts = self.config.max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                with self._opener(req, timeout=self.config.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                logger.info(
                    "AliExpress operation=%s success duration_ms=%d",
                    method,
                    int((time.monotonic() - started) * 1000),
                )
                return self._validate_response(payload)
            except error.HTTPError as exc:
                if exc.code in {429, 500, 502, 503, 504} and attempt < attempts:
                    logger.warning(
                        "AliExpress operation=%s retry=%d http_status=%d",
                        method,
                        attempt,
                        exc.code,
                    )
                    continue
                raise AliExpressTransportError(
                    f"AliExpress HTTP error {exc.code}"
                ) from exc
            except (error.URLError, TimeoutError) as exc:
                if attempt < attempts:
                    logger.warning(
                        "AliExpress operation=%s retry=%d transport_error",
                        method,
                        attempt,
                    )
                    continue
                raise AliExpressTransportError("AliExpress transport error") from exc
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise AliExpressResponseError(
                    "Invalid AliExpress response payload"
                ) from exc
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
                raise AliExpressAuthenticationError(
                    f"AliExpress authentication error: {message}"
                )
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

    def search_products(
        self,
        keyword: str,
        country: str = "PT",
        currency: str = "EUR",
        page_no: int = 1,
        page_size: int = 20,
    ):
        result = self._result(
            self._call(
                self.SEARCH_METHOD,
                {
                    "keywords": keyword,
                    "ship_to_country": country,
                    "target_currency": currency,
                    "page_no": page_no,
                    "page_size": page_size,
                    "tracking_id": self.config.tracking_id,
                },
            ),
            self.SEARCH_METHOD,
        )
        products = result.get("products", {}).get("product", [])
        return [normalize_product(item, country) for item in products]

    def get_product_detail(
        self, product_id: str, country: str = "PT", currency: str = "EUR"
    ):
        result = self._result(
            self._call(
                self.DETAIL_METHOD,
                {
                    "product_ids": product_id,
                    "ship_to_country": country,
                    "target_currency": currency,
                    "tracking_id": self.config.tracking_id,
                },
            ),
            self.DETAIL_METHOD,
        )
        products = (
            result.get("products", {}).get("product", [])
            if isinstance(result, dict)
            else []
        )
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
        return links[0].get("promotion_link") or links[0].get("promotion_url")
