from dataclasses import dataclass, field

from apps.catalog.services.candidate_discovery import (
    CandidateDiscoveryResult,
    discover_family_candidates,
)
from apps.catalog.services.candidate_learning import prioritize_existing_keywords
from apps.integrations.aliexpress.client import AliExpressClient


@dataclass
class DeepDiscoveryPage:
    keyword: str
    keyword_index: int
    page: int
    result: CandidateDiscoveryResult
    new_raw_ids: int
    repeated_raw_ids: int
    cross_keyword_repeated_ids: int = 0
    stop_reason: str = ""


@dataclass
class DeepDiscoveryResult:
    pages: list[DeepDiscoveryPage] = field(default_factory=list)
    search_operations: int = 0
    detail_attempts: int = 0
    created: int = 0
    stop_reason: str = ""
    last_keyword: str = ""
    last_page: int = 0
    unique_product_ids: set[str] = field(default_factory=set)
    cross_page_duplicates: int = 0
    cross_keyword_duplicates: int = 0


def discover_family_deep(
    family,
    keywords,
    *,
    start_keyword_index=1,
    start_page=1,
    max_pages=3,
    limit=15,
    max_details=8,
    max_search_operations=60,
    max_detail_attempts=180,
    client=None,
):
    if start_keyword_index < 1:
        raise ValueError("start_keyword_index must be at least 1")
    if start_page < 1:
        raise ValueError("start_page must be at least 1")
    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    client = client or AliExpressClient()
    aggregate = DeepDiscoveryResult()
    keywords = tuple(keywords)
    if start_keyword_index == 1 and start_page == 1:
        keywords = prioritize_existing_keywords(family, keywords)
    global_seen = set()

    for keyword_index, keyword in enumerate(keywords, start=1):
        if keyword_index < start_keyword_index:
            continue
        seen_for_keyword = set()
        first_page = start_page if keyword_index == start_keyword_index else 1
        for page in range(first_page, max_pages + 1):
            if aggregate.search_operations >= max_search_operations:
                aggregate.stop_reason = "SEARCH_BUDGET"
                return aggregate
            if aggregate.detail_attempts >= max_detail_attempts:
                aggregate.stop_reason = "DETAIL_BUDGET"
                return aggregate
            remaining_details = max_detail_attempts - aggregate.detail_attempts
            page_max_details = min(max_details, remaining_details)
            try:
                result = discover_family_candidates(
                    family,
                    keyword,
                    page_no=page,
                    limit=limit,
                    max_details=page_max_details,
                    client=client,
                )
            except Exception as exc:
                aggregate.last_keyword = keyword
                aggregate.last_page = page
                aggregate.stop_reason = exc.__class__.__name__
                setattr(exc, "deep_discovery_result", aggregate)
                raise
            aggregate.search_operations += 1
            aggregate.detail_attempts += result.detail_attempts
            aggregate.created += result.created
            aggregate.last_keyword = keyword
            aggregate.last_page = page

            raw_ids = set(result.raw_product_ids)
            new_ids = raw_ids - seen_for_keyword
            repeated_ids = raw_ids & seen_for_keyword
            cross_keyword_ids = (raw_ids & global_seen) - seen_for_keyword
            aggregate.cross_page_duplicates += len(repeated_ids)
            aggregate.cross_keyword_duplicates += len(cross_keyword_ids)
            aggregate.unique_product_ids.update(raw_ids)
            stop_reason = ""
            if (
                result.total_page_no is not None
                and result.current_page_no is not None
                and result.current_page_no >= result.total_page_no
            ):
                stop_reason = "LAST_PAGE"
            elif not raw_ids:
                stop_reason = "EMPTY_PAGE"
            elif not new_ids:
                stop_reason = "NO_NEW_IDS"
            seen_for_keyword.update(raw_ids)
            global_seen.update(raw_ids)
            aggregate.pages.append(
                DeepDiscoveryPage(
                    keyword=keyword,
                    keyword_index=keyword_index,
                    page=page,
                    result=result,
                    new_raw_ids=len(new_ids),
                    repeated_raw_ids=len(repeated_ids),
                    cross_keyword_repeated_ids=len(cross_keyword_ids),
                    stop_reason=stop_reason,
                )
            )
            if stop_reason:
                break
            if aggregate.detail_attempts >= max_detail_attempts:
                aggregate.stop_reason = "DETAIL_BUDGET"
                return aggregate
    return aggregate
