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
from apps.catalog.services.public_eligibility import (
    MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY,
    public_eligibility_q,
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
    """Persist a human protocol-match approval without inventing ship-from country."""
    _require_staff(user)
    now = now or timezone.now()

    with transaction.atomic():
        family = candidate.product_family
        ProductFamily = type(family)
        ProductFamily.objects.select_for_update().get(pk=family.pk)
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        eligible_count = OfferFamilyPlacement.objects.filter(
            product_family=family,
            offer__in=Offer.objects.filter(public_eligibility_q(now)),
        ).count()
        if eligible_count >= MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY:
            if not (
                locked.approved_offer_id
                and Offer.objects.filter(pk=locked.approved_offer_id)
                .filter(public_eligibility_q(now))
                .exists()
            ):
                raise CandidateApprovalError("Family already has 20 fresh public-eligible offers")

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
            "is_active": True,
            "protocol_verified_at": now,
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
            offer.is_active = True
            offer.protocol_verified_at = now
            offer.last_seen_at = now
        # Historical ship-from fields are preserved and never inferred by one-click approval.
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
        if not normalized_signals:
            raise CandidateApprovalError("Selecione pelo menos uma opção para rejeitar")
        # The new multi-signal flow never invents a legacy primary reason.
        reason = ""
        ship_from_country = ""
        evidence_url = ""
        note = ""
    elif reason:
        # Legacy/internal compatibility for historical semantic workflows and tests.
        if reason not in CandidateDecision.Reason.values:
            raise CandidateApprovalError("Valid rejection reason required")
        if reason == CandidateDecision.Reason.OTHER and not (note or "").strip():
            raise CandidateApprovalError("Other rejection reason requires a note")
    else:
        raise CandidateApprovalError("Selecione pelo menos uma opção para rejeitar")

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
    """Record one-click human protocol revalidation without touching country history."""
    _require_staff(user)
    now = now or timezone.now()
    with transaction.atomic():
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        if not locked.approved_offer_id:
            raise CandidateApprovalError("Candidate has no approved offer to revalidate")
        Offer.objects.filter(pk=locked.approved_offer_id).update(protocol_verified_at=now)
        decision = CandidateDecision.objects.create(
            candidate=locked,
            decision=CandidateDecision.Decision.APPROVE,
            ship_from_country="",
            note="Protocol revalidated",
            decided_by=user,
            decided_at=now,
        )
        return decision
