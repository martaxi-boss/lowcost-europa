from django.db import transaction

from apps.catalog.models import OfferCandidate, ProductFamily


class CandidateMoveError(ValueError):
    pass


_COPY_FIELDS = (
    "title",
    "image_url",
    "product_url",
    "price",
    "original_price",
    "currency",
    "evaluation_rate_percent",
    "sales_count",
    "commission_rate",
    "search_ship_to_days_raw",
    "search_delivery_days",
    "detail_ship_to_days_raw",
    "detail_delivery_days",
    "last_observed_at",
)


@transaction.atomic
def move_candidate_to_family(candidate, *, target_family, user):
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateMoveError("Staff user required")
    if not isinstance(target_family, ProductFamily):
        raise CandidateMoveError("Target family required")

    locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
    if locked.product_family_id == target_family.pk:
        raise CandidateMoveError("Candidate already belongs to target family")

    existing = (
        OfferCandidate.objects.select_for_update()
        .filter(
            product_family=target_family,
            source=locked.source,
            external_product_id=locked.external_product_id,
        )
        .first()
    )
    if existing:
        for field in _COPY_FIELDS:
            setattr(existing, field, getattr(locked, field))
        if existing.status != OfferCandidate.Status.APPROVED:
            existing.status = OfferCandidate.Status.PENDING
            existing.approved_offer = None
            update_fields = [*_COPY_FIELDS, "status", "approved_offer", "updated_at"]
        else:
            update_fields = [*_COPY_FIELDS, "updated_at"]
        existing.save(update_fields=update_fields)
        return existing, False

    locked.product_family = target_family
    locked.status = OfferCandidate.Status.PENDING
    locked.approved_offer = None
    locked.save(update_fields=["product_family", "status", "approved_offer", "updated_at"])
    return locked, True
