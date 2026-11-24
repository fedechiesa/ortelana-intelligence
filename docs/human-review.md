# Human supervision

Commercial risk, technical execution state and approval state are separate persisted fields. A critical result is a reason to request review, not permission to act.

1. The report transaction stores evidence, risk, immutable review and audit. Approval becomes PENDING and technical state WAITING_REVIEW.
2. The graph interrupts at `human_review`. Its PostgreSQL checkpoint survives service restart.
3. The UI shows matched totals, excluded pairs, coverage, segment evidence, recommendation, original policy and trace ID.
4. An authenticated supervisor posts `APROBADO` or `RECHAZADO` with a meaningful comment. The backend does not accept a free-form responsible name.
5. A transaction locks/conditionally updates the pending record and inserts exactly one immutable decision with actor, time, evidence and policy. The audit event commits with it.
6. The graph resumes only after commit and reads that stored decision. Approval marks a **simulated** authorization; rejection finishes without it. No external business action is performed.

Missing reviews, noncritical cases, already decided requests and changes to final decisions are rejected. Operator and automation tokens receive 403 on decisions. Missing tokens receive 401. Invalid/spoofed inputs receive 422. Duplicate or invalid-state decisions receive 409. A deferred PostgreSQL constraint additionally prevents a final approval state without a matching stored critical-review decision.

The immutable decision primary key is the execution/review ID. Row locks, compare-and-set and uniqueness protect simultaneous operators. Database triggers reject edits/deletions to decisions, audit, reviews and policies; evidence and policy snapshots are protected after report persistence.

n8n does not hold a second approval state or a human-approval Wait node. Its critical branch records the backend execution ID and directs the operator to the authenticated review inbox. Its only Wait node is bounded technical backoff. This avoids two competing sources of truth.

A crash after decision commit leaves a recoverable RESUMING state. Startup reconciliation resumes it. A temporary resume failure never loses or reverses the committed human decision. A supervisor may invoke `/executions/{id}/recover`; the endpoint cannot rewrite a final decision or create authorization without one.

For a decision arriving while the report/interrupt checkpoint is still finishing, continuation waits up to five seconds for the execution lock. It rechecks the persisted final state before invoking again, preventing duplicate finalization. A prolonged lock returns 503 with an explicit **decision recorded** message, preserving the decision and RESUMING state for recovery.
