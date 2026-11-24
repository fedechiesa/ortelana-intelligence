# Architecture and invariants

The system is a modular monolith with a separate static UI and supporting local infrastructure. FastAPI is the sole authority over commercial calculations, review eligibility and authorization. LangGraph coordinates internal stateful work; n8n triggers and routes external events, without reproducing business rules.

## Modules

| Module | Responsibility |
| --- | --- |
| `core` | Environment settings, authenticated fixed local identities and domain errors |
| `domain` | Decimal percentage calculations and threshold classification |
| `services/ingestion` | Strict immutable dataset import and provenance |
| `services/analytics` | Query persisted rows; observed totals, matched comparisons and rankings |
| `graph` | Typed shared state, parallel specialists, join, risk/report, interrupt and finish |
| `services/executions` | Idempotent reservation, database locks, report/review transactions, decisions and recovery |
| `repositories` | SQLAlchemy schema, session boundaries and engine configuration |
| `api` / `schemas` | Authenticated REST contracts and validated request/response models |
| `observability` | Low-cardinality real metrics and structured application events |

## Execution lifecycle

1. Validate filters and supported reporting years. Reserve a UUID execution and unique idempotency key in a transaction. Pin dataset identity and policy snapshot.
2. Obtain a PostgreSQL session advisory lock for the execution. It remains held through graph processing, even though individual business/checkpoint writes commit separately.
3. Invoke or recover the graph with `thread_id=execution_id`, recursion limit 16, maximum parallelism three and synchronous checkpoint durability.
4. Persist report, commercial risk, review (if critical) and audit in one transaction. Replays do not duplicate this side effect.
5. Interrupt the critical path. Update the execution's recorded steps and technical state from the actual checkpoint.
6. On a human decision, lock/update only a pending critical record, insert a uniquely constrained immutable decision and audit it; commit before attempting resume.
7. Resume with `Command(resume=True)`. The human node reads the committed decision from the database, ignoring the resume payload as a source of authority.

## Crash windows

Business rows and LangGraph checkpoints use separate transactions. The design therefore provides replay-safe recovery rather than claiming a distributed atomic commit. A crash after report commit but before its checkpoint replays `persist_report` idempotently. A crash after decision commit but before resume leaves `RESUMING`; startup recovery consults the durable decision and advances the checkpoint. A crash before an interrupt is captured advances until the interrupt, then resumes only if a committed decision exists.

`RUNNING`, `RESUMING` and `WAITING_REVIEW` executions are reconciled on startup. `ERROR` executions require explicit supervisor recovery after the underlying issue is addressed. An incomplete replay can be queried by ID. Completed runs are not silently recomputed.

Unique database constraints protect execution idempotency and one decision per review. Row locks and compare-and-set approval updates handle concurrent decisions. PostgreSQL triggers protect final decisions, evidence, inputs, policy snapshots, review history and audit. A deferred constraint prevents an approved/rejected state without the matching persisted decision in the same transaction.

SQLite is a documented single-process testing/diagnostic fallback with persistent SQLite checkpoints and local locking. It does not claim to provide the PostgreSQL distributed advisory-lock or trigger guarantees.

## Scope boundaries

All commercial actions are simulated. No LLM is required or invoked. The system operates on bounded historical files; synchronous processing is acceptable at the supplied scale, while a production-sized import should use a background job queue. The frontend owns display preferences only; the backend owns all analysis and approval states.
