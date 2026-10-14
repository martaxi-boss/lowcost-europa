import re
from dataclasses import dataclass
from urllib import parse, request

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Offer, OfferCandidate, ProductFamily
from apps.integrations.aliexpress.client import AliExpressClient

_ALIEXPRESS_HOST_SUFFIX = "aliexpress.com"
_PRODUCT_PATH_RE = re.compile(r"/item/(\d+)\.html(?:$|[/?#])")


class ManualCandidateIntakeError(Exception):
    pass


@dataclass(frozen=True)
class ManualCandidateIntakeResult:
    outcome: str
    external_product_id: str
    candidate: OfferCandidate | None = None
    offer: Offer | None = None


def _is_aliexpress_host(hostname: str | None) -> bool:
    host = (hostname or "").lower().rstrip(".")
    return host == _ALIEXPRESS_HOST_SUFFIX or host.endswith("." + _ALIEXPRESS_HOST_SUFFIX)


def _product_id_from_url(url: str) -> str | None:
    parsed = parse.urlparse(url)
    match = _PRODUCT_PATH_RE.search(parsed.path)
    if match:
        return match.group(1)
    query = parse.parse_qs(parsed.query)
    for key in ("productId", "product_id"):
        value = query.get(key)
        if value and str(value[0]).isdigit():
            return str(value[0])
    return None


def _validated_aliexpress_url(url: str, *, allow_http: bool):
    """Validate a URL before any HTTP request or redirect to its destination."""
    parsed = parse.urlparse(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ManualCandidateIntakeError("O endereço AliExpress contém uma porta inválida.") from exc
    permitted_schemes = {"https", "http"} if allow_http else {"https"}
    if (
        parsed.scheme not in permitted_schemes
        or not _is_aliexpress_host(parsed.hostname)
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
    ):
        raise ManualCandidateIntakeError("O link tem de ser um URL AliExpress seguro.")
    return parsed


class _AliExpressOnlyRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validated_aliexpress_url(newurl, allow_http=False)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _safe_product_urlopen(req, *, timeout):
    # urllib's default opener follows arbitrary hosts before a final URL check.
    # A dedicated redirect handler checks each hop before network access.
    return request.build_opener(_AliExpressOnlyRedirectHandler()).open(req, timeout=timeout)


def resolve_aliexpress_product_url(url: str, *, opener=None) -> tuple[str, str]:
    raw = (url or "").strip()
    parsed = _validated_aliexpress_url(raw, allow_http=True)

    product_id = _product_id_from_url(raw)
    if product_id is None:
        if parsed.scheme != "https":
            raise ManualCandidateIntakeError(
                "Os links encurtados AliExpress têm de usar HTTPS."
            )
        req = request.Request(
            raw,
            method="GET",
            headers={"User-Agent": "Mozilla/5.0 LowcostEuropaManualIntake/1.0"},
        )
        try:
            with (opener or _safe_product_urlopen)(req, timeout=15) as response:
                resolved_url = response.geturl()
        except Exception as exc:
            raise ManualCandidateIntakeError(
                "Não foi possível resolver o link AliExpress."
            ) from exc
        _validated_aliexpress_url(resolved_url, allow_http=False)
        product_id = _product_id_from_url(resolved_url)

    if not product_id:
        raise ManualCandidateIntakeError("Não foi possível identificar o produto AliExpress.")

    canonical_url = f"https://www.aliexpress.com/item/{product_id}.html"
    return product_id, canonical_url


def _existing_result(
    product_id: str, target_family: ProductFamily
) -> ManualCandidateIntakeResult | None:
    candidate = (
        OfferCandidate.objects.select_related("product_family", "approved_offer")
        .filter(source=Offer.Source.ALIEXPRESS, external_product_id=product_id)
        .first()
    )
    if candidate is not None:
        suffix = "" if candidate.product_family_id == target_family.pk else "_OTHER_FAMILY"
        return ManualCandidateIntakeResult(
            outcome=f"ALREADY_{candidate.status}{suffix}",
            external_product_id=product_id,
            candidate=candidate,
            offer=candidate.approved_offer,
        )

    offer = Offer.objects.filter(
        source=Offer.Source.ALIEXPRESS,
        external_product_id=product_id,
    ).first()
    if offer is not None:
        return ManualCandidateIntakeResult(
            outcome="OFFER_EXISTS",
            external_product_id=product_id,
            offer=offer,
        )
    return None


def intake_manual_aliexpress_candidate(
    *,
    url: str,
    family: ProductFamily,
    client: AliExpressClient | None = None,
    resolver=resolve_aliexpress_product_url,
    now=None,
) -> ManualCandidateIntakeResult:
    if family.status == ProductFamily.Status.RETIRED:
        raise ManualCandidateIntakeError("A família selecionada está retirada.")

    product_id, canonical_url = resolver(url)

    existing = _existing_result(product_id, family)
    if existing is not None:
        return existing

    api = client or AliExpressClient()
    detail = api.get_product_detail(product_id, "PT", "EUR")
    if detail.product_id != product_id:
        raise ManualCandidateIntakeError(
            "O detalhe AliExpress não corresponde ao produto resolvido."
        )

    observed_at = now or timezone.now()
    with transaction.atomic():
        existing = _existing_result(product_id, family)
        if existing is not None:
            return existing

        candidate = OfferCandidate.objects.create(
            product_family=family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=product_id,
            status=OfferCandidate.Status.PENDING,
            title=detail.title or "",
            image_url=detail.image_url or "",
            product_url=canonical_url,
            price=detail.price,
            original_price=detail.original_price,
            currency=detail.currency,
            evaluation_rate_percent=detail.evaluation_rate_percent,
            sales_count=detail.sales_count,
            commission_rate=detail.commission_rate,
            detail_ship_to_days_raw=detail.ship_to_days_raw,
            detail_delivery_days=detail.delivery_days,
            discovered_at=observed_at,
            last_observed_at=observed_at,
        )

    return ManualCandidateIntakeResult(
        outcome="CREATED",
        external_product_id=product_id,
        candidate=candidate,
    )
