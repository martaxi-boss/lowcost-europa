from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class ProductFamily(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        TESTING = "TESTING", "Testing"
        VERIFIED = "VERIFIED", "Verified"
        PROVEN = "PROVEN", "Proven"
        WINNER = "WINNER", "Winner / Top Pick"
        OBSERVATION = "OBSERVATION", "Observation"
        RETIRED = "RETIRED", "Retired"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(slug=""),
                name="catalog_family_slug_not_blank",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "NEW",
                        "TESTING",
                        "VERIFIED",
                        "PROVEN",
                        "WINNER",
                        "OBSERVATION",
                        "RETIRED",
                    ]
                ),
                name="catalog_family_status_valid",
            ),
        ]
        ordering = ["display_order", "name", "pk"]

    def __str__(self):
        return self.name


class Offer(models.Model):
    class Source(models.TextChoices):
        ALIEXPRESS = "ALIEXPRESS", "AliExpress"

    class EquipmentType(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        DEDICATED = "DEDICATED", "Dedicated"
        COMBO = "COMBO", "Combo"

    class AffiliatePromotionStatus(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        ELIGIBLE = "ELIGIBLE", "Eligible"
        INELIGIBLE = "INELIGIBLE", "Ineligible"

    source = models.CharField(max_length=30, choices=Source.choices)
    external_product_id = models.CharField(max_length=120)
    product_family = models.ForeignKey(
        ProductFamily,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="offers",
    )
    title = models.CharField(max_length=500, blank=True)
    product_url = models.URLField(max_length=1000, blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    affiliate_url = models.URLField(max_length=1000, blank=True)
    affiliate_promotion_status = models.CharField(
        max_length=20,
        choices=AffiliatePromotionStatus.choices,
        default=AffiliatePromotionStatus.UNKNOWN,
    )
    affiliate_promotion_verified_at = models.DateTimeField(null=True, blank=True)
    ship_from_country = models.CharField(max_length=2, null=True, blank=True)
    ship_from_verified_at = models.DateTimeField(null=True, blank=True)
    protocol_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    owner_hidden = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    equipment_type = models.CharField(
        max_length=20, choices=EquipmentType.choices, default=EquipmentType.UNKNOWN
    )
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_product_id"],
                name="catalog_offer_source_external_id_uniq",
            ),
            models.CheckConstraint(
                condition=~Q(external_product_id=""),
                name="catalog_offer_external_id_not_blank",
            ),
            models.CheckConstraint(
                condition=Q(source__in=["ALIEXPRESS"]),
                name="catalog_offer_source_valid",
            ),
            models.CheckConstraint(
                condition=Q(last_seen_at__gte=F("first_seen_at")),
                name="catalog_offer_seen_timeline_valid",
            ),
            models.UniqueConstraint(
                fields=["product_family"],
                condition=Q(is_primary=True, product_family__isnull=False),
                name="catalog_offer_one_primary_per_family",
            ),
            models.CheckConstraint(
                condition=Q(is_primary=False) | Q(product_family__isnull=False),
                name="catalog_offer_primary_requires_family",
            ),
            models.CheckConstraint(
                condition=Q(is_primary=False) | Q(is_active=True),
                name="catalog_offer_primary_requires_active",
            ),
            models.CheckConstraint(
                condition=Q(equipment_type__in=["UNKNOWN", "DEDICATED", "COMBO"]),
                name="catalog_offer_equipment_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    affiliate_promotion_status__in=["UNKNOWN", "ELIGIBLE", "INELIGIBLE"]
                ),
                name="catalog_offer_affiliate_promotion_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(ship_from_country__isnull=True)
                | Q(ship_from_country__in=["PL", "CZ", "FR", "ES", "DE"]),
                name="catalog_offer_ship_from_allowed",
            ),
        ]
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.source}:{self.external_product_id}"


class OfferFamilyPlacement(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.PROTECT,
        related_name="family_placements",
    )
    product_family = models.ForeignKey(
        ProductFamily,
        on_delete=models.PROTECT,
        related_name="offer_placements",
    )
    selection_position = models.PositiveSmallIntegerField(null=True, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    selection_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["offer", "product_family"],
                name="catalog_placement_offer_family_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    Q(selection_position__isnull=True)
                    | (Q(selection_position__gte=1) & Q(selection_position__lte=5))
                ),
                name="catalog_placement_selection_position_range",
            ),
            models.UniqueConstraint(
                fields=["product_family", "selection_position"],
                condition=Q(selection_position__isnull=False),
                name="catalog_placement_family_selection_uniq",
            ),
        ]
        ordering = ["product_family", "selection_position", "display_order", "pk"]

    def __str__(self):
        return f"{self.product_family}: {self.offer}"


