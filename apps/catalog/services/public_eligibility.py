from datetime import timedelta

from django.conf import settings
from django.db.models import Exists, OuterRef, Q
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


def public_eligibility_q(as_of=None, prefix="", *, require_recent_price=None):
    """Return the identical public gate for storefront, search and /go/.

    Price freshness is opt-in outside production. An approved offer with an
    expired price remains in editorial history and in the maintenance queue,
    but cannot be advertised publicly as a current commercial listing.
    """
    as_of = as_of or timezone.now()
    base_gate = Q(
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

    if require_recent_price is None:
        require_recent_price = settings.PUBLIC_RECENT_PRICE_REQUIRED
    if not require_recent_price:
        return base_gate

    # A new UNKNOWN stock observation must not erase independently observed
    # price data. Equally, an old price must not count as current evidence.
    # The condition is correlated with Offer (or placement.offer if prefixed).
    from apps.catalog.models import OfferObservation

    recent_positive_eur_price = OfferObservation.objects.filter(
        offer_id=OuterRef(f"{prefix}pk"),
        observed_at__gte=as_of - timedelta(hours=24),
        observed_at__lte=as_of,
        price__gt=0,
        currency__iexact="EUR",
    ).exclude(destination_country="ES")
    return base_gate & Q(Exists(recent_positive_eur_price))
