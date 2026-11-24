# Executed validation evidence

Date: 2026-11-24 (Buenos Aires). Results describe executed checks against synthetic fixtures and the local demo. No original-company performance metrics are distributed.

## Final local checks

| Check | Executed result |
| --- | --- |
| Backend Pytest, including dedicated PostgreSQL integration | **48 passed**, 5.97 s |
| Ruff lint | Passed, backend and Python scripts |
| Ruff format | Passed, 38 files |
| Mypy | Passed, 22 application source files |
| Frontend ESLint / Prettier / TypeScript | All passed |
| Frontend Vitest | **3 passed** |
| Frontend production build | Passed, Vite 6.4.6 |
| Production npm dependency audit | **0 known vulnerabilities** reported by `npm audit --omit=dev` at validation time |
| Frozen Python installation | `uv sync --project backend --frozen` succeeded in a newly created environment; 48 tests collected |
| Docker Compose configuration and image build | Passed |
| Six service health checks | backend, frontend, postgres, n8n, prometheus and grafana all healthy |
| Live stack validation | **27 checks passed** including actual restart and twenty Grafana datasource queries |
| Real n8n engine | **5 synthetic scenarios passed** |
| Real Chromium E2E | **2 passed**, 14.4 s; business review and both Grafana dashboards |
| Clean initialization | Passed with isolated temporary database/backend containers and fresh storage |
| Synthetic regeneration | Generator reproduced both committed demo files byte-for-byte |

## What the checks establish

Backend coverage includes exact Decimal thresholds; missing/zero baselines; supported report formats; invalid, negative and non-finite quantities; incompatible cohorts; strict API requests; real graph routing; persisted evidence; unauthorized/spoofed/duplicate decisions; concurrency; immutable policy snapshots; sanitized errors; checkpoint restart/recovery; a committed-decision crash window; actual PostgreSQL advisory/row locks, integrity triggers and a decision arriving during report checkpoint persistence. Independent synthetic compatibility cases replace copied teaching tests.

PostgreSQL tests use the dedicated `ortelana_test` database and refuse names without `_test`. The application identity has no superuser, database creation, role creation, replication or row-security bypass privileges. The clean-initialization check exercised migrations, synthetic import, PostgreSQL checkpoints, a critical interruption and authenticated approval without reusing or deleting existing project volumes.

The live suite verified NORMAL, ADVERTENCIA and CRITICO, idempotent replay, real container restart, approval and rejection, unauthorized 403 and duplicate 409 responses. Prometheus returned `up=1`. Both Grafana datasources were healthy and all twenty provisioned queries actually ran through `/api/ds/query` without datasource errors.

n8n executed normal, warning, critical, permanent invalid-year and refused-connection scenarios. Permanent 4xx did not retry; the transient scenario retried exactly once using the same key. Workflows remained unpublished. Browser tests exercised connected analytics/review/history, responsive navigation/themes and real Grafana dashboards; screenshots are actual synthetic application captures.

## Publication audit

Gitleaks 8.30.1, downloaded from its official release and checksum-verified, found no secrets in the initial complete development history. Private reference files were compared with historical blobs, and ignored source/runtime paths were inspected. Original dataset files were absent. Copied teaching tests and internal documents with original-data aggregates were excluded from public history; personal author email was replaced with GitHub noreply. Both development commits were retained in sanitized form.

The published tree and reachable history also passed `scripts/check_public_tree.py --history`, a second Gitleaks scan and a local original-record/hash comparison. The first published candidate contained 124 tracked files and 153 unique historical blobs across three commits. A fresh clone contained only the demo CSV/catalog under its data paths. Private inputs, logs, browser traces, virtual environments, database dumps/volumes and the local audit backup are not published. This is a scoped publication audit, not a guarantee against every possible security defect.

## GitHub-hosted evidence

The publication candidate `9ead148` passed both GitHub-hosted workflows on Ubuntu Linux:

- [Continuous integration: passed](https://github.com/fedechiesa/ortelana-intelligence/actions/runs/45458823712). All three jobs passed; backend reported 48 tests passed, including PostgreSQL integration. Frontend checks/build and full-history Gitleaks also passed.
- [Full local stack integration: passed](https://github.com/fedechiesa/ortelana-intelligence/actions/runs/45458814715). Fresh six-service build/health, isolated clean initialization, 27 live checks, 5 n8n scenarios and 2 Chromium E2E tests passed. Sanitized summaries and actual screenshots were uploaded as `actual-stack-evidence`.

The first runs exposed deprecated Node 20 action runtimes. The release workflow definitions use official Node 24 actions pinned to verified full commit SHAs. They are rerun before tagging; the [v1.0.0 release notes](https://github.com/fedechiesa/ortelana-intelligence/releases/tag/v1.0.0) record the final validated commit and run URLs. README badges show subsequent workflow status rather than a static success claim.

## Remaining limits

- No generative/predictive model is implemented; the agents, recommendations and risk rules are deterministic. Commercial actions are simulated.
- Shared demo identities and loopback configuration are for local review. Individual identity, TLS and shared deployment hardening remain future work.
- Scheduled n8n timer firing has not been tested; editor first-owner setup remains manual. Optional Python runner warnings do not affect these HTTP workflows.
- Verification covered Windows Docker Desktop with Linux containers and a fresh GitHub-hosted Ubuntu Linux runner. Other host platforms have not been independently exercised.
- Project-wide MIT licensing remains withheld because upstream academic publication rights could not be confirmed. Original teaching material is excluded.

Sanitized local summaries are stored under ignored `.local/validation/`. Raw n8n execution dumps may contain internal resume tokens and are deliberately not attached to public artifacts.
