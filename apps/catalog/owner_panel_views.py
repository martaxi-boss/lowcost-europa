import os
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Exists, OuterRef, Prefetch, Q, Subquery
from django.db.models.functions import TruncDate
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from apps.catalog.models import (
    ExternalMetricsSnapshot,
    Offer,
    OfferCandidate,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.candidate_approval import (
    OWNER_REJECTION_REASON_CHOICES,
    CandidateApprovalError,
    approve_candidate,
    reject_candidate,
    revalidate_candidate,
)
from apps.catalog.services.candidate_move import CandidateMoveError, move_candidate_to_family
from apps.catalog.services.manual_candidate_intake import (
    ManualCandidateIntakeError,
    intake_manual_aliexpress_candidate,
)
from apps.catalog.services.observation_display import (
    build_observation_display,
    observation_history_queryset,
)
from apps.catalog.services.owner_editorial import (
    OwnerEditorialError,
    hide_offer_from_storefront,
    publish_offer_to_storefront,
)
from apps.catalog.services.public_eligibility import (
    is_protocol_verified,
    public_eligibility_q,
)
from apps.catalog.services.weekly_discovery import PENDING_CAP_PER_FAMILY
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


def _private(response):
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Cache-Control"] = "private, no-store"
    return response


def _owner_staff_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _private(redirect("owner-panel:login"))
        if not request.user.is_staff:
            return _private(HttpResponseForbidden("Acesso negado."))
        return view_func(request, *args, **kwargs)

    return wrapped


def _family_or_404(slug):
    return get_object_or_404(ProductFamily, slug=slug)


def _candidate_or_404(family, candidate_id):
    return get_object_or_404(
        OfferCandidate.objects.select_related("approved_offer", "product_family"),
        pk=candidate_id,
        product_family=family,
    )


def _offer_or_404(family, offer_id):
    return get_object_or_404(
        Offer.objects.filter(family_placements__product_family=family).distinct(), pk=offer_id
    )


def _decorate_offer(offer):
    offer.approved_candidate = (
        OfferCandidate.objects.filter(approved_offer=offer, status=OfferCandidate.Status.APPROVED)
        .order_by("pk")
        .first()
    )
    offer.observation_display = build_observation_display(offer.observation_history)
    offer.protocol_fresh = is_protocol_verified(offer)
    offer.was_editorially_hidden = offer.editorial_events.filter(action="HIDE").exists()
    if not offer.is_active:
        offer.owner_state_label = "Indisponível"
    elif offer.affiliate_promotion_status == Offer.AffiliatePromotionStatus.INELIGIBLE:
        offer.owner_state_label = "Não elegível para promoção / afiliado"
    elif offer.affiliate_promotion_status == Offer.AffiliatePromotionStatus.UNKNOWN:
        offer.owner_state_label = "Elegibilidade promocional por confirmar"
    elif not offer.protocol_fresh:
        offer.owner_state_label = "Revalidação necessária"
    elif offer.owner_hidden and offer.was_editorially_hidden:
        offer.owner_state_label = "Retirado da montra"
    elif offer.owner_hidden:
        offer.owner_state_label = "Aprovado fora da montra"
    else:
        offer.owner_state_label = "Na montra"
    return offer


def _decorate_candidate(candidate):
    offer = candidate.approved_offer
    candidate.review_required = bool(
        candidate.status == OfferCandidate.Status.APPROVED
        and offer
        and not is_protocol_verified(offer)
    )
    candidate.status_label = {
        OfferCandidate.Status.PENDING: "A rever",
        OfferCandidate.Status.APPROVED: "Aprovado",
        OfferCandidate.Status.REJECTED: "Rejeitado",
    }[candidate.status]
    if offer:
        _decorate_offer(offer)
    return candidate


def _family_counts(family):
    candidates = list(
        OfferCandidate.objects.filter(product_family=family).select_related("approved_offer")
    )
    return {
        "pending": sum(c.status == OfferCandidate.Status.PENDING for c in candidates),
        "approved": sum(c.status == OfferCandidate.Status.APPROVED for c in candidates),
        "rejected": sum(c.status == OfferCandidate.Status.REJECTED for c in candidates),
        "review_required": sum(
            c.status == OfferCandidate.Status.APPROVED
            and c.approved_offer_id
            and not is_protocol_verified(c.approved_offer)
            for c in candidates
        ),
        "storefront": OfferFamilyPlacement.objects.filter(
            product_family=family,
            offer__in=Offer.objects.filter(public_eligibility_q()),
        ).count(),
        "hidden": OfferFamilyPlacement.objects.filter(
            product_family=family,
            offer__owner_hidden=True,
            offer__editorial_events__action="HIDE",
        )
        .distinct()
        .count(),
        "promotion_ineligible": OfferFamilyPlacement.objects.filter(
            product_family=family,
            offer__affiliate_promotion_status=Offer.AffiliatePromotionStatus.INELIGIBLE,
        )
        .distinct()
        .count(),
    }


@require_http_methods(["GET", "POST"])
def owner_login(request):
    next_url = request.GET.get("next", "") or request.POST.get("next", "")
    safe_next = (
        next_url
        if next_url
        and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
        else ""
    )
    destination = safe_next or reverse("storefront:home")
    if request.user.is_authenticated and request.user.is_staff:
        return _private(redirect(destination))
    error = ""
    if request.method == "POST":
        password = request.POST.get("password", "")
        user = authenticate(
            request,
            username=settings.OWNER_PANEL_USERNAME,
            password=password,
        )
        if user is not None and user.is_active and user.is_staff:
            login(request, user)
            return _private(redirect(destination))
        error = "Palavra-passe incorreta."
    return _private(
        render(
            request,
            "catalog/owner_panel/login.html",
            {"error": error, "next": safe_next},
        )
    )


@require_POST
def owner_logout(request):
    logout(request)
    return _private(redirect("owner-panel:login"))


@_owner_staff_required
def dashboard(request):
    """Read-only Owner metrics; external advertising and orders are not inferred."""
    now = timezone.now()
    recent_cutoff = now - timedelta(days=7)
    previous_cutoff = now - timedelta(days=14)
    last_day_cutoff = now - timedelta(days=1)
    month_cutoff = now - timedelta(days=30)
    operational_statuses = [
        ProductFamily.Status.NEW,
        ProductFamily.Status.TESTING,
        ProductFamily.Status.VERIFIED,
        ProductFamily.Status.PROVEN,
        ProductFamily.Status.WINNER,
        ProductFamily.Status.OBSERVATION,
    ]
    families = list(
        ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED).order_by(
            "display_order", "name", "pk"
        )
    )

    # Counts are raw /go/ outbound redirects, not people, purchases, or ad clicks.
    recent_clicks = OfferClick.objects.filter(clicked_at__gte=recent_cutoff)
    recent_clicks_total = recent_clicks.count()
    previous_clicks_total = OfferClick.objects.filter(
        clicked_at__gte=previous_cutoff, clicked_at__lt=recent_cutoff
    ).count()
    clicks_24h = OfferClick.objects.filter(clicked_at__gte=last_day_cutoff).count()
    clicks_30d = OfferClick.objects.filter(clicked_at__gte=month_cutoff).count()
    recent_clicks_by_family = dict(
        recent_clicks.filter(
            offer__family_placements__product_family__status__in=operational_statuses
        )
        .values("offer__family_placements__product_family_id")
        .annotate(total=Count("id"))
        .values_list("offer__family_placements__product_family_id", "total")
    )
    top_clicked_offers = list(
        recent_clicks.values("offer_id", "offer__title")
        .annotate(total=Count("id"))
        .order_by("-total", "offer_id")[:5]
    )

    # The chart groups by local calendar days, while headline periods are
    # rolling 24-hour windows. Missing dates are real zero-click dates.
    first_chart_day = timezone.localdate(now) - timedelta(days=13)
    counts_by_day = dict(
        OfferClick.objects.filter(clicked_at__date__gte=first_chart_day)
        .annotate(local_day=TruncDate("clicked_at", tzinfo=timezone.get_current_timezone()))
        .values("local_day")
        .annotate(total=Count("id"))
        .values_list("local_day", "total")
    )
    chart_max = max([1, *counts_by_day.values()])
    daily_clicks = []
    for day_offset in range(14):
        day = first_chart_day + timedelta(days=day_offset)
        count = counts_by_day.get(day, 0)
        daily_clicks.append(
            {
                "date_label": day.strftime("%d/%m/%Y"),
                "short_label": day.strftime("%d/%m"),
                "total": count,
                "height": max(8, round(count * 100 / chart_max)) if count else 0,
            }
        )

    # Show only the actual technical gate and never imply a paid conversion.
    visible_offers = Offer.objects.filter(
        is_active=True,
        owner_hidden=False,
        family_placements__product_family__status__in=operational_statuses,
    ).distinct()
    eligible_queryset = visible_offers.filter(public_eligibility_q(now))
    eligible_public_offers = eligible_queryset.count()
    origin_without_individual_proof = eligible_queryset.filter(
        Q(ship_from_country__isnull=True) | Q(ship_from_verified_at__isnull=True)
    ).count()

    # Seller listing status is not the same as variant-level stock. Read the
    # newest observation for availability, but keep historical price evidence
    # distinct so an UNKNOWN observation does not erase earlier facts.
    newest_observation = OfferObservation.objects.filter(
        offer_id=OuterRef("pk")
    ).order_by("-observed_at", "-pk")
    newest_price = (
        OfferObservation.objects.filter(
            offer_id=OuterRef("pk"),
            price__isnull=False,
            currency__isnull=False,
        )
        .exclude(currency="")
        .order_by("-observed_at", "-pk")
    )
    numeric_delivery_evidence = OfferObservation.objects.filter(
        offer_id=OuterRef("pk")
    ).filter(Q(delivery_days__isnull=False) | Q(search_delivery_days__isnull=False))
    eligible_with_evidence = eligible_queryset.annotate(
        last_availability=Subquery(newest_observation.values("availability")[:1]),
        last_price_at=Subquery(newest_price.values("observed_at")[:1]),
        has_delivery_days=Exists(numeric_delivery_evidence),
    )
    latest_availability_unconfirmed = eligible_with_evidence.filter(
        Q(last_availability=OfferObservation.Availability.UNKNOWN)
        | Q(last_availability__isnull=True)
    ).count()
    current_price_unconfirmed = eligible_with_evidence.filter(
        Q(last_price_at__isnull=True) | Q(last_price_at__lt=last_day_cutoff)
    ).count()
    delivery_days_unproven = eligible_with_evidence.filter(
        has_delivery_days=False
    ).count()

    # Historical candidates in retired families remain immutable here. They
    # must be visible as an Owner reconciliation item, not silently deleted,
    # rejected, approved or counted in the five active discovery queues.
    retired_pending_by_family = list(
        OfferCandidate.objects.filter(
            status=OfferCandidate.Status.PENDING,
            product_family__status=ProductFamily.Status.RETIRED,
        )
        .values("product_family__name", "product_family__slug")
        .annotate(total=Count("pk"))
        .order_by("product_family__name", "product_family__slug")
    )
    retired_pending_total = sum(row["total"] for row in retired_pending_by_family)
    visible_blocked_offers = visible_offers.exclude(public_eligibility_q(now)).count()
    stale_public_by_family = dict(
        OfferFamilyPlacement.objects.filter(
            offer__is_active=True,
            offer__owner_hidden=False,
            offer__last_seen_at__lt=recent_cutoff,
        )
        .values("product_family_id")
        .annotate(total=Count("offer_id", distinct=True))
        .values_list("product_family_id", "total")
    )
    paused_discovery_families = 0
    for family in families:
        family.owner_counts = _family_counts(family)
        family.discovery_paused = family.owner_counts["pending"] >= PENDING_CAP_PER_FAMILY
        family.reviews_to_resume_discovery = max(
            0, family.owner_counts["pending"] - PENDING_CAP_PER_FAMILY + 1
        )
        paused_discovery_families += int(family.discovery_paused)
        family.recent_raw_clicks = recent_clicks_by_family.get(family.pk, 0)
        family.stale_public_offers = stale_public_by_family.get(family.pk, 0)

    affiliate_report = ExternalMetricsSnapshot.objects.filter(source="ALIEXPRESS").first()
    affiliate_report_payload = (
        affiliate_report.payload
        if affiliate_report and isinstance(affiliate_report.payload, dict)
        else None
    )
    affiliate_report_fresh = bool(
        affiliate_report_payload
        and affiliate_report.checked_at <= now
        and now - affiliate_report.checked_at <= timedelta(hours=12)
    )
    meta_report = ExternalMetricsSnapshot.objects.filter(source="META").first()
    meta_report_payload = (
        meta_report.payload
        if meta_report and isinstance(meta_report.payload, dict)
        else None
    )
    meta_report_fresh = bool(
        meta_report_payload
        and meta_report.checked_at <= now
        and now - meta_report.checked_at <= timedelta(hours=12)
    )

    return _private(
        render(
            request,
            "catalog/owner_panel/dashboard.html",
            {
                "families": families,
                "recent_raw_clicks_total": recent_clicks_total,
                "previous_raw_clicks_total": previous_clicks_total,
                "raw_clicks_24h": clicks_24h,
                "raw_clicks_30d": clicks_30d,
                "daily_raw_clicks": daily_clicks,
                "top_clicked_offers": top_clicked_offers,
                "eligible_public_offers": eligible_public_offers,
                "origin_without_individual_proof": origin_without_individual_proof,
                "latest_availability_unconfirmed": latest_availability_unconfirmed,
                "current_price_unconfirmed": current_price_unconfirmed,
                "delivery_days_unproven": delivery_days_unproven,
                "retired_pending_by_family": retired_pending_by_family,
                "retired_pending_total": retired_pending_total,
                "paused_discovery_families": paused_discovery_families,
                "visible_blocked_offers": visible_blocked_offers,
                "affiliate_tracking_id": os.environ.get("ALIEXPRESS_TRACKING_ID", "").strip(),
                "owner_metrics_checked_at": now,
                "affiliate_report": affiliate_report,
                "affiliate_report_payload": affiliate_report_payload,
                "affiliate_report_fresh": affiliate_report_fresh,
                "meta_report": meta_report,
                "meta_report_payload": meta_report_payload,
                "meta_report_fresh": meta_report_fresh,
            },
        )
    )

