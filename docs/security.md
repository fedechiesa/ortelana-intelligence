# Security boundaries

This repository targets a local portfolio demonstration. All exposed service ports bind to loopback. Docker services communicate by internal DNS names on the project network. The frontend uses a same-origin `/api` proxy, a restrictive content security policy, no third-party fonts/scripts and no permissive CORS configuration.

The backend authenticates three distinct tokens with constant-time comparison: local operator (read/analyze), local supervisor (plus review/recovery/policy) and n8n automation (read/analyze, no approval). Identity is derived from the verified token; client-supplied responsible names are forbidden. These are fixed local identities, not individual multi-user accounts. Tokens are stored in the browser's session storage and sent as Authorization headers, never URL parameters. Sign-out clears the token and query cache.

All supplied credentials are clearly marked demo values. Real `.env` files are ignored. n8n encrypts its dedicated automation credential in its persistent volume; its encryption key must remain stable. Grafana has a separate read-only database identity. Health/metrics endpoints are intentionally available for the local/internal infrastructure. An untrusted shared deployment requires TLS, individual accounts/OIDC, token rotation, stronger session management and operational access controls.

Strict JSON request schemas reject unknown fields, invalid decisions, non-finite thresholds and invalid year ordering. Query schemas intentionally parse textual URL numbers. Bounded pagination, query/connect timeouts, graph limits and safe retry policies constrain processing. Responses expose sanitized technical errors and correlation IDs, never stack traces or credentials.

PostgreSQL constraints, locks and triggers enforce one decision per review, immutable final decisions and evidence, append-only audit and policy snapshots, and committed human authority. A normal/warning/no-baseline run cannot receive an approval. Actions are simulations only.

## Pending environment hardening

The original project-local PostgreSQL bootstrap user `ortelana` remains a superuser. An attempted separation into `ortelana_admin` (local administrator) and a reduced-privilege application user was **rejected by automatic approval review** because creating the persistent administrator and changing privileges required specific authorization for that resource. The statement was not executed. An explicit authorization request is pending. No workaround or indirect role mutation was used.

Until authorized, keep this stack on localhost with synthetic data. This is a material limitation of the running database role, not a claim of completed least-privilege deployment. Application approval roles and Grafana read-only access remain enforced. No unrelated database/project is modified.

Original teaching materials/dataset are excluded pending redistribution review. No project-wide license is assigned to third-party materials. Dependency locks, `.dockerignore`, `.gitignore`, container non-root backend execution and local-only exposure reduce accidental leakage; inspect the staged tree before publication.
