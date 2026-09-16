import re
from decimal import Decimal, InvalidOperation

from .exceptions import AliExpressResponseError
from .types import AliExpressCategory, AliExpressProduct


def _first(data: dict, *keys):
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace("%", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _required_id(data: dict, *keys: str, entity: str) -> str:
    value = _first(data, *keys)
    if value in (None, ""):
        raise AliExpressResponseError(f"Missing required {entity} identifier")
    return str(value)


def _shipping_days(raw_value):
    if raw_value in (None, ""):
        return None, None
    raw = str(raw_value).strip()
    if raw.isdigit():
        return raw, int(raw)
    match = re.fullmatch(r"Ship to [A-Za-z]{2} in ([0-9]+) Days?", raw, flags=re.IGNORECASE)
    if match:
        return raw, int(match.group(1))
    return raw, None


def normalize_category(data: dict) -> AliExpressCategory:
    return AliExpressCategory(
        category_id=_required_id(data, "category_id", "id", entity="category"),
        name=_first(data, "category_name", "name"),
        parent_category_id=(
            str(_first(data, "parent_category_id"))
            if _first(data, "parent_category_id") is not None
            else None
        ),
    )


def normalize_product(data: dict, destination_country: str | None = None) -> AliExpressProduct:
    shipping_raw, delivery_days = _shipping_days(
        _first(data, "ship_to_days", "delivery_days", "estimated_delivery_days")
    )
    return AliExpressProduct(
        product_id=_required_id(data, "product_id", "item_id", entity="product"),
        title=_first(data, "product_title", "title"),
        image_url=_first(data, "product_main_image_url", "product_image", "image_url"),
        product_url=_first(data, "product_detail_url", "product_url"),
        price=_decimal(_first(data, "target_sale_price", "sale_price", "price")),
        currency=_first(data, "target_sale_price_currency", "currency"),
        original_price=_decimal(_first(data, "target_original_price", "original_price")),
        evaluation_rate_percent=_decimal(_first(data, "evaluate_rate")),
        sales_count=_int(_first(data, "lastest_volume", "sales_count", "volume")),
        commission_rate=_decimal(_first(data, "commission_rate", "commission")),
        ship_to_days_raw=shipping_raw,
        delivery_days=delivery_days,
        destination_country=destination_country,
        availability_raw=_first(data, "availability", "product_status", "item_status", "status"),
        affiliate_url=_first(data, "promotion_link", "affiliate_url"),
    )
