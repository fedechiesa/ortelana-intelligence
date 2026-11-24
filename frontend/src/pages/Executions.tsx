import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ArrowUpRight, ChevronLeft, ChevronRight } from "lucide-react";
import { api, queryString } from "../services/api";
import type { Collection, Execution } from "../types";
import {
  Badge,
  Change,
  date,
  Empty,
  ErrorPanel,
  Loading,
} from "../components/ui";
export function Executions({ onDetail }: { onDetail: (id: string) => void }) {
  const [page, setPage] = useState(1),
    [status, setStatus] = useState(""),
    [risk, setRisk] = useState("");
  const q = useQuery({
    queryKey: ["executions", page, status, risk],
    queryFn: () =>
      api<Collection<Execution>>(
        `/executions?${queryString({ page, status, risk, page_size: 15 })}`,
      ),
    refetchInterval: 15000,
  });
  return (
    <>
      <div className="filter-bar">
        <label>
          Technical state
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All states</option>
            {[
              "COMPLETED",
              "WAITING_REVIEW",
              "ERROR",
              "RUNNING",
              "RESUMING",
            ].map((s) => (
              <option key={s} value={s}>
                {s.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <label>
          Commercial risk
          <select
            value={risk}
            onChange={(e) => {
              setRisk(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All risks</option>
            {["NORMAL", "ADVERTENCIA", "CRITICO", "SIN_BASE"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <span className="filter-note">
          {q.data?.total ?? "—"} executions · refreshed every 15s
        </span>
      </div>
      <section className="panel">
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorPanel error={q.error} retry={() => void q.refetch()} />
        ) : q.data?.items.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Execution / date</th>
                  <th>Scope</th>
                  <th>Risk</th>
                  <th>Technical state</th>
                  <th>Change</th>
                  <th>Processing</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {q.data.items.map((e) => (
                  <tr key={e.ejecucion_id}>
                    <td>
                      <button
                        className="table-link mono"
                        onClick={() => onDetail(e.ejecucion_id)}
                      >
                        {e.ejecucion_id.slice(0, 8)}
                      </button>
                      <small>{date(e.fecha)}</small>
                    </td>
                    <td>
                      <strong>{e.producto || "Analysis"}</strong>
                      <small>
                        {e.request.anio_base} → {e.request.anio_actual} ·{" "}
                        {e.request.sucursal_id
                          ? `Branch ${e.request.sucursal_id}`
                          : "All branches"}
                      </small>
                    </td>
                    <td>
                      {e.business_status ? (
                        <Badge status={e.business_status} />
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td>
                      <Badge status={e.technical_status} />
                    </td>
                    <td>
                      <Change value={e.variacion} />
                    </td>
                    <td>
                      {e.duracion_ms} ms
                      <small>{e.steps.length} completed nodes</small>
                    </td>
                    <td>
                      <button
                        className="icon-button"
                        aria-label={`View execution ${e.ejecucion_id.slice(0, 8)}`}
                        onClick={() => onDetail(e.ejecucion_id)}
                      >
                        <ArrowUpRight size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="No executions found">
            Run an analysis or adjust the filters.
          </Empty>
        )}
        <div className="pagination">
          <span>
            Page {page} · {q.data?.total ?? 0} records
          </span>
          <div>
            <button
              className="icon-button"
              aria-label="Previous page"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              <ChevronLeft size={18} />
            </button>
            <button
              className="icon-button"
              aria-label="Next page"
              disabled={!q.data || page * 15 >= q.data.total}
              onClick={() => setPage(page + 1)}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </section>
    </>
  );
}
