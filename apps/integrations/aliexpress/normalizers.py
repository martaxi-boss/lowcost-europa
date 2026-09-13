from decimal import Decimal, InvalidOperation

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
        return Decimal(str(value).replace("%", ""))
    except (InvalidOperation, ValueError):
        return None


def _int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_category(data: dict) -> AliExpressCategory:
    return AliExpressCategory(
        category_id=str(_first(data, "category_id", "id")),
        name=_first(data, "category_name", "name"),
        parent_category_id=(
            str(_first(data, "parent_category_id")) if _first(data, "parent_category_id") else None
        ),
    )


def normalize_product(data: dict, destination_country: str | None = None) -> AliExpressProduct:
    return AliExpressProduct(
        product_id=str(_first(data, "product_id", "item_id")),
        title=_first(data, "product_title", "title"),
        image_url=_first(data, "product_main_image_url", "product_image", "image_url"),
        product_url=_first(data, "product_detail_url", "product_url"),
        price=_decimal(_first(data, "target_sale_price", "sale_price", "price")),
        currency=_first(data, "target_sale_price_currency", "currency"),
        original_price=_decimal(_first(data, "target_original_price", "original_price")),
        rating=_decimal(_first(data, "evaluate_rate", "rating")),
        sales_count=_int(_first(data, "lastest_volume", "sales_count", "volume")),
        commission_rate=_decimal(_first(data, "commission_rate", "commission")),
        delivery_days=_int(_first(data, "delivery_days", "estimated_delivery_days")),
        destination_country=destination_country,
        affiliate_url=_first(data, "promotion_link", "affiliate_url"),
    )
