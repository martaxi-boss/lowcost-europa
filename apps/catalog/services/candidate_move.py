from django.db import transaction

from apps.catalog.models import CandidateFamilyMoveEvent, OfferCandidate, ProductFamily


class CandidateMoveError(ValueError):
    pass


@transaction.atomic
def move_candidate_to_family(candidate, *, target_family, user):
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateMoveError("Staff user required")
    if not isinstance(target_family, ProductFamily):
        raise CandidateMoveError("Target family required")
    if target_family.status == ProductFamily.Status.RETIRED:
        raise CandidateMoveError("Retired family cannot receive candidates")

    locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
    if locked.product_family_id == target_family.pk:
        raise CandidateMoveError("Candidate already belongs to target family")
    if locked.status == OfferCandidate.Status.APPROVED or locked.approved_offer_id:
        raise CandidateMoveError("Approved candidate must be rejected before reclassification")

    from_family = locked.product_family
    title_snapshot = locked.title
    locked.product_family = target_family
    locked.status = OfferCandidate.Status.PENDING
    locked.approved_offer = None
    locked.save(update_fields=["product_family", "status", "approved_offer", "updated_at"])
    CandidateFamilyMoveEvent.objects.create(
        candidate=locked,
        from_family=from_family,
        to_family=target_family,
        title_snapshot=title_snapshot,
        acted_by=user,
    )
    return locked, True
