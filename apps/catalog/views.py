from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_approval import (
    OWNER_REJECTION_REASON_CHOICES,
    CandidateApprovalError,
    approve_candidate,
    reject_candidate,
    revalidate_candidate,
)
from apps.catalog.services.candidate_move import CandidateMoveError, move_candidate_to_family
from apps.catalog.services.public_eligibility import (
    is_protocol_verified,
    public_eligibility_q,
)
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError

def _ops_headers(response):
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Cache-Control"] = "private, no-store"
    return response


def _decorate_candidate(candidate):
    offer = candidate.approved_offer
    status_labels = {
        OfferCandidate.Status.PENDING: "A rever",
        OfferCandidate.Status.APPROVED: "Aprovado",
        OfferCandidate.Status.REJECTED: "Rejeitado",
    }
    candidate.status_label = status_labels[candidate.status]
    candidate.review_required = bool(
        offer
        and candidate.status == OfferCandidate.Status.APPROVED
        and not is_protocol_verified(offer)
    )
    candidate.fresh_approved = bool(
        offer
        and candidate.status == OfferCandidate.Status.APPROVED
        and is_protocol_verified(offer)
    )
    candidate.history = list(candidate.decisions.all()[:5])
    signal_labels = dict(CandidateDecision.ReviewSignal.choices)
    for decision in candidate.history:
        decision.decision_label = (
            "Aprovado" if decision.decision == CandidateDecision.Decision.APPROVE else "Rejeitado"
        )
        decision.review_signal_labels = [
            signal_labels[signal] for signal in decision.review_signals if signal in signal_labels
        ]
    return candidate


@staff_member_required(login_url="admin:login")
def candidate_queue(request, family_slug):
    family = get_object_or_404(ProductFamily, slug=family_slug)
    all_candidates = [
        _decorate_candidate(candidate)
        for candidate in OfferCandidate.objects.filter(product_family=family)
        .select_related("approved_offer")
        .prefetch_related("decisions__decided_by")
        .order_by("status", "-last_observed_at", "pk")
    ]
    view = request.GET.get("view", "review")
    if view not in {"review", "approved", "rejected", "all"}:
        view = "review"
    if view == "review":
        candidates = [
            c
            for c in all_candidates
            if c.status == OfferCandidate.Status.PENDING or c.review_required
        ]
    elif view == "approved":
        candidates = [c for c in all_candidates if c.status == OfferCandidate.Status.APPROVED]
    elif view == "rejected":
        candidates = [c for c in all_candidates if c.status == OfferCandidate.Status.REJECTED]
    else:
        candidates = all_candidates

    counts = {
        "pending": sum(c.status == OfferCandidate.Status.PENDING for c in all_candidates),
        "review_required": sum(c.review_required for c in all_candidates),
        "approved_fresh": sum(c.fresh_approved for c in all_candidates),
        "rejected": sum(c.status == OfferCandidate.Status.REJECTED for c in all_candidates),
        "eligible": family.offer_placements.filter(
            offer__in=Offer.objects.filter(public_eligibility_q())
        ).count(),
    }
    ops_error = request.session.pop("ops_error", "")
    response = render(
        request,
        "catalog/candidate_queue.html",
        {
            "ops_error": ops_error,
            "family": family,
            "candidates": candidates,
            "counts": counts,
            "active_view": view,
            "families": ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED)
            .exclude(pk=family.pk)
            .order_by("display_order", "pk"),
            "rejection_reason_choices": OWNER_REJECTION_REASON_CHOICES,
        },
    )
    return _ops_headers(response)


def _candidate_for_family(candidate_id, family_slug):
    return get_object_or_404(
        OfferCandidate.objects.select_related("product_family", "approved_offer"),
        pk=candidate_id,
        product_family__slug=family_slug,
    )


@require_POST
@staff_member_required(login_url="admin:login")
def candidate_approve(request, family_slug, candidate_id):
    candidate = _candidate_for_family(candidate_id, family_slug)
    try:
        approve_candidate(candidate, user=request.user)
    except AliExpressRateLimitError:
        request.session["ops_error"] = (
            "A AliExpress está temporariamente indisponível. "
            "Tente novamente dentro de instantes."
        )
    except (AliExpressError, CandidateApprovalError) as exc:
        request.session["ops_error"] = str(exc)
    return redirect("catalog:candidate-queue", family_slug=family_slug)


@require_POST
@staff_member_required(login_url="admin:login")
def candidate_reject(request, family_slug, candidate_id):
    candidate = _candidate_for_family(candidate_id, family_slug)
    try:
        reject_candidate(
            candidate,
            user=request.user,
            reason=request.POST.get("reason", ""),
            note=request.POST.get("note", ""),
        )
    except CandidateApprovalError as exc:
        request.session["ops_error"] = str(exc)
    return redirect("catalog:candidate-queue", family_slug=family_slug)


@require_POST
@staff_member_required(login_url="admin:login")
def candidate_revalidate(request, family_slug, candidate_id):
    candidate = _candidate_for_family(candidate_id, family_slug)
    try:
        revalidate_candidate(candidate, user=request.user)
    except CandidateApprovalError as exc:
        request.session["ops_error"] = str(exc)
    return redirect("catalog:candidate-queue", family_slug=family_slug)


@require_POST
@staff_member_required(login_url="admin:login")
def candidate_move(request, family_slug, candidate_id):
    candidate = _candidate_for_family(candidate_id, family_slug)
    target = get_object_or_404(
        ProductFamily.objects.exclude(status=ProductFamily.Status.RETIRED),
        pk=request.POST.get("target_family"),
    )
    try:
        moved, _ = move_candidate_to_family(candidate, target_family=target, user=request.user)
        return redirect("catalog:candidate-queue", family_slug=moved.product_family.slug)
    except CandidateMoveError as exc:
        request.session["ops_error"] = str(exc)
        return redirect("catalog:candidate-queue", family_slug=family_slug)
