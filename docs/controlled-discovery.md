# Controlled discovery — LE-005

LE-005 studies small, manual AliExpress candidate batches for Portugal. Each run accepts one explicit keyword, uses PT/EUR, defaults to 10 candidates and rejects limits outside 1..25.

The flow reuses `AliExpressClient.search_products()`, normalized `AliExpressProduct` objects and the LE-004 controlled persistence service. Candidates are deduplicated by product ID, processed sequentially, and failures are counted per product without creating a second persistence pipeline.

Metrics describe factual data coverage only: price, currency, evaluation percentage, sales, commission, raw shipping, interpreted delivery days and the observed split of delivery days within/over five days. Missing logistics is unknown data, not failure or rejection. No scoring, ranking, winner selection or ProductFamily assignment occurs.

Use `python manage.py aliexpress_discover --keyword HIFU --limit 10 --dry-run` for the first study. Dry-run may call the real API and persistence path but LE-004 rolls back each product so database state is unchanged.

Out of scope: multiple automated keywords, pagination engine, mass crawling, scheduler/cron, cache, scoring, frontend, deployment and new infrastructure.
