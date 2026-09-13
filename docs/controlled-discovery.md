# Controlled discovery — LE-005 / LE-006

Controlled discovery studies small, manual AliExpress candidate batches for Portugal. Each run accepts one explicit keyword, uses PT/EUR, defaults to 10 candidates and rejects limits outside 1..25.

The flow reuses `AliExpressClient.search_products_diagnostic()`, normalized `AliExpressProduct` objects and the LE-004 controlled persistence service. Candidates are deduplicated by product ID, processed sequentially, and expected failures are counted per product without creating a second persistence pipeline.

LE-006 adds two optional search controls without changing older calls: `target_language` and `delivery_days`. The command accepts `EN`/`PT` for language; delivery filtering is restricted to the documented study values 3, 5, 7 and 10. A value such as 6 is rejected explicitly.

For the LE-006 studies, `target_language=EN` and `delivery_days=5` are sent only to the AliExpress search request. `delivery_days=5` means the source was asked to return results matching that filter; it is not a customer delivery guarantee.

Search and detail provenance remain separate. Search-level `ship_to_days_raw` / `delivery_days` are measured from the normalized search candidate. Detail-level logistics come only from the normalized product returned by the persistence path. Discovery counts search/detail mismatches by `product_id`. From LE-007 onward, when discovery runs in commit mode, the same search candidate is passed to persistence so its search logistics can be stored separately in `search_ship_to_days_raw` / `search_delivery_days`; detail logistics remain in `ship_to_days_raw` / `delivery_days`. There is no fallback, precedence rule or effective delivery value.

The existing data-coverage metrics for price, currency, evaluation percentage, sales, commission and detail logistics remain factual observations. LE-006 adds separate search logistics metrics and a delivery mismatch count. Missing logistics means unknown data, not rejection or slow delivery.

LE-008 adds a derived diagnostic assessment for each successful candidate. Output may show `evidence_state` (`UNKNOWN`, `SEARCH_ONLY`, `DETAIL_ONLY`, `CONSISTENT` or `CONFLICT`) and `supports_5d`. This is an in-memory interpretation of the already-separated delivery values only. It does not filter, rank, deactivate or skip persistence, and it does not create a final/effective delivery value or customer-facing promise.

Example:

```text
python manage.py aliexpress_discover \
  --keyword "HIFU machine" \
  --limit 10 \
  --target-language EN \
  --delivery-days 5 \
  --dry-run
```

Dry-run may call the real API and the real persistence path, but LE-004 rolls back each product so database state remains unchanged. Output includes a short sanitized candidate table and never prints raw payloads, complete product/affiliate URLs or credentials.

Out of scope: automatic keyword expansion, relevance/commercial scoring, ranking, winner selection, search/detail data fusion, ProductFamily assignment, mass crawling, scheduler/cron, cache, frontend, deployment and new infrastructure.
