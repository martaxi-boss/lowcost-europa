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
    ALLOWED_SHIP_FROM_COUNTRIES,
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


def _affiliate_url(candidate, client):
    if not candidate.product_url:
        raise CandidateApprovalError("Candidate has no product URL")
    return client.generate_affiliate_link(candidate.product_url)


def approve_candidate(
    candidate, *, ship_from_country, user, evidence_url="", note="", client=None, now=None
):
    country = (ship_from_country or "").upper()
    if country not in ALLOWED_SHIP_FROM_COUNTRIES:
        raise CandidateApprovalError("Approval requires PL/CZ/FR/ES/DE")
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateApprovalError("Staff user required")
    now = now or timezone.now()
    if (
        candidate.approved_offer_id
        and candidate.approved_offer
        and candidate.approved_offer.affiliate_url
    ):
        affiliate_url = candidate.approved_offer.affiliate_url
    else:
        client = client or AliExpressClient()
        affiliate_url = _affiliate_url(candidate, client)
    with transaction.atomic():
        family = candidate.product_family
        ProductFamily = type(family)
        ProductFamily.objects.select_for_update().get(pk=family.pk)
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        eligible_count = OfferFamilyPlacement.objects.filter(
            product_family=family, offer__in=Offer.objects.filter(public_eligibility_q(now))
        ).count()
        if eligible_count >= MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY:
            if not (
                locked.approved_offer_id
                and Offer.objects.filter(pk=locked.approved_offer_id)
                .filter(public_eligibility_q(now))
                .exists()
            ):
                raise CandidateApprovalError("Family already has 20 fresh public-eligible offers")
        defaults = dict(
            title=locked.title,
            product_url=locked.product_url,
            image_url=locked.image_url,
            affiliate_url=affiliate_url,
            is_active=True,
            first_seen_at=now,
            last_seen_at=now,
        )
        offer, created = Offer.objects.get_or_create(
            source=locked.source, external_product_id=locked.external_product_id, defaults=defaults
        )
        if not created:
            offer.title = locked.title or offer.title
            offer.product_url = locked.product_url or offer.product_url
            offer.image_url = locked.image_url or offer.image_url
            offer.affiliate_url = affiliate_url
            offer.is_active = True
            offer.last_seen_at = now
        offer.ship_from_country = country
        offer.ship_from_verified_at = now
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
            offer=offer, product_family=family, defaults={"selection_position": None}
        )
        locked.status = OfferCandidate.Status.APPROVED
        locked.approved_offer = offer
        locked.save(update_fields=["status", "approved_offer", "updated_at"])
        decision = CandidateDecision.objects.create(
            candidate=locked,
            decision=CandidateDecision.Decision.APPROVE,
            ship_from_country=country,
            note=note,
            evidence_url=evidence_url,
            decided_by=user,
            decided_at=now,
        )
    return ApprovalResult(locked, offer, observation, placement, decision)


def reject_candidate(
    candidate, *, user, reason, ship_from_country="", evidence_url="", note="", now=None
):
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateApprovalError("Staff user required")
    if reason not in CandidateDecision.Reason.values:
        raise CandidateApprovalError("Valid rejection reason required")
    now = now or timezone.now()
    with transaction.atomic():
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        locked.status = OfferCandidate.Status.REJECTED
        locked.save(update_fields=["status", "updated_at"])
        if locked.approved_offer_id:
            Offer.objects.filter(pk=locked.approved_offer_id).update(
                ship_from_country=None, ship_from_verified_at=None
            )
        return CandidateDecision.objects.create(
            candidate=locked,
            decision=CandidateDecision.Decision.REJECT,
            ship_from_country=(ship_from_country or "").upper(),
            reason=reason,
            note=note,
            evidence_url=evidence_url,
            decided_by=user,
            decided_at=now,
        )


def revalidate_candidate(
    candidate,
    *,
    user,
    ship_from_country=None,
    confirmed=True,
    reason=CandidateDecision.Reason.ORIGIN_NOT_CONFIRMED,
    evidence_url="",
    note="",
    now=None,
):
    candidate = OfferCandidate.objects.select_related("approved_offer").get(pk=candidate.pk)
    if not candidate.approved_offer_id:
        raise CandidateApprovalError("Candidate has no approved offer to revalidate")
    if confirmed:
        return approve_candidate(
            candidate,
            ship_from_country=ship_from_country,
            user=user,
            evidence_url=evidence_url,
            note=note,
            now=now,
        )
    return reject_candidate(
        candidate,
        user=user,
        reason=reason,
        ship_from_country=ship_from_country or "",
        evidence_url=evidence_url,
        note=note,
        now=now,
    )
