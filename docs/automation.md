# n8n automation

`workflows/manual-analysis.json` and `scheduled-analysis.json` are exportable, inactive/unpublished n8n workflows. Both have a manual trigger; the scheduled version additionally has a Monday 09:00 trigger in `America/Argentina/Buenos_Aires`. They remain unpublished after import. The timer has not been enabled or fired as part of validation.

Startup imports the two workflow files explicitly once (marker version v2) and imports the automation header credential. An initial attempt to import a directory with `--separate` yielded no workflows on the validated n8n release; explicit file imports replaced it and were executed successfully.

The bootstrap reads only the dedicated automation token from its environment, creates a mode-0600 temporary credential import and removes it after n8n encrypts it into its project volume. The supervisor token is never supplied to n8n. No credentials are exported in workflow JSON. For a manual refresh, use `scripts/configure_n8n_demo.ps1`.

The n8n editor requires manual creation of its local owner account at first visit. This is distinct from a cloud account. Owner setup and editor authentication were not automated. CLI execution works without publishing the workflows.

## Flow

Manual/schedule event → prepare year/product inputs and idempotency key → authenticated HTTP POST `http://backend:8000/analizar` → inspect technical response → route by the **backend's persisted risk** → record outcome in n8n execution history.

NORMAL, ADVERTENCIA, CRITICO, SIN_BASE and technical errors have distinct outputs. The critical output links to the backend/UI review inbox and has no approval authority. Its data includes execution ID and correlation ID. Business calculations and policies exist only in FastAPI/LangGraph.

HTTP connection failures and 502/503/504 responses take one two-second backoff and one additional request with the same idempotency key. Permanent 4xx failures are not retried. API requests time out at 45 seconds; a workflow has a 120-second execution limit. A request whose response is lost can be reconciled using its idempotency key and execution record, without repeating side effects.

Keys are stable within one n8n execution (`workflow ID + execution ID`), including its HTTP retry. A new intentional manual execution has a new key. Rerunning a whole n8n execution creates a new analysis unless its original key is explicitly retained; this is documented rather than claiming cross-execution exactly-once delivery.

## Actual validation

`scripts/validate_n8n.py` imports separate clearly named SYNTHETIC VALIDATION workflows and runs the real n8n engine for normal, warning, critical, invalid-year permanent error and a refused-connection transient retry. It asserts the final executed node and confirms only the transient scenario reaches the retry node. All five passed. It captures a sanitized summary under ignored `.local/validation/n8n.json`. These disposable test workflows remain unpublished and separate from the shipped workflows.

When a running n8n owns its default task-broker port, CLI validation uses a distinct broker port:

```powershell
docker compose exec -T -e N8N_RUNNERS_BROKER_PORT=5680 n8n n8n execute --id ortelanaManual01 --rawOutput
```

Avoid posting raw execution exports publicly: they may include internal resume tokens. The validation script stores only selected non-secret summaries. The image logs an unavailable optional Python task runner; these workflows have no Python/Code node and executed successfully with the required engine.

Reference: [n8n server CLI](https://docs.n8n.io/hosting/cli-commands/).
