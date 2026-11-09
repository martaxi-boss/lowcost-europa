"""Publish an Owner-provided affiliate URL verbatim, without generating links.

This is deliberately separate from the legacy candidate/review workflow.
The distinct ALIEXPRESS_OWNER source is excluded from automatic AliExpress
maintenance and discovery. Replace-family removes only placements, not the
historical OfferClick/Offer/Order records required for reporting.
"""

import hashlib
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlsplit

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily
from apps.catalog.services.manual_candidate_intake import (
    ManualCandidateIntakeError,
    resolve_aliexpress_product_url,
)
from apps.catalog.services.public_eligibility import MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY
from apps.integrations.aliexpress.affiliate_url import is_https_affiliate_url
from apps.integrations.aliexpress.client import AliExpressClient
from apps.integrations.aliexpress.exceptions import AliExpressError


class Command(BaseCommand):
    help = (
        "Publish one Owner-supplied AliExpress affiliate link verbatim into a category, "
        "optionally replacing all its prior placements, without candidate approval "
        "or any affiliate link generation."
    )

    def add_arguments(self, parser):
        parser.add_argument("--family", required=True, help="Existing public category slug")
        parser.add_argument(
            "--replace-family",
            action="store_true",
            help="Atomically remove every old placement from this category before publishing",
        )
        parser.add_argument("url", help="Owner-provided HTTPS AliExpress affiliate link")

    def handle(self, *args, **options):
        original_url = options["url"]
        if not is_https_affiliate_url(original_url):
            raise CommandError("O link manual não é um URL HTTPS seguro.")
        host = urlsplit(original_url).hostname or ""
        if host != "aliexpress.com" and not host.endswith(".aliexpress.com"):
            raise CommandError("O link manual tem de apontar para um domínio AliExpress.")

        try:
            external_id, canonical_url = resolve_aliexpress_product_url(original_url)
        except ManualCandidateIntakeError as exc:
            raise CommandError(
                "Não foi possível identificar o produto a partir do link fornecido."
            ) from exc

        try:
            details = AliExpressClient().get_product_detail(external_id, "PT", "EUR")
        except AliExpressError as exc:
            raise CommandError(
                "Não foi possível obter informação verificável do produto no parceiro."
            ) from exc

        if details.product_id != external_id:
            raise CommandError("O parceiro devolveu dados de outro produto.")
        if not details.title or not details.title.strip():
            raise CommandError("O parceiro não devolveu nome do produto.")
        if (
            details.price is None
            or Decimal(str(details.price)) <= 0
            or details.currency != "EUR"
        ):
            raise CommandError("O parceiro não devolveu um preço EUR positivo verificável.")
        image_url = details.image_url or ""
        if image_url and not is_https_affiliate_url(image_url):
            image_url = ""

        now = timezone.now()
        with transaction.atomic():
            try:
                family = ProductFamily.objects.select_for_update().get(
                    slug=options["family"]
                )
            except ProductFamily.DoesNotExist as exc:
                raise CommandError("A categoria indicada não existe.") from exc
            if family.status == ProductFamily.Status.RETIRED:
                raise CommandError("A categoria indicada está retirada.")

            placements = OfferFamilyPlacement.objects.select_for_update().filter(
                product_family=family
            )
            existing_count = placements.count()
            if (
                not options["replace_family"]
                and existing_count >= MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY
            ):
                raise CommandError("A montra já atingiu o limite de 20 produtos.")

            offer = Offer.objects.select_for_update().filter(
                source=Offer.Source.ALIEXPRESS_OWNER,
                external_product_id=external_id,
            ).first()
            if offer is not None and offer.affiliate_url != original_url:
                raise CommandError(
                    "Produto manual já existente com outro link. "
                    "Não substituir links anteriores automaticamente."
                )

            removed = 0
            if options["replace_family"]:
                removed = existing_count
                placements.delete()

            if offer is None:
                offer = Offer.objects.create(
                    source=Offer.Source.ALIEXPRESS_OWNER,
                    external_product_id=external_id,
                    title=details.title,
                    product_url=canonical_url,
                    image_url=image_url,
                    affiliate_url=original_url,
                    affiliate_promotion_status=Offer.AffiliatePromotionStatus.UNKNOWN,
                    affiliate_promotion_verified_at=None,
                    protocol_verified_at=now,
                    is_active=True,
                    owner_hidden=False,
                    first_seen_at=now,
                    last_seen_at=now,
                )
            elif not offer.is_active or offer.owner_hidden:
                raise CommandError("O produto manual existente não está publicável.")

            if not OfferObservation.objects.filter(
                offer=offer,
                observed_at__gte=now - timedelta(minutes=1),
                destination_country="PT",
            ).exists():
                OfferObservation.objects.create(
                    offer=offer,
                    observed_at=now,
                    destination_country="PT",
                    price=details.price,
                    original_price=details.original_price,
                    currency="EUR",
                    evaluation_rate_percent=details.evaluation_rate_percent,
                    sales_count=details.sales_count,
                    commission_rate=details.commission_rate,
                    ship_to_days_raw=details.ship_to_days_raw,
                    delivery_days=details.delivery_days,
                    availability=OfferObservation.Availability.UNKNOWN,
                )

            placement, created = OfferFamilyPlacement.objects.get_or_create(
                offer=offer,
                product_family=family,
                defaults={"selection_position": None, "display_order": 0},
            )
            final_count = OfferFamilyPlacement.objects.filter(product_family=family).count()
            if final_count > MAX_PUBLIC_ELIGIBLE_OFFERS_PER_FAMILY:
                raise CommandError("A montra ultrapassaria o limite de 20 produtos.")

        digest = hashlib.sha256(original_url.encode("utf-8")).hexdigest()
        self.stdout.write(
            "OWNER_MANUAL_AFFILIATE_PUBLISHED=PASS"
            f" family={family.slug}"
            f" offer={offer.pk}"
            f" external_product={external_id}"
            f" old_placements_removed={removed}"
            f" final_placements={final_count}"
            f" affiliate_url_sha256={digest}"
            f" new_placement={str(created).upper()}"
        )
