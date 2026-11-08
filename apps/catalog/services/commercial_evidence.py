"""Read-only, evidence-backed commercial status for the private Owner panel.

No provider calls on GET, no editorial writes and no invented stock/warehouse facts.
Do not conflate seller listing signals with verified SKU inventory.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily
from apps.catalog.services.public_eligibility import (
    is_protocol_verified,
    is_ship_from_verified,
    public_eligibility_q,
)

ACTIVE_FAMILY_STATUSES = (
    ProductFamily.Status.NEW,
    ProductFamily.Status.TESTING,
    ProductFamily.Status.VERIFIED,
    ProductFamily.Status.PROVEN,
    ProductFamily.Status.WINNER,
    ProductFamily.Status.OBSERVATION,
)


@dataclass(frozen=True)
class CommercialEvidenceRow:
    offer_id: int
    title: str
    family_name: str
    family_slug: str
    product_url: str
    publication: str
    price: Decimal | None
    price_at: datetime | None
    price_state: str
    origin: str
    origin_at: datetime | None
    availability: str
    availability_at: datetime | None
    delivery: str
    delivery_at: datetime | None
    delivery_state: str


def _delivery_label(search_days, detail_days):
    search_days = search_days if search_days and search_days > 0 else None
    detail_days = detail_days if detail_days and detail_days > 0 else None
    if search_days and detail_days:
        if search_days == detail_days:
            return f"Pesquisa e detalhe: {search_days} dias"
        return f"Estimativas divergentes: {search_days} / {detail_days} dias"
    if search_days:
        return f"Pesquisa: {search_days} dias"
    if detail_days:
        return f"Detalhe: {detail_days} dias"
    return "Prazo não confirmado"


def owner_commercial_evidence_rows(*, as_of=None):
    """One bounded DB query per fact; no N+1 and no external requests."""
    as_of = as_of or timezone.now()
    active = Offer.objects.filter(
        is_active=True,
        owner_hidden=False,
        family_placements__product_family__status__in=ACTIVE_FAMILY_STATUSES,
    ).distinct()
    public_ids = set(
        active.filter(public_eligibility_q(as_of)).values_list("pk", flat=True)
    )
    technical_ids = set(
        active.filter(
            public_eligibility_q(as_of, require_recent_price=False)
        ).values_list("pk", flat=True)
    )
    newest = OfferObservation.objects.filter(
        offer_id=OuterRef("pk"), observed_at__lte=as_of
    ).order_by("-observed_at", "-pk")
    eur_price = newest.filter(price__gt=0, currency__iexact="EUR")
    # Do not display an estimate for Spain or an unknown destination as PT.
    delivery = newest.filter(destination_country="PT").filter(
        Q(search_delivery_days__gt=0) | Q(delivery_days__gt=0)
    )
    offers = (
        active.annotate(
            evidence_last_availability=Subquery(newest.values("availability")[:1]),
            evidence_last_checked=Subquery(newest.values("observed_at")[:1]),
            evidence_last_eur_price=Subquery(eur_price.values("price")[:1]),
            evidence_last_eur_price_at=Subquery(eur_price.values("observed_at")[:1]),
            evidence_search_delivery=Subquery(
                delivery.values("search_delivery_days")[:1]
            ),
            evidence_detail_delivery=Subquery(delivery.values("delivery_days")[:1]),
            evidence_delivery_at=Subquery(delivery.values("observed_at")[:1]),
        )
        .prefetch_related(
            Prefetch(
                "family_placements",
                queryset=OfferFamilyPlacement.objects.select_related(
                    "product_family"
                ).order_by("product_family__display_order", "pk"),
                to_attr="evidence_placements",
            )
        )
        .order_by("pk")
    )
    rows = []
    for offer in offers:
        placements = [
            item for item in offer.evidence_placements
            if item.product_family.status in ACTIVE_FAMILY_STATUSES
        ]
        if not placements:
            continue
        if offer.pk in public_ids:
            publication = "Na montra"
        elif offer.pk in technical_ids:
            publication = "Retida — preço sem prova recente"
        elif (
            not offer.affiliate_url.startswith("https://")
            or offer.affiliate_promotion_status
            != Offer.AffiliatePromotionStatus.ELIGIBLE
            or offer.affiliate_promotion_verified_at is None
        ):
            publication = "Bloqueada — promoção/link"
        elif not is_protocol_verified(offer, as_of):
            publication = "Bloqueada — revisão editorial"
        else:
            publication = "Bloqueada — verificar"

        price_at = offer.evidence_last_eur_price_at
        if price_at is None:
            price_state = "Sem preço positivo EUR registado"
        elif price_at >= as_of - timedelta(hours=24):
            price_state = "Observação recente (até 24 h)"
        else:
            price_state = "Histórico — preço não confirmado em 24 h"

        origin_at = offer.ship_from_verified_at if is_ship_from_verified(
            offer, as_of=as_of
        ) else None
        origin = (
            f"{offer.ship_from_country} — registado em revisão editorial"
            if origin_at is not None
            else "País/armazém por confirmar"
        )

        status = offer.evidence_last_availability
        if status == OfferObservation.Availability.UNAVAILABLE:
            availability = "Anúncio indicado como indisponível"
        elif status == OfferObservation.Availability.AVAILABLE:
            availability = "Anúncio indica disponível; SKU por confirmar"
        else:
            availability = "Stock por variante não confirmado"

        delivery_at = offer.evidence_delivery_at
        delivery_label = _delivery_label(
            offer.evidence_search_delivery, offer.evidence_detail_delivery
        )
        if delivery_at is None:
            delivery_state = "Sem prova de prazo"
        elif delivery_at < as_of - timedelta(days=7):
            delivery_state = "Histórico antigo — confirmar no vendedor"
        else:
            delivery_state = "Estimativa observada — não é garantia"

        rows.append(
            CommercialEvidenceRow(
                offer_id=offer.pk,
                title=offer.title or "Oferta sem título",
                family_name=", ".join(dict.fromkeys(
                    item.product_family.name for item in placements
                )),
                family_slug=placements[0].product_family.slug,
                product_url=offer.product_url
                if offer.product_url.startswith("https://") else "",
                publication=publication,
                price=offer.evidence_last_eur_price,
                price_at=price_at,
                price_state=price_state,
                origin=origin,
                origin_at=origin_at,
                availability=availability,
                availability_at=offer.evidence_last_checked,
                delivery=delivery_label,
                delivery_at=delivery_at,
                delivery_state=delivery_state,
            )
        )
    return rows
