from django.db import transaction

from apps.catalog.models import (
    CandidateFamilyMoveEvent,
    Offer,
    OfferCandidate,
    OfferFamilyPlacement,
    ProductFamily,
)


class CandidateMoveError(ValueError):
    pass


def _require_staff(user):
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateMoveError("Staff user required")


def _move_approved_offer(locked_candidate, *, from_family, target_family):
    offer = Offer.objects.select_for_update().get(pk=locked_candidate.approved_offer_id)
    origin_placements = list(
        OfferFamilyPlacement.objects.select_for_update().filter(
            offer=offer, product_family=from_family
        )
    )
    target_placement = (
        OfferFamilyPlacement.objects.select_for_update()
        .filter(offer=offer, product_family=target_family)
        .first()
    )
    if target_placement is None:
        source = origin_placements[0] if origin_placements else None
        target_placement = OfferFamilyPlacement.objects.create(
            offer=offer,
            product_family=target_family,
            selection_position=None,
            display_order=source.display_order if source else 0,
            selection_reason=source.selection_reason if source else "",
        )
    OfferFamilyPlacement.objects.filter(offer=offer, product_family=from_family).delete()

    update_fields = []
    if not offer.owner_hidden:
        offer.owner_hidden = True
        update_fields.append("owner_hidden")
    if offer.product_family_id != target_family.pk:
        offer.product_family = target_family
        update_fields.append("product_family")
    if offer.is_primary:
        conflicting_primary = (
            Offer.objects.select_for_update()
            .filter(product_family=target_family, is_primary=True)
            .exclude(pk=offer.pk)
            .exists()
        )
        if conflicting_primary:
            offer.is_primary = False
            update_fields.append("is_primary")
    if update_fields:
        offer.save(update_fields=[*update_fields, "updated_at"])
    return offer, target_placement


@transaction.atomic
def move_candidate_to_family(candidate, *, target_family, user):
    _require_staff(user)
    if not isinstance(target_family, ProductFamily):
        raise CandidateMoveError("Target family required")

    try:
        locked_target = ProductFamily.objects.select_for_update().get(pk=target_family.pk)
    except ProductFamily.DoesNotExist as exc:
        raise CandidateMoveError("Target family required") from exc
    if locked_target.status == ProductFamily.Status.RETIRED:
        raise CandidateMoveError("Retired family cannot receive candidates")

    locked = (
        OfferCandidate.objects.select_for_update()
        .select_related("product_family")
        .get(pk=candidate.pk)
    )
    if locked.product_family_id == locked_target.pk:
        raise CandidateMoveError("Candidate already belongs to target family")

    from_family = locked.product_family
    title_snapshot = locked.title
    was_approved = locked.status == OfferCandidate.Status.APPROVED

    if was_approved:
        if not locked.approved_offer_id:
            raise CandidateMoveError("Approved candidate has no approved offer")
        _move_approved_offer(locked, from_family=from_family, target_family=locked_target)
        locked.product_family = locked_target
        locked.save(update_fields=["product_family", "updated_at"])
    else:
        locked.product_family = locked_target
        locked.status = OfferCandidate.Status.PENDING
        locked.approved_offer = None
        locked.save(update_fields=["product_family", "status", "approved_offer", "updated_at"])

    CandidateFamilyMoveEvent.objects.create(
        candidate=locked,
        from_family=from_family,
        to_family=locked_target,
        title_snapshot=title_snapshot,
        acted_by=user,
    )
    return locked, True
