from django.db import transaction

from apps.catalog.models import OfferCandidate, ProductFamily


class CandidateMoveError(ValueError):
    pass


@transaction.atomic
def move_candidate_to_family(candidate, *, target_family, user):
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateMoveError("Staff user required")
    if not isinstance(target_family, ProductFamily):
        raise CandidateMoveError("Target family required")

    locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
    if locked.product_family_id == target_family.pk:
        raise CandidateMoveError("Candidate already belongs to target family")
    if locked.status == OfferCandidate.Status.APPROVED or locked.approved_offer_id:
        raise CandidateMoveError("Approved candidate must be rejected before reclassification")

    locked.product_family = target_family
    locked.status = OfferCandidate.Status.PENDING
    locked.approved_offer = None
    locked.save(update_fields=["product_family", "status", "approved_offer", "updated_at"])
    return locked, True
