# Final mission — PT/ES evidence isolation

## Verified administrative operation

Ruleset `26818755` (Low Cost Europa — main) was created active. API readback confirmed default-branch targeting, deletion and non-fast-forward restrictions, PR requirement with zero required reviews, and the real `test` check bound to GitHub Actions integration 15368. No bypass actors were added. Owner emergency administration remains available through Settings; ordinary development uses branches and PRs. No force-push or deletion of main was attempted.

`audit` and `source-browser` exist but have path-filtered triggers, so requiring them globally would strand unrelated PRs. They remain executable checks, not fictional required contexts. This PR exercises the protected development path.

## Commercial correction

Previously the public freshness gate, public observation selector, owner price table and maintenance rotation could consume a Spanish observation as if it were Portuguese. No ES observations were persisted at the previous audit, so isolate these selectors before collecting Spanish evidence. ES observations now remain separate private evidence. The public store explicitly identifies Portuguese reference data and does not claim confirmed Spanish price or delivery. The private table separates PT/legacy unknown-destination history from strictly ES observations; delivery always requires its exact destination. General publication and editorial origin are not market-specific certification.

`observe_market_offers --country ES --limit 5` only previews selection. Explicit `--persist` uses the existing official product-detail client, shared lock/cadence/backoff and a maximum of five offers. It writes observations only, never changes Offer fields, editorial state, affiliate URLs or publication, and aborts on API/rate/runtime errors or response-identity mismatch. No recurring task or API quota increase. Absence of stock or delivery remains UNKNOWN/null. No schema or dependency changes.

## Search Console

Owner completed OAuth in the existing Windsor account. The connected-account tool confirms `sc-domain:lowcost-europa.eu`. Explicit-account 30-day summary and country/page queries completed with zero rows. This is no returned data, not demonstrated zero impressions/clicks. Authenticated Google performance UI says data are processing. No demo metrics or fabricated zero snapshot were stored.

Google sitemap UI still reports unable to fetch, 0 discovered. Bing sitemap detail reports page not accessible / Bingbot unable to access, 0 discovered. Public HTTPS sitemap returned valid XML with 23 unique URLs and robots permits the public routes. No repeat IndexNow notification or speculative production transport change. Current index inclusion requires separate inspection, never inferred from receipt.

## Validation

Local targeted SQLite: 13 tests passed (market isolation, no publication/link mutations, dry-run, mismatched market, rate-limit abort, PT rotation and private evidence). Ruff all-source passed. PostgreSQL full CI, browser QA, guarded backup/deploy and independent production readback are required before claiming deployment. See PR checks and issue #206 for subsequent evidence.

Website edits and GitHub administration are ChatGPT Work/GitHub operations; they are not a new Ferrari executor certification. Existing Ferrari/SSH architecture is unchanged.
