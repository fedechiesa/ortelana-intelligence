# Security boundaries

This repository targets a local portfolio demonstration. All exposed service ports bind to loopback. Docker services communicate by internal DNS names on the project network. The frontend uses a same-origin `/api` proxy, a restrictive content security policy, no third-party fonts/scripts and no permissive CORS configuration.

The backend authenticates three distinct tokens with constant-time comparison: local operator (read/analyze), local supervisor (plus review/recovery/policy) and n8n automation (read/analyze, no approval). Identity is derived from the verified token; client-supplied responsible names are forbidden. These are fixed local identities, not individual multi-user accounts. Tokens are stored in the browser's session storage and sent as Authorization headers, never URL parameters. Sign-out clears the token and query cache.

All supplied credentials are clearly marked demo values. Real `.env` files are ignored. n8n encrypts its dedicated automation credential in its persistent volume; its encryption key must remain stable. Grafana has a separate read-only database identity. Health/metrics endpoints are intentionally available for the local/internal infrastructure. An untrusted shared deployment requires TLS, individual accounts/OIDC, token rotation, stronger session management and operational access controls.

Strict JSON request schemas reject unknown fields, invalid decisions, non-finite thresholds and invalid year ordering. Query schemas intentionally parse textual URL numbers. Bounded pagination, query/connect timeouts, graph limits and safe retry policies constrain processing. Responses expose sanitized technical errors and correlation IDs, never stack traces or credentials.

PostgreSQL constraints, locks and triggers enforce one decision per review, immutable final decisions and evidence, append-only audit and policy snapshots, and committed human authority. A normal/warning/no-baseline run cannot receive an approval. Actions are simulations only.

## Database role separation

`ortelana_admin` is the cluster administrator. `ortelana` is the application/migration identity: it owns the two project databases and their public application objects, with `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOREPLICATION` and no row-security bypass. `grafana_reader` receives SELECT on the commercial schema and no writes. Administrator credentials are not passed to the backend, frontend or n8n.

The original local cluster had been initialized using the application name. PostgreSQL requires its bootstrap identity to remain a superuser. The authorized upgrade therefore preserved that identity as `ortelana_admin`, created a new restricted `ortelana` identity and transferred only project public objects and database ownership. A temporary migration identity was removed after the operation. All existing executions were preserved. No unrelated database/project was modified.

The bootstrap creates these roles on a new volume. A clean isolated initialization verifies migrations, import, PostgreSQL checkpoints, critical interruption and authenticated approval. The final backend suite passed using the restricted application identity; a dedicated test asserts its actual global privilege flags. See [executed evidence](VALIDATION.md) and [PostgreSQL role changes](https://www.postgresql.org/docs/16/sql-alterrole.html).

Original teaching materials/dataset are excluded pending redistribution review. No project-wide license is assigned to third-party materials. Dependency locks, `.dockerignore`, `.gitignore`, container non-root backend execution and local-only exposure reduce accidental leakage; inspect the staged tree before publication.
