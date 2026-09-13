from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AliExpressCategory:
    category_id: str
    name: str | None = None
    parent_category_id: str | None = None


@dataclass(frozen=True)
class AliExpressProduct:
    product_id: str
    title: str | None = None
    image_url: str | None = None
    product_url: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    original_price: Decimal | None = None
    rating: Decimal | None = None
    sales_count: int | None = None
    commission_rate: Decimal | None = None
    delivery_days: int | None = None
    destination_country: str | None = None
    affiliate_url: str | None = None