@_owner_staff_required
def family_manage(request, family_slug):
    family = _family_or_404(family_slug)
    if family.status == ProductFamily.Status.RETIRED:
        return _private(HttpResponseForbidden("Acesso negado."))
    view = request.GET.get("vista", "rever")
    allowed = {
        "rever",
        "montra",
        "aprovados",
        "retirados",
        "revalidar",
        "rejeitados",
        "nao-promovivel",
    }
    if view not in allowed:
        view = "rever"
    candidates = [
        _decorate_candidate(candidate)
        for candidate in OfferCandidate.objects.filter(product_family=family)
        .select_related("approved_offer")
        .prefetch_related(
            Prefetch(
                "approved_offer__observations",
                queryset=observation_history_queryset(),
                to_attr="observation_history",
            )
        )
        .order_by("status", "-last_observed_at", "pk")
    ]
    placements = list(
        OfferFamilyPlacement.objects.filter(product_family=family)
        .select_related("offer")
        .prefetch_related(
            Prefetch(
                "offer__observations",
                queryset=observation_history_queryset(),
                to_attr="observation_history",
            )
        )
        .order_by("display_order", "pk")
    )
    offers = [_decorate_offer(p.offer) for p in placements]
    eligible_ids = set(
        OfferFamilyPlacement.objects.filter(
            product_family=family,
            offer__in=Offer.objects.filter(public_eligibility_q()),
        ).values_list("offer_id", flat=True)
    )
    for offer in offers:
        offer.in_storefront = offer.pk in eligible_ids

    if view == "rever":
        shown_candidates = [c for c in candidates if c.status == OfferCandidate.Status.PENDING]
        shown_offers = []
    elif view == "aprovados":
        shown_candidates = [
            c
            for c in candidates
            if c.status == OfferCandidate.Status.APPROVED
            and c.approved_offer
            and c.approved_offer.owner_hidden
            and not c.review_required
            and not c.approved_offer.editorial_events.filter(action="HIDE").exists()
        ]
        shown_offers = []
    elif view == "rejeitados":
        shown_candidates = [c for c in candidates if c.status == OfferCandidate.Status.REJECTED]
        shown_offers = []
    elif view == "revalidar":
        shown_candidates = [c for c in candidates if c.review_required]
        shown_offers = []
    elif view == "retirados":
        shown_candidates = []
        shown_offers = [o for o in offers if o.owner_hidden and o.was_editorially_hidden]
    elif view == "nao-promovivel":
        shown_candidates = []
        shown_offers = [
            o
            for o in offers
            if o.affiliate_promotion_status == Offer.AffiliatePromotionStatus.INELIGIBLE
        ]
    else:
        shown_candidates = []
        shown_offers = [o for o in offers if o.in_storefront]

    error = request.session.pop("owner_panel_error", "")
    notice = request.session.pop("owner_panel_notice", "")
    return _private(
        render(
            request,
            "catalog/owner_panel/family.html",
            {
                "family": family,
                "counts": _family_counts(family),
                "active_view": view,
                "candidates": shown_candidates,
                "offers": shown_offers,
                "families": ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
                .exclude(pk=family.pk)
                .order_by("display_order", "name", "pk"),
                "rejection_reason_choices": OWNER_REJECTION_REASON_CHOICES,
                "owner_error": error,
                "owner_notice": notice,
            },
        )
    )


