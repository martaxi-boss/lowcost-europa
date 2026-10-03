# ADR-002 — Initial infrastructure and scaling

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

## Status

Accepted

## Decision

Lowcost Europa starts on the existing DigitalOcean Droplet: 1 vCPU, 1 GB RAM, 25 GB storage, London region, approximately US$6/month. This server is the initial system target.

When validated deployment is authorized, the architecture should remain light enough for Django, PostgreSQL, Gunicorn and Nginx to coexist initially on the same Droplet.

## Cost rule

Do not create a second Droplet, managed PostgreSQL, Redis, Celery, Elasticsearch, Kubernetes, microservices, distributed infrastructure or additional paid services without demonstrated need.

## Docker

Do not introduce Docker only by convention. Use it in the future only if it provides a concrete operational advantage.

## Staging

Staging does not require buying another server at this stage. It may be logical, temporary, CI-based or use separate configuration, whichever is most efficient.

## Future scaling

The 1 GB Droplet is not a permanent limit. Scale only when real metrics demonstrate need, such as consistently insufficient RAM, saturated CPU, degraded response times, real traffic volume, periodic tasks competing with traffic, database growth, or revenue/usage that justifies the cost.

Principle: **First prove it works. Then prove it sells. Only then scale.**
