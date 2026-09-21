from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import (
    CandidateDecision,
    Offer,
    OfferCandidate,
    OfferFamilyPlacement,
    OfferObservation,
)
from apps.integrations.aliexpress.client import AliExpressClient


class CandidateApprovalError(ValueError):
    pass


@dataclass(frozen=True)
class ApprovalResult:
    candidate: OfferCandidate
    offer: Offer
    observation: OfferObservation
    placement: OfferFamilyPlacement
    decision: CandidateDecision


def _require_staff(user):
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateApprovalError("Staff user required")


def _affiliate_url(candidate, client):
    if not candidate.product_url:
        raise CandidateApprovalError("Candidate has no product URL")
    return client.generate_affiliate_link(candidate.product_url)


def approve_candidate(candidate, *, user, client=None, now=None):
    """Persist the Owner's fixed-protocol human attestation as an approval."""
    _require_staff(user)
    now = now or timezone.now()

    with transaction.atomic():
        family = candidate.product_family
        ProductFamily = type(family)
        locked_family = ProductFamily.objects.select_for_update().get(pk=family.pk)
        if locked_family.status == ProductFamily.Status.RETIRED:
            raise CandidateApprovalError("Retired family cannot receive approvals")
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)

        existing_offer = (
            Offer.objects.filter(pk=locked.approved_offer_id).first()
            if locked.approved_offer_id
            else None
        )
        if existing_offer and existing_offer.affiliate_url:
            affiliate_url = existing_offer.affiliate_url
        else:
            client = client or AliExpressClient()
            affiliate_url = _affiliate_url(locked, client)

        defaults = {
            "title": locked.title,
            "product_url": locked.product_url,
            "image_url": locked.image_url,
            "affiliate_url": affiliate_url,
            "affiliate_promotion_status": Offer.AffiliatePromotionStatus.ELIGIBLE,
            "affiliate_promotion_verified_at": now,
            "protocol_verified_at": now,
            "is_active": True,
            "owner_hidden": True,
            "first_seen_at": now,
            "last_seen_at": now,
        }
        offer, created = Offer.objects.get_or_create(
            source=locked.source,
            external_product_id=locked.external_product_id,
            defaults=defaults,
        )
        if not created:
            offer.title = locked.title or offer.title
            offer.product_url = locked.product_url or offer.product_url
            offer.image_url = locked.image_url or offer.image_url
            offer.affiliate_url = affiliate_url
            offer.protocol_verified_at = now
            offer.is_active = True
            offer.last_seen_at = now
            # Approval is not an editorial publish action: preserve owner_hidden exactly.
        offer.save()

        observation = OfferObservation.objects.create(
            offer=offer,
            observed_at=now,
            destination_country="PT",
            price=locked.price,
            original_price=locked.original_price,
            currency=locked.currency,
            evaluation_rate_percent=locked.evaluation_rate_percent,
            sales_count=locked.sales_count,
            commission_rate=locked.commission_rate,
            search_ship_to_days_raw=locked.search_ship_to_days_raw,
            search_delivery_days=locked.search_delivery_days,
            ship_to_days_raw=locked.detail_ship_to_days_raw,
            delivery_days=locked.detail_delivery_days,
            availability=OfferObservation.Availability.UNKNOWN,
        )
        placement, _ = OfferFamilyPlacement.objects.get_or_create(
            offer=offer,
            product_family=family,
            defaults={"selection_position": None},
        )
        locked.status = OfferCandidate.Status.APPROVED
        locked.approved_offer = offer
        locked.save(update_fields=["status", "approved_offer", "updated_at"])
        decision = CandidateDecision.objects.create(
            candidate=locked,
            decision=CandidateDecision.Decision.APPROVE,
            ship_from_country="",
            review_signals=[CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED],
            decided_by=user,
            decided_at=now,
        )
    return ApprovalResult(locked, offer, observation, placement, decision)


def reject_candidate(
    candidate,
    *,
    user,
    review_signals=None,
    reason="",
    ship_from_country="",
    evidence_url="",
    note="",
    now=None,
):
    _require_staff(user)
    normalized_signals = []
    if review_signals is not None:
        valid_signals = set(CandidateDecision.ReviewSignal.values)
        for signal in review_signals:
            if signal not in valid_signals:
                raise CandidateApprovalError("Sinal de revisão inválido")
            if signal not in normalized_signals:
                normalized_signals.append(signal)
    note = (note or "").strip()
    if reason:
        if reason not in CandidateDecision.Reason.values:
            raise CandidateApprovalError("Valid rejection reason required")
        if reason == CandidateDecision.Reason.OTHER and not note:
            raise CandidateApprovalError("Other rejection reason requires a note")
    if not normalized_signals and not reason:
        raise CandidateApprovalError("Selecione pelo menos um sinal ou motivo para rejeitar")
    if review_signals is not None:
        ship_from_country = ""
        evidence_url = ""

    now = now or timezone.now()
    with transaction.atomic():
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        locked.status = OfferCandidate.Status.REJECTED
        locked.save(update_fields=["status", "updated_at"])
        if locked.approved_offer_id:
            Offer.objects.filter(pk=locked.approved_offer_id).update(protocol_verified_at=None)
        return CandidateDecision.objects.create(
            candidate=locked,
            decision=CandidateDecision.Decision.REJECT,
            ship_from_country=(ship_from_country or "").upper(),
            reason=reason,
            review_signals=normalized_signals,
            note=note,
            evidence_url=evidence_url,
            decided_by=user,
            decided_at=now,
        )


def revalidate_candidate(candidate, *, user, now=None):
    """Refresh the Owner's fixed-protocol human attestation without inventing country."""
    _require_staff(user)
    now = now or timezone.now()
    with transaction.atomic():
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        if not locked.approved_offer_id:
            raise CandidateApprovalError("Candidate has no approved offer to revalidate")
        offer = Offer.objects.select_for_update().get(pk=locked.approved_offer_id)
        offer.protocol_verified_at = now
        offer.save(update_fields=["protocol_verified_at", "updated_at"])
        decision = CandidateDecision.objects.create(
            candidate=locked,
            decision=CandidateDecision.Decision.APPROVE,
            ship_from_country="",
            review_signals=[CandidateDecision.ReviewSignal.DELIVERS_TO_PT_CONFIRMED],
            note="Protocol revalidated",
            decided_by=user,
            decided_at=now,
        )
        return decision
