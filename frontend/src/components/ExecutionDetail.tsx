import { useQuery } from "@tanstack/react-query";
import { Check, Clock3, GitBranch, ShieldCheck } from "lucide-react";
import { api } from "../services/api";
import type { Audit, Collection, Execution } from "../types";
import { Badge, Change, date, ErrorPanel, Loading, Modal, number } from "./ui";

export function ExecutionDetail({
  id,
  onClose,
}: {
  id: string;
  onClose: () => void;
}) {
  const q = useQuery({
    queryKey: ["execution", id],
    queryFn: () => api<Execution>(`/executions/${id}`),
  });
  const audit = useQuery({
    queryKey: ["audit", id],
    queryFn: () =>
      api<Collection<Audit>>(`/audit?execution_id=${id}&page_size=100`),
  });
  const e = q.data;
  return (
    <Modal title="Analysis evidence" onClose={onClose} wide>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorPanel error={q.error} />
      ) : (
        e && (
          <>
            <div className="detail-heading">
              <div>
                <span className="eyebrow">EXECUTION / {id.slice(0, 8)}</span>
                <h2>{e.producto || "Commercial analysis"}</h2>
                <p>
                  {date(e.fecha)} · {e.request.anio_base} →{" "}
                  {e.request.anio_actual}
                </p>
              </div>
              <div className="badge-stack">
                <Badge status={e.estado} />
                <Badge status={e.approval_status} />
              </div>
            </div>
            <div className="detail-metrics">
              <div>
                <span>Matched baseline</span>
                <strong>
                  {number(e.sales?.base_total)} <small>m</small>
                </strong>
              </div>
              <div>
                <span>Matched current</span>
                <strong>
                  {number(e.sales?.current_total)} <small>m</small>
                </strong>
              </div>
              <div>
                <span>Network change</span>
                <Change value={e.variacion} />
              </div>
              <div>
                <span>Coverage</span>
                <strong>{number(e.sales?.coverage_pct)}%</strong>
              </div>
            </div>
            <div className="recommendation">
              <ShieldCheck size={22} />
              <div>
                <strong>Proposed recommendation</strong>
                <p>{e.recomendacion || e.error}</p>
                <small>
                  Commercial authorization is simulated. No inventory, pricing
                  or orders are changed.
                </small>
              </div>
            </div>
            <div className="section-title">
              <h3>
                <GitBranch size={16} /> Actual graph path
              </h3>
              <span>{e.duracion_ms} ms recorded processing</span>
            </div>
            <div className="graph-path">
              {e.steps.map((s) => (
                <div className="graph-node" key={s.node}>
                  <Check size={14} />
                  <strong>{s.node.replace("_", " ")}</strong>
                  <small>{s.duration_ms.toFixed(2)} ms</small>
                </div>
              ))}
              {e.approval_status === "PENDING" && (
                <div className="graph-node waiting">
                  <Clock3 size={14} />
                  <strong>Human review</strong>
                  <small>Checkpoint paused</small>
                </div>
              )}
            </div>
            <div className="detail-columns">
              <section>
                <h3>Product evidence</h3>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Matched change</th>
                        <th>Coverage</th>
                        <th>Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {e.products?.map((p) => (
                        <tr key={p.id}>
                          <td>
                            <strong>{p.name}</strong>
                            <small>{p.id}</small>
                          </td>
                          <td>
                            <Change value={p.variation} />
                          </td>
                          <td>{p.coverage_pct}%</td>
                          <td>
                            <Badge status={p.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
              <section>
                <h3>Branch evidence</h3>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Branch</th>
                        <th>Matched change</th>
                        <th>Coverage</th>
                        <th>Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {e.branches?.map((b) => (
                        <tr key={b.id}>
                          <td>{b.name}</td>
                          <td>
                            <Change value={b.variation} />
                          </td>
                          <td>{b.coverage_pct}%</td>
                          <td>
                            <Badge status={b.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
            <div className="detail-columns">
              <section>
                <h3>Evidence & policy</h3>
                <dl>
                  <dt>Technical state</dt>
                  <dd>
                    <Badge status={e.technical_status} />
                  </dd>
                  <dt>Policy snapshot</dt>
                  <dd>
                    v{e.policy.version} · warning ≤ {e.policy.warning}% ·
                    critical ≤ {e.policy.critical}%
                  </dd>
                  <dt>Matched / excluded pairs</dt>
                  <dd>
                    {e.sales?.matched_pairs ?? "—"} /{" "}
                    {e.sales?.excluded_pairs ?? "—"}
                  </dd>
                  <dt>Risk basis</dt>
                  <dd>
                    Highest risk across the network and its selected segments
                  </dd>
                  <dt>Trace ID</dt>
                  <dd className="mono break">{e.trace_id}</dd>
                  <dt>Dataset snapshot</dt>
                  <dd className="mono break">{e.dataset_id.slice(0, 20)}…</dd>
                </dl>
              </section>
              <section>
                <h3>Audit trail</h3>
                <div className="audit-list">
                  {audit.data?.items.map((a) => (
                    <div key={a.id}>
                      <i />
                      <div>
                        <strong>{a.event.replaceAll("_", " ")}</strong>
                        <small>
                          {a.actor} · {date(a.created_at)}
                        </small>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
            <div className="note">{e.limitations?.join(" ")}</div>
          </>
        )
      )}
    </Modal>
  );
}