@require_POST
@_owner_staff_required
def manual_candidate_intake(request, family_slug):
    family = _family_or_404(family_slug)
    if family.status == ProductFamily.Status.RETIRED:
        return _private(HttpResponseForbidden("Acesso negado."))
    product_url = request.POST.get("product_url", "").strip()
    if not product_url:
        request.session["owner_panel_error"] = "Indique um link AliExpress."
        return _return_family(family, "rever", request)
    try:
        result = intake_manual_aliexpress_candidate(url=product_url, family=family)
    except (ManualCandidateIntakeError, AliExpressError) as exc:
        request.session["owner_panel_error"] = str(exc)
        return _return_family(family, "rever", request)

    if result.outcome == "CREATED":
        request.session["owner_panel_notice"] = (
            f"Produto adicionado a A rever (Candidate #{result.candidate.pk})."
        )
    elif result.outcome == "ALREADY_PENDING":
        request.session["owner_panel_notice"] = (
            f"Este produto já está em A rever (Candidate #{result.candidate.pk})."
        )
    elif result.outcome == "ALREADY_APPROVED":
        request.session["owner_panel_notice"] = (
            f"Este produto já está aprovado (Candidate #{result.candidate.pk})."
        )
    elif result.outcome == "ALREADY_REJECTED":
        request.session["owner_panel_notice"] = (
            f"Este produto já foi rejeitado (Candidate #{result.candidate.pk})."
        )
    elif result.outcome.endswith("_OTHER_FAMILY"):
        request.session["owner_panel_notice"] = (
            f"Este produto já existe na família {result.candidate.product_family.name} "
            f"(Candidate #{result.candidate.pk}); não foi movido."
        )
    elif result.outcome == "OFFER_EXISTS":
        request.session["owner_panel_notice"] = (
            f"Este produto já existe como Offer #{result.offer.pk}."
        )
    return _return_family(family, "rever", request)


