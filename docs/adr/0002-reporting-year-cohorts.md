# ADR 0002: matched reporting-year comparisons

Status: accepted.

The actual source contains M/B/S/C rows with different temporal granularities, missing combinations, an E/C dictionary discrepancy and seasons crossing calendar years. The older PDF's storage convention conflicts with the supplied CSV.

Import the explicit consecutive-column CSV profile, normalize E/C, validate active cells and retain exact period values. Never allocate season/semester totals to months. Show observed reporting-year totals separately from comparisons of compatible common branch/product pairs. Expose excluded keys and coverage.

Trade-off: comparisons discard unmatched observations instead of pretending coverage changes are sales declines. No monthly claims can be made for the full mixed-granularity dataset.
