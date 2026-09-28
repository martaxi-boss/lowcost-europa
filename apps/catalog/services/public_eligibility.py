from django.db.models import Q
from django.utils import timezone

ALLOWED_SHIP_FROM_COUNTRIES = frozenset({"PL", "CZ", "FR", "ES", "DE"})
MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY = 20


def is_protocol_verified(offer, as_of=None):
    as_of = as_of or timezone.now()
    verified_at = offer.protocol_verified_at
    return bool(verified_at is not None and verified_at <= as_of)


def public_eligibility_q(as_of=None, prefix=""):
    as_of = as_of or timezone.now()
    return Q(
        **{
            f"{prefix}is_active": True,
            f"{prefix}owner_hidden": False,
            f"{prefix}affiliate_url__gt": "",
            f"{prefix}affiliate_promotion_status": "ELIGIBLE",
            f"{prefix}affiliate_promotion_verified_at__isnull": False,
            f"{prefix}protocol_verified_at__isnull": False,
            f"{prefix}protocol_verified_at__lte": as_of,
        }
    )
