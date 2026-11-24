# Deterministic agents and graph

These specialists are deterministic processing agents, not LLM-based autonomous reasoning. Each has a concrete objective and accesses only persisted evidence. No model, prompt, API key or model download is required.

| Node | Input / output and responsibility |
| --- | --- |
| coordinator | Validates selected data and reporting years before delegation |
| sales | Network matched-cohort totals, percentage and coverage |
| products | Product master identity, observed ranking, matched changes and risk |
| branches | Branch-specific ranking, compatible pairs, variation and risk |
| risk | Joins all three outputs; flags declining segments and chooses highest supported risk |
| report | Produces structured quantitative evidence, deterministic recommendation and limitations; persists report/review |
| human_review | `interrupt()`; after resume reads the committed human decision |
| finish | Ends the run with a simulated authorization flag, never a commercial side effect |

Sales, products and branches read the same immutable dataset snapshot and write different state fields, so they are independent. A list reducer (`operator.add`) merges their step records. A multi-source edge joins all branches before risk consolidation. Logs and histograms record actual node durations; the UI renders the recorded path, not a fabricated ideal path. A pending human node is explicitly marked as paused rather than completed.

The coordinator and graph edges bound the flow. A recursion limit of 16 and parallelism limit three provide additional guards. Queries have connection/statement timeouts. Permanent validation/business errors are not retried. Tenacity retries only recognized transient SQL states, at most three attempts with exponential jitter. n8n handles external HTTP retries separately; it never computes a risk threshold.

`thread_id` equals the unique execution UUID. Checkpoints use synchronous durability. The resume payload is only a signal; it cannot authorize anything. Startup reconciliation and the dedicated supervisor recovery endpoint handle supported crash windows described in the architecture document.

Potential future generative explanations would be optional decorations over already calculated evidence. They must never replace deterministic arithmetic, classification or authenticated human authority.

Reference: [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) and [persistence](https://docs.langchain.com/oss/python/langgraph/persistence).
