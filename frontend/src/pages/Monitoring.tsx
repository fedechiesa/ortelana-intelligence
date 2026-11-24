import { useQuery } from "@tanstack/react-query";
import { ExternalLink, Activity, Database, GitBranch } from "lucide-react";
import { api } from "../services/api";
import type { Collection, Execution, Indicators } from "../types";
import { Badge, date, Empty, ErrorPanel, number } from "../components/ui";
export function Monitoring({
  indicators,
  onDetail,
}: {
  indicators: Indicators;
  onDetail: (id: string) => void;
}) {
  const ready = useQuery({
    queryKey: ["ready"],
    queryFn: () =>
      api<{ status: string; database: string; checkpoint: string }>(
        "/health/ready",
      ),
    refetchInterval: 10000,
  });
  const errors = useQuery({
    queryKey: ["errors"],
    queryFn: () => api<Collection<Execution>>("/executions?status=ERROR"),
  });
  return (
    <>
      <div className="system-grid">
        {[
          {
            name: "API readiness",
            value: ready.data?.status || "Unavailable",
            icon: Activity,
          },
          {
            name: "PostgreSQL",
            value: ready.data?.database || "Unknown",
            icon: Database,
          },
          {
            name: "Graph checkpointer",
            value: ready.data?.checkpoint || "Unknown",
            icon: GitBranch,
          },
        ].map((s) => (
          <section className="panel service-card" key={s.name}>
            <s.icon size={24} />
            <h3>{s.name}</h3>
            <span
              className={`service-state ${ready.isSuccess ? "online" : ""}`}
            >
              <i />
              {s.value}
            </span>
          </section>
        ))}
      </div>
      {ready.error && <ErrorPanel error={ready.error} />}
      <div className="analytics-summary">
        <div>
          <span>Total executions</span>
          <strong>{number(indicators.executions)}</strong>
        </div>
        <div>
          <span>Success / awaiting review</span>
          <strong>
            {indicators.success_rate == null
              ? "—"
              : `${indicators.success_rate}%`}
          </strong>
        </div>
        <div>
          <span>Average processing</span>
          <strong>{number(indicators.average_duration_ms)} ms</strong>
        </div>
        <div>
          <span>Technical errors</span>
          <strong>{indicators.errors}</strong>
        </div>
      </div>
      <div className="two-columns">
        <a
          className="panel integration-link"
          href="http://localhost:3000/d/ortelana-operations"
          target="_blank"
          rel="noreferrer"
        >
          <span className="integration-icon orange">G</span>
          <div>
            <h2>Grafana</h2>
            <p>Operational monitoring & business intelligence</p>
            <small>Real PostgreSQL queries and Prometheus time series</small>
          </div>
          <ExternalLink size={18} />
        </a>
        <a
          className="panel integration-link"
          href="http://localhost:5678"
          target="_blank"
          rel="noreferrer"
        >
          <span className="integration-icon coral">n8n</span>
          <div>
            <h2>Automation workspace</h2>
            <p>Manual runs and explicitly enabled schedules</p>
            <small>Local owner setup and header credential required</small>
          </div>
          <ExternalLink size={18} />
        </a>
      </div>
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Recent technical errors</h2>
            <p>Commercial risk is tracked separately</p>
          </div>
        </div>
        {errors.error ? (
          <ErrorPanel error={errors.error} />
        ) : errors.data?.items.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Execution</th>
                  <th>Recorded</th>
                  <th>Status</th>
                  <th>Sanitized error</th>
                </tr>
              </thead>
              <tbody>
                {errors.data.items.map((e) => (
                  <tr key={e.ejecucion_id}>
                    <td>
                      <button
                        className="table-link mono"
                        onClick={() => onDetail(e.ejecucion_id)}
                      >
                        {e.ejecucion_id.slice(0, 8)}
                      </button>
                    </td>
                    <td>{date(e.fecha)}</td>
                    <td>
                      <Badge status="ERROR" />
                    </td>
                    <td>{e.error}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="No recorded technical errors">
            Execution failures will appear here with a trace ID and recovery
            controls in the API.
          </Empty>
        )}
      </section>
    </>
  );
}
