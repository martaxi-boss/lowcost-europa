import errno
import fcntl
import os
import stat
from contextlib import contextmanager
from dataclasses import dataclass, field

from django.conf import settings
from django.db.models import F, Max
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import (
    AliExpressAPIError,
    AliExpressError,
    AliExpressRateLimitError,
    AliExpressRuntimeStateError,
)

MAINTENANCE_LOCK_PATH = "/run/lowcost-europa/catalog-maintenance.lock"

_UNAVAILABLE_VALUES = frozenset(
    {
        "unavailable",
        "not available",
        "no longer available",
        "offline",
        "removed",
        "deleted",
        "invalid",
    }
)

_DEAD_LISTING_ERROR_FRAGMENTS = (
    "product does not exist",
    "item does not exist",
    "product not found",
    "item not found",
    "product removed",
    "item removed",
    "product unavailable",
    "item unavailable",
)


@dataclass
class MaintenanceResult:
    offers_selected: int = 0
    detail_attempts: int = 0
    available_confirmed: int = 0
    unavailable_confirmed: int = 0
    transient_failures: int = 0
    offers_deactivated: int = 0
    promotion_attempts: int = 0
    promotion_eligible: int = 0
    promotion_ineligible: int = 0
    promotion_transient_failures: int = 0
    failures: list[str] = field(default_factory=list)



_PROMOTION_INELIGIBLE_FRAGMENT = "cannot be sold or promoted in the selected country"


def verify_affiliate_promotion(offer, *, client, now):
    """Refresh technical promotional eligibility without changing editorial state."""
    if offer.source != Offer.Source.ALIEXPRESS:
        return None
    if not offer.product_url:
        raise ValueError("Offer has no product URL for affiliate verification")
    try:
        affiliate_url = client.generate_affiliate_link(offer.product_url)
    except AliExpressAPIError as exc:
        if _PROMOTION_INELIGIBLE_FRAGMENT in str(exc).lower():
            offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.INELIGIBLE
            offer.affiliate_promotion_verified_at = now
            offer.save(
                update_fields=[
                    "affiliate_promotion_status",
                    "affiliate_promotion_verified_at",
                    "updated_at",
                ]
            )
            return Offer.AffiliatePromotionStatus.INELIGIBLE
        raise
    if not affiliate_url:
        raise ValueError("AliExpress returned no promotion link")
    offer.affiliate_url = affiliate_url
    offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.ELIGIBLE
    offer.affiliate_promotion_verified_at = now
    offer.save(
        update_fields=[
            "affiliate_url",
            "affiliate_promotion_status",
            "affiliate_promotion_verified_at",
            "updated_at",
        ]
    )
    return Offer.AffiliatePromotionStatus.ELIGIBLE

def is_factually_unavailable(product):
    raw = " ".join(str(getattr(product, "availability_raw", "") or "").lower().split())
    return raw in _UNAVAILABLE_VALUES


def is_factually_unavailable_error(exc):
    message = " ".join(str(exc).lower().split())
    return any(fragment in message for fragment in _DEAD_LISTING_ERROR_FRAGMENTS)


def is_factually_available(product):
    if is_factually_unavailable(product):
        return False
    return bool(product.product_id and (product.product_url or product.title))


@contextmanager
def maintenance_run_lock(path=None):
    path = path or getattr(settings, "CATALOG_MAINTENANCE_LOCK_PATH", MAINTENANCE_LOCK_PATH)
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    handle = None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            raise RuntimeError("Catalog maintenance lock ownership/type mismatch")
        os.fchmod(fd, 0o600)
        handle = os.fdopen(fd, "a+", encoding="utf-8")
        fd = -1
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in {errno.EACCES, errno.EAGAIN}:
                raise RuntimeError("Catalog maintenance already running") from exc
            raise
        yield
    finally:
        if handle is not None:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
        elif fd >= 0:
            os.close(fd)


def select_maintenance_batch(batch_size):
    return list(
        Offer.objects.filter(source=Offer.Source.ALIEXPRESS, is_active=True)
        .annotate(last_check=Max("observations__observed_at"))
        .order_by(F("last_check").asc(nulls_first=True), "pk")[:batch_size]
    )


