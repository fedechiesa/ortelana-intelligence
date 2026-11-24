import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, queryString } from "../services/api";
import type { Analytics, Collection, Dataset, Filters } from "../types";
import { SalesChart, BranchChart } from "../components/Charts";
import { Badge, Change, ErrorPanel, Loading, number } from "../components/ui";
export function Sales({ dataset }: { dataset: Dataset }) {
  const [filters, setFilters] = useState<Filters>({
    anio_base: dataset.years.at(-2)!,
    anio_actual: dataset.years.at(-1)!,
  });
  const q = useQuery({
    queryKey: ["analytics", filters],
    queryFn: () => api<Analytics>(`/analytics?${queryString(filters)}`),
  });
  const products = useQuery({
    queryKey: ["products"],
    queryFn: () => api<Collection<{ id: string; name: string }>>("/products"),
  });
  const branches = useQuery({
    queryKey: ["branches"],
    queryFn: () => api<{ id: number; name: string }[]>("/branches"),
  });
  return (
    <>
      <div className="filter-bar">
        <label>
          Baseline
          <select
            value={filters.anio_base}
            onChange={(e) =>
              setFilters({ ...filters, anio_base: +e.target.value })
            }
          >
            {dataset.years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>
        </label>
        <label>
          Current
          <select
            value={filters.anio_actual}
            onChange={(e) =>
              setFilters({ ...filters, anio_actual: +e.target.value })
            }
          >
            {dataset.years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>
        </label>
        <label>
          Branch
          <select
            value={filters.sucursal_id || ""}
            onChange={(e) =>
              setFilters({
                ...filters,
                sucursal_id: e.target.value ? +e.target.value : undefined,
              })
            }
          >
            <option value="">All branches</option>
            {branches.data?.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Product
          <select
            value={filters.producto_id || ""}
            onChange={(e) =>
              setFilters({
                ...filters,
                producto_id: e.target.value || undefined,
              })
            }
          >
            <option value="">All products</option>
            {products.data?.items.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorPanel error={q.error} retry={() => void q.refetch()} />
      ) : (
        q.data && (
          <>
            <div className="analytics-summary">
              <div>
                <span>Matched baseline</span>
                <strong>{number(q.data.summary.base_total)} m</strong>
              </div>
              <div>
                <span>Matched current</span>
                <strong>{number(q.data.summary.current_total)} m</strong>
              </div>
              <div>
                <span>Matched change</span>
                <Change value={q.data.summary.variation} />
              </div>
              <div>
                <span>Comparable pairs</span>
                <strong>
                  {q.data.summary.matched_pairs}{" "}
                  <small>· {q.data.summary.coverage_pct}% coverage</small>
                </strong>
              </div>
            </div>
            <div className="two-columns">
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h2>Historical volume</h2>
                    <p>Observed reporting-year totals; coverage can vary</p>
                  </div>
                </div>
                <SalesChart data={q.data.trends} />
              </section>
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h2>Branches</h2>
                    <p>Current observed volume</p>
                  </div>
                </div>
                <BranchChart data={q.data.branches} />
              </section>
            </div>
            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Product ranking</h2>
                  <p>
                    Ordered by current observed volume. Risk uses comparable
                    pairs.
                  </p>
                </div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Line</th>
                      <th>Observed current</th>
                      <th>Matched baseline</th>
                      <th>Matched current</th>
                      <th>Variation</th>
                      <th>Coverage</th>
                      <th>Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {q.data.products.map((p) => (
                      <tr key={p.id}>
                        <td>
                          <strong>{p.name}</strong>
                          <small>{p.id}</small>
                        </td>
                        <td>{p.line}</td>
                        <td>{number(p.observed_current)} m</td>
                        <td>{number(p.base_total)} m</td>
                        <td>{number(p.current_total)} m</td>
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
            <div className="note">
              {q.data.summary.excluded_pairs} pairs excluded from the
              comparison. Missing records are unknown, not zero. Seasons retain
              their original reporting-year basis.
            </div>
          </>
        )
      )}
    </>
  );
}
