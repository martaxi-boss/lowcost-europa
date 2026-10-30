from django.db.models import Q
from django.utils import timezone

ALLOWED_SHIP_FROM_COUNTRY_CHOICES = (
    ("PL", "PL"),
    ("CZ", "CZ"),
    ("FR", "FR"),
    ("ES", "ES"),
    ("DE", "DE"),
)
ALLOWED_SHIP_FROM_COUNTRIES = frozenset(code for code, _label in ALLOWED_SHIP_FROM_COUNTRY_CHOICES)
MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY = 20


def is_protocol_verified(offer, as_of=None):
    as_of = as_of or timezone.now()
    verified_at = offer.protocol_verified_at
    return bool(verified_at is not None and verified_at <= as_of)


def is_ship_from_verified(offer, as_of=None):
    as_of = as_of or timezone.now()
    country = (offer.ship_from_country or "").upper()
    verified_at = offer.ship_from_verified_at
    return bool(
        country in ALLOWED_SHIP_FROM_COUNTRIES
        and verified_at is not None
        and verified_at <= as_of
    )


def public_eligibility_q(as_of=None, prefix=""):
    as_of = as_of or timezone.now()
    return Q(
        **{
            f"{prefix}is_active": True,
            f"{prefix}owner_hidden": False,
            f"{prefix}affiliate_url__startswith": "https://",
            f"{prefix}affiliate_promotion_status": "ELIGIBLE",
            f"{prefix}affiliate_promotion_verified_at__isnull": False,
            f"{prefix}protocol_verified_at__isnull": False,
            f"{prefix}protocol_verified_at__lte": as_of,
        }
    )