class OfferEditorialEvent(models.Model):
    class Action(models.TextChoices):
        HIDE = "HIDE", "Retirar da montra"
        PUBLISH = "PUBLISH", "Voltar a publicar"

    offer = models.ForeignKey(
        Offer, on_delete=models.PROTECT, related_name="editorial_events"
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    previous_owner_hidden = models.BooleanField()
    new_owner_hidden = models.BooleanField()
    acted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="offer_editorial_events"
    )
    acted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-acted_at", "-pk"]

    def __str__(self):
        return f"{self.offer} {self.action} {self.acted_at.isoformat()}"


class OfferClick(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.PROTECT,
        related_name="clicks",
    )
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["offer", "-clicked_at"], name="catalog_click_offer_time_idx")
        ]
        ordering = ["-clicked_at", "-pk"]

    def __str__(self):
        return f"{self.offer} @ {self.clicked_at.isoformat()}"


class OfferObservation(models.Model):
    class Availability(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        AVAILABLE = "AVAILABLE", "Available"
        UNAVAILABLE = "UNAVAILABLE", "Unavailable"

    offer = models.ForeignKey(
        Offer,
        on_delete=models.PROTECT,
        related_name="observations",
    )
    observed_at = models.DateTimeField(default=timezone.now)
    destination_country = models.CharField(max_length=2, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    evaluation_rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    sales_count = models.PositiveBigIntegerField(null=True, blank=True)
    commission_rate = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    search_ship_to_days_raw = models.CharField(max_length=255, null=True, blank=True)
    search_delivery_days = models.PositiveSmallIntegerField(null=True, blank=True)
    ship_to_days_raw = models.CharField(max_length=255, null=True, blank=True)
    delivery_days = models.PositiveSmallIntegerField(null=True, blank=True)
    availability = models.CharField(
        max_length=20,
        choices=Availability.choices,
        default=Availability.UNKNOWN,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    availability__in=[
                        "UNKNOWN",
                        "AVAILABLE",
                        "UNAVAILABLE",
                    ]
                ),
                name="catalog_obs_availability_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(evaluation_rate_percent__isnull=True)
                    | (Q(evaluation_rate_percent__gte=0) & Q(evaluation_rate_percent__lte=100))
                ),
                name="catalog_obs_eval_rate_range",
            ),
            models.CheckConstraint(
                condition=(
                    Q(commission_rate__isnull=True)
                    | (Q(commission_rate__gte=0) & Q(commission_rate__lte=100))
                ),
                name="catalog_obs_commission_range",
            ),
            models.CheckConstraint(
                condition=Q(price__isnull=True) | Q(price__gte=0),
                name="catalog_obs_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(original_price__isnull=True) | Q(original_price__gte=0),
                name="catalog_obs_original_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(search_delivery_days__isnull=True) | Q(search_delivery_days__gte=0),
                name="catalog_obs_search_delivery_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=["offer", "-observed_at"], name="catalog_obs_offer_time_idx")
        ]
        ordering = ["-observed_at"]

    def __str__(self):
        return f"{self.offer} @ {self.observed_at.isoformat()}"


class OfferCandidate(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    product_family = models.ForeignKey(
        ProductFamily, on_delete=models.PROTECT, related_name="candidates"
    )
    source = models.CharField(max_length=30, choices=Offer.Source.choices)
    external_product_id = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    title = models.CharField(max_length=500, blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    product_url = models.URLField(max_length=1000, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    evaluation_rate_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    sales_count = models.PositiveBigIntegerField(null=True, blank=True)
    commission_rate = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    search_ship_to_days_raw = models.CharField(max_length=255, null=True, blank=True)
    search_delivery_days = models.PositiveSmallIntegerField(null=True, blank=True)
    detail_ship_to_days_raw = models.CharField(max_length=255, null=True, blank=True)
    detail_delivery_days = models.PositiveSmallIntegerField(null=True, blank=True)
    discovered_at = models.DateTimeField(default=timezone.now)
    last_observed_at = models.DateTimeField(default=timezone.now)
    approved_offer = models.ForeignKey(
        Offer, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_candidates"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_product_id"],
                name="catalog_candidate_source_external_id_uniq",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["PENDING", "APPROVED", "REJECTED"]),
                name="catalog_candidate_status_valid",
            ),
        ]
        ordering = ["status", "-last_observed_at", "pk"]

    def __str__(self):
        return f"{self.product_family}:{self.source}:{self.external_product_id}"


