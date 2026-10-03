# MVP PRELAUNCH 004 — AUTHORIZED PUBLIC CONTACT CHANNELS

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

## Authorized public contacts

The only public contact channels authorized for this task are:

- Email: `help.onlinefuture@gmail.com`
- WhatsApp: `+351 965 471 236`
- WhatsApp link: `https://wa.me/351965471236`

No operator legal identity, registration data or private address is introduced by this task.

## Pages changed

- New `/contacto/` institutional page.
- Footer adds `Contacto` alongside the existing institutional links.
- Privacy adds the authorized institutional contact and links to `/contacto/`.
- Terms replaces the pending official-contact state with the authorized public channels while keeping operator legal identity pending.
- Affiliates links to Contacto for transparency questions.
- Sitemap includes `/contacto/`; with five active ProductFamilies the expected total is 11 URLs.

## Privacy and launch boundaries

The existing distinction between application-level `OfferClick` tracking and technical server/security logs is preserved. No new absolute data-processing claims are introduced.

Staging indexing remains fail-closed. No change is made to `DJANGO_PUBLIC_INDEXING_ENABLED=false`, `DJANGO_PUBLIC_SITE_URL=`, or canonical behavior.

Operator legal identity remains `PENDING OWNER INPUT`. The final public domain remains pending. Off-server backup remains pending. Public launch is not authorized.

## Data and scope

This task performs zero database writes, zero catalog changes, zero OfferObservation creation and zero `/go/` calls. It introduces no model, schema or migration changes.