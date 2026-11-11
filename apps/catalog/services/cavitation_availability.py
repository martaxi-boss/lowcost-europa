"""Read-only AliExpress availability checks for both manually curated storefronts.

Only two distinct, explicit unavailable signals can deactivate a listing.
Never create or replace affiliate URLs, and never reactivate hidden items.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from django.db import transaction
from django.db.models import F, Max, Q
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.manual_storefront import MANUAL_ONLY_FAMILY_SLUGS
from apps.catalog.services.offer_maintenance import (
    is_factually_available,
    is_factually_unavailable,
    is_factually_unavailable_error,
    maintenance_run_lock,
)
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import (
    AliExpressAPIError,
    AliExpressError,
    AliExpressRateLimitError,
    AliExpressRuntimeStateError,
)

# A single negative response is not sufficient to remove an Owner-curated offer.
MIN_CONFIRMATION_GAP = timedelta(hours=3)
MAX_CONFIRMATION_AGE = timedelta(days=7)
MAX_BATCH_SIZE = 5


@dataclass
class AvailabilityReport:
    selected: int = 0
    checked: int = 0
    explicit_unavailable: int = 0
    awaiting_confirmation: int = 0
    removed_from_storefront: int = 0
    available: int = 0
    unknown: int = 0
    errors: list[str] = field(default_factory=list)


def select_manual_cavitation_batch(batch_size=MAX_BATCH_SIZE):
    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        raise ValueError("batch_size must be 1..5")
    # The historical ALIEXPRESS offers are intentionally NOT selected.
    # Only published Owner links in either manual-only category are eligible.
    queryset = (
        Offer.objects.filter(
            source=Offer.Source.ALIEXPRESS_OWNER,
            is_active=True,
            owner_hidden=False,
            family_placements__product_family__slug__in=MANUAL_ONLY_FAMILY_SLUGS,
        )
        .distinct()
        .annotate(
            last_pt_check=Max(
                "observations__observed_at",
                filter=Q(observations__destination_country="PT"),
            )
        )
        .order_by(F("last_pt_check").asc(nulls_first=True), "pk")
    )
    return list(queryset[:batch_size])


def _record_check(offer_id, status, now):
    """Lock each offer and commit only the availability observation or hide flag."""
    with transaction.atomic():
        offer = Offer.objects.select_for_update().get(pk=offer_id)
        if (
            offer.source != Offer.Source.ALIEXPRESS_OWNER
            or offer.owner_hidden
            or not offer.is_active
        ):
            return "SKIPPED"
        if not offer.family_placements.filter(
            product_family__slug__in=MANUAL_ONLY_FAMILY_SLUGS
        ).exists():
            return "SKIPPED"

        previous = (
            OfferObservation.objects.filter(
                offer=offer, destination_country="PT", observed_at__lte=now
            )
            .order_by("-observed_at", "-pk")
            .first()
        )
        OfferObservation.objects.create(
            offer=offer,
            observed_at=now,
            destination_country="PT",
            availability=status,
        )
        if status != OfferObservation.Availability.UNAVAILABLE:
            return status

        confirmed = (
            previous is not None
            and previous.availability == OfferObservation.Availability.UNAVAILABLE
            and MIN_CONFIRMATION_GAP <= now - previous.observed_at <= MAX_CONFIRMATION_AGE
        )
        if not confirmed:
            return "AWAITING_CONFIRMATION"

        # The affiliate URL itself, commercial details and historical clicks
        # remain immutable. Hide also blocks /go/ before anybody can click.
        offer.owner_hidden = True
        offer.is_active = False
        offer.save(update_fields=["owner_hidden", "is_active", "updated_at"])
        return "REMOVED"


def monitor_cavitation_availability(*, batch_size=MAX_BATCH_SIZE, client=None, now=None):
    now = now or timezone.now()
    client = client or AliExpressClient()
    report = AvailabilityReport()
    with maintenance_run_lock():
        offers = select_manual_cavitation_batch(batch_size)
        report.selected = len(offers)
        for offer in offers:
            status = OfferObservation.Availability.UNKNOWN
            try:
                detail = client.get_product_detail(offer.external_product_id, "PT", "EUR")
            except (AliExpressRateLimitError, AliExpressRuntimeStateError):
                # Do not interpret rate limits, credentials or failed runtime as
                # seller unavailability; signal failure to the systemd job.
                raise
            except AliExpressAPIError as exc:
                if is_factually_unavailable_error(exc):
                    status = OfferObservation.Availability.UNAVAILABLE
                else:
                    report.errors.append(offer.external_product_id + ":API")
            except AliExpressError as exc:
                report.errors.append(offer.external_product_id + ":" + exc.__class__.__name__)
            else:
                if detail.product_id == offer.external_product_id:
                    if is_factually_unavailable(detail):
                        status = OfferObservation.Availability.UNAVAILABLE
                    elif is_factually_available(detail):
                        status = OfferObservation.Availability.AVAILABLE
                else:
                    report.errors.append(offer.external_product_id + ":ProductIdMismatch")

            result = _record_check(offer.pk, status, now)
            if result == "SKIPPED":
                continue
            report.checked += 1
            if status == OfferObservation.Availability.UNAVAILABLE:
                report.explicit_unavailable += 1
            if result == "AWAITING_CONFIRMATION":
                report.awaiting_confirmation += 1
            elif result == "REMOVED":
                report.removed_from_storefront += 1
            elif result == OfferObservation.Availability.AVAILABLE:
                report.available += 1
            else:
                report.unknown += 1
    return report
