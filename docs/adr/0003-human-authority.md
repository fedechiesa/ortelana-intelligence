# ADR 0003: database authority over graph resume

Status: accepted.

A graph resume payload alone must not approve a recommendation. Reviews, decisions, policy/evidence snapshots and audit belong in PostgreSQL, with uniqueness, row locks, immutable history and a deferred matching-decision constraint.

Commit the authenticated decision before resume. The resumed node reads that decision from PostgreSQL. Idempotent report persistence and startup reconciliation bridge the separate business/checkpoint transactions. n8n has no second human Wait state.

Trade-off: a crash can leave an honest intermediate RESUMING state. Recovery advances it; it never changes the immutable human decision. Exactly-once external commercial actions are not claimed or implemented.
