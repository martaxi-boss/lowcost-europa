# Controlled AliExpress catalog persistence

LE-004 connects the validated AliExpress integration to the approved catalog model for one explicitly supplied product ID. It does not perform discovery or batch imports.

## Flow

`AliExpressClient.get_product_detail()` returns the normalized `AliExpressProduct`. If the normalized product has a usable `product_url`, the existing client generates an affiliate link. All external calls complete before a database transaction is opened.

Only then does the service capture one `observed_at` timestamp and enter `transaction.atomic()`. It upserts `Offer` by `(ALIEXPRESS, product_id)` and appends one new `OfferObservation`.

## Offer semantics

A first import sets both `first_seen_at` and `last_seen_at` to the same observation timestamp. Later imports preserve `first_seen_at` and update `last_seen_at`. A successful lookup sets `is_active=True`, meaning only that the external listing was seen successfully in this observation; it is not confirmation of physical stock.

The importer never assigns or replaces `ProductFamily`. Current title, product URL, image URL and affiliate URL are updated only when the latest normalized response supplies a useful value. An omitted field does not erase useful current metadata already stored.

## Observation semantics

Every successful import appends a factual observation. Price, original price, currency, evaluation percentage, sales count, commission, destination and logistics come only from the current normalized `AliExpressProduct`. Missing values remain `NULL`; old facts are never copied into a new observation. `availability` remains `UNKNOWN` because the normalized source does not yet provide a sufficiently explicit availability state.

## Atomicity and failures

Network calls are outside the database transaction. Database writes are short and atomic: an error rolls back the Offer update and Observation creation together. Product-detail, authentication, transport or required affiliate-link failures occur before persistence and therefore leave no partial database state.

## Manual command

```bash
python manage.py aliexpress_import_product --product-id <ID> --country PT --currency EUR
```

Use `--dry-run` to execute the real external calls and persistence path but deliberately roll back the database transaction:

```bash
python manage.py aliexpress_import_product --product-id <ID> --country PT --currency EUR --dry-run
```

The command prints only safe structural status and never dumps raw API payloads, secrets, signatures or unnecessary URLs.
