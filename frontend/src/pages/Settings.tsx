import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Save, ExternalLink } from "lucide-react";
import { api } from "../services/api";
import type { Dataset, Policy } from "../types";
import { date, ErrorPanel, number } from "../components/ui";
export function SettingsPage({
  dataset,
  role,
  dark,
  onTheme,
}: {
  dataset: Dataset;
  role: string;
  dark: boolean;
  onTheme: () => void;
}) {
  const [warning, setWarning] = useState(-10),
    [critical, setCritical] = useState(-20);
  const client = useQueryClient();
  const policies = useQuery({
    queryKey: ["policies"],
    queryFn: () => api<Policy[]>("/policies"),
  });
  const save = useMutation({
    mutationFn: () =>
      api<Policy>("/policies", {
        method: "POST",
        body: JSON.stringify({ warning, critical }),
      }),
    onSuccess: () => void client.invalidateQueries(),
  });
  return (
    <>
      <div className="two-columns settings-grid">
        <section className="panel padded">
          <span className="eyebrow">GOVERNANCE</span>
          <h2>Commercial risk policy</h2>
          <p>
            New versions apply to future executions. Existing evidence keeps its
            original policy snapshot.
          </p>
          <div className="note">
            Current: v{policies.data?.[0]?.version ?? "—"} · warning ≤{" "}
            {policies.data?.[0]?.warning ?? "—"}% · critical ≤{" "}
            {policies.data?.[0]?.critical ?? "—"}%
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            <div className="form-grid">
              <label>
                Warning threshold (%)
                <input
                  type="number"
                  min={-100}
                  max={-0.01}
                  step="0.01"
                  value={warning}
                  onChange={(e) => setWarning(+e.target.value)}
                />
              </label>
              <label>
                Critical threshold (%)
                <input
                  type="number"
                  min={-100}
                  max={-0.01}
                  step="0.01"
                  value={critical}
                  onChange={(e) => setCritical(+e.target.value)}
                />
              </label>
            </div>
            {save.error && <ErrorPanel error={save.error} />}
            <button
              className="button primary"
              disabled={
                role !== "supervisor" || save.isPending || critical >= warning
              }
            >
              <Save size={16} />
              Create policy version
            </button>
            {save.isSuccess && (
              <p className="success-message" role="status">
                Policy version saved and audited.
              </p>
            )}
            {role !== "supervisor" && (
              <p>Supervisor access is required to change policy.</p>
            )}
          </form>
        </section>
        <section className="panel padded">
          <span className="eyebrow">WORKSPACE</span>
          <h2>Display & automation</h2>
          <div className="setting-row">
            <div>
              <strong>Color theme</strong>
              <p>Stored in this browser</p>
            </div>
            <button className="button secondary" onClick={onTheme}>
              {dark ? "Use light mode" : "Use dark mode"}
            </button>
          </div>
          <div className="setting-row">
            <div>
              <strong>Scheduled analysis</strong>
              <p>
                Disabled in the supplied workflows. Enable deliberately in n8n
                after testing.
              </p>
            </div>
            <a
              href="http://localhost:5678"
              target="_blank"
              rel="noreferrer"
              className="icon-button"
              aria-label="Open n8n"
            >
              <ExternalLink size={18} />
            </a>
          </div>
          <div className="note">
            This is a local portfolio system. All commercial actions are
            simulated. No external accounts or language models are required.
          </div>
        </section>
      </div>
      <section className="panel padded">
        <span className="eyebrow">DATA INTEGRITY</span>
        <h2>
          {dataset.mode === "demo"
            ? "Independent synthetic dataset"
            : "Original historical dataset"}
        </h2>
        <div className="data-grid">
          <div>
            <span>Records</span>
            <strong>{number(dataset.rows)}</strong>
          </div>
          <div>
            <span>Products</span>
            <strong>{dataset.products}</strong>
          </div>
          <div>
            <span>Branches</span>
            <strong>{dataset.branches}</strong>
          </div>
          <div>
            <span>Missing combinations</span>
            <strong>{dataset.missing_combinations}</strong>
          </div>
        </div>
        <p>{dataset.limitations.join(" ")}</p>
        <dl>
          <dt>Source SHA256</dt>
          <dd className="mono break">{dataset.source_sha256}</dd>
          <dt>Reporting formats</dt>
          <dd>
            {Object.entries(dataset.formats)
              .map(([k, v]) => `${k}: ${v} records`)
              .join(" · ")}
          </dd>
        </dl>
      </section>
      <section className="panel">
        <div className="panel-head">
          <h2>Policy history</h2>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Version</th>
                <th>Warning</th>
                <th>Critical</th>
                <th>Responsible</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {policies.data?.map((p) => (
                <tr key={p.version}>
                  <td>v{p.version}</td>
                  <td>≤ {p.warning}%</td>
                  <td>≤ {p.critical}%</td>
                  <td>{p.actor}</td>
                  <td>{p.created_at && date(p.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
