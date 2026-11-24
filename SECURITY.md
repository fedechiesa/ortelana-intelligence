# Security policy

Version 1.0.x is the maintained portfolio line. This is a local demonstration with loopback bindings and intentionally public demo credentials. It is not a hardened shared deployment. See [the security model](docs/security.md) for role boundaries, integrity guarantees and operating assumptions.

## Reporting a vulnerability

Use **Security → Report a vulnerability** when available. Do not include working exploits, real tokens, private data or raw n8n execution dumps in public issues. If private reporting is unavailable, request a private reporting channel in an issue without sensitive details. No response-time SLA or bounty is offered.

Include the affected commit/version, prerequisites, minimal synthetic reproduction, expected/actual behavior and impact. Relevant boundaries include supervisor authority, immutable evidence, idempotency, checkpoint recovery and data disclosure.

## Operating safely

- Keep demo services on localhost. Replace demo passwords/tokens and the n8n encryption key, implement individual identity and HTTPS, and review permissions before shared deployment.
- `.env`, `data/private/`, teaching materials, logs, database volumes and browser traces are excluded from Git. Do not attach them to issues or releases.
- The API identity is not a cluster superuser. Grafana has a separate SELECT-only identity. Database administrators remain trusted and can alter integrity controls.
- Back up state before schema or credential changes. Destructive downgrades are disabled; environment edits do not rotate existing database passwords.
- Use locked dependencies and digest-pinned images. Check advisories before exposing services; no continuous vulnerability-monitoring service is claimed.

If a secret is committed, revoke/rotate it first, remove it from all affected history, and re-audit before publishing. Removing it only from the latest tree is insufficient.
