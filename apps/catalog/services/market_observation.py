"""Bounded official market evidence; never edits offers or affiliate links."""

from django.db.models import F, Max, Q
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.offer_maintenance import (
    is_factually_available,
    is_factually_unavailable,
    maintenance_run_lock,
)
from apps.catalog.services.public_eligibility import public_eligibility_q
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError


def observe_market_offers(*, country, limit=5, persist=False, client=None):
    if country not in {"PT", "ES"} or not 1 <= limit <= 5:
        raise ValueError("Market must be PT/ES and limit must be between 1 and 5")
    result = {"country": country, "selected": 0, "attempts": 0, "persisted": 0,
              "eur_prices": 0, "listing_signals": 0, "numeric_delivery": 0}
    with maintenance_run_lock():
        offers = list(
            Offer.objects.filter(
                public_eligibility_q(require_recent_price=False),
                source=Offer.Source.ALIEXPRESS,
            ).annotate(market_checked=Max(
                "observations__observed_at",
                filter=Q(observations__destination_country=country),
            )).order_by(F("market_checked").asc(nulls_first=True), "pk")[:limit]
        )
        result["selected"] = len(offers)
        if not persist:
            return result
        client = client or AliExpressClient()
        for offer in offers:
            result["attempts"] += 1
            # The existing client enforces the shared cadence, retries and
            # breaker. Any API/rate-limit/runtime failure stops this batch.
            detail = client.get_product_detail(
                offer.external_product_id, country=country, currency="EUR"
            )
            if (detail.product_id != offer.external_product_id
                    or detail.destination_country != country
                    or not (detail.title or detail.product_url)):
                raise AliExpressError("Market response identity mismatch")
            availability = OfferObservation.Availability.UNKNOWN
            if is_factually_unavailable(detail):
                availability = OfferObservation.Availability.UNAVAILABLE
            elif is_factually_available(detail):
                availability = OfferObservation.Availability.AVAILABLE
            OfferObservation.objects.create(
                offer=offer, destination_country=country, observed_at=timezone.now(),
                price=detail.price, original_price=detail.original_price,
                currency=detail.currency,
                evaluation_rate_percent=detail.evaluation_rate_percent,
                sales_count=detail.sales_count, commission_rate=detail.commission_rate,
                ship_to_days_raw=detail.ship_to_days_raw,
                delivery_days=detail.delivery_days, availability=availability,
            )
            result["persisted"] += 1
            result["eur_prices"] += int(
                detail.price is not None and detail.price > 0
                and (detail.currency or "").upper() == "EUR"
            )
            result["listing_signals"] += int(
                availability != OfferObservation.Availability.UNKNOWN
            )
            result["numeric_delivery"] += int(detail.delivery_days is not None)
    return result
