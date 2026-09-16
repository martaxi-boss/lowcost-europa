from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
from apps.catalog.services.candidate_approval import (
    CandidateApprovalError,
    approve_candidate,
    reject_candidate,
    revalidate_candidate,
)
from apps.catalog.services.public_eligibility import (
    is_ship_from_verification_fresh,
    public_eligibility_q,
)
from apps.integrations.aliexpress.exceptions import AliExpressError, AliExpressRateLimitError


def _ops_headers(response):
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Cache-Control"] = "private, no-store"
    return response


@staff_member_required(login_url="admin:login")
def candidate_queue(request, family_slug):
    family = get_object_or_404(ProductFamily, slug=family_slug)
    candidates = list(
        OfferCandidate.objects.filter(product_family=family)
        .select_related("approved_offer")
        .prefetch_related("decisions__decided_by")
        .order_by("status", "-last_observed_at", "pk")
    )
    for candidate in candidates:
        offer = candidate.approved_offer
        candidate.review_required = bool(
            offer
            and candidate.status == OfferCandidate.Status.APPROVED
            and not is_ship_from_verification_fresh(offer)
        )
        candidate.fresh_approved = bool(
            offer
            and candidate.status == OfferCandidate.Status.APPROVED
            and is_ship_from_verification_fresh(offer)
        )
        candidate.history = list(candidate.decisions.all()[:5])
    counts = {
        "pending": sum(c.status == OfferCandidate.Status.PENDING for c in candidates),
        "review_required": sum(c.review_required for c in candidates),
        "approved_fresh": sum(c.fresh_approved for c in candidates),
        "rejected": sum(c.status == OfferCandidate.Status.REJECTED for c in candidates),
        "eligible": family.offer_placements.filter(
            offer__in=Offer.objects.filter(public_eligibility_q())
        ).count(),
    }
    response = render(
        request,
        "catalog/candidate_queue.html",
        {
            "family": family,
            "candidates": candidates,
            "counts": counts,
            "countries": [
                ("PL", "Polónia"),
                ("CZ", "República Checa"),
                ("FR", "França"),
                ("ES", "Espanha"),
                ("DE", "Alemanha"),
            ],
            "reasons": CandidateDecision.Reason.choices,
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
        approve_candidate(
            candidate,
            ship_from_country=request.POST.get("ship_from_country"),
            evidence_url=request.POST.get("evidence_url", ""),
            note=request.POST.get("note", ""),
            user=request.user,
        )
    except AliExpressRateLimitError:
        raise
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
            ship_from_country=request.POST.get("ship_from_country", ""),
            evidence_url=request.POST.get("evidence_url", ""),
            note=request.POST.get("note", ""),
        )
    except CandidateApprovalError as exc:
        request.session["ops_error"] = str(exc)
    return redirect("catalog:candidate-queue", family_slug=family_slug)


@require_POST
@staff_member_required(login_url="admin:login")
def candidate_revalidate(request, family_slug, candidate_id):
    candidate = _candidate_for_family(candidate_id, family_slug)
    confirmed = request.POST.get("confirmed") == "yes"
    try:
        revalidate_candidate(
            candidate,
            user=request.user,
            ship_from_country=request.POST.get("ship_from_country"),
            confirmed=confirmed,
            reason=request.POST.get("reason", CandidateDecision.Reason.ORIGIN_NOT_CONFIRMED),
            evidence_url=request.POST.get("evidence_url", ""),
            note=request.POST.get("note", ""),
        )
    except AliExpressRateLimitError:
        raise
    except (AliExpressError, CandidateApprovalError) as exc:
        request.session["ops_error"] = str(exc)
    return redirect("catalog:candidate-queue", family_slug=family_slug)