def _safe_next(request):
    next_url = request.POST.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return ""


def _return_family(family, view="rever", request=None):
    if request is not None:
        next_url = _safe_next(request)
        if next_url:
            return _private(redirect(next_url))
    return _private(redirect(f"/painel/familias/{family.slug}/?vista={view}"))


def _moved_candidate_view(candidate):
    if candidate.status == OfferCandidate.Status.PENDING:
        return "rever"
    if candidate.status != OfferCandidate.Status.APPROVED or not candidate.approved_offer_id:
        return "rever"
    offer = candidate.approved_offer
    if not offer.is_active:
        return "retirados"
    if not is_protocol_verified(offer):
        return "revalidar"
    return "aprovados" if offer.owner_hidden else "montra"


@require_POST
@_owner_staff_required
def candidate_approve(request, family_slug, candidate_id):
    family = _family_or_404(family_slug)
    candidate = _candidate_or_404(family, candidate_id)
    try:
        approve_candidate(candidate, user=request.user)
        request.session["owner_panel_notice"] = "Produto aprovado."
    except AliExpressRateLimitError:
        request.session["owner_panel_error"] = (
            "A AliExpress está temporariamente indisponível. "
            "Tente novamente dentro de instantes."
        )
    except (AliExpressError, CandidateApprovalError) as exc:
        request.session["owner_panel_error"] = str(exc)
    return _return_family(family, "rever", request)