def _observation_from_detail(offer, detail, *, now, availability):
    return OfferObservation.objects.create(
        offer=offer,
        observed_at=now,
        destination_country="PT",
        price=detail.price,
        original_price=detail.original_price,
        currency=detail.currency,
        evaluation_rate_percent=detail.evaluation_rate_percent,
        sales_count=detail.sales_count,
        commission_rate=detail.commission_rate,
        ship_to_days_raw=detail.ship_to_days_raw,
        delivery_days=detail.delivery_days,
        availability=availability,
    )


def _unknown_observation(offer, *, now):
    return OfferObservation.objects.create(
        offer=offer,
        observed_at=now,
        destination_country="PT",
        availability=OfferObservation.Availability.UNKNOWN,
    )


def _unavailable_observation(offer, *, now):
    return OfferObservation.objects.create(
        offer=offer,
        observed_at=now,
        destination_country="PT",
        availability=OfferObservation.Availability.UNAVAILABLE,
    )


def _deactivate_unavailable_offer(offer, *, result):
    result.unavailable_confirmed += 1
    if offer.is_active:
        offer.is_active = False
        offer.save(update_fields=["is_active", "updated_at"])
        result.offers_deactivated += 1


def maintain_catalog_offers(*, batch_size, client=None, now=None):
    client = client or AliExpressClient()
    now = now or timezone.now()
    result = MaintenanceResult()
    offers = select_maintenance_batch(batch_size)
    result.offers_selected = len(offers)

    with maintenance_run_lock():
        for offer in offers:
            # Avoid creating a new affiliate URL for an approved-but-unpublished offer.
            # Already linked offers can still be rechecked without publishing them.
            if not (offer.owner_hidden and not offer.affiliate_url):
                result.promotion_attempts += 1
                try:
                    promotion_status = verify_affiliate_promotion(offer, client=client, now=now)
                except AliExpressRuntimeStateError:
                    raise
                except AliExpressRateLimitError:
                    raise
                except (AliExpressError, ValueError) as exc:
                    result.promotion_transient_failures += 1
                    result.failures.append(
                        f"{offer.external_product_id}:Promotion:{exc.__class__.__name__}"
                    )
                else:
                    if promotion_status == Offer.AffiliatePromotionStatus.ELIGIBLE:
                        result.promotion_eligible += 1
                    elif promotion_status == Offer.AffiliatePromotionStatus.INELIGIBLE:
                        result.promotion_ineligible += 1

            result.detail_attempts += 1
            try:
                detail = client.get_product_detail(offer.external_product_id, "PT", "EUR")
            except AliExpressRuntimeStateError:
                raise
            except AliExpressRateLimitError:
                raise
            except AliExpressAPIError as exc:
                if is_factually_unavailable_error(exc):
                    _unavailable_observation(offer, now=now)
                    _deactivate_unavailable_offer(offer, result=result)
                    continue
                result.transient_failures += 1
                result.failures.append(f"{offer.external_product_id}:{exc.__class__.__name__}")
                _unknown_observation(offer, now=now)
                continue
            except AliExpressError as exc:
                result.transient_failures += 1
                result.failures.append(f"{offer.external_product_id}:{exc.__class__.__name__}")
                _unknown_observation(offer, now=now)
                continue

            if detail.product_id != offer.external_product_id:
                result.transient_failures += 1
                result.failures.append(f"{offer.external_product_id}:ProductIdMismatch")
                _unknown_observation(offer, now=now)
                continue

            if is_factually_unavailable(detail):
                _observation_from_detail(
                    offer,
                    detail,
                    now=now,
                    availability=OfferObservation.Availability.UNAVAILABLE,
                )
                _deactivate_unavailable_offer(offer, result=result)
                continue

            if not is_factually_available(detail):
                result.transient_failures += 1
                result.failures.append(f"{offer.external_product_id}:InsufficientDetail")
                _unknown_observation(offer, now=now)
                continue

            _observation_from_detail(
                offer,
                detail,
                now=now,
                availability=OfferObservation.Availability.AVAILABLE,
            )
            result.available_confirmed += 1
            offer.title = detail.title or offer.title
            offer.product_url = detail.product_url or offer.product_url
            offer.image_url = detail.image_url or offer.image_url
            offer.last_seen_at = now
            offer.save(
                update_fields=[
                    "title",
                    "product_url",
                    "image_url",
                    "last_seen_at",
                    "updated_at",
                ]
            )
    return result
