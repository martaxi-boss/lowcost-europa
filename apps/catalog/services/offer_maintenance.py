import errno
import fcntl
import os
import stat
from contextlib import contextmanager
from dataclasses import dataclass, field

from django.db.models import F, Max
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError

MAINTENANCE_LOCK_PATH = "/tmp/lowcost-europa-catalog-maintenance.lock"

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


@dataclass
class MaintenanceResult:
    offers_selected: int = 0
    detail_attempts: int = 0
    available_confirmed: int = 0
    unavailable_confirmed: int = 0
    transient_failures: int = 0
    offers_deactivated: int = 0
    failures: list[str] = field(default_factory=list)


def is_factually_unavailable(product):
    raw = " ".join(str(getattr(product, "availability_raw", "") or "").lower().split())
    return raw in _UNAVAILABLE_VALUES


def is_factually_available(product):
    if is_factually_unavailable(product):
        return False
    return bool(product.product_id and (product.product_url or product.title))


@contextmanager
def maintenance_run_lock(path=MAINTENANCE_LOCK_PATH):
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
        Offer.objects.filter(source=Offer.Source.ALIEXPRESS)
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


def maintain_catalog_offers(*, batch_size, client=None, now=None):
    client = client or AliExpressClient()
    now = now or timezone.now()
    result = MaintenanceResult()
    offers = select_maintenance_batch(batch_size)
    result.offers_selected = len(offers)

    with maintenance_run_lock():
        for offer in offers:
            result.detail_attempts += 1
            try:
                detail = client.get_product_detail(offer.external_product_id, "PT", "EUR")
            except AliExpressRateLimitError:
                raise
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
                result.unavailable_confirmed += 1
                if offer.is_active:
                    offer.is_active = False
                    offer.save(update_fields=["is_active", "updated_at"])
                    result.offers_deactivated += 1
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
            offer.is_active = True
            offer.save(
                update_fields=[
                    "title",
                    "product_url",
                    "image_url",
                    "last_seen_at",
                    "is_active",
                    "updated_at",
                ]
            )
    return result
