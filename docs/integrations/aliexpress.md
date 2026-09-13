# AliExpress integration

## Purpose

`apps.integrations.aliexpress` isolates all communication with the AliExpress Open Platform. Business code should use `AliExpressClient` rather than implement signing, HTTP calls or raw-response parsing itself.

## Configuration

Required environment variables:

- `ALIEXPRESS_APP_KEY`
- `ALIEXPRESS_APP_SECRET`
- `ALIEXPRESS_TRACKING_ID`
- `ALIEXPRESS_GATEWAY` (default/example: `https://api-sg.aliexpress.com/sync`)

Optional operational variables:

- `ALIEXPRESS_TIMEOUT_SECONDS` (default `10`)
- `ALIEXPRESS_MAX_RETRIES` (default `2`)

Never commit real secrets. `.env.example` contains placeholders only.

## Capabilities

The client supports category retrieval, product search, product detail lookup and affiliate-link generation. Search supports destination country, target currency and pagination. Portugal (`PT`) and EUR are the initial defaults.

## Signing and HTTP

Requests use HMAC-SHA256 over canonicalized sorted parameters, matching the previously validated project behavior for the AliExpress `/sync` gateway. Network calls use the Python standard library, explicit timeouts and bounded retries for transient network failures and HTTP 429/5xx responses.

Authentication, deterministic API errors and invalid responses are not retried blindly.

## Normalization

Raw responses are converted into lightweight dataclasses. Only fields supported by the response are populated. Missing optional values remain `None`; sales, commission, logistics and warehouse data are never invented.

`evaluate_rate` is normalized as `evaluation_rate_percent`. It is a percentage from the source, not a 0–5 star rating. For example, `96.5%` becomes `Decimal("96.5")`, meaning 96.5 percent. A future genuine star-rating field would be represented separately.

For logistics, `ship_to_days_raw` preserves the source text when `ship_to_days` (or an equivalent supported field) is present. `delivery_days` is populated only when a day count can be extracted safely and deterministically; otherwise it remains `None`. The commercial `<= 5 days` rule is intentionally not applied in this integration layer.

Products and categories require valid identifiers. Responses without a required `product_id`/equivalent or `category_id`/equivalent raise `AliExpressResponseError`; fictitious IDs such as `"None"` are never created.

## Errors and logging

Integration-specific exceptions distinguish configuration, authentication, transport, API and response failures. Logging records operation/retry information without App Secret, signatures, tokens or credentials.

## Tests

Run the full project suite:

```bash
python manage.py test
ruff check .
```

Automated tests use mocks and synthetic responses and require no live AliExpress credentials.

## Live smoke test

On an authorized environment with credentials already stored securely:

```bash
python manage.py aliexpress_smoke_test --keyword HIFU --country PT --currency EUR
```

The command checks configuration, categories, search, product detail and affiliate-link generation when a source URL is available. It reports only safe structural information such as counts, whether logistics/evaluation data are present, and interpreted `delivery_days` when available. It does not dump raw JSON, URLs, signatures, credentials or secrets, and it does not persist results.

## Scope boundaries

LE-002 does not add commercial database models, discovery, scoring, public UI, catalog mirroring, background workers, Redis, Celery or deployment infrastructure.
