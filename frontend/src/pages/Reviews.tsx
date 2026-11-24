import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Check, ShieldCheck, X } from "lucide-react";
import { api } from "../services/api";
import type { Collection, Decision, Execution } from "../types";
import {
  Badge,
  Change,
  date,
  Empty,
  ErrorPanel,
  Loading,
  Modal,
  number,
} from "../components/ui";
export function Reviews({
  role,
  onDetail,
}: {
  role: string;
  onDetail: (id: string) => void;
}) {
  const client = useQueryClient();
  const [selected, setSelected] = useState<Execution | null>(null),
    [comment, setComment] = useState(""),
    [page, setPage] = useState(1);
  const q = useQuery({
    queryKey: ["reviews", page],
    queryFn: () =>
      api<Collection<Execution>>(`/reviews?page=${page}&page_size=10`),
    refetchInterval: 10000,
  });
  const history = useQuery({
    queryKey: ["decisions"],
    queryFn: () => api<Collection<Decision>>("/decisions"),
  });
  const decide = useMutation({
    mutationFn: (decision: string) =>
      api<Execution>("/decision", {
        method: "POST",
        body: JSON.stringify({
          ejecucion_id: selected!.ejecucion_id,
          decision,
          comentario: comment,
        }),
      }),
    onSuccess: () => {
      setSelected(null);
      setComment("");
      void client.invalidateQueries();
    },
  });
  return (
    <>
      <div className="review-banner">
        <ShieldCheck size={25} />
        <div>
          <strong>Human authority is part of the workflow.</strong>
          <p>
            Review the evidence before authorizing a simulated recommendation.
            Decisions are final and linked to your authenticated identity.
          </p>
        </div>
        <Badge status={role === "supervisor" ? "APPROVED" : "PENDING"} />
      </div>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorPanel error={q.error} />
      ) : q.data?.items.length ? (
        <div className="review-grid">
          {q.data.items.map((e) => (
            <section className="panel review-card" key={e.ejecucion_id}>
              <div className="panel-head">
                <Badge status={e.estado} />
                <span className="mono">{e.ejecucion_id.slice(0, 8)}</span>
              </div>
              <h2>{e.producto}</h2>
              <p>{e.recomendacion}</p>
              <div className="review-evidence">
                <div>
                  <span>Network change</span>
                  <Change value={e.variacion} />
                </div>
                <div>
                  <span>Coverage</span>
                  <strong>{number(e.sales?.coverage_pct)}%</strong>
                </div>
                <div>
                  <span>Policy</span>
                  <strong>v{e.policy.version}</strong>
                </div>
              </div>
              <small>
                {date(e.fecha)} · {e.request.anio_base} →{" "}
                {e.request.anio_actual}
              </small>
              <footer>
                <button
                  className="button secondary"
                  onClick={() => onDetail(e.ejecucion_id)}
                >
                  Inspect evidence
                </button>
                <button
                  className="button primary"
                  disabled={role !== "supervisor"}
                  onClick={() => {
                    decide.reset();
                    setSelected(e);
                  }}
                >
                  Review decision
                </button>
              </footer>
              {role !== "supervisor" && (
                <small>
                  Supervisor sign-in is required to approve or reject.
                </small>
              )}
            </section>
          ))}
        </div>
      ) : (
        <section className="panel">
          <Empty title="Nothing waiting for review">
            Critical findings will appear here after their evidence is
            persisted.
          </Empty>
        </section>
      )}
      <div className="pagination">
        <span>{q.data?.total ?? 0} pending reviews</span>
        <div>
          <button
            className="button secondary"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </button>
          <button
            className="button secondary"
            disabled={!q.data || page * 10 >= q.data.total}
            onClick={() => setPage(page + 1)}
          >
            Next
          </button>
        </div>
      </div>
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Decision history</h2>
            <p>Authenticated, immutable human decisions · latest 20</p>
          </div>
        </div>
        {history.error ? (
          <ErrorPanel error={history.error} />
        ) : history.data?.items.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Execution</th>
                  <th>Decision</th>
                  <th>Responsible</th>
                  <th>Comment</th>
                  <th>Recorded</th>
                </tr>
              </thead>
              <tbody>
                {history.data.items.map((d) => (
                  <tr key={d.execution_id}>
                    <td>
                      <button
                        className="table-link mono"
                        onClick={() => onDetail(d.execution_id)}
                      >
                        {d.execution_id.slice(0, 8)}
                      </button>
                    </td>
                    <td>
                      <Badge
                        status={
                          d.decision === "APROBADO" ? "APPROVED" : "REJECTED"
                        }
                      />
                    </td>
                    <td>{d.actor}</td>
                    <td>{d.comment}</td>
                    <td>{date(d.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="No decisions recorded" />
        )}
      </section>
      {selected && (
        <Modal
          title="Record a human decision"
          onClose={() => setSelected(null)}
        >
          <p className="modal-copy">
            You are deciding on <strong>{selected.producto}</strong>, execution{" "}
            <code>{selected.ejecucion_id.slice(0, 8)}</code>. This decision is
            final.
          </p>
          <div className="note">
            Policy v{selected.policy.version} · Critical threshold ≤{" "}
            {selected.policy.critical}% · Matched change{" "}
            {selected.variacion?.toFixed(2) ?? "unknown"}%
          </div>
          <label>
            Decision comment
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              minLength={3}
              maxLength={2000}
              placeholder="Explain your decision and the evidence you reviewed"
              autoFocus
            />
          </label>
          {decide.error && <ErrorPanel error={decide.error} />}
          <footer className="modal-actions">
            <button
              className="button danger"
              disabled={comment.trim().length < 3 || decide.isPending}
              onClick={() => decide.mutate("RECHAZADO")}
            >
              <X size={16} />
              Reject
            </button>
            <button
              className="button primary"
              disabled={comment.trim().length < 3 || decide.isPending}
              onClick={() => decide.mutate("APROBADO")}
            >
              <Check size={16} />
              Approve simulation
            </button>
          </footer>
        </Modal>
      )}
    </>
  );
}
