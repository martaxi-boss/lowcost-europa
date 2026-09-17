from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Offer, OfferEditorialEvent, OfferFamilyPlacement, ProductFamily
from apps.catalog.services.public_eligibility import (
    ALLOWED_SHIP_FROM_COUNTRIES,
    MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY,
    is_protocol_verification_fresh,
    public_eligibility_q,
)


class OwnerEditorialError(ValueError):
    pass


@dataclass(frozen=True)
class OwnerEditorialResult:
    offer: Offer
    event: OfferEditorialEvent | None
    changed: bool


def _require_staff(user):
    if not user or not user.is_authenticated or not user.is_staff:
        raise OwnerEditorialError("Acesso de proprietário necessário")


@transaction.atomic
def hide_offer_from_storefront(offer, *, user, now=None):
    _require_staff(user)
    now = now or timezone.now()
    locked = Offer.objects.select_for_update().get(pk=offer.pk)
    if locked.owner_hidden:
        return OwnerEditorialResult(locked, None, False)
    previous = locked.owner_hidden
    locked.owner_hidden = True
    locked.save(update_fields=["owner_hidden", "updated_at"])
    event = OfferEditorialEvent.objects.create(
        offer=locked,
        action=OfferEditorialEvent.Action.HIDE,
        previous_owner_hidden=previous,
        new_owner_hidden=True,
        acted_by=user,
        acted_at=now,
    )
    return OwnerEditorialResult(locked, event, True)


@transaction.atomic
def publish_offer_to_storefront(offer, *, family, user, now=None):
    _require_staff(user)
    now = now or timezone.now()
    locked_family = ProductFamily.objects.select_for_update().get(pk=family.pk)
    locked = Offer.objects.select_for_update().get(pk=offer.pk)
    if not locked.owner_hidden:
        return OwnerEditorialResult(locked, None, False)
    if locked_family.status == ProductFamily.Status.RETIRED:
        raise OwnerEditorialError("Não é possível publicar numa família retirada")
    if not OfferFamilyPlacement.objects.filter(offer=locked, product_family=locked_family).exists():
        raise OwnerEditorialError("A oferta não tem uma colocação válida nesta família")
    if not locked.is_active:
        raise OwnerEditorialError("A oferta está indisponível")
    if locked.ship_from_country not in ALLOWED_SHIP_FROM_COUNTRIES:
        raise OwnerEditorialError("Envio a partir de PL/CZ/FR/ES/DE é obrigatório")
    if locked.ship_from_verified_at is None:
        raise OwnerEditorialError("É necessário confirmar a origem antes de publicar")
    if not is_protocol_verification_fresh(locked, as_of=now):
        raise OwnerEditorialError("É necessário revalidar o protocolo antes de publicar")
    if not locked.affiliate_url:
        raise OwnerEditorialError("A oferta não tem link de parceiro disponível")
    operational_family_ids = list(
        OfferFamilyPlacement.objects.filter(offer=locked)
        .exclude(product_family__status=ProductFamily.Status.RETIRED)
        .values_list("product_family_id", flat=True)
        .distinct()
    )
    operational_families = list(
        ProductFamily.objects.select_for_update()
        .filter(pk__in=operational_family_ids)
        .order_by("pk")
    )
    for placement_family in operational_families:
        eligible_count = OfferFamilyPlacement.objects.filter(
            product_family=placement_family,
            offer__in=Offer.objects.filter(public_eligibility_q(now)),
        ).count()
        if eligible_count >= MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY:
            raise OwnerEditorialError(
                f"A família {placement_family.name} já tem 20 ofertas na montra"
            )
    previous = locked.owner_hidden
    locked.owner_hidden = False
    locked.save(update_fields=["owner_hidden", "updated_at"])
    event = OfferEditorialEvent.objects.create(
        offer=locked,
        action=OfferEditorialEvent.Action.PUBLISH,
        previous_owner_hidden=previous,
        new_owner_hidden=False,
        acted_by=user,
        acted_at=now,
    )
    return OwnerEditorialResult(locked, event, True)
