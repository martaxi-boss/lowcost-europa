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


OWNER_REJECTION_REASON_CHOICES = (
    (CandidateDecision.Reason.DOES_NOT_SHIP_TO_PT, "Não envia para Portugal"),
    (
        CandidateDecision.Reason.PT_DELIVERY_NOT_CONFIRMED,
        "Não consigo confirmar entrega em Portugal",
    ),
    (
        CandidateDecision.Reason.ORIGIN_NOT_CONFIRMED,
        "País de envio não aparece / não consigo confirmar",
    ),
    (
        CandidateDecision.Reason.ORIGIN_NOT_ALLOWED,
        "País de envio fora dos cinco países permitidos",
    ),
    (CandidateDecision.Reason.WRONG_FAMILY, "Produto pertence a outra família"),
    (
        CandidateDecision.Reason.ACCESSORY_OR_PART,
        "Acessório, peça, cartucho ou consumível",
    ),
    (CandidateDecision.Reason.DUPLICATE, "Produto duplicado"),
    (CandidateDecision.Reason.LISTING_UNAVAILABLE, "Anúncio indisponível"),
    (CandidateDecision.Reason.LISTING_CHANGED, "Anúncio ou variante mudou"),
    (
        CandidateDecision.Reason.POOR_LISTING,
        "Oferta/listagem sem qualidade suficiente",
    ),
    (CandidateDecision.Reason.OTHER, "Outro motivo"),
)


@dataclass(frozen=True)
class ApprovalResult:
    candidate: OfferCandidate
    offer: Offer
    observation: OfferObservation
    placement: OfferFamilyPlacement
    decision: CandidateDecision


def _require_staff(user):
    if not user or not user.is_authenticated or not user.is_staff:
        raise CandidateApprovalError("Acesso de proprietário necessário")


def _affiliate_url(candidate, client):
    if not candidate.product_url:
        raise CandidateApprovalError("O produto não tem link do anúncio.")
    return client.generate_affiliate_link(candidate.product_url)


def approve_candidate(candidate, *, user, client=None, now=None):
    """Persist the Owner's composite fixed-protocol human attestation."""
    _require_staff(user)
    now = now or timezone.now()

    with transaction.atomic():
        family = candidate.product_family
        ProductFamily = type(family)
        locked_family = ProductFamily.objects.select_for_update().get(pk=family.pk)
        if locked_family.status == ProductFamily.Status.RETIRED:
            raise CandidateApprovalError("Não é possível aprovar numa família retirada.")
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        if locked.status != OfferCandidate.Status.PENDING:
            raise CandidateApprovalError("Este produto já não está em A rever.")
        if not locked.product_url:
            raise CandidateApprovalError("O produto não tem link do anúncio.")

        existing_offer = (
            Offer.objects.select_for_update()
            .filter(
                source=locked.source,
                external_product_id=locked.external_product_id,
            )
            .first()
        )
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
        if existing_offer is None:
            offer, created = Offer.objects.get_or_create(
                source=locked.source,
                external_product_id=locked.external_product_id,
                defaults=defaults,
            )
        else:
            offer, created = existing_offer, False
        if not created:
            offer.title = locked.title or offer.title
            offer.product_url = locked.product_url or offer.product_url
            offer.image_url = locked.image_url or offer.image_url
            offer.affiliate_url = affiliate_url
            offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.ELIGIBLE
            offer.affiliate_promotion_verified_at = now
            offer.protocol_verified_at = now
            offer.is_active = True
            offer.last_seen_at = now
            # Preserve independently known factual ship-from metadata.
            offer.save(
                update_fields=[
                    "title",
                    "product_url",
                    "image_url",
                    "affiliate_url",
                    "affiliate_promotion_status",
                    "affiliate_promotion_verified_at",
                    "protocol_verified_at",
                    "is_active",
                    "last_seen_at",
                    "updated_at",
                ]
            )

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
            review_signals=[],
            decided_by=user,
            decided_at=now,
        )
    return ApprovalResult(locked, offer, observation, placement, decision)


def reject_candidate(candidate, *, user, reason="", note="", now=None):
    _require_staff(user)
    if reason not in CandidateDecision.Reason.values:
        raise CandidateApprovalError("Selecione o motivo da rejeição.")
    note = (note or "").strip()
    if reason == CandidateDecision.Reason.OTHER and not note:
        raise CandidateApprovalError("Descreva o motivo em Outro motivo.")

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
            ship_from_country="",
            reason=reason,
            review_signals=[],
            note=note,
            evidence_url="",
            decided_by=user,
            decided_at=now,
        )


def revalidate_candidate(candidate, *, user, now=None):
    """Refresh the Owner's composite human attestation without inventing country."""
    _require_staff(user)
    now = now or timezone.now()
    with transaction.atomic():
        locked = OfferCandidate.objects.select_for_update().get(pk=candidate.pk)
        if not locked.approved_offer_id:
            raise CandidateApprovalError("O produto não tem oferta aprovada para revalidar.")
        offer = Offer.objects.select_for_update().get(pk=locked.approved_offer_id)
        offer.protocol_verified_at = now
        offer.save(update_fields=["protocol_verified_at", "updated_at"])
        decision = CandidateDecision.objects.create(
            candidate=locked,
            decision=CandidateDecision.Decision.APPROVE,
            ship_from_country="",
            review_signals=[],
            note="Protocolo revalidado",
            decided_by=user,
            decided_at=now,
        )
        return decision