class CandidateFamilyMoveEvent(models.Model):
    candidate = models.ForeignKey(
        "OfferCandidate", on_delete=models.PROTECT, related_name="family_move_events"
    )
    from_family = models.ForeignKey(
        ProductFamily, on_delete=models.PROTECT, related_name="candidate_moves_from"
    )
    to_family = models.ForeignKey(
        ProductFamily, on_delete=models.PROTECT, related_name="candidate_moves_to"
    )
    title_snapshot = models.CharField(max_length=500, blank=True)
    acted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="candidate_family_moves"
    )
    acted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-acted_at", "-pk"]

    def __str__(self):
        return f"{self.candidate} {self.from_family} -> {self.to_family}"


class CandidateDecision(models.Model):
    class Decision(models.TextChoices):
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"

    class ReviewSignal(models.TextChoices):
        DELIVERS_TO_PT_CONFIRMED = "DELIVERS_TO_PT_CONFIRMED", "Sim, entrega em Portugal"
        DOES_NOT_DELIVER_TO_PT = "DOES_NOT_DELIVER_TO_PT", "Não entrega em Portugal"
        DOES_NOT_SHIP_TO_PT = "DOES_NOT_SHIP_TO_PT", "Não envia para Portugal"
        ORIGIN_NOT_ALLOWED = "ORIGIN_NOT_ALLOWED", "País de envio fora dos cinco permitidos"
        LISTING_UNAVAILABLE = "LISTING_UNAVAILABLE", "Anúncio indisponível"

    class Reason(models.TextChoices):
        DOES_NOT_SHIP_TO_PT = "DOES_NOT_SHIP_TO_PT", "Não envia para Portugal"
        PT_DELIVERY_NOT_CONFIRMED = (
            "PT_DELIVERY_NOT_CONFIRMED",
            "Não consigo confirmar entrega em Portugal",
        )
        ORIGIN_NOT_CONFIRMED = (
            "ORIGIN_NOT_CONFIRMED",
            "País de envio não aparece / não consigo confirmar",
        )
        ORIGIN_NOT_ALLOWED = "ORIGIN_NOT_ALLOWED", "País de envio fora dos 5 permitidos"
        WRONG_FAMILY = "WRONG_FAMILY", "Produto pertence a outra família"
        ACCESSORY_OR_PART = (
            "ACCESSORY_OR_PART",
            "Acessório, peça, cartucho ou consumível",
        )
        DUPLICATE = "DUPLICATE", "Produto duplicado"
        LISTING_UNAVAILABLE = "LISTING_UNAVAILABLE", "Anúncio indisponível"
        LISTING_CHANGED = "LISTING_CHANGED", "Anúncio ou variante mudou"
        POOR_LISTING = "POOR_LISTING", "Oferta/listagem sem qualidade suficiente"
        OTHER = "OTHER", "Outro motivo"
        IRRELEVANT = "IRRELEVANT", "Irrelevante (legado)"

    candidate = models.ForeignKey(
        OfferCandidate, on_delete=models.PROTECT, related_name="decisions"
    )
    decision = models.CharField(max_length=10, choices=Decision.choices)
    ship_from_country = models.CharField(max_length=2, blank=True)
    reason = models.CharField(max_length=30, choices=Reason.choices, blank=True)
    review_signals = models.JSONField(default=list, blank=True)
    note = models.TextField(blank=True)
    evidence_url = models.URLField(max_length=1000, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="candidate_decisions"
    )
    decided_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-decided_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(decision__in=["APPROVE", "REJECT"]),
                name="catalog_candidate_decision_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(decision="REJECT")
                    | Q(ship_from_country="")
                    | Q(ship_from_country__in=["PL", "CZ", "FR", "ES", "DE"])
                ),
                name="catalog_candidate_approve_country_optional_allowed",
            ),
        ]

    def __str__(self):
        return f"{self.candidate} {self.decision} {self.decided_at.isoformat()}"


class ExternalMetricsSnapshot(models.Model):
    """One verified and timestamped provider aggregate, never a fabricated conversion."""

    source = models.CharField(max_length=24, primary_key=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    checked_at = models.DateTimeField(default=timezone.now)
    payload = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.source} @ {self.checked_at.isoformat()}"
