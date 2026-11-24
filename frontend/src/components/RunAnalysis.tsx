import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Play, ShieldCheck } from "lucide-react";
import { api } from "../services/api";
import type { Collection, Dataset, Execution, Filters } from "../types";
import { ErrorPanel, Modal } from "./ui";

export function RunAnalysis({
  dataset,
  onClose,
  onSuccess,
}: {
  dataset: Dataset;
  onClose: () => void;
  onSuccess: (id: string) => void;
}) {
  const [filters, setFilters] = useState<Filters>({
    anio_base: dataset.years.at(-2)!,
    anio_actual: dataset.years.at(-1)!,
  });
  const [key, setKey] = useState(() => crypto.randomUUID());
  const client = useQueryClient();
  const products = useQuery({
    queryKey: ["products"],
    queryFn: () => api<Collection<{ id: string; name: string }>>("/products"),
  });
  const branches = useQuery({
    queryKey: ["branches"],
    queryFn: () => api<{ id: number; name: string }[]>("/branches"),
  });
  function change(next: Partial<Filters>) {
    setFilters({ ...filters, ...next });
    setKey(crypto.randomUUID());
  }
  const run = useMutation({
    mutationFn: () =>
      api<Execution>("/analizar", {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify(filters),
      }),
    onSuccess: (e) => {
      void client.invalidateQueries();
      onSuccess(e.ejecucion_id);
    },
  });
  return (
    <Modal title="Run a business analysis" onClose={onClose}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          run.mutate();
        }}
      >
        <div className="form-intro">
          <div className="intro-icon">
            <Play size={22} />
          </div>
          <p>
            Compare reporting years with deterministic agents. Critical findings
            pause for human review.
          </p>
        </div>
        <div className="form-grid">
          <label>
            Baseline year
            <select
              value={filters.anio_base}
              onChange={(e) => change({ anio_base: +e.target.value })}
            >
              {dataset.years.map((y) => (
                <option key={y}>{y}</option>
              ))}
            </select>
          </label>
          <label>
            Current year
            <select
              value={filters.anio_actual}
              onChange={(e) => change({ anio_actual: +e.target.value })}
            >
              {dataset.years.map((y) => (
                <option key={y}>{y}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Product
          <select
            value={filters.producto_id || ""}
            onChange={(e) =>
              change({ producto_id: e.target.value || undefined })
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
        <label>
          Branch
          <select
            value={filters.sucursal_id || ""}
            onChange={(e) =>
              change({
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
        <div className="note">
          <ShieldCheck size={16} />
          {dataset.mode === "demo"
            ? "Synthetic demo data. Results are simulated commercial scenarios."
            : "Original historical data. Reporting years are not a live sales feed."}
        </div>
        {run.error && <ErrorPanel error={run.error} />}
        <footer className="modal-actions">
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="button primary"
            disabled={run.isPending || filters.anio_actual <= filters.anio_base}
          >
            {run.isPending ? "Agents are analysing…" : "Start analysis"}
            <ArrowRight size={16} />
          </button>
        </footer>
      </form>
    </Modal>
  );
}