@require_POST
@_owner_staff_required
def candidate_reject(request, family_slug, candidate_id):
    family = _family_or_404(family_slug)
    candidate = _candidate_or_404(family, candidate_id)
    try:
        reject_candidate(
            candidate,
            user=request.user,
            reason=request.POST.get("reason", ""),
            note=request.POST.get("note", ""),
        )
    except CandidateApprovalError as exc:
        request.session["owner_panel_error"] = str(exc)
    return _return_family(family, "rever", request)


@require_POST
@_owner_staff_required
def candidate_move(request, family_slug, candidate_id):
    family = _family_or_404(family_slug)
    candidate = _candidate_or_404(family, candidate_id)
    target = get_object_or_404(
        ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED),
        pk=request.POST.get("target_family"),
    )
    try:
        moved, _ = move_candidate_to_family(candidate, target_family=target, user=request.user)
        moved = OfferCandidate.objects.select_related("approved_offer", "product_family").get(
            pk=moved.pk
        )
        return _return_family(moved.product_family, _moved_candidate_view(moved), request)
    except CandidateMoveError as exc:
        request.session["owner_panel_error"] = str(exc)
        return _return_family(family, "rever", request)


@require_POST
@_owner_staff_required
def candidate_revalidate(request, family_slug, candidate_id):
    family = _family_or_404(family_slug)
    candidate = _candidate_or_404(family, candidate_id)
    try:
        revalidate_candidate(candidate, user=request.user)
        request.session["owner_panel_notice"] = "Protocolo revalidado."
    except CandidateApprovalError as exc:
        request.session["owner_panel_error"] = str(exc)
    return _return_family(
        family,
        "retirados"
        if candidate.approved_offer and candidate.approved_offer.owner_hidden
        else "revalidar",
        request,
    )


@require_POST
@_owner_staff_required
def offer_hide(request, family_slug, offer_id):
    family = _family_or_404(family_slug)
    offer = _offer_or_404(family, offer_id)
    try:
        hide_offer_from_storefront(offer, user=request.user)
        request.session["owner_panel_notice"] = "Oferta retirada da montra."
    except OwnerEditorialError as exc:
        request.session["owner_panel_error"] = str(exc)
    return _return_family(family, "retirados", request)


@require_POST
@_owner_staff_required
def offer_publish(request, family_slug, offer_id):
    family = _family_or_404(family_slug)
    offer = _offer_or_404(family, offer_id)
    try:
        publish_offer_to_storefront(offer, family=family, user=request.user)
        request.session["owner_panel_notice"] = "Oferta publicada na montra."
    except OwnerEditorialError as exc:
        request.session["owner_panel_error"] = str(exc)
    return _return_family(family, "retirados", request)
