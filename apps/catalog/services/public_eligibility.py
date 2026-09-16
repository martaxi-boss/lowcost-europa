from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

ALLOWED_SHIP_FROM_COUNTRIES = frozenset({"PL", "CZ", "FR", "ES", "DE"})
SHIP_FROM_VERIFICATION_MAX_AGE = timedelta(days=7)
MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY = 20


def is_ship_from_verification_fresh(offer, as_of=None):
    as_of = as_of or timezone.now()
    verified_at = offer.ship_from_verified_at
    return bool(
        offer.ship_from_country in ALLOWED_SHIP_FROM_COUNTRIES
        and verified_at is not None
        and verified_at <= as_of
        and as_of - verified_at <= SHIP_FROM_VERIFICATION_MAX_AGE
    )


def public_eligibility_q(as_of=None, prefix=""):
    as_of = as_of or timezone.now()
    return Q(
        **{
            f"{prefix}is_active": True,
            f"{prefix}ship_from_country__in": ALLOWED_SHIP_FROM_COUNTRIES,
            f"{prefix}ship_from_verified_at__isnull": False,
            f"{prefix}ship_from_verified_at__lte": as_of,
            f"{prefix}ship_from_verified_at__gte": as_of - SHIP_FROM_VERIFICATION_MAX_AGE,
        }
    )
