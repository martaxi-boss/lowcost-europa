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
        ordering = ["name"]

    def __str__(self):
        return self.name


class Offer(models.Model):
    class Source(models.TextChoices):
        ALIEXPRESS = "ALIEXPRESS", "AliExpress"

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
    is_active = models.BooleanField(default=True)
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
        ]
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.source}:{self.external_product_id}"


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
        ]
        indexes = [
            models.Index(fields=["offer", "-observed_at"], name="catalog_obs_offer_time_idx")
        ]
        ordering = ["-observed_at"]

    def __str__(self):
        return f"{self.offer} @ {self.observed_at.isoformat()}"
