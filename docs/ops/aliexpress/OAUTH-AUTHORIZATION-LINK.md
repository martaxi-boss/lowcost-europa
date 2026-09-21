# AliExpress OAuth — Authorization Link

## Purpose

Keep the canonical AliExpress OAuth authorization entry point inside the Lowcost Europa project so a future reauthorization does not require rediscovering the AliExpress console/documentation flow.

This page stores **only the reusable authorization URL and callback configuration**. It must never contain an authorization `code`, `access_token`, `refresh_token`, App Secret, or any other secret.

## Canonical callback

```text
https://lowcost-europa.165-22-114-67.sslip.io/aliexpress/callback
```

This must continue to match the Callback URL registered in the AliExpress App Console.

## One-click authorization link

[Open AliExpress OAuth authorization](https://api-sg.aliexpress.com/oauth/authorize?response_type=code&force_auth=true&redirect_uri=https%3A%2F%2Flowcost-europa.165-22-114-67.sslip.io%2Faliexpress%2Fcallback&client_id=535144)

Raw URL:

```text
https://api-sg.aliexpress.com/oauth/authorize?response_type=code&force_auth=true&redirect_uri=https%3A%2F%2Flowcost-europa.165-22-114-67.sslip.io%2Faliexpress%2Fcallback&client_id=535144
```

## Reauthorization procedure

1. Open the authorization link above.
2. Log in to the intended AliExpress account if requested.
3. Approve/authorize the application.
4. AliExpress redirects to the canonical callback with a temporary `code`.
5. Exchange that `code` immediately through the official AliExpress token endpoint.
6. Store the resulting access/refresh tokens only in the existing protected server environment.

## Security rules

- The OAuth authorization `code` is temporary and single-use. Do **not** archive it in GitHub.
- Do **not** commit the App Secret.
- Do **not** commit access or refresh tokens.
- Do **not** paste codes/tokens into PRs, issues, logs, or chat output.
- AppKey/AppSecret/Tracking ID remain managed by the existing secure server configuration.
- If the callback hostname changes in the AliExpress App Console, update this page and the live callback configuration together.

## Context

This is the reusable entry point for AliExpress OAuth when an API requires a user access token, including controlled validation of `aliexpress.ds.freight.query`.

The reusable item is the authorization URL. The temporary `code` itself is deliberately not retained.
