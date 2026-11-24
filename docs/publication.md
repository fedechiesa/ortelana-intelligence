# Release and publication procedure

The portfolio repository is `fedechiesa/ortelana-intelligence`. Publication is separate from deployment; no paid hosted environment is provisioned.

## Audit

Inspect the tracked tree, all reachable history and commit metadata. Run `python scripts/check_public_tree.py --history` and a redacted Gitleaks scan: `gitleaks git . --log-opts=--all --redact`. Compare private reference hashes with historical blobs locally, regenerate synthetic data and inspect screenshots. Never upload local audit backups, raw n8n dumps or reference material.

Before v1.0.0, both development commits were preserved with sanitized identities and content. Copied teaching tests, internal progress/final reports, a source-specific validation script and documents containing original-data aggregates were excluded from public history. An ignored local backup was retained. Authors use the maintainer's GitHub noreply address. Original dataset files were absent before sanitation and remain absent afterwards.

No MIT license is assigned because rights to all upstream academic contributions have not been confirmed. See `THIRD_PARTY_NOTICES.md`.

## Validation and release

1. Run backend/PostgreSQL tests, Ruff/Mypy, frontend tests/lint/typecheck/build, Compose validation, six-service health, live API/n8n/Grafana/browser checks and isolated clean initialization.
2. Record executed outcomes in `docs/VALIDATION.md`. Review the staged tree and commit on `main`.
3. Verify GitHub CLI authentication and push `main`. Confirm Continuous integration passes on that exact commit.
4. Dispatch Full local stack integration on `main`; inspect its real results/artifacts. Correct failures and rerun affected checks before tagging.
5. Create annotated `v1.0.0` at the validated commit and publish release notes with GitHub CLI. Verify tag, release URL, remote SHA and clean worktree.

`gh run list`, `gh run view RUN_ID` and `gh release view v1.0.0` provide current remote evidence. CI badges link to actual workflows. Scheduled n8n timers remain inactive and commercial actions remain simulated.
